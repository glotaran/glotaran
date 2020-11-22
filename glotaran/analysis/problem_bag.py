import collections
import itertools

import numpy as np
import xarray as xr
from dask import array as da
from dask import bag as db

ProblemDescriptor = collections.namedtuple(
    "ProblemDescriptor", "dataset data model_axis global_axis weight"
)
GroupedProblem = collections.namedtuple("GroupedProblem", "data weight descriptor")
GroupedProblemDescriptor = collections.namedtuple("ProblemDescriptor", "dataset index axis")


def create_ungrouped_bag(scheme):
    bag = {}
    for label in scheme.model.dataset:
        dataset = scheme.data[label]
        data = dataset.data
        weight = dataset.weight if "weight" in dataset else None
        if weight is not None:
            data = data * weight
        bag[label] = ProblemDescriptor(
            scheme.model.dataset[label],
            data,
            dataset.coords[scheme.model.model_dimension].values,
            dataset.coords[scheme.model.global_dimension].values,
            weight,
        )
    return bag


def create_grouped_bag(scheme):
    bag = None
    datasets = None
    full_axis = None
    for label in scheme.model.dataset:
        dataset = scheme.data[label]
        weight = (
            dataset.weight
            if "weight" in dataset
            else xr.DataArray(np.ones_like(dataset.data), coords=dataset.data.coords)
        )
        data = dataset.data * weight
        global_axis = dataset.coords[scheme.model.global_dimension].values
        model_axis = dataset.coords[scheme.model.model_dimension].values
        if bag is None:
            bag = collections.deque(
                GroupedProblem(
                    data.isel({scheme.model.global_dimension: i}).values,
                    weight.isel({scheme.model.global_dimension: i}).values,
                    [GroupedProblemDescriptor(label, value, model_axis)],
                )
                for i, value in enumerate(global_axis)
            )
            datasets = collections.deque([label] for _, _ in enumerate(global_axis))
            full_axis = collections.deque(global_axis)
        else:
            i1, i2 = _find_overlap(full_axis, global_axis, atol=scheme.group_tolerance)

            for i, j in enumerate(i1):
                datasets[j].append(label)
                bag[j] = GroupedProblem(
                    da.concatenate(
                        [
                            bag[j][0],
                            data.isel({scheme.model.global_dimension: i2[i]}).values,
                        ]
                    ),
                    da.concatenate(
                        [
                            bag[j][1],
                            weight.isel({scheme.model.global_dimension: i2[i]}).values,
                        ]
                    ),
                    bag[j][2] + [GroupedProblemDescriptor(label, global_axis[i2[i]], model_axis)],
                )

            # Add non-overlaping regions
            begin_overlap = i2[0] if len(i2) != 0 else 0
            end_overlap = i2[-1] + 1 if len(i2) != 0 else 0
            for i in itertools.chain(range(begin_overlap), range(end_overlap, len(global_axis))):
                problem = GroupedProblem(
                    data.isel({scheme.model.global_dimension: i}).values,
                    weight.isel({scheme.model.global_dimension: i}).values,
                    [GroupedProblemDescriptor(label, global_axis[i], model_axis)],
                )
                if i < end_overlap:
                    datasets.appendleft([label])
                    full_axis.appendleft(global_axis[i])
                    bag.appendleft(problem)
                else:
                    datasets.append([label])
                    full_axis.append(global_axis[i])
                    bag.append(problem)

    return db.from_sequence(bag), {"".join(d): d for d in datasets if len(d) > 1}


def _find_overlap(a, b, rtol=1e-05, atol=1e-08):
    ovr_a = []
    ovr_b = []
    start_b = 0
    for i, ai in enumerate(a):
        for j, bj in itertools.islice(enumerate(b), start_b, None):
            if np.isclose(ai, bj, rtol=rtol, atol=atol, equal_nan=False):
                ovr_a.append(i)
                ovr_b.append(j)
            elif bj > ai:  # (more than tolerance)
                break  # all the rest will be farther away
            else:  # bj < ai (more than tolerance)
                start_b += 1  # ignore further tests of this item
    return (ovr_a, ovr_b)
