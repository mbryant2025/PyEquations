from pyequations.inheritables import PyEquations
from pyequations.decorators import eq, func
from sympy.physics.units import meter, second
from sympy import symbols
from copy import deepcopy, copy


class InheritedClass(PyEquations):

    def __init__(self):
        variables = [
            'x', 'y'
        ]
        super().__init__(variables)

    @eq
    def calc_z(self):
        return self.x, self.y


inherit = InheritedClass()
inherit.x = 35

print('DONE')

