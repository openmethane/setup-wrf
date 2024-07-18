import pdb

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
