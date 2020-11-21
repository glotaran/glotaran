import collections

import dask
import lmfit
import numpy as np

from glotaran.parameter import ParameterGroup

from . import problem_bag
from . import residual_calculation
from .matrix_calculation import calculate_index_independent_grouped_matrices
from .matrix_calculation import calculate_index_independent_ungrouped_matrices
from .matrix_calculation import create_index_dependent_grouped_matrix_jobs
from .matrix_calculation import create_index_dependent_ungrouped_matrix_jobs
from .nnls import residual_nnls
from .result import Result
from .variable_projection import residual_variable_projection

ResultFuture = collections.namedtuple(
    "ResultFuture", "bag clp_label matrix full_clp_label clp residual"
)


def optimize(scheme, verbose=True, client=None):

    initial_parameter = scheme.parameter.as_parameter_dict()

    if client is None:
        return optimize_task(initial_parameter, scheme, verbose)

    scheme = client.scatter(scheme)
    optimization_result_future = client.submit(optimize_task, initial_parameter, scheme, verbose)
    return optimization_result_future.result()


def optimize_task(initial_parameter, scheme, verbose):

    scheme.prepare_data(copy=False)
    problem_bag, groups = _create_problem_bag(scheme)

    minimizer = lmfit.Minimizer(
        calculate_penalty,
        initial_parameter,
        fcn_args=[scheme, problem_bag, groups],
        fcn_kws=None,
        iter_cb=None,
        scale_covar=True,
        nan_policy="omit",
        reduce_fcn=None,
        **{},
    )
    verbose = 2 if verbose else 0
    lm_result = minimizer.minimize(method="least_squares", verbose=verbose, max_nfev=scheme.nfev)

    parameter = ParameterGroup.from_parameter_dict(lm_result.params)
    datasets = _create_result(scheme, parameter)
    covar = lm_result.covar if hasattr(lm_result, "covar") else None

    return Result(
        scheme,
        datasets,
        parameter,
        lm_result.nfev,
        lm_result.nvarys,
        lm_result.ndata,
        lm_result.nfree,
        lm_result.chisqr,
        lm_result.redchi,
        lm_result.var_names,
        covar,
    )


def calculate_penalty(parameter, scheme, bag, groups):
    parameter = ParameterGroup.from_parameter_dict(parameter)
    residual_function = residual_nnls if scheme.nnls else residual_variable_projection
    if scheme.model.grouped():
        if scheme.model.index_dependent():
            (
                full_clp_label,
                _,
                constraint_labels_and_matrices,
            ) = create_index_dependent_grouped_matrix_jobs(scheme, bag, parameter)
            _, _, _, penalty = residual_calculation.create_index_dependent_grouped_residual(
                scheme,
                parameter,
                bag,
                full_clp_label,
                constraint_labels_and_matrices,
                residual_function,
            )
        else:

            (
                full_clp_label,
                _,
                constraint_labels_and_matrices,
            ) = calculate_index_independent_grouped_matrices(scheme, groups, parameter)

            _, _, _, penalty = residual_calculation.create_index_independent_grouped_residual(
                scheme,
                parameter,
                bag,
                full_clp_label,
                constraint_labels_and_matrices,
                residual_function,
            )
    else:
        if scheme.model.index_dependent():
            (
                full_clp_label,
                _,
                constraint_labels_and_matrices,
            ) = create_index_dependent_ungrouped_matrix_jobs(scheme, bag, parameter)
            _, _, _, penalty = residual_calculation.create_index_dependent_ungrouped_residual(
                scheme,
                parameter,
                bag,
                full_clp_label,
                constraint_labels_and_matrices,
                residual_function,
            )
        else:

            (
                full_clp_label,
                _,
                constraint_labels_and_matrices,
            ) = calculate_index_independent_ungrouped_matrices(scheme, parameter)

            _, _, _, penalty = residual_calculation.create_index_independent_ungrouped_residual(
                scheme,
                parameter,
                bag,
                full_clp_label,
                constraint_labels_and_matrices,
                residual_function,
            )
    penalty = penalty.compute()
    return penalty


