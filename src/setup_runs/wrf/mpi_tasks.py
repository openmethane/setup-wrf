import math
import os

WRF_MIN_PATCH_SIZE=10

def safe_mpi_tasks(geo_dims: tuple[int, int], cpu_count = os.cpu_count()) -> int:
    """
    Determine a reasonable default MPI task count for running WRF over the
    specified domain, with the available number of cores. This method does
    not replace manually testing different task counts for a specific domain
    and host system, but should provide a safe default when domain size and
    core count are not known ahead of time.

    WRF patches cannot be smaller than 10 cells in either dimension, so small
    domains are likely to end up with a task count of 1 to prevent parallelism.

    See: https://www2.mmm.ucar.edu/wrf/site_linked_files/tutorials/wrf_computation.pdf

    :param geo_dims: Number of cells in the domain in (y, x)
    :param cpu_count: Maximum number of cores to use
    :return: Number of MPI tasks to use when running WRF
    """
    geo_dims_y, geo_dims_x = geo_dims

    # find the largest mpi task count with "square-ish" factors
    target_tasks = cpu_count
    while target_tasks > 1:
        # WRF splits the domain into a number of "patches" based on the number
        # of MPI tasks. WRF is more efficient when patch cell dims are closer
        # to squares or rectangles, so we look for task counts with factors
        # that are similarly sized.
        fac_a, fac_b = find_largest_factors(target_tasks)

        # find factors that are similar in size, and result in patch sizes
        # at least 10 cells in both dimensions
        if fac_b <= fac_a * 2 \
            and geo_dims_y / fac_b >= WRF_MIN_PATCH_SIZE \
            and geo_dims_x / fac_a >= WRF_MIN_PATCH_SIZE:
            return target_tasks
        target_tasks -= 1

    return target_tasks

def find_largest_factors(num: int) -> tuple[int, int]:
    check_factor = math.floor(math.sqrt(num))
    while check_factor > 0:
        if num % check_factor == 0:
            return check_factor, int(num / check_factor)
        check_factor -= 1
    return 1, num


