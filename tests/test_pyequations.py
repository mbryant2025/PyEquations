from sympy import symbols, Eq
from sympy.physics.units import cm
from pyequations import __version__

from pyequations.pyequations import _get_symbols, eq, func, PyEquations, solved

# Make a tolerance function mark as exempt from testing

def within_tolerance(expected, actual, percent=1):
    return abs(expected - actual) <= abs(expected * percent / 100)

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

        @eq
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

        @eq
        def calc_x(self):
            return self.x, self.y + self.z

        @eq
        def calc_y(self):
            return 5 * self.x + self.z, -self.y

        @eq
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

        @eq
        def calc_x(self):
            return self.x, self.y + self.z

        @eq
        def calc_y(self):
            return 5 * self.x + self.z, -self.y

        @eq
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

        @eq
        def calc_x(self):
            return self.x, 5

        @eq
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

        @eq
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

        @eq
        def calc_x(self):
            return self.x, 5

        @eq
        def calc_y(self):
            return self.y, 1 + self.z

    inherit = InheritedClass()

    inherit.solve()

    print(inherit.get_all_variables())

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

        @eq
        def calc_x(self):
            return self.x**2, 4

        @eq
        def calc_y(self):
            return self.y**2, 16

    inherit = InheritedClass()

    # Should raise an exception as there are multiple solutions
    # Expect this exception:  Exception: Equations have multiple solutions: [(-2,), (2,)]
    try:
        inherit.solve()
    except RuntimeError:
        assert True
    else:
        assert False


def test_infinite_solutions():
    class InheritedClass(PyEquations):

        def __init__(self):
            super().__init__()
            self.add_variable('x')
            self.add_variable('y')

        @eq
        def calc_x(self):
            return self.x, self.y

        @eq
        def calc_y(self):
            return self.y, self.x

    inherit = InheritedClass()

    # Should not raise an exception as there are no contradictions, simply not enough information
    inherit.solve()

    assert inherit.x == symbols('x')
    assert inherit.y == symbols('y')


def test_func():
    class InheritedClass(PyEquations):

        def __init__(self):
            super().__init__()
            self.add_variable('x')
            self.add_variable('y')

        @func
        def calc_x(self):
            # Do some random logic here
            if self.x > 5:
                self.y = 10
            else:
                self.y = 3

    inherit = InheritedClass()

    inherit.x = 10

    inherit.solve()

    assert inherit.x == 10
    assert inherit.y == 10

    inherit.x = 1

    inherit.solve()

    assert inherit.x == 1
    assert inherit.y == 3


def test_silicon():
    n_i_300K = 1.07e10 * cm ** -3

    class Silicon(PyEquations):

        def __init__(self):
            super().__init__()
            self.add_variable('Si_type', 'Silicon type')
            self.add_variable('N_a', 'Acceptor concentration')
            self.add_variable('N_d', 'Donor concentration')
            self.add_variable('n_oN', 'Thermal equilibrium electron concentration in n-type silicon')
            self.add_variable('p_oP', 'Thermal equilibrium hole concentration in p-type silicon')
            self.add_variable('n_oP', 'Thermal equilibrium electron concentration in p-type silicon')
            self.add_variable('p_oN', 'Thermal equilibrium hole concentration in n-type silicon')

        @func
        def calc_si_type(self):
            if solved(self.N_a, self.N_d):
                if self.N_a > self.N_d:
                    self.Si_type = 'p-type'
                elif self.N_a < self.N_d:
                    self.Si_type = 'n-type'
                else:
                    self.Si_type = 'intrinsic'
            elif solved(self.N_a):
                self.Si_type = 'p-type'
            elif solved(self.N_d):
                self.Si_type = 'n-type'
            else:
                self.Si_type = 'intrinsic'

        @eq
        def calc_p_oP1(self):
            return self.p_oP, self.N_a

        @eq
        def calc_p_oP2(self):
            return self.p_oP, n_i_300K ** 2 / self.n_oP

        @eq
        def calc_n_oN1(self):
            return self.n_oN, n_i_300K ** 2 / self.p_oN

        @eq
        def calc_n_oN2(self):
            return self.n_oN, self.N_d

    s = Silicon()

    s.N_a = 1e16 * cm ** -3
    s.N_d = 3e15 * cm ** -3

    s.solve()

    assert s.N_a == 1e16 * cm ** -3
    assert s.N_d == 3e15 * cm ** -3
    assert s.Si_type == 'p-type'
    assert s.n_oN == 3e15 * cm ** -3
    assert s.n_oP == 11449.0 * cm ** -3
    assert within_tolerance(s.p_oN, 38163.3333333333 * cm ** -3)
    assert s.p_oP == 1e16 * cm ** -3


# TODO test get descirption and such

# TODO test incorrectly made functions
