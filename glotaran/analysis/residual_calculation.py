import dask
import dask.bag as db
import numpy as np


def create_index_independend_ungrouped_residual(
        scheme, problem_bag, matrix_jobs, residual_function):

    global_dimension = scheme.model.global_dimension
    clp_label = {}
    clps = {}
    residuals = {}
    full_residuals = []
    for label in problem_bag:
        data = problem_bag[label].data
        size = problem_bag[label].global_axis.size
        clp_label[label] = matrix_jobs[label][0]
        matrix = matrix_jobs[label][1]

        clps[label] = []
        residuals[label] = []
        for i in range(size):
            data_stripe = data.isel({global_dimension: i}).values
            clp, residual = \
                dask.delayed(residual_function, nout=2)(matrix, data_stripe)
            clps[label].append(clp)
            residuals[label].append(residual)
            full_residuals.append(residual)

    full_residuals = dask.delayed(np.concatenate)(full_residuals)
    return clp_label, clps, residuals, full_residuals


def create_index_dependend_ungrouped_residual(
        scheme, problem_bag, matrix_jobs, residual_function):

    global_dimension = scheme.model.global_dimension
    reduced_clp_labels = {}
    reduced_clps = {}
    residuals = {}
    full_residual = []
    for label in problem_bag:
        data = problem_bag[label].data
        size = problem_bag[label].global_axis.size
        matrices = matrix_jobs[label]
        reduced_clp_labels[label] = []
        reduced_clps[label] = []
        residuals[label] = []
        for i in range(size):
            clp, residual = \
                dask.delayed(residual_function, nout=2)(
                    matrices[i][1], data.isel({global_dimension: i}).values)

            reduced_clp_labels[label].append(matrices[i][0])
            reduced_clps[label].append(clp)
            residuals[label].append(residual)
            full_residual.append(residual)
    full_residual = db.concat(full_residual)
    return reduced_clp_labels, reduced_clps, residuals, full_residual


def create_index_independend_grouped_residual(
        scheme, problem_bag, matrix_jobs, residual_function):

    data_bag = problem_bag.pluck(0)

    matrices = problem_bag.pluck(1)\
        .map(lambda group: "".join(problem.dataset for problem in group))\

    reduced_clp_label = matrices.map(lambda group: matrix_jobs[group][0]).compute()

    def residual(matrix, data, jobs):
        return residual_function(jobs[matrix][1], data)

    residual_bag = db.map(residual, matrices, data_bag, matrix_jobs)
    clps = residual_bag.pluck(0)
    full_residuals = dask.delayed(np.concatenate)(residual_bag.pluck(1))
    return reduced_clp_label, clps, residual_bag.pluck(1), full_residuals


def create_index_dependend_grouped_residual(
        scheme, problem_bag, matrix_jobs, residual_function):

    data_bag = problem_bag.pluck(0)
    reduced_clp_labels = matrix_jobs.pluck(0)
    matrices = matrix_jobs.pluck(1)

    residual_bag = db.map(residual_function, matrices, data_bag)
    reduced_clps = residual_bag.pluck(0)
    residuals = residual_bag.pluck(1)
    full_residuals = dask.delayed(np.concatenate)(residual_bag.pluck(1))
    return reduced_clp_labels, reduced_clps, residuals, full_residuals