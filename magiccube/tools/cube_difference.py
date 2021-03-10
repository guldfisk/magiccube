from magiccube.collections.meta import MetaCube


def cube_difference(
    from_meta: MetaCube,
    to_meta: MetaCube,
    *,
    trap_redistribution_weighting: float = .25,
) -> float:
    new_non_trap_cubeables = to_meta.cube.cubeables - to_meta.cube.garbage_traps
    return (
        (
            len(new_non_trap_cubeables - (from_meta.cube.cubeables - from_meta.cube.garbage_traps))
            / len(to_meta.cube.cubeables)
        )
        + (
            (
                len(to_meta.node_collection.nodes - from_meta.node_collection.nodes)
                / len(to_meta.node_collection.nodes)
                * len(to_meta.cube.garbage_traps)
                / len(to_meta.cube.cubeables)
                if to_meta.node_collection.nodes else
                0.
            )
            * (1 - trap_redistribution_weighting)
        )
        + (
            len(to_meta.cube.garbage_traps - from_meta.cube.garbage_traps)
            / len(to_meta.cube.cubeables)
            * trap_redistribution_weighting
        )
    )
