#!/bin/bash
# Temporary debugging entrypoint
#
# Wraps every command the image runs to log what a container cost in time, CPU
# and memory, so that the wrf-run and wrf-download_geog jobs can be sized from
# measured numbers rather than guessed. The output matches the [om-metrics]
# lines the openmethane image logs, so the same tooling reads both.
#
# This is here to gather data and is meant to be removed once it has. To remove
# it: delete this file and its test, and drop the ENTRYPOINT from the
# Dockerfile.

# Usage is read from the cgroup, which only cgroup v2 is handled for: anything
# it does not provide is reported as null rather than failing the run.
CGROUP=/sys/fs/cgroup
METRICS_ENABLED=${OM_METRICS:-1}
# Memory has to be sampled while the command runs, since by the time it exits
# its processes have handed everything back.
METRICS_INTERVAL=${OM_METRICS_INTERVAL:-30}

# The command is run in the background so that its usage can be measured, and a
# non-interactive shell gives a background command /dev/null as stdin. That
# would leave an interactive `docker run -it` session with nothing to read, so
# run those directly and unmeasured.
if [ "$METRICS_ENABLED" = "0" ] || [ -t 0 ]; then
  exec "$@"
fi

MEMORY_HIGH_WATER=$(mktemp 2>/dev/null)
SAMPLER_PID=""
CHILD_PID=""
START_SECONDS=""
START_CPU_USEC=""
START_THROTTLED_USEC=""


# First line of a cgroup file, or nothing if the kernel does not provide it.
cgroup_value() {
  [ -r "${CGROUP}/$1" ] && head -n 1 "${CGROUP}/$1"
}

# One key out of a "key value" cgroup file such as memory.stat.
cgroup_field() {
  [ -r "${CGROUP}/$1" ] && awk -v key="$2" '$1 == key { print $2; exit }' "${CGROUP}/$1"
}

# A JSON number, or null when the value could not be read.
number() {
  echo "${1:-null}"
}

# Microseconds as seconds, to two decimal places.
seconds() {
  [ -n "$1" ] && awk -v usec="$1" 'BEGIN { printf "%.2f", usec / 1000000 }'
}

# Difference between a counter now and where it started.
since_start() {
  local now=$1 start=$2
  [ -n "$now" ] && [ -n "$start" ] && echo $((now - start))
}

# Space left on the filesystem holding a path.
free_bytes() {
  [ -n "$1" ] && [ -d "$1" ] && df -B1 --output=avail "$1" 2>/dev/null | tail -n 1 | tr -d ' '
}


# Track the highest anonymous memory the cgroup reaches. This is what the
# processes actually need resident, as opposed to memory.peak, which counts the
# page cache that writing WRF output leaves behind.
sample_memory() {
  # A forked copy of this shell, so it carries the traps set below and must not
  # run them.
  trap - SIGTERM SIGINT SIGQUIT SIGHUP EXIT

  local high_water=0 anon
  while true; do
    anon=$(cgroup_field memory.stat anon)
    if [ -n "$anon" ] && [ "$anon" -gt "$high_water" ]; then
      high_water=$anon
      echo "$high_water" > "$MEMORY_HIGH_WATER"
    fi
    sleep "$METRICS_INTERVAL"
  done
}


