from types import SimpleNamespace

import cloudpickle
import equinox as eqx


def load(path):
    with open(path, "rb") as file:
        obj = cloudpickle.load(file)
    return obj


def save(obj, path, metadata={}, verbose=True):

    if isinstance(obj, eqx.Module):
        raise Exception(
            """Not possible. Use `eqx.tree_serialise_leaves(path, obj)` instead.
            To de-serialise use `eqx.tree_deserialise_leaves`."""
        )

    if metadata == {}:
        with open(path, "wb") as file:
            cloudpickle.dump(obj, file)
        return

    if isinstance(metadata, dict):
        metadata = SimpleNamespace(**metadata)

    obj_w_metadata = SimpleNamespace()
    obj_w_metadata.obj = obj
    obj_w_metadata.meta = metadata
    with open(path, "wb") as file:
        cloudpickle.dump(obj_w_metadata, file)

    if verbose:
        print(f"Saving object {type(obj)} as `{path}`.")
