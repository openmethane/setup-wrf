import os


from setup_runs.wrf.mpi_tasks import find_largest_factors, physical_cpu_count, safe_mpi_tasks


def test_safe_mpi_tasks():
    cases = [
        # grids too small
        (((1, 1), 32), 1),
        (((19, 19), 32), 1),

        # limited by grid size
        (((20, 20), 4), 4),
        (((20, 20), 8), 4),
        (((20, 20), 1024), 4),
        (((64, 64), 1024), 36),

        # cpu_count has similar-sized factors
        (((2000, 2000), 64), 64),
        (((2000, 2000), 63), 63),
        (((2000, 2000), 60), 60),

        # cpu_count factors are not ideal, scale down
        (((2000, 2000), 62), 60),
        (((2000, 2000), 61), 60),
    ]
    for args, expected in cases:
        assert safe_mpi_tasks(*args) == expected


def test_find_largest_factors():
    cases = [
        (3, (1, 3)),
        (4, (2, 2)),
        (6, (2, 3)),
        (8, (2, 4)),
        (16, (4, 4)),
        (17, (1, 17)),
        (18, (3, 6)),
        (64, (8, 8)),
        (128, (8, 16)),
        (256, (16, 16)),
        (63, (7, 9)),
        (62, (2, 31)),
    ]

    for num, expected in cases:
        assert find_largest_factors(num) == expected


def cpuinfo(tmp_path, cpus):
    """A /proc/cpuinfo listing one entry per (physical id, core id)."""
    path = tmp_path / "cpuinfo"
    path.write_text("".join(
        f"processor\t: {n}\nphysical id\t: {socket}\ncore id\t\t: {core}\n\n"
        for n, (socket, core) in enumerate(cpus)
    ))
    return str(path)


def test_physical_cpu_count_with_hyperthreading(tmp_path):
    # 4 cores, each listed twice
    cpus = [(0, core) for core in range(4)] * 2
    assert physical_cpu_count(cpuinfo(tmp_path, cpus)) == 4


def test_physical_cpu_count_across_sockets(tmp_path):
    # core ids repeat on each socket, so they only identify a core together
    cpus = [(socket, core) for socket in range(2) for core in range(4)]
    assert physical_cpu_count(cpuinfo(tmp_path, cpus)) == 8


def test_physical_cpu_count_falls_back_to_cpu_count(tmp_path):
    path = tmp_path / "cpuinfo"
    path.write_text("processor\t: 0\nBogoMIPS\t: 50.00\n\n")
    assert physical_cpu_count(str(path)) == os.cpu_count()
    assert physical_cpu_count(str(tmp_path / "missing")) == os.cpu_count()
