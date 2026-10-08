import f90nml

from setup_runs.wrf.namelists import apply_namelist_overrides, quilt_tasks

NAMELIST = """
&time_control
    history_interval = 5
    debug_level = 100
/
&namelist_quilt
    nio_tasks_per_group = 0
    nio_groups = 1
/
"""


def test_overrides_replace_existing_values():
    namelist = apply_namelist_overrides(
        f90nml.reads(NAMELIST), "&time_control debug_level = 0 /"
    )

    assert namelist["time_control"]["debug_level"] == 0
    assert namelist["time_control"]["history_interval"] == 5


def test_overrides_add_variables_and_groups():
    namelist = apply_namelist_overrides(
        f90nml.reads(NAMELIST),
        "&time_control history_begin_h = 12, use_netcdf_classic = .true. / &dynamics w_damping = 1 /",
    )

    assert namelist["time_control"]["history_begin_h"] == 12
    assert namelist["time_control"]["use_netcdf_classic"] is True
    assert namelist["dynamics"]["w_damping"] == 1


def test_overrides_survive_writing(tmp_path):
    namelist = apply_namelist_overrides(
        f90nml.reads(NAMELIST), "&namelist_quilt nio_tasks_per_group = 2 /"
    )
    namelist.write(tmp_path / "namelist.input")

    assert f90nml.read(tmp_path / "namelist.input")["namelist_quilt"]["nio_tasks_per_group"] == 2


def test_quilt_tasks():
    assert quilt_tasks(f90nml.reads(NAMELIST)) == 0
    assert quilt_tasks(f90nml.reads("&namelist_quilt nio_tasks_per_group = 2, nio_groups = 2 /")) == 4
    assert quilt_tasks(f90nml.reads("&namelist_quilt nio_tasks_per_group = 1 /")) == 1
    assert quilt_tasks(f90nml.reads("&time_control debug_level = 0 /")) == 0
