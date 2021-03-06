from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from glotaran.deprecation import deprecate
from glotaran.io import load_scheme

if TYPE_CHECKING:

    from typing import Literal

    import xarray as xr

    from glotaran.model import Model
    from glotaran.parameter import ParameterGroup

default_data_filters = {"minimal": ["fitted_data", "residual"], "full": None}


@dataclass
class SavingOptions:
    level: Literal["minimal", "full"] = "full"
    data_filter: list[str] | None = None
    data_format: str = "nc"
    parameter_format: str = "csv"
    report: bool = True


@dataclass
class Scheme:
    model: Model | str
    parameters: ParameterGroup | str
    data: dict[str, xr.DataArray | xr.Dataset | str]
    group_tolerance: float = 0.0
    non_negative_least_squares: bool = False
    maximum_number_function_evaluations: int = None
    ftol: float = 1e-8
    gtol: float = 1e-8
    xtol: float = 1e-8
    optimization_method: Literal[
        "TrustRegionReflection",
        "Dogbox",
        "Levenberg-Marquardt",
    ] = "TrustRegionReflection"
    saving: SavingOptions = SavingOptions()
    result_path: str | None = None

    def problem_list(self) -> list[str]:
        """Returns a list with all problems in the model and missing parameters."""
        return self.model.problem_list(self.parameters)

    def validate(self) -> str:
        """Returns a string listing all problems in the model and missing parameters."""
        return self.model.validate(self.parameters)

    def valid(self, parameters: ParameterGroup = None) -> bool:
        """Returns `True` if there are no problems with the model or the parameters,
        else `False`."""
        return self.model.valid(parameters)

    def markdown(self):
        s = self.model.markdown(parameters=self.parameters)

        s += "\n\n"
        s += "__Scheme__\n\n"

        s += f"* *nnls*: {self.nnls}\n"
        s += f"* *nfev*: {self.nfev}\n"
        s += f"* *group_tolerance*: {self.group_tolerance}\n"

        return s

    @staticmethod
    @deprecate(
        deprecated_qual_name_usage="glotaran.project.scheme.Scheme.from_yaml_file(filename)",
        new_qual_name_usage="glotaran.io.load_scheme(filename)",
        to_be_removed_in_version="0.6.0",
        importable_indices=(2, 1),
    )
    def from_yaml_file(filename: str) -> Scheme:
        """Create :class:`Scheme` from specs in yaml file.

        Warning
        -------
        Deprecated use ``glotaran.io.load_scheme(filename)`` instead.

        Parameters
        ----------
        filename : str
            Path to the spec file.

        Returns
        -------
        Scheme
            Analysis schmeme
        """
        return load_scheme(filename)
