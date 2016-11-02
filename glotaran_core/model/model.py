from .parameter import Parameter
from .parameter_constraints import ParameterConstraint
from .compartment_constraints import CompartmentConstraint
from .relation import Relation
from .dataset_descriptor import DatasetDescriptor
from .initial_concentration import InitialConcentration
from .megacomplex import Megacomplex


class Model(object):
    """
    Model represents a global analysis model.

    Consists of parameters, megacomplexes, relations and constraints.
    """
    def type_string(self):
        raise NotImplementedError

    @property
    def parameter(self):
        return self._parameter

    @parameter.setter
    def parameter(self, parameter):
        if not isinstance(parameter, list):
            parameter = [parameter]

        self._parameter = []
        for p in parameter:
            if not isinstance(p, Parameter):
                raise TypeError
            p.index = len(self._parameter)+1
            self._parameter.append(p)

    @property
    def megacomplexes(self):
        return self._megacomplexes

    @megacomplexes.setter
    def megacomplexes(self, value):
        if not isinstance(value, dict):
            raise TypeError("Megacomplexes must be dict.")
        if any(not issubclass(type(value[val]), Megacomplex) for val in value):
            raise TypeError("Megacomplexes must be subclass of 'Megacomplex'")
        self._megacomplexes = value

    def add_megacomplex(self, megacomplex):
        if not issubclass(type(megacomplex), Megacomplex):
            raise TypeError("Megacomplexes must be subclass of 'Megacomplex'")
        try:
            if megacomplex.label in self.megacomplexes:
                raise Exception("Megacomplex labels must be unique")
            self.megacomplexes[megacomplex.label] = megacomplex
        except:
            self.megacomplexes = {megacomplex.label: megacomplex}

    @property
    def relations(self):
        return self._relations

    @relations.setter
    def relations(self, value):
        if not isinstance(value, list):
            value = [value]
        if any(not isinstance(val, Relation) for val in value):
            raise TypeError("Relations must be instance of class 'Relation'")
        self._relations = value

    def add_relation(self, relation):
        if not isinstance(relation, Relation):
            raise TypeError("Relations must be instance of class 'Relation'")
        try:
            self.relations.append(relation)
        except:
            self.relations = relation

    @property
    def parameter_constraints(self):
        return self._parameter_constraints

    @parameter_constraints.setter
    def parameter_constraints(self, value):
        if not isinstance(value, list):
            value = [value]
        if any(not isinstance(val, ParameterConstraint) for val in value):
            raise TypeError("ParameterConstraint must be instance of class"
                            " 'ParameterConstraint'")
        self._parameter_constraints = value

    def add_parameter_constraint(self, constraint):
        if not isinstance(constraint, ParameterConstraint):
            raise TypeError("ParameterConstraint must be instance of class"
                            " 'ParameterConstraint'")
        try:
            self.parameter_constraints.append(constraint)
        except:
            self.parameter_constraints = constraint

    @property
    def compartment_constraints(self):
        return self._compartment_constraints

    @compartment_constraints.setter
    def compartment_constraints(self, value):
        if not isinstance(value, list):
            value = [value]
        if any(not isinstance(val, CompartmentConstraint) for val in value):
            raise TypeError("CompartmentConstraint must be instance of class"
                            " 'CompartmentConstraint'")
        self._compartment_constraints = value

    def add_compartment_constraint(self, constraint):
        if not issubclass(type(constraint), CompartmentConstraint):
            raise TypeError("CompartmentConstraint must be instance of class"
                            " 'CompartmentConstraint'")
        try:
            self.compartment_constraints.append(constraint)
        except:
            self.compartment_constraints = constraint

    @property
    def datasets(self):
        return self._datasets

    @datasets.setter
    def datasets(self, value):
        if not isinstance(value, dict):
            raise TypeError("Datasets must be dict.")
        if any(not issubclass(type(value[val]), DatasetDescriptor) for val in value):
            raise TypeError("Dataset must be subclass of 'DatasetDescriptor'")
        self._datasets = value

    def add_dataset(self, dataset):
        if not issubclass(type(dataset), DatasetDescriptor):
            raise TypeError("Dataset must be subclass of 'DatasetDescriptor'")
        try:
            self.datasets[dataset.label] = dataset
        except:
            self.datasets = {dataset.label: dataset}

    @property
    def initial_concentrations(self):
        return self._initial_concentrations

    @initial_concentrations.setter
    def initial_concentrations(self, value):
        if not isinstance(value, dict):
            raise TypeError("Initial concentrations must be dict.")
        if any(not isinstance(value[val],
                              InitialConcentration) for val in value):
            raise TypeError("Initial concentrations must be instance of"
                            " 'InitialConcentration'")
        self._initial_concentrations = value

    def add_initial_concentration(self, initial_concentration):
        if not isinstance(initial_concentration, InitialConcentration):
            raise TypeError("Initial concentrations must be instance of"
                            " 'InitialConcentration'")
        try:
            self.initial_concentrations[initial_concentration.label] =\
                initial_concentration
        except:
            self.initial_concentrations = {initial_concentration.label:
                                           initial_concentration}

    def __str__(self):
        s = "Modeltype: {}\n\n".format(self.type_string())

        s += "Parameter\n---------\n\n"

        for p in self.parameter:
            s += "{}\n".format(p)

        s += "\nParameter Constraints\n--------------------\n\n"

        for p in self._parameter_constraints:
            s += "{}\n".format(p)

        s += "\nParameter Relations\n------------------\n\n"

        for p in self._relations:
            s += "{}\n".format(p)

        s += "\nMegacomplexes\n-------------\n\n"

        for m in self._megacomplexes:
            s += "{}\n".format(self._megacomplexes[m])

        s += "\nCompartment Constraints\n------------------------\n\n"

        for c in self._compartment_constraints:
            s += "{}\n".format(c)

        s += "\nInitital Concentrations\n-----------------------\n\n"

        for i in self._initial_concentrations:
            s += "{}\n".format(self._initial_concentrations[i])

        s += "\nDatasets\n--------\n\n"

        for d in self._datasets:
            s += "{}\n".format(self._datasets[d])
        return s
