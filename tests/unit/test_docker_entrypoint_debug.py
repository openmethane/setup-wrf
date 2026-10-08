"""
Tests for the temporary debugging entrypoint.

It wraps every command the image runs, meaning a mistake in it breaks
everything at once. These run it directly rather than through Docker: the
metrics it logs come from the cgroup it happens to be in, so the values are
whatever the test machine is doing, and only the shape of the output is
checked.
"""

import json
import pathlib
import signal
import subprocess
import time

import pytest

ENTRYPOINT = pathlib.Path(__file__).parents[2] / "scripts" / "docker-entrypoint-debug.sh"

METRICS_PREFIX = "[om-metrics] "


def run_entrypoint(*command, env=None, timeout=60):
    return subprocess.run(
        ["/bin/bash", str(ENTRYPOINT), *command],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        env={"PATH": "/usr/bin:/bin", "OM_METRICS_INTERVAL": "1", **(env or {})},
        timeout=timeout,
        check=False,
    )


def metrics(result) -> dict[str, dict]:
    """Metrics lines from a run, keyed by their event."""
    lines = [
        json.loads(line[len(METRICS_PREFIX):])
        for line in result.stdout.splitlines()
        if line.startswith(METRICS_PREFIX)
    ]
    return {line["event"]: line for line in lines}


def test_runs_the_command():
    result = run_entrypoint("echo", "hello")

    assert result.returncode == 0
    assert "hello" in result.stdout


def test_passes_on_the_exit_status():
    result = run_entrypoint("bash", "-c", "exit 7")

    assert result.returncode == 7
    assert metrics(result)["finish"]["exit_code"] == 7


def test_logs_metrics_for_a_successful_command():
    result = run_entrypoint("bash", "-c", "sleep 1")
    logged = metrics(result)

    assert logged["start"]["cpus_visible"] >= 1
    assert logged["finish"]["exit_code"] == 0
    assert logged["finish"]["wall_seconds"] >= 1


@pytest.mark.parametrize(
    "event, field",
    [
        ("start", "cpus_visible"),
        ("start", "cpus_physical"),
        ("start", "cpus_quota"),
        ("start", "memory_limit_bytes"),
        ("start", "chk_path_free_bytes"),
        ("finish", "exit_code"),
        ("finish", "wall_seconds"),
        ("finish", "cpu_seconds"),
        ("finish", "mean_parallelism"),
        ("finish", "cpu_throttled_seconds"),
        ("finish", "memory_anon_bytes"),
        ("finish", "memory_peak_bytes"),
        ("finish", "memory_events"),
        ("finish", "chk_path_free_bytes"),
    ],
)
def test_metrics_line_carries_every_field(event, field):
    # Values the kernel does not provide are logged as null, so that a field is
    # never simply missing.
    assert field in metrics(run_entrypoint("true"))[event]


def test_metrics_can_be_disabled():
    result = run_entrypoint("echo", "hello", env={"OM_METRICS": "0"})

    assert result.returncode == 0
    assert "hello" in result.stdout
    assert METRICS_PREFIX not in result.stdout


def test_reports_free_space_on_the_checkpoint_path(tmp_path):
    result = run_entrypoint("true", env={"CHK_PATH": str(tmp_path)})
    logged = metrics(result)

    assert logged["start"]["chk_path_free_bytes"] > 0
    assert logged["finish"]["chk_path_free_bytes"] > 0


def test_waits_for_the_command_to_finish_after_a_signal():
    """run-wrf.sh copies partial output off the scratch disk as it exits."""
    process = subprocess.Popen(
        [
            "/bin/bash",
            str(ENTRYPOINT),
            "bash",
            "-c",
            "sleep 30 & trap 'kill $!; sleep 2; echo cleaned up; exit 5' TERM; wait",
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        text=True,
        env={"PATH": "/usr/bin:/bin", "OM_METRICS_INTERVAL": "1"},
    )
    time.sleep(1)
    process.send_signal(signal.SIGTERM)
    stdout, _ = process.communicate(timeout=10)

    assert "cleaned up" in stdout
    assert process.returncode == 5


def test_stops_the_memory_sampler():
    """The sampler is a forked copy of the shell, and must not outlive it."""
    result = run_entrypoint("bash", "-c", "sleep 2", timeout=10)

    assert result.returncode == 0
