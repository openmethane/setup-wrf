import pdb

import f90nml

NAMELIST_PARAMS_TO_MATCH = [
    {
        "wrf_var": "max_dom",
        "wrf_group": "domains",
        "wps_var": "max_dom",
        "wps_group": "share",
    },
    {
        "wrf_var": "interval_seconds",
        "wrf_group": "time_control",
        "wps_var": "interval_seconds",
        "wps_group": "share",
    },
    {
        "wrf_var": "parent_id",
        "wrf_group": "domains",
        "wps_var": "parent_id",
        "wps_group": "geogrid",
    },
    {
        "wrf_var": "parent_grid_ratio",
        "wrf_group": "domains",
        "wps_var": "parent_grid_ratio",
        "wps_group": "geogrid",
    },
    {
        "wrf_var": "i_parent_start",
        "wrf_group": "domains",
        "wps_var": "i_parent_start",
        "wps_group": "geogrid",
    },
    {
        "wrf_var": "j_parent_start",
        "wrf_group": "domains",
        "wps_var": "j_parent_start",
        "wps_group": "geogrid",
    },
    {
        "wrf_var": "e_we",
        "wrf_group": "domains",
        "wps_var": "e_we",
        "wps_group": "geogrid",
    },
    {
        "wrf_var": "e_sn",
        "wrf_group": "domains",
        "wps_var": "e_sn",
        "wps_group": "geogrid",
    },
    {
        "wrf_var": "dx",
        "wrf_group": "domains",
        "wps_var": "dx",
        "wps_group": "geogrid",
    },
    {
        "wrf_var": "dy",
        "wrf_group": "domains",
        "wps_var": "dy",
        "wps_group": "geogrid",
    },
]


def validate_wrf_namelists(namelist_wps, namelist_wrf):
    ## check that the parameters do agree between the WRF and WPS namelists
    ## parameters that should agree for the WRF and WPS namelists

    print(
        "\t\tCheck for consistency between key parameters of the WRF and WPS namelists"
    )
    for param_dict in NAMELIST_PARAMS_TO_MATCH:
        value_wrf = namelist_wrf[param_dict["wrf_group"]][param_dict["wrf_var"]]
        value_wps = namelist_wps[param_dict["wps_group"]][param_dict["wps_var"]]
        ## the dx,dy variables need special treatment - they are handled differently in the two namelists
        if param_dict["wrf_var"] in ["dx", "dy"]:
            if namelist_wps["share"]["max_dom"] == 1:
                if isinstance(value_wrf, list):
                    assert (
                        value_wrf[0] == value_wps
                    ), "Mismatched values for variable {} between the WRF and WPS namelists".format(
                        param_dict["wrf_var"]
                    )
                else:
                    assert (
                        value_wrf == value_wps
                    ), "Mismatched values for variable {} between the WRF and WPS namelists".format(
                        param_dict["wrf_var"]
                    )
            else:
                expectedVal = [float(namelist_wps["geogrid"][param_dict["wps_var"]])]
                for idom in range(1, namelist_wps["share"]["max_dom"]):
                    try:
                        expectedVal.append(
                            expectedVal[-1]
                            / float(namelist_wps["geogrid"]["parent_grid_ratio"][idom])
                        )
                    except Exception:
                        pdb.set_trace()
                ##
                assert (
                    len(value_wrf) == len(expectedVal)
                ), "Mismatched length for variable {} between the WRF and WPS namelists".format(
                    param_dict["wrf_var"]
                )
                assert all(
                    [a == b for a, b in zip(value_wrf, expectedVal)]
                ), "Mismatched values for variable {} between the WRF and WPS namelists".format(
                    param_dict["wrf_var"]
                )
        else:
            assert (
                type(value_wrf) == type(value_wps)
            ), "Mismatched type for variable {} between the WRF and WPS namelists".format(
                param_dict["wrf_var"]
            )
            if isinstance(value_wrf, list):
                assert (
                    len(value_wrf) == len(value_wps)
                ), "Mismatched length for variable {} between the WRF and WPS namelists".format(
                    param_dict["wrf_var"]
                )
                assert all(
                    [a == b for a, b in zip(value_wrf, value_wps)]
                ), "Mismatched values for variable {} between the WRF and WPS namelists".format(
                    param_dict["wrf_var"]
                )
            else:
                assert (
                    value_wrf == value_wps
                ), "Mismatched values for variable {} between the WRF and WPS namelists".format(
                    param_dict["wrf_var"]
                )


def apply_namelist_overrides(namelist: f90nml.Namelist, overrides: str) -> f90nml.Namelist:
    """
    Set the values in `overrides` on a WRF namelist, adding any group or
    variable that is not already present.

    :param namelist: The namelist to change, which is modified in place
    :param overrides: Fortran namelist text, for example
        "&time_control history_begin_h = 12 / &namelist_quilt nio_tasks_per_group = 1 /"
    :return: The changed namelist
    """
    for group, values in f90nml.reads(overrides).items():
        if group not in namelist:
            namelist[group] = {}
        for name, value in values.items():
            namelist[group][name] = value

    return namelist


def quilt_tasks(namelist: f90nml.Namelist) -> int:
    """
    Number of MPI tasks WRF sets aside as I/O servers, which come out of the
    total given to mpirun rather than in addition to it.
    """
    quilt = namelist.get("namelist_quilt", {})
    return quilt.get("nio_tasks_per_group", 0) * quilt.get("nio_groups", 1)
