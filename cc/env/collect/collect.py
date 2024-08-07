from collections import OrderedDict
from typing import Sequence, Tuple, Union

import dm_env
import numpy as np
from tqdm.autonotebook import tqdm
from tree_utils import tree_batch
from tree_utils import tree_shape

from cc.acme import EnvironmentLoop
from cc.acme.utils import loggers
from cc.acme.utils.observers import EnvLoopObserver

from ...core import AbstractController
from ...core.config import use_tqdm
from ...core.types import TimeSeriesOfAct
from ...examples.feedforward_controller import make_feedforward_controller
from ...utils import timestep_array_from_env
from ...utils import to_jax
from ...utils import to_numpy
from ..buffer import make_episodic_buffer_adder_iterator
from ..buffer import ReplaySample
from .actor import ModuleActor
from .source import draw_u_from_cosines
from .source import draw_u_from_gaussian_process
from .source import ObservationReferenceSource


def concat_samples(*samples) -> ReplaySample:
    return tree_batch(samples, True)


def sample_feedforward_and_collect(
    env: dm_env.Environment,
    seeds_gp: list[int] = [],
    seeds_cos: list[Union[int, float]] = [],
    global_scale_u: float = 1.0,
) -> ReplaySample:
    samples = []
    if len(seeds_gp) > 0:
        _, sample_gp, _ = sample_feedforward_collect_and_make_source(
            env, seeds=seeds_gp, global_scale_u=global_scale_u
        )
        samples.append(sample_gp)
    if len(seeds_cos) > 0:
        _, sample_cos, _ = sample_feedforward_collect_and_make_source(
            env, draw_u_from_cosines, seeds=seeds_cos, global_scale_u=global_scale_u
        )
        samples.append(sample_cos)

    assert len(samples) > 0, "Either `seeds_gp` or `seeds_cos` must be given"
    return concat_samples(*samples)


def collect_exhaust_source(
    env: dm_env.Environment,
    controller: AbstractController,
    observers: Sequence[EnvLoopObserver] = (),
) -> Tuple[ReplaySample, dict]:
    source = env._source

    N = tree_shape(source._yss)
    # collect performance of controller in environment
    pbar = tqdm(range(N), desc="Reference Iterator", disable=not use_tqdm())
    samples, loop_results = [], []
    for i_actor in pbar:
        source.change_reference_of_actor(i_actor)
        sample, loop_result = collect(env, controller, observers)
        samples.append(sample)
        loop_results.append(loop_result)

    # concat samples
    sample = concat_samples(*samples)

    return sample, tree_batch(loop_results)


def collect(
    env: dm_env.Environment,
    controller: AbstractController,
    observers: Sequence[EnvLoopObserver] = (),
) -> Tuple[ReplaySample, loggers.LoggingData]:
    env.reset()

    buffer, adder, iterator = make_episodic_buffer_adder_iterator(
        bs=1,
        env=env,
        buffer_size_n_trajectories=1,
    )

    actor = ModuleActor(
        controller=controller, action_spec=env.action_spec(), adder=adder
    )
    loop = EnvironmentLoop(env, actor, logger=loggers.NoOpLogger(), observers=observers)
    loop_result = loop.run_episode()
    sample = next(iterator)
    buffer.close()
    return sample, loop_result


def sample_feedforward_collect_and_make_source(
    env: dm_env.Environment,
    draw_fn=draw_u_from_gaussian_process,
    seeds: list[int] = [
        0,
    ],
    observers: Sequence[EnvLoopObserver] = (),
    global_scale_u: float = 1.0,
) -> Tuple[ObservationReferenceSource, ReplaySample, dict]:
    assert len(seeds) > 0

    ts = timestep_array_from_env(env)

    samples, loop_results = [], []
    for seed in seeds:
        us: TimeSeriesOfAct = to_jax(draw_fn(to_numpy(ts), seed=seed))
        us = us * global_scale_u
        controller = make_feedforward_controller(us)
        sample, loop_result = collect(env, controller, observers)
        samples.append(sample)
        loop_results.append(loop_result)

    sample = concat_samples(*samples)
    source = ObservationReferenceSource(sample.obs, ts, sample.action)
    return source, sample, tree_batch(loop_results)


def append_source(
    first: ObservationReferenceSource, second: ObservationReferenceSource
):
    yss = OrderedDict()
    for key in first._yss.keys():
        yss[key] = np.concatenate([first._yss[key], second._yss[key]], axis=0)

    return ObservationReferenceSource(yss, ts=first._ts)
