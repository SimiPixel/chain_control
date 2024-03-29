from collections import OrderedDict
from typing import Union

from dm_env import specs as dm_env_specs
import jax
import numpy as np


def sample_action_from_action_spec(key, action_spec):
    return jax.random.uniform(
        key,
        shape=action_spec.shape,
        minval=action_spec.minimum,
        maxval=action_spec.maximum,
    )


ArraySpecs = Union[dm_env_specs.Array, dm_env_specs.BoundedArray]


def sample_from_specs(specs: ArraySpecs):
    if isinstance(specs, dm_env_specs.Array):
        return np.random.uniform(low=-1e5, high=1e5, size=specs.shape).astype(
            specs.dtype
        )
    else:
        return np.random.uniform(
            low=specs.minimum, high=specs.maximum, size=specs.shape
        ).astype(specs.dtype)


def sample_from_tree_of_specs(specs):
    return jax.tree_util.tree_map(lambda specs: sample_from_specs(specs), specs)


def _spec_from_observation(observation):
    result = OrderedDict()
    for key, value in observation.items():
        if isinstance(value, OrderedDict):
            result[key] = _spec_from_observation(value)
        else:
            result[key] = dm_env_specs.Array(value.shape, value.dtype, name=key)
    return result