def _create_problem_bag(scheme):
    groups = None
    if scheme.model.grouped():
        bag, groups = problem_bag.create_grouped_bag(scheme)
        bag = bag.persist()
    else:
        bag = problem_bag.create_ungrouped_bag(scheme)
    return bag, groups


def _create_result(scheme, parameter):

    residual_function = residual_nnls if scheme.nnls else residual_variable_projection
    model = scheme.model
    datasets = scheme.data

    if model.grouped():
        bag, groups = problem_bag.create_grouped_bag(scheme)

        if model.index_dependent():
            (
                clp_labels,
                matrices,
                constraint_labels_and_matrices,
            ) = create_index_dependent_grouped_matrix_jobs(scheme, bag, parameter)
            (
                reduced_clp_labels,
                reduced_clps,
                residuals,
                _,
            ) = residual_calculation.create_index_dependent_grouped_residual(
                scheme,
                parameter,
                bag,
                clp_labels,
                constraint_labels_and_matrices,
                residual_function,
            )
        else:
            (
                clp_labels,
                matrices,
                constraint_labels_and_matrices,
            ) = calculate_index_independent_grouped_matrices(scheme, groups, parameter)
            (
                reduced_clp_labels,
                reduced_clps,
                residuals,
                _,
            ) = residual_calculation.create_index_independent_grouped_residual(
                scheme,
                parameter,
                bag,
                clp_labels,
                constraint_labels_and_matrices,
                residual_function,
            )
    else:
        bag = problem_bag.create_ungrouped_bag(scheme)

        if model.index_dependent():
            (
                clp_labels,
                matrices,
                constraint_labels_and_matrices,
            ) = create_index_dependent_ungrouped_matrix_jobs(scheme, bag, parameter)
            (
                reduced_clp_labels,
                reduced_clps,
                residuals,
                _,
            ) = residual_calculation.create_index_dependent_ungrouped_residual(
                scheme,
                parameter,
                bag,
                clp_labels,
                constraint_labels_and_matrices,
                residual_function,
            )
        else:
            (
                clp_labels,
                matrices,
                constraint_labels_and_matrices,
            ) = calculate_index_independent_ungrouped_matrices(scheme, parameter)
            (
                reduced_clp_labels,
                reduced_clps,
                residuals,
                _,
            ) = residual_calculation.create_index_independent_ungrouped_residual(
                scheme,
                parameter,
                bag,
                clp_labels,
                constraint_labels_and_matrices,
                residual_function,
            )

    indices = None

    if model.grouped():
        indices = bag.map(lambda group: [d.index for d in group.descriptor])
        if model.index_dependent():
            (
                groups,
                indices,
                clp_labels,
                matrices,
                reduced_clp_labels,
                reduced_clps,
                residuals,
            ) = dask.compute(
                groups, indices, clp_labels, matrices, reduced_clp_labels, reduced_clps, residuals
            )
        else:
            groups, indices, reduced_clp_labels, reduced_clps, residuals = dask.compute(
                groups, indices, reduced_clp_labels, reduced_clps, residuals
            )

    for label, dataset in datasets.items():
        if model.grouped():
            if model.index_dependent():
                groups = bag.map(lambda group: [d.dataset for d in group.descriptor]).compute()
                for i, group in enumerate(groups):
                    if label in group:
                        group_index = group.index(label)
                        if "matrix" not in dataset:
                            # we assume that the labels are the same, this might not be true in
                            # future models
                            dataset.coords["clp_label"] = clp_labels[i][group_index]

                            dim1 = dataset.coords[model.global_dimension].size
                            dim2 = dataset.coords[model.model_dimension].size
                            dim3 = dataset.clp_label.size
                            dataset["matrix"] = (
                                (
                                    (model.global_dimension),
                                    (model.model_dimension),
                                    ("clp_label"),
                                ),
                                np.zeros((dim1, dim2, dim3), dtype=np.float64),
                            )
                        dataset.matrix.loc[
                            {model.global_dimension: indices[i][group_index]}
                        ] = matrices[i][group_index]
            else:
                clp_label, matrix = dask.compute(
                    clp_labels[label],
                    matrices[label],
                )
                dataset.coords["clp_label"] = clp_label
                dataset["matrix"] = (((model.model_dimension), ("clp_label")), matrix)
            dim1 = dataset.coords[model.global_dimension].size
            dim2 = dataset.coords["clp_label"].size
            dataset["clp"] = (
                (model.global_dimension, "clp_label"),
                np.zeros((dim1, dim2), dtype=np.float64),
            )

            dim1 = dataset.coords[model.model_dimension].size
            dim2 = dataset.coords[model.global_dimension].size
            dataset["residual"] = (
                (model.model_dimension, model.global_dimension),
                np.zeros((dim1, dim2), dtype=np.float64),
            )
            idx = 0
            for i, group in enumerate(groups):
                if label in group:
                    index = indices[i][group.index(label)]
                    for j, clp in enumerate(reduced_clp_labels[i]):
                        if clp in dataset.clp_label:
                            dataset.clp.loc[
                                {"clp_label": clp, model.global_dimension: index}
                            ] = reduced_clps[i][j]
                    start = 0
                    for dset in group:
                        if dset == label:
                            break
                        start += datasets[dset].coords[model.model_dimension].size
                    end = start + dataset.coords[model.model_dimension].size
                    dataset.residual.loc[{model.global_dimension: index}] = residuals[i][start:end]

        else:
            clp_label, matrix, reduced_clp_label, reduced_clp, residual = dask.compute(
                clp_labels[label],
                matrices[label],
                reduced_clp_labels[label],
                reduced_clps[label],
                residuals[label],
            )
            reduced_clp = np.asarray(reduced_clp)

            if model.index_dependent():
                # we assume that the labels are the same, this might not be true in future models
                dataset.coords["clp_label"] = clp_label[0]
                dataset["matrix"] = (
                    ((model.global_dimension), (model.model_dimension), ("clp_label")),
                    matrix,
                )
            else:
                dataset.coords["clp_label"] = clp_label
                dataset["matrix"] = (((model.model_dimension), ("clp_label")), matrix)

            dim1 = dataset.coords[model.global_dimension].size
            dim2 = dataset.coords["clp_label"].size
            dataset["clp"] = (
                (model.global_dimension, "clp_label"),
                np.zeros((dim1, dim2), dtype=np.float64),
            )
            for i, clp in enumerate(reduced_clp_label):
                if model.index_dependent():
                    idx = dataset.coords[model.global_dimension][i]
                    for c in clp:
                        if c not in reduced_clp_label[i]:
                            continue
                        j = reduced_clp_label[i].index(c)
                        dataset.clp.loc[
                            {"clp_label": c, model.global_dimension: idx}
                        ] = reduced_clp[i][j]
                else:
                    dataset.clp.loc[{"clp_label": clp}] = reduced_clp[:, i]

            dataset["residual"] = (
                ((model.model_dimension), (model.global_dimension)),
                np.asarray(residual).T,
            )

    if "weight" in dataset:
        dataset["weighted_residual"] = dataset.residual
        dataset["residual"] = dataset.weighted_residual / dataset.weight
        _create_svd("weighted_residual", dataset, model)
    _create_svd("residual", dataset, model)

    # Calculate RMS
    size = dataset.residual.shape[0] * dataset.residual.shape[1]
    dataset.attrs["root_mean_square_error"] = np.sqrt((dataset.residual ** 2).sum() / size).values

    # reconstruct fitted data
    dataset["fitted_data"] = dataset.data - dataset.residual

    if callable(model.finalize_data):
        model.finalize_data(indices, reduced_clp_labels, reduced_clps, parameter, datasets)

    return datasets


def _create_svd(name, dataset, model):
    l, v, r = np.linalg.svd(dataset[name])

    dataset[f"{name}_left_singular_vectors"] = (
        (model.model_dimension, "left_singular_value_index"),
        l,
    )

    dataset[f"{name}_right_singular_vectors"] = (
        ("right_singular_value_index", model.global_dimension),
        r,
    )

    dataset[f"{name}_singular_values"] = (("singular_value_index"), v)
