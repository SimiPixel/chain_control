from collections import OrderedDict
from typing import NewType

import jax.numpy as jnp

PRNGKey = NewType("PRNGKey", jnp.ndarray)

Observation = NewType("Observation", OrderedDict)
TimeSeriesOfObs = NewType("TimeSeriesOfObs", OrderedDict)
BatchedTimeSeriesOfObs = NewType("BatchedTimeSeriesOfObs", OrderedDict)

Reference = NewType("Reference", OrderedDict)
TimeSeriesOfRef = NewType("TimeSeriesOfRef", OrderedDict)
BatchedTimeSeriesOfRef = NewType("BatchedTimeSeriesOfRef", OrderedDict)

Action = NewType("Action", jnp.ndarray)
TimeSeriesOfAct = NewType("TimeSeriesOfAct", jnp.ndarray)
BatchedTimeSeriesOfAct = NewType("BatchedTimeSeriesOfAct", jnp.ndarray)
