#!/usr/bin/env bash
# Downloads the required WRF Geog data
#
# The output will be stored in `data/geog`
# with the geog data required by WRF being stored in `data/geog/WPS_GEOG`.
#
# Required datasets: Defaults + USGS

set -Eeuo pipefail

parse_params() {
  # default values of variables set from params
  low_res=0

  while :; do
    case "${1-}" in
#    -h | --help) usage ;;
    -v | --verbose) set -x ;;
    -l | --low-res) low_res=1 ;; # Download low res data
    -?*) die "Unknown option: $1" ;;
    *) break ;;
    esac
    shift
  done

  args=("$@")

  return 0
}

parse_params "$@"

output_dir="data/geog"

mkdir -p $output_dir

if ((low_res)); then
  echo "Downloading low resolution data"
  wget -N -nv https://www2.mmm.ucar.edu/wrf/src/wps_files/geog_low_res_mandatory.tar.gz -P $output_dir
  wget -N -nv https://www2.mmm.ucar.edu/wrf/src/wps_files/landuse_10m.tar.bz2 -P $output_dir
  tar -xf $output_dir/geog_low_res_mandatory.tar.gz -C $output_dir
	echo "Extracting data to $output_dir/WPS_GEOG..."
  tar -xf $output_dir/landuse_10m.tar.bz2 -C $output_dir/WPS_GEOG_LOW_RES
  if [[ -d $output_dir/WPS_GEOG ]]; then
    cp -r $output_dir/WPS_GEOG_LOW_RES/* $output_dir/WPS_GEOG/
    rm -r $output_dir/WPS_GEOG_LOW_RES
  else
    mv $output_dir/WPS_GEOG_LOW_RES $output_dir/WPS_GEOG
  fi
else
  echo "Downloading high resolution data"
  wget -N -nv https://www2.mmm.ucar.edu/wrf/src/wps_files/geog_high_res_mandatory.tar.gz -P $output_dir
	wget -N -nv https://www2.mmm.ucar.edu/wrf/src/wps_files/landuse_30s.tar.bz2 -P $output_dir
	echo "Extracting data to $output_dir/WPS_GEOG..."
	echo "This may take a few minutes"
	tar -xzf $output_dir/geog_high_res_mandatory.tar.gz -C $output_dir
	tar -xzf $output_dir/landuse_30s.tar.bz2 -C $output_dir/WPS_GEOG
fi
