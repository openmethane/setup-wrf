import pytest
from pathlib import Path
import xarray as xr


@pytest.fixture
def root_dir() -> Path:
    return Path(__file__).parent.parent


def _clean_attrs(
    attrs: dict,
    excluded_fields: tuple[str, ...] = ("HISTORY", "CDATE", "CTIME", "WDATE", "WTIME"),
) -> dict:
    clean = {}
    for key, value in attrs.items():
        if key in excluded_fields:
            continue
        if hasattr(value, "item"):
            try:
                clean[key] = value.item()
            except ValueError:
                clean[key] = value.tolist()
        else:
            clean[key] = value

    return clean


def _extract_group(ds: xr.Dataset):
    return {
        "attrs": _clean_attrs(ds.attrs),
        "coords": dict(ds.coords),
        "dims": dict(ds.sizes),
        "variables": {
            k: {"attrs": dict(v.attrs), "dims": v.dims} for k, v in ds.variables.items()
        },
    }


@pytest.fixture
def compare_dataset(data_regression):
    """
    Check if the structure of xarray dataset/datatree instance has changed
    """

    def compare(ds: xr.Dataset | str, basename: str | None = None):
        if isinstance(ds, str) or isinstance(ds, Path):
            ds = xr.load_dataset(ds)

        if not hasattr(ds, "groups"):
            content = _extract_group(ds)
        else:
            content = {
                "groups": {k: _extract_group(ds[k]) for k in ds.groups},
                "attrs": _clean_attrs(ds.attrs),
            }
        data_regression.check(content, basename=basename)

    return compare
