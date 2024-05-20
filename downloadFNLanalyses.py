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
LOGIN_URL = 'https://rda.ucar.edu/cgi-bin/login'
DATASET_URL = 'https://rda.ucar.edu/ds083.3/'


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
        status_forcelist=[408, 429, 500, 502, 503, 504],  # HTTP status codes to retry on
    )
    # Create an HTTP adapter with the retry strategy and mount it to session
    adapter = HTTPAdapter(max_retries=retry_strategy)

    # Create a new session object
    session = requests.Session()
    session.mount('http://', adapter)
    session.mount('https://', adapter)


    return session


def authenticate(session: requests.Session, orcid: str, api_token: str):
    """
    Authenticate with the RDA API

    This will set some cookies on the session to allow for downloading data

    Args:
        session:
            Session to authenticate
        orcid:
            ORCID for the user
        api_token:
            API token for the user
    """

    values = {'orcid_id': orcid, 'api_token': api_token, 'action': 'tokenlogin'}
    ret = session.post(LOGIN_URL,data=values)
    if ret.status_code != 200:
        print('Bad Authentication')
        print(ret.text)
        raise RuntimeError("Invalid RDA credentials")

def download_file(session: requests.Session, target_dir: str, url: str):
    """
    Download a file from a URL

    Args:
        session:
            Authenticated session
        target_dir:
            Directory to save the downloaded file
        url:
            URL of the file to download

    Returns:
        Path to the downloaded file
    """
    try:
        with session.get(url, stream=True) as r:
            r.raise_for_status()
            filename = os.path.join(target_dir, os.path.basename(url))
            with open(filename, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            return filename
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Error downloading {url}") from e


def downloadFNL(orcid: str, api_token: str, targetDir: str, times: list[datetime.datetime]) -> list[str]:
    """
    Download NCEP GDAS/FNL 0.25 Degree Global Tropospheric Analyses and Forecast Grids, ds083.3

    DOI: 10.5065/D65Q4T4Z

    Args:
        orcid:
            orcid for which you have an account on rda.ucar.edu / CISL
        api_token:
            api_token for rda.ucar.edu / CISL
        targetDir:
            Directory where the data should be downloaded
        times:
            times to get analyses.

            Should be strictly at 00Z, 06Z, 12Z, 18Z and not before 2015-07-08

    Returns:
        List of downloaded files
    """
    print('downloading FNL data')

    # check that the target directory is indeed a directory
    assert os.path.exists(targetDir) and os.path.isdir(targetDir), (
            "Target directory {} not found...".format(targetDir))

    # Create a new session and authenticate
    print('authenticate credentials')
    session = create_session()
    authenticate(session, orcid, api_token)

    FNLstartDate = pytz.UTC.localize(datetime.datetime(2015,7,8,0,0,0))

    file_list = []
    for time in times:
        assert (time.hour % 6) == 0 and time.minute == 0 and time.second == 0,\
            "Analysis time should be staggered at 00Z, 06Z, 12Z, 18Z intervals"
        assert time > FNLstartDate, "Analysis times should not be before 2015-07-08"
        filepath = time.strftime('%Y/%Y%m/gdas1.fnl0p25.%Y%m%d%H.f00.grib2')
        file_list.append(filepath)

    downloaded_files = list(
        tqdm(
            Parallel(return_as="generator", n_jobs=N_JOBS)(
                delayed(download_file)(session, targetDir, DATASET_URL + filename)
                for filename in file_list
            ),
            total=len(file_list),
        )
    )

    return downloaded_files