log_start() {
  START_SECONDS=$SECONDS
  START_CPU_USEC=$(cgroup_field cpu.stat usage_usec)
  START_THROTTLED_USEC=$(cgroup_field cpu.stat throttled_usec)

  # Cores the CPU quota allows, which is not the number of CPUs visible: a
  # container limited with --cpus still sees every CPU on the machine.
  local quota period cpus_quota
  read -r quota period <<< "$(cgroup_value cpu.max)"
  [ "$quota" = "max" ] && quota=""
  [ -n "$quota" ] && cpus_quota=$(awk -v q="$quota" -v p="$period" 'BEGIN { printf "%.2f", q / p }')

  local memory_limit
  memory_limit=$(cgroup_value memory.max)
  [ "$memory_limit" = "max" ] && memory_limit=""

  # Physical cores behind the visible CPUs, which is half of them under SMT.
  local cpus_physical
  cpus_physical=$(awk -F': ' '
    /^physical id/ { socket = $2 }
    /^core id/ { cores[socket ":" $2] = 1 }
    END { if (length(cores)) print length(cores) }' /proc/cpuinfo 2>/dev/null)

  echo "[om-metrics] {\"event\": \"start\"\
, \"cpus_visible\": $(number "$(nproc 2>/dev/null)")\
, \"cpus_physical\": $(number "$cpus_physical")\
, \"cpus_quota\": $(number "$cpus_quota")\
, \"memory_limit_bytes\": $(number "$memory_limit")\
, \"chk_path_free_bytes\": $(number "$(free_bytes "${CHK_PATH:-}")")}"

  if [ -n "$MEMORY_HIGH_WATER" ] && [ -n "$(cgroup_field memory.stat anon)" ]; then
    sample_memory &
    SAMPLER_PID=$!
  fi
}

log_finish() {
  [ -n "$START_SECONDS" ] || return 0

  local wall cpu_usec cpu_seconds parallelism events
  wall=$((SECONDS - START_SECONDS))

  cpu_usec=$(since_start "$(cgroup_field cpu.stat usage_usec)" "$START_CPU_USEC")
  cpu_seconds=$(seconds "$cpu_usec")

  # Cores kept busy on average. Compare it against the ranks the run was given:
  # well below means they were idle, blocked on I/O, or throttled.
  [ -n "$cpu_usec" ] && [ "$wall" -gt 0 ] && parallelism=$(
    awk -v usec="$cpu_usec" -v wall="$wall" 'BEGIN { printf "%.2f", usec / 1000000 / wall }')

  # How often the cgroup was held at its memory limit, or had something killed.
  events=$(awk '{ printf "%s\"%s\": %s", (NR > 1 ? ", " : "{"), $1, $2 } END { print (NR ? "}" : "null") }' \
    "${CGROUP}/memory.events" 2>/dev/null)

  echo "[om-metrics] {\"event\": \"finish\"\
, \"exit_code\": $1\
, \"wall_seconds\": ${wall}\
, \"cpu_seconds\": $(number "$cpu_seconds")\
, \"mean_parallelism\": $(number "$parallelism")\
, \"cpu_throttled_seconds\": $(number "$(seconds "$(since_start "$(cgroup_field cpu.stat throttled_usec)" "$START_THROTTLED_USEC")")")\
, \"memory_anon_bytes\": $(number "$(head -n 1 "$MEMORY_HIGH_WATER" 2>/dev/null)")\
, \"memory_peak_bytes\": $(number "$(cgroup_value memory.peak)")\
, \"memory_events\": ${events:-null}\
, \"chk_path_free_bytes\": $(number "$(free_bytes "${CHK_PATH:-}")")}"
}


# Pass signals on to the command, which is waited on rather than run in the
# foreground so that they arrive while it is still running.
forward_signal() {
  [ -n "$CHILD_PID" ] && kill -TERM "$CHILD_PID" 2>/dev/null
}

on_exit() {
  local status=$?

  [ -n "$SAMPLER_PID" ] && kill "$SAMPLER_PID" 2>/dev/null
  log_finish "$status"
  rm -f "$MEMORY_HIGH_WATER"

  exit "$status"
}

trap forward_signal SIGTERM SIGINT SIGQUIT SIGHUP
trap on_exit EXIT


log_start

"$@" &
CHILD_PID=$!

# A trapped signal returns from wait before the command has finished, and
# exiting then would end the container while the command is still cleaning up,
# such as run-wrf.sh copying partial output off the scratch disk. Keep waiting
# until it has actually exited.
while kill -0 "$CHILD_PID" 2>/dev/null; do
  wait "$CHILD_PID"
done

# Bash keeps the status of a job it has already reaped.
wait "$CHILD_PID"
exit $?
