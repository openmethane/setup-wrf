#!/usr/bin/env python
"""
Download CAMS data on pressure levels

TODO: This was provided via email by Peter and needs to be cleaned up
"""

import cdsapi
import pathlib


OUTPUT_DIR = pathlib.Path("data/inputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


c = cdsapi.Client(url="https://ads.atmosphere.copernicus.eu/api/v2")

c.retrieve(
    'cams-global-reanalysis-eac4',
    {
        'variable': 'methane_chemistry',
        'pressure_level': [
            '1', '2', '3',
            '5', '7', '10',
            '20', '30', '50',
            '70', '100', '150',
            '200', '250', '300',
            '400', '500', '600',
            '700', '800', '850',
            '900', '925', '950',
            '1000',
        ],
        'date': '2023-12-01/2023-12-31',
        'time': [
            '00:00', '03:00', '06:00',
            '09:00', '12:00', '15:00',
            '18:00', '21:00',
        ],
        'format': 'netcdf',
    },
    OUTPUT_DIR / 'cams_eac4_4.nc')
