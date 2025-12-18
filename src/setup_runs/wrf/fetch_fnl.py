#################################################################
# This script was derived from code provided by CISL/rda.ucar.edu
# to download data from their archives
#
# Python Script to retrieve online Data files of 'ds083.3',
# This script uses the Python 'requests' module to download data.
#
# The original script suggests contacting
# rpconroy@ucar.edu (Riley Conroy) for further assistance.
#################################################################

import os

import requests
import datetime
import pytz

from joblib import Parallel, delayed
from tqdm import tqdm
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

N_JOBS = 8
DATASET_URL = "https://osdf-director.osg-htc.org/ncar/gdex/d083003/" # OSDF
# Backup data source
# DATASET_URL = "https://tds.gdex.ucar.edu/thredds/fileServer/files/g/d083003/" # THREDDS

FNL_START_DATE = pytz.UTC.localize(datetime.datetime(2015, 7, 8, 0, 0, 0))


def create_session() -> requests.Session:
    """
    Create a requests session

    This session will retry failed downloads up to 5 times

    Returns:
        New session with a backoff retry strategy
    """
    # Define the retry strategy
    retry_strategy = Retry(
        total=5,  # Maximum number of retries
        status_forcelist=[
            408,
            429,
            500,
            502,
            503,
            504,
        ],  # HTTP status codes to retry on
    )
    # Create an HTTP adapter with the retry strategy and mount it to session
    adapter = HTTPAdapter(max_retries=retry_strategy)

    # Create a new session object
    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


def download_file(session: requests.Session, target_dir: str, url: str) -> str:
    """
    Download a file from a URL

    Args:
        session:
            Authenticated session
        target_dir:
            Directory to save the downloaded file
        url:
            URL of the file to download

    Raises:
        RuntimeError: If the download fails

    Returns:
        Path to the downloaded file
    """
    filename = os.path.join(target_dir, os.path.basename(url))

    try:
        with session.get(url, stream=True) as r:
            r.raise_for_status()
            with open(filename, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            return filename
    except requests.exceptions.RequestException as e:
        if os.path.exists(filename):
            os.remove(filename)
        raise RuntimeError(f"Error downloading {url}") from e


def download_gdas_fnl_data(
    target_dir: str, download_dts: list[datetime.datetime]
) -> list[str]:
    """
    Download NCEP GDAS/FNL 0.25 Degree Global Tropospheric Analyses and Forecast Grids, ds083.3

    DOI: 10.5065/D65Q4T4Z

    If any of the files fail to download (after 5 retries),
    an exception will be raised and any other downloads will be aborted.
    If that occurs, any files being downloaded may be incomplete and should be deleted.

    We are downloading raw grib files without any subsetting.
    This operation does not require any RDA credentials.

    Args:
        target_dir:
            Directory where the data should be downloaded
        download_dts:
            Datetimes to download analysis data for

            Should be strictly at 00Z, 06Z, 12Z, 18Z and not before 2015-07-08

    Returns:
        List of downloaded files
    """
    print("downloading FNL data")

    # check that the target directory is indeed a directory
    assert os.path.exists(target_dir) and os.path.isdir(
        target_dir
    ), "Target directory {} not found...".format(target_dir)

    # Create a new session with a retry strategy
    session = create_session()

    file_list = []
    for time in download_dts:
        assert (
            (time.hour % 6) == 0 and time.minute == 0 and time.second == 0
        ), "Analysis time should be staggered at 00Z, 06Z, 12Z, 18Z intervals"
        assert time > FNL_START_DATE, "Analysis times should not be before 2015-07-08"
        file_path = time.strftime("%Y/%Y%m/gdas1.fnl0p25.%Y%m%d%H.f00.grib2")
        file_list.append(file_path)

    downloaded_files = list(
        tqdm(
            Parallel(return_as="generator", n_jobs=N_JOBS)(
                delayed(download_file)(session, target_dir, DATASET_URL + filename)
                for filename in file_list
            ),
            total=len(file_list),
        )
    )

    return downloaded_files
