from .dataset import Dataset
from .dataset_scaling import DatasetScaling
from .megacomplex_scaling import MegacomplexScaling


class DatasetDescriptor(object):
    """
    Class representing a dataset for fitting.
    """
    def __init__(self, label, initial_concentration, megacomplexes,
                 megacomplex_scaling, dataset, dataset_scaling):
        self.label = label
        self.initial_concentration = initial_concentration
        self.megacomplexes = megacomplexes
        self.megacomplex_scaling = megacomplex_scaling
        self.dataset = dataset
        self.dataset_scaling = dataset_scaling

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, value):
        self._label = value

    @property
    def initial_concentration(self):
        '''Returns the label of the initial concentration to be used to fit the
        dataset.'''
        return self._initial_concentration

    @initial_concentration.setter
    def initial_concentration(self, value):
        '''Sets the label of the initial concentration to be used to fit the
        dataset.'''
        self._initial_concentration = value

    @property
    def dataset(self):
        return self._dataset

    @dataset.setter
    def dataset(self, dataset):
        if not issubclass(type(dataset), Dataset):
            raise TypeError("Dataset must be of subclass of 'Dataset' class.")
        self._dataset = dataset

    @property
    def dataset_scaling(self):
        return self._dataset_scaling

    @dataset_scaling.setter
    def dataset_scaling(self, scaling):
        if not isinstance(scaling, DatasetScaling):
            raise TypeError
        self._dataset_scaling = scaling

    @property
    def megacomplexes(self):
        return self._megacomplexes

    @megacomplexes.setter
    def megacomplexes(self, megacomplex):
        if not isinstance(megacomplex, list):
            megacomplex = [megacomplex]
        if any(not isinstance(m, str) for m in megacomplex):
            raise TypeError("Megacomplex labels must be string.")
        self._megacomplexes = megacomplex

    @property
    def megacomplex_scaling(self):
        return self._megacomplex_scaling

    @megacomplex_scaling.setter
    def megacomplex_scaling(self, scaling):
        if not isinstance(scaling, list):
            scaling = [scaling]
        if any(not isinstance(s, MegacomplexScaling) for s in scaling):
            raise TypeError
        self._megacomplex_scaling = scaling

    def __str__(self):
        s = "Dataset '{}'\n\n".format(self.label)

        s += "\tDataset Scaling: {}\n".format(self.dataset_scaling)

        s += "\tInitial Concentration: {}\n"\
            .format(self.initial_concentration)

        s += "\tMegacomplexes: {}\n".format(self.megacomplexes)

        if len(self.megacomplex_scaling) is not 0:
            s += "\tScalings:\n"
            for sc in self.megacomplex_scaling:
                s += "\t\t- {}\n".format(sc)

        return s
