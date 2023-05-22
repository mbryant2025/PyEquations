from sympy import symbols, Eq
from sympy.physics.units import cm
from pyequations import __version__

from pyequations.pyequations import _get_symbols, calc, PyEquations


def test_version():
    assert __version__ == '0.1.0'


def test_get_symbols():
    # Basic test
    w, x, y, z = symbols('w x y z')
    eqs = [
        Eq(x, 1),
        Eq(y, 2.5),
        Eq(w, 5 + 6j),
        Eq(z, 1e5 * x * cm + y * cm)
    ]

    assert set(_get_symbols(eqs)) == {w, x, y, z}

    # Test with just variable = number
    eqs = [
        Eq(x, 1),
    ]

    assert set(_get_symbols(eqs)) == {x}


def test_inherit_basic():
    class InheritedClass(PyEquations):

        def __init__(self):
            super().__init__()
            self.add_variable('x')
            self.add_variable('y')

        @calc
        def calc_z(self):
            return self.x, self.y

    inherit = InheritedClass()
    inherit.x = 35 * cm

    inherit.solve()

    assert inherit.x == 35 * cm
    assert inherit.y == 35 * cm


def test_multiple_variables():
    class InheritedClass(PyEquations):

        def __init__(self):
            super().__init__()
            self.add_variable('x')
            self.add_variable('y')
            self.add_variable('z')

        @calc
        def calc_x(self):
            return self.x, self.y + self.z

        @calc
        def calc_y(self):
            return 5 * self.x + self.z, -self.y

        @calc
        def calc_z(self):
            return self.x + self.y, self.z / 4 + 10

    inherit = InheritedClass()

    inherit.solve()

    assert inherit.x == 0
    assert inherit.y == 8
    assert inherit.z == -8

    print(inherit.x, inherit.y, inherit.z)


def test_no_solutions():
    class InheritedClass(PyEquations):

        def __init__(self):
            super().__init__()
            self.add_variable('x')
            self.add_variable('y')
            self.add_variable('z')

        @calc
        def calc_x(self):
            return self.x, self.y + self.z

        @calc
        def calc_y(self):
            return 5 * self.x + self.z, -self.y

        @calc
        def calc_z(self):
            return self.x + self.y, self.z / 4 + 10

    inherit = InheritedClass()

    inherit.x = 1

    # Should raise an exception as there are no solutions with x = 1
    try:
        inherit.solve()
        assert False
    except Exception:
        assert True


def test_mix_units():
    class InheritedClass(PyEquations):

        def __init__(self):
            super().__init__()
            self.add_variable('x')
            self.add_variable('y')

        @calc
        def calc_x(self):
            return self.x, 5

        @calc
        def calc_y(self):
            return self.y, 10 * cm * self.x

    inherit = InheritedClass()

    inherit.solve()

    assert inherit.x == 5
    assert inherit.y == 50 * cm


def test_not_enough_information():
    class InheritedClass(PyEquations):

        def __init__(self):
            super().__init__()
            self.add_variable('x')
            self.add_variable('y')

        @calc
        def calc_y(self):
            return self.y, self.x * 2

    inherit = InheritedClass()

    inherit.solve()

    # Check that x and y are still just their symbols as there is not enough information
    assert inherit.x == symbols('x')
    assert inherit.y == symbols('y')


def test_solved_maximum():
    class InheritedClass(PyEquations):

        def __init__(self):
            super().__init__()
            self.add_variable('x')
            self.add_variable('y')
            self.add_variable('z')

        @calc
        def calc_x(self):
            return self.x, 5

        @calc
        def calc_y(self):
            return self.y, 1 + self.z

    inherit = InheritedClass()

    inherit.solve()

    # Check that as much as possible is solved
    assert inherit.x == 5
    assert inherit.y == symbols('y')
    assert inherit.z == symbols('z')


def test_multiple_solutions():
    class InheritedClass(PyEquations):

        def __init__(self):
            super().__init__()
            self.add_variable('x')
            self.add_variable('y')

        @calc
        def calc_x(self):
            return self.x**2, 4

        @calc
        def calc_y(self):
            return self.y**2, 16

    inherit = InheritedClass()

    # Should raise an exception as there are multiple solutions
    try:
        inherit.solve()
        assert False
    except Exception:
        assert True


def test_infinite_solutions():
    class InheritedClass(PyEquations):

        def __init__(self):
            super().__init__()
            self.add_variable('x')
            self.add_variable('y')

        @calc
        def calc_x(self):
            return self.x, self.y

        @calc
        def calc_y(self):
            return self.y, self.x

    inherit = InheritedClass()

    # Should raise an exception as there are infinite solutions
    try:
        inherit.solve()
        assert False
    except Exception:
        assert True

