class InitialConcentration(object):
    """
    An InitialConcentration constration has label and parameters.
    """
    def __init__(self, label, parameter):
        self.label = label
        self.parameter = parameter

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, value):
        self._label = value

    @property
    def parameter(self):
        return self._parameter

    @parameter.setter
    def parameter(self, value):
        if not isinstance(value, list):
            value = [value]
        if any(not isinstance(val, int) for val in value):
            raise TypeError("Parameter must integer or list of integer")
        self._parameter = value

    def __str__(self):
        return "Label: {}, Parameters, {}".format(self.label,
                                                  self.parameter)
