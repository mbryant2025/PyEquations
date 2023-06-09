from sympy import symbols, Eq, sqrt, I, Symbol, pi, Number, N, simplify
from sympy.physics.units import cm, meter, second, mm, km, centimeter, farad, ampere, kg
from pyequations import __version__
from pyequations.inheritables import PyEquations
from pyequations.utils import solved, get_symbols, remove_units, is_constant, get_units, composes_equation
from pyequations.decorators import eq, func
from pytest import raises, warns
from pyequations import EPSILON
from pyequations.context_stack import ContextStack
import math


def within_tolerance(expected, actual, percent=0.001):
    tolerance = abs(expected * percent / 100)
    diff = abs(expected - actual)
    return bool(diff <= tolerance)


def assert_dicts_equal(expected, actual):
    expected_set = {frozenset(d.items()) for d in expected}
    actual_set = {frozenset(d.items()) for d in actual}

    assert expected_set == actual_set


def assert_set_values_within_tolerance(expected, actual, percent=0.001):
    # Check if there is a difference in the number of values
    if len(expected) != len(actual):
        raise AssertionError(f'Expected {len(expected)} values, got {len(actual)}')
    # Checks for each value in the expected and sees if there is a value within tolerance in the actual
    for expected_value in expected:
        for actual_value in actual:
            if within_tolerance(expected_value, actual_value, percent):
                break
        else:
            raise AssertionError(f'Expected value {expected_value} not found in actual values {actual}')

    # To double-check, do the same thing but with the actual values
    for actual_value in actual:
        for expected_value in expected:
            if within_tolerance(expected_value, actual_value, percent):
                break
        else:
            raise AssertionError(f'Actual value {actual_value} not found in expected values {expected}')


def test_version():
    assert __version__ == '0.1.4'


def test_get_symbols():
    # Basic test
    w, x, y, z = symbols('w x y z')
    eqs = [
        Eq(x, 1),
        Eq(y, 2.5),
        Eq(w, 5 + 6j),
        Eq(z, 1e5 * x * cm + y * cm)
    ]

    assert set(get_symbols(eqs)) == {w, x, y, z}

    # Test with just variable = number
    eqs = [
        Eq(x, 1),
    ]

    assert set(get_symbols(eqs)) == {x}


def test_get_units():
    x = 1
    assert get_units(x) == set()

    x = Symbol('x')
    assert get_units(x) == set()

    x = 1 * cm
    assert get_units(x) == {cm}

    x = 1 * cm / second
    assert get_units(x) == {cm, second}

    x = 1 + cm
    assert get_units(x) == {cm}

    x = 1 + cm / second
    assert get_units(x) == {cm, second}

    x = cm + 1
    assert get_units(x) == {cm}

    x = cm / second + cm
    assert get_units(x) == {cm, second}

    x = sqrt(32) * cm * Symbol('cm') + 1
    assert get_units(x) == {cm}

    x = sqrt(32) * cm * Symbol('cm') * cm + 1
    assert get_units(x) == {cm}

    x = sqrt(32) * cm * Symbol('cm') * cm / second + 1
    assert get_units(x) == {cm, second}

    x = (sqrt(32) * cm * Symbol('cm') + 1) / second
    assert get_units(x) == {cm, second}


def test_is_constant():
    x = Symbol('x')
    assert not is_constant(x)

    x = 1
    assert is_constant(x)

    x = 1 * cm
    assert is_constant(x)

    x = 1 * cm / second
    assert is_constant(x)

    x = 1 * cm / second ** 2
    assert is_constant(x)

    x = 5.4
    assert is_constant(x)

    x = 5.4 * cm
    assert is_constant(x)

    x = 5.4 * cm / second
    assert is_constant(x)

    x = 5.4 * cm / second ** 2
    assert is_constant(x)

    x = Symbol('x') * cm
    assert not is_constant(x)

    x = pi
    assert is_constant(x)

    x = pi * cm
    assert is_constant(x)

    x = pi * cm / second
    assert is_constant(x)

    x = pi * cm / second ** 2
    assert is_constant(x)

    x = Symbol('x') * cm / second
    assert not is_constant(x)

    x = Symbol('x') * cm / second ** 2
    assert not is_constant(x)

    x = Symbol('x') * cm / second ** 2 + 1
    assert not is_constant(x)

    x = Symbol('x') * cm / second ** 2 + 1 * cm
    assert not is_constant(x)

    x = 10 * cm / second ** 2 + 1 * cm / second
    assert is_constant(x)

    x = 10 + Symbol('x')
    assert not is_constant(x)

    x = 10 * cm + Symbol('x')
    assert not is_constant(x)

    x = 10 * pi + Symbol('x') - Symbol('x')
    assert is_constant(x)

    x = Symbol('x') * (1 * cm / second ** 2 + 1) / Symbol('x')
    assert is_constant(x)

    y = Symbol('y')

    # This mess evaluates to 0
    # Simplify will already have been called on the equation
    x = simplify((y + sqrt(y) / 42) - (1 / 42 * (42 * sqrt(y) + 1) * sqrt(y)))
    assert is_constant(x)

    x = -7 * sqrt(41) * meter / second + 10 * meter
    assert is_constant(x)


def test_composes_equation():
    # Test with a single equation
    lhs = Symbol('x')
    rhs = 1

    assert composes_equation(lhs, rhs) == 1

    # Test with an identity
    lhs = Symbol('x')
    rhs = Symbol('x')

    assert composes_equation(lhs, rhs) == 0

    # Test with a numerical identity
    lhs = 1
    rhs = 1

    assert composes_equation(lhs, rhs) == 0

    # Test with a numerical identity with units

    lhs = 1 * cm
    rhs = 1 * cm

    assert composes_equation(lhs, rhs) == 0

    # Test with units and symbols
    y = Symbol('y')
    lhs = y * cm
    rhs = 1 * cm

    assert composes_equation(lhs, rhs) == 1

    # Test with units and symbols but invalid
    y = Symbol('y')
    lhs = y * cm
    rhs = 0.01 * y * meter

    assert composes_equation(lhs, rhs) == 0

    # Test with units and one symbol but valid
    lhs = 1 * cm * Symbol('x')
    rhs = 0.01 * meter

    assert composes_equation(lhs, rhs) == 1

    # Test with values that are not equal but close enough (within EPSILON)
    lhs = 1
    rhs = 1 + EPSILON / 1e5

    assert composes_equation(lhs, rhs) == 0

    # Test with values that are not equal but close enough (within EPSILON)
    lhs = -1
    rhs = -1 - EPSILON / 1e5

    assert composes_equation(lhs, rhs) == 0

    # Test with values that are not equal but close enough (within EPSILON)
    lhs = -1
    rhs = -1 + EPSILON / 1e5

    assert composes_equation(lhs, rhs) == 0

    # Test with values that are equal but not identical
    lhs = 1
    rhs = 1.0

    assert composes_equation(lhs, rhs) == 0

    # Test with values that are equal but not identical with units

    lhs = 1 * cm
    rhs = 1.0 * cm

    assert composes_equation(lhs, rhs) == 0

    # Test with expressions that evaluate to the same value
    lhs = sqrt(2) * sqrt(2)
    rhs = 2

    assert composes_equation(lhs, rhs) == 0

    # Test with valids that are not equal
    lhs = 1
    rhs = 2

    assert composes_equation(lhs, rhs) == -1

    # Test with valids that are not equal with units
    lhs = 1 * cm
    rhs = 2 * cm

    assert composes_equation(lhs, rhs) == -1

    # Test with different units

    lhs = 1 * cm
    rhs = 1 * second

    assert composes_equation(lhs, rhs) == -1

    # Test with expressions that evaluate to the same value with different units
    lhs = sqrt(2) * sqrt(2) * cm
    rhs = 2 * second

    assert composes_equation(lhs, rhs) == -1

    # Another 'close enough' test
    lhs = -7 * sqrt(41) * meter / second
    rhs = -44.8218696620299 * meter / second

    assert composes_equation(lhs, rhs) == 0

    # Now make it even more annoying
    lhs = -7 * sqrt(41) * meter / second + 44.8218696620299 * meter
    rhs = -44.8218696620299 * meter / second + 7 * sqrt(41) * meter

    assert composes_equation(lhs, rhs) == 0

    # Now make it even more annoying but with a contradiction
    lhs = -7 * sqrt(41) * meter / second + 10 * meter
    rhs = -44.8218696620299 * meter / second + 11 * meter

    assert composes_equation(lhs, rhs) == -1

    # Flip units for extra annoyance
    lhs = -7 * sqrt(41) * meter + 10 * meter / second
    rhs = -7 * sqrt(41) * meter / second + 10 * meter

    assert composes_equation(lhs, rhs) == -1

    # Test off by a negative
    lhs = 1
    rhs = -1

    assert composes_equation(lhs, rhs) == -1

    # Test off by a negative with units
    lhs = meter
    rhs = -meter

    assert composes_equation(lhs, rhs) == -1

    # Test to make sure we still account for relations between units
    lhs = 1 * cm
    rhs = 10 * mm

    assert composes_equation(lhs, rhs) == 0

    # Test with a mess of units
    # These two sides are actually equal
    lhs = 10 * meter
    rhs = 10 * cm + 85 * mm + 0.009815 * km

    assert composes_equation(lhs, rhs) == 0

    # Test with a mess of contradictory units
    lhs = 10 * meter
    rhs = 10 * cm + 85 * mm + 0.009815 * second

    assert composes_equation(lhs, rhs) == -1

    # Test with a mess of valid units that are off
    lhs = 10 * meter
    rhs = 10 * cm + 85 * mm + 0.0098151 * km

    assert composes_equation(lhs, rhs) == -1

    # Test with cm and centimeter
    lhs = 10 * cm
    rhs = 10 * centimeter

    assert composes_equation(lhs, rhs) == 0

    # Test with cm and centimeter unequal
    lhs = 10 * cm
    rhs = 10 * centimeter + 1 * mm

    assert composes_equation(lhs, rhs) == -1

    # Test that units are relative to each other
    lhs = 10 * farad
    rhs = 10 * second ** 4 * ampere ** 2 / kg ** 1 / meter ** 2

    assert composes_equation(lhs, rhs) == 0

    # Test that units are relative to each other -- just off
    lhs = 10 * farad
    rhs = 10 * second ** 4 * ampere ** 2 / kg ** 1 / meter ** 2 + 0.000001 * meter

    assert composes_equation(lhs, rhs) == -1

    # Test that we can handle tiny numbers
    lhs = 1e-8 * farad
    rhs = 1e-8 * second ** 4 * ampere ** 2 / kg ** 1 / meter ** 2

    assert composes_equation(lhs, rhs) == 0

    # Test that we can identify invalid tiny numbers
    lhs = 1e-35 * farad
    rhs = 1e-35 * second ** 4 * ampere ** 2 / kg ** 1 / meter ** 2 + 1e-40 * meter

    assert composes_equation(lhs, rhs) == -1

    # Test that aliases work
    lhs = 10 * cm
    rhs = 10 * centimeter

    assert composes_equation(lhs, rhs) == 0

    # Exhaustive test # TODO

    # TODO test with all units


def test_class_variables():
    class InheritedClass(PyEquations):

        def __init__(self):
            variables = [
                'x', 'y'
            ]
            super().__init__(variables)

        @eq
        def calc_x(self):
            return self.x, self.y

        @func
        def print_x(self):
            pass  # Don't want to actually print anything

    inherit = InheritedClass()

    # In this test, we want to ensure that we can access the class variables
    # and that it is set up properly

    # Check that we have a context_stack
    assert hasattr(inherit, 'context_stack')
    # Check that the type of the context_stack is ContextStack
    assert isinstance(inherit.context_stack, ContextStack)
    # Check that the context_stack has the correct number of contexts
    assert inherit.context_stack.num_contexts == 1
    # Check that it contains the correct variables
    assert inherit.context_stack.x == Symbol('x')

    # Check that the eqs list has the one function
    assert hasattr(inherit, 'eqs')
    assert len(inherit.eqs) == 1
    assert hasattr(inherit, 'calc_x')
    # Check that this function is decorated with eq
    assert hasattr(inherit.calc_x, '__equation__')

    # Same with funcs
    assert hasattr(inherit, 'funcs')
    assert len(inherit.funcs) == 1
    assert hasattr(inherit, 'print_x')
    # Check that this function is decorated with func
    assert hasattr(inherit.print_x, '__user_func__')

    # Test that we can substitute a value into a variable
    inherit.x = 5 * cm

    assert inherit.x == 5 * cm

    # Check that the change propagates to the context_stack
    assert inherit.context_stack.x == 5 * cm


def test_solve_basic():
    class InheritedClass(PyEquations):

        def __init__(self):
            variables = [
                'x', 'y'
            ]
            super().__init__(variables)

        @eq
        def calc_x(self):
            return self.x, self.y

    inherit = InheritedClass()
    inherit.x = 35 * cm

    inherit.solve()

    assert inherit.x == 35 * cm
    assert inherit.y == 35 * cm

    # Check that the values of x and y are stored in the context stack (rather than the class)
    assert inherit.context_stack.x == 35 * cm
    assert inherit.context_stack.y == 35 * cm


def test_multiple_variables():
    class InheritedClass(PyEquations):

        def __init__(self):
            super().__init__([
                'x', 'y', 'z'
            ])

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


def test_no_solutions():
    class InheritedClass(PyEquations):

        def __init__(self):
            super().__init__([
                'x', 'y'
            ])

        @eq
        def eq1(self):
            return self.y, self.x + 1

        @eq
        def eq2(self):
            return self.y, 2 * self.x

    inherit = InheritedClass()

    # The solution to this system is x=1, y=2

    # So...
    inherit.x = 5

    # Solving should raise runtime error
    with raises(RuntimeError):
        inherit.solve()


def test_parallel_lines():
    class Parallel(PyEquations):

        def __init__(self):
            super().__init__([
                'x', 'y'
            ])

        @eq
        def eq1(self):
            return self.y, self.x + 1

        @eq
        def eq2(self):
            return self.y, self.x + 2

    # Parallel lines have no intersection and therefore no solution
    # Should raise runtime error
    parallel = Parallel()

    with raises(RuntimeError):
        parallel.solve()


def test_mix_units():
    class InheritedClass(PyEquations):

        def __init__(self):
            super().__init__([
                'x', 'y'
            ])

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
            super().__init__([
                'x', 'y'
            ])

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
            super().__init__([
                'x', 'y', 'z'
            ])

        @eq
        def calc_x(self):
            return self.x, 5

        @eq
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
            super().__init__([
                'x', 'y'
            ])

        @eq
        def calc_x(self):
            return self.x ** 2, 4

        @eq
        def calc_y(self):
            return self.y ** 2, 16

    inherit = InheritedClass()

    inherit.solve()

    # For multiple solutions, should branch for each possible set of solutions
    assert inherit.num_branches == 4

    assert_dicts_equal([{'x': 2, 'y': 4}, {'x': 2, 'y': -4}, {'x': -2, 'y': 4}, {'x': -2, 'y': -4}], inherit.vars)


def test_multiple_solutions_2():
    class Problem(PyEquations):

        def __init__(self):
            super().__init__([
                'x', 'y'
            ])

        @eq
        def eq1(self):
            return 2 * self.x ** 2 + 3 * self.y ** 2, 1

        @eq
        def eq2(self):
            return self.x ** 2, self.y ** 2

    p = Problem()

    p.solve()

    # Should be four different solution branches
    assert p.num_branches == 4

    expected = [{'x': -sqrt(5) / 5, 'y': -sqrt(5) / 5}, {'x': -sqrt(5) / 5, 'y': sqrt(5) / 5},
                {'x': sqrt(5) / 5, 'y': -sqrt(5) / 5}, {'x': sqrt(5) / 5, 'y': sqrt(5) / 5}]

    assert_dicts_equal(expected, p.vars)


def test_some_multiple_some_single_solution():
    class Problem(PyEquations):

        def __init__(self):
            super().__init__([
                'x', 'y', 'z'
            ])

        @eq
        def eq1(self):
            return 2 * self.x ** 2 + 3 * self.y ** 2, 1

        @eq
        def eq2(self):
            return self.x ** 2, self.y ** 2

        @eq
        def eq3(self):
            return self.z, 10

    # Identical as before, except that we have an extra equation that is not dependent on x or y
    # In this case, we should only have two branches, as the third equation is the same

    p = Problem()

    p.solve()

    # Importantly, we should still only have 4 branches
    assert p.num_branches == 4

    expected = [{'x': -sqrt(5) / 5, 'y': -sqrt(5) / 5, 'z': 10}, {'x': -sqrt(5) / 5, 'y': sqrt(5) / 5, 'z': 10},
                {'x': sqrt(5) / 5, 'y': -sqrt(5) / 5, 'z': 10}, {'x': sqrt(5) / 5, 'y': sqrt(5) / 5, 'z': 10}]

    assert_dicts_equal(expected, p.vars)


def test_some_multiple_some_single_solution_2():
    class Problem(PyEquations):

        def __init__(self):
            super().__init__([
                'x', 'y', 'a', 'b', 'c'
            ])

        @eq
        def eq1(self):
            return 2 * self.x ** 2 + 3 * self.y ** 2, 1

        @eq
        def eq2(self):
            return self.x ** 2, self.y ** 2

        @eq
        def eq3(self):
            return self.c, self.b + self.a

        @eq
        def eq4(self):
            return self.b, self.c - 1

        @eq
        def eq5(self):
            return self.b / 2, self.a

    # Identical as before, once again
    # Except, that we have a consistent system of equations
    # This tests highlights a consistent system with more variables than the one with multiple branches
    # This highlights that the number of branches is not dependent on the number of variables

    p = Problem()

    p.solve()

    assert p.num_branches == 4

    expected = [{'a': 1, 'b': 2, 'c': 3, 'x': -sqrt(5) / 5, 'y': sqrt(5) / 5},
                {'a': 1, 'b': 2, 'c': 3, 'x': sqrt(5) / 5, 'y': -sqrt(5) / 5},
                {'a': 1, 'b': 2, 'c': 3, 'x': -sqrt(5) / 5, 'y': -sqrt(5) / 5},
                {'a': 1, 'b': 2, 'c': 3, 'x': sqrt(5) / 5, 'y': sqrt(5) / 5}]

    assert_dicts_equal(expected, p.vars)


def test_multiple_multiple_solutions():
    class Problem(PyEquations):

        def __init__(self):
            super().__init__([
                'x', 'y', 'a', 'b', 'c'
            ])

        @eq
        def eq1(self):
            return 2 * self.x ** 2 + 3 * self.y ** 2, 1

        @eq
        def eq2(self):
            return self.x ** 2, self.y ** 2

        @eq
        def eq3(self):
            return self.a, self.b + self.c

        @eq
        def eq4(self):
            return self.b, 3 * self.c + self.a

        @eq
        def eq5(self):
            return self.c, self.a ** 2 - 4

    # Identical as before, once again
    # Except, that we have a second system with multiple solutions
    # Again, checking mostly branch number, and also that the solutions are correct, of course
    # Want to avoid redundant results from different branches

    p = Problem()

    p.solve()

    assert p.num_branches == 8

    expected = [{'a': -2, 'b': -2, 'c': 0, 'x': -sqrt(5) / 5, 'y': -sqrt(5) / 5},
                {'a': -2, 'b': -2, 'c': 0, 'x': -sqrt(5) / 5, 'y': sqrt(5) / 5},
                {'a': 2, 'b': 2, 'c': 0, 'x': -sqrt(5) / 5, 'y': sqrt(5) / 5},
                {'a': -2, 'b': -2, 'c': 0, 'x': sqrt(5) / 5, 'y': -sqrt(5) / 5},
                {'a': 2, 'b': 2, 'c': 0, 'x': sqrt(5) / 5, 'y': -sqrt(5) / 5},
                {'a': -2, 'b': -2, 'c': 0, 'x': sqrt(5) / 5, 'y': sqrt(5) / 5},
                {'a': 2, 'b': 2, 'c': 0, 'x': sqrt(5) / 5, 'y': sqrt(5) / 5},
                {'a': 2, 'b': 2, 'c': 0, 'x': -sqrt(5) / 5, 'y': -sqrt(5) / 5}]

    assert_dicts_equal(expected, p.vars)


def test_multiple_multiple_solutions_2():
    class Problem(PyEquations):

        def __init__(self):
            super().__init__([
                'x', 'y', 'a', 'b', 'c', 'm'
            ])

        @eq
        def eq1(self):
            return 2 * self.x ** 2 + 3 * self.y ** 2, 1

        @eq
        def eq2(self):
            return self.x ** 2, self.y ** 2

        @eq
        def eq3(self):
            return self.a, self.b + self.c

        @eq
        def eq4(self):
            return self.b, 3 * self.c + self.a

        @eq
        def eq5(self):
            return self.c, self.a ** 2 - 4

        @eq
        def eq6(self):
            return self.m ** 2, 16

    # Identical as before, once again
    # Except, that we have a third system with multiple solutions
    # Again, checking mostly branch number, and also that the solutions are correct, of course
    # Want to avoid redundant results from different branches

    p = Problem()

    p.solve()

    assert p.num_branches == 16

    expected = [{'a': -2, 'b': -2, 'c': 0, 'm': -4, 'x': -sqrt(5) / 5, 'y': -sqrt(5) / 5},
                {'a': -2, 'b': -2, 'c': 0, 'm': 4, 'x': -sqrt(5) / 5, 'y': -sqrt(5) / 5},
                {'a': -2, 'b': -2, 'c': 0, 'm': 4, 'x': -sqrt(5) / 5, 'y': sqrt(5) / 5},
                {'a': 2, 'b': 2, 'c': 0, 'm': 4, 'x': -sqrt(5) / 5, 'y': sqrt(5) / 5},
                {'a': -2, 'b': -2, 'c': 0, 'm': 4, 'x': sqrt(5) / 5, 'y': -sqrt(5) / 5},
                {'a': 2, 'b': 2, 'c': 0, 'm': 4, 'x': sqrt(5) / 5, 'y': -sqrt(5) / 5},
                {'a': -2, 'b': -2, 'c': 0, 'm': 4, 'x': sqrt(5) / 5, 'y': sqrt(5) / 5},
                {'a': 2, 'b': 2, 'c': 0, 'm': 4, 'x': sqrt(5) / 5, 'y': sqrt(5) / 5},
                {'a': 2, 'b': 2, 'c': 0, 'm': 4, 'x': -sqrt(5) / 5, 'y': -sqrt(5) / 5},
                {'a': -2, 'b': -2, 'c': 0, 'm': -4, 'x': -sqrt(5) / 5, 'y': sqrt(5) / 5},
                {'a': 2, 'b': 2, 'c': 0, 'm': -4, 'x': -sqrt(5) / 5, 'y': sqrt(5) / 5},
                {'a': -2, 'b': -2, 'c': 0, 'm': -4, 'x': sqrt(5) / 5, 'y': -sqrt(5) / 5},
                {'a': 2, 'b': 2, 'c': 0, 'm': -4, 'x': sqrt(5) / 5, 'y': -sqrt(5) / 5},
                {'a': -2, 'b': -2, 'c': 0, 'm': -4, 'x': sqrt(5) / 5, 'y': sqrt(5) / 5},
                {'a': 2, 'b': 2, 'c': 0, 'm': -4, 'x': sqrt(5) / 5, 'y': sqrt(5) / 5},
                {'a': 2, 'b': 2, 'c': 0, 'm': -4, 'x': -sqrt(5) / 5, 'y': -sqrt(5) / 5}]

    assert_dicts_equal(expected, p.vars)


def test_complex_solutions():
    class ComplexSystem(PyEquations):

        def __init__(self):
            super().__init__([
                'x'
            ])

        @eq
        def eq1(self):
            return self.x ** 2 + 4, 0

    # This is a system with complex solutions

    c = ComplexSystem()

    c.solve()

    assert c.num_branches == 2

    expected = [{'x': -2 * I}, {'x': 2 * I}]

    assert_dicts_equal(expected, c.vars)


def test_infinite_solutions():
    class InheritedClass(PyEquations):

        def __init__(self):
            super().__init__([
                'x', 'y'
            ])

        @eq
        def calc_x(self):
            return self.x, self.y

        @eq
        def calc_y(self):
            return 3 * self.y, 3 * self.x

    inherit = InheritedClass()

    # Should not raise an exception as there are no contradictions, simply not enough information
    inherit.solve()

    assert inherit.x == symbols('x')
    assert inherit.y == symbols('y')


def test_complicated_solution_set():
    class Inherit(PyEquations):

        def __init__(self):
            super().__init__([
                'x', 'y', 'z', 'w'
            ])

        @eq
        def eq1(self):
            return self.w, 64

        @eq
        def eq2(self):
            return self.y ** 2, self.z ** 2 + self.w

        @eq
        def eq3(self):
            return self.y, 8 * self.z

        @eq
        def eq4(self):
            return self.z, self.y + self.x

    inherit = Inherit()

    # In this setup, w is always 64 whereas y and z have multiple solutions.
    # Furthermore, z is dependent on y and x, so z also has multiple solutions.

    inherit.solve()

    assert inherit.num_branches == 2

    expected = [{'w': 64, 'x': 8 * sqrt(7) / 3, 'y': -64 * sqrt(7) / 21, 'z': -8 * sqrt(7) / 21},
                {'w': 64, 'x': -8 * sqrt(7) / 3, 'y': 64 * sqrt(7) / 21, 'z': 8 * sqrt(7) / 21}]

    assert_dicts_equal(expected, inherit.vars)


def test_func():
    class InheritedClass(PyEquations):

        def __init__(self):
            super().__init__([
                'x', 'y'
            ])

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

    inherit = InheritedClass()

    inherit.x = 1

    inherit.solve()

    assert inherit.x == 1
    assert inherit.y == 3


def test_func_2():
    class InheritedClass(PyEquations):

        def __init__(self):
            super().__init__([
                'x', 'y', 'z'
            ])

        @func
        def calc_x(self):
            # Do some random logic here
            if self.x > 5 * meter:
                self.y = 10
            else:
                self.y = 3 * second

        @func
        def calc_z(self):
            if self.x > 0:
                self.z = 10 * meter / second

    # Test that functions work with units (especially in comparison)
    inherit = InheritedClass()

    inherit.x = 10 * meter

    inherit.solve()

    assert inherit.x == 10 * meter
    assert inherit.y == 10
    assert inherit.z == 10 * meter / second

    inherit = InheritedClass()

    inherit.x = -1 * meter

    inherit.solve()

    assert inherit.x == -1 * meter
    assert inherit.y == 3 * second
    assert inherit.z == Symbol('z')


def test_del_branch():
    class Problem(PyEquations):

        def __init__(self):
            super().__init__([
                'x'
            ])

        @eq
        def eq1(self):
            return self.x ** 2, 4

        @func
        def constraint(self):
            if self.x < 0:
                self.del_branch()

    # Check for func that deletes branch if a condition is met

    problem = Problem()

    problem.solve()

    assert problem.num_branches == 1


def test_del_branch_2():
    class Problem(PyEquations):

        def __init__(self):
            super().__init__([
                'x'
            ])

        @eq
        def eq1(self):
            return self.x ** 2, 4

        @func
        def constraint(self):
            if self.x > 0:
                self.del_branch()

    # Check for func that deletes branch if the inverse of the previous condition is met

    problem = Problem()

    problem.solve()

    assert problem.num_branches == 1


def test_get_branches_var():
    class Problem(PyEquations):

        def __init__(self):
            super().__init__([
                'x', 'y'
            ])

        @eq
        def eq1(self):
            return self.x ** 2, 4

        @eq
        def eq2(self):
            return self.y, 24

    # Check all possible values for a single variable given the solution branches
    problem = Problem()

    problem.solve()

    assert problem.num_branches == 2

    assert set(problem.get_var_vals('x')) == {-2, 2}
    assert problem.get_var_vals('y') == [24]


def test_get_branches_var2():
    class Problem(PyEquations):

        def __init__(self):
            super().__init__([
                'x', 'y', 'a', 'b', 'c'
            ])

        @eq
        def eq1(self):
            return 2 * self.x ** 2 + 3 * self.y ** 2, 1

        @eq
        def eq2(self):
            return self.x ** 2, self.y ** 2

        @eq
        def eq3(self):
            return self.a, self.b + self.c

        @eq
        def eq4(self):
            return self.b, 3 * self.c + self.a

        @eq
        def eq5(self):
            return self.c, self.a ** 2 - 4

    # Check all possible values for a single variable given the solution branches
    # Except now there are 8 branches
    # And, except for 'c' all variables have two possible values
    problem = Problem()

    problem.solve()

    assert problem.num_branches == 8

    assert set(problem.get_var_vals('x')) == {sqrt(5) / 5, -sqrt(5) / 5}
    assert set(problem.get_var_vals('y')) == {sqrt(5) / 5, -sqrt(5) / 5}
    assert problem.get_var_vals('a') == [2, -2]
    assert problem.get_var_vals('b') == [2, -2]
    assert problem.get_var_vals('c') == [0]


def test_incorrect_functions():
    class InheritedClass(PyEquations):

        def __init__(self):
            super().__init__([
                'x', 'y'
            ])

        @func
        def calc_x(self):
            return self.x

        @eq
        def calc_y(self):
            return 1

    inherit = InheritedClass()

    try:
        inherit.solve()
    except RuntimeError:
        assert True
    except TypeError:
        assert True
    else:
        assert False


def test_silicon():
    n_i = 1.07e10 * cm ** -3

    class Silicon(PyEquations):

        def __init__(self):

            super().__init__({
                'Si_type': 'Silicon type',
                'N_a': 'Acceptor concentration',
                'N_d': 'Donor concentration',
                'n_oN': 'Thermal equilibrium electron concentration in n-type silicon',
                'p_oP': 'Thermal equilibrium hole concentration in p-type silicon',
                'n_oP': 'Thermal equilibrium electron concentration in p-type silicon',
                'p_oN': 'Thermal equilibrium hole concentration in n-type silicon'
            })

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
            return self.p_oP, n_i ** 2 / self.n_oP

        @eq
        def calc_n_oN1(self):
            return self.n_oN, n_i ** 2 / self.p_oN

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


def test_kinematic():
    class Kinematic(PyEquations):

        def __init__(self):
            super().__init__({
                'x_0': 'Initial position',
                'x_f': 'Final position',
                'v_0': 'Initial velocity',
                'v_f': 'Final velocity',
                'a': 'Acceleration',
                't': 'Time'
            })

        @eq
        def calc_v_f(self):
            return self.v_f, self.v_0 + self.a * self.t

        @eq
        def calc_x_f(self):
            return self.x_f, self.x_0 + self.v_0 * self.t + 0.5 * self.a * self.t ** 2

        @eq
        def calc_v_f_2(self):
            return self.v_f ** 2, self.v_0 ** 2 + 2 * self.a * (self.x_f - self.x_0)

        @eq
        def calc_x_f_2(self):
            return self.x_f, self.x_0 + 0.5 * (self.v_0 + self.v_f) * self.t

    k = Kinematic()

    k.x_0 = 100 * meter
    k.v_0 = 3 * meter / second
    k.a = -9.8 * meter / second ** 2
    k.t = 2 * second

    k.solve()

    # Check that only one solution was found
    assert k.num_branches == 1

    # Calculated values are correct
    assert within_tolerance(k.x_f, 86.4 * meter)
    assert within_tolerance(k.v_f, -16.6 * meter / second)

    # Original values are maintained
    assert k.x_0 == 100 * meter
    assert k.v_0 == 3 * meter / second
    assert k.a == -9.8 * meter / second ** 2
    assert k.t == 2 * second

    # Create another object instead with unknown initial velocity and time
    k = Kinematic()

    k.x_0 = 100 * meter
    k.v_f = -16.6 * meter / second
    k.x_f = 86.4 * meter
    k.a = -9.8 * meter / second ** 2

    # Re-solve the equations
    k.solve()

    # Check that there are two solution branches
    assert k.num_branches == 2

    assert set(k.get_var_vals('v_0')) == {3.0 * meter / second, -3.0 * meter / second}
    assert set(k.get_var_vals('t')) == {2.0 * second, 68 / 49 * second}


def test_kinematic_parse():
    class Kinematic(PyEquations):

        def __init__(self):
            super().__init__({
                'x_0': 'Initial position',
                'x_f': 'Final position',
                'v_0': 'Initial velocity',
                'v_f': 'Final velocity',
                'a': 'Acceleration',
                't': 'Time'
            })

        @eq
        def calc_v_f(self):
            return self.v_f, self.v_0 + self.a * self.t

        @eq
        def calc_x_f(self):
            return self.x_f, self.x_0 + self.v_0 * self.t + 0.5 * self.a * self.t ** 2

        @eq
        def calc_v_f_2(self):
            return self.v_f ** 2, self.v_0 ** 2 + 2 * self.a * (self.x_f - self.x_0)

        @eq
        def calc_x_f_2(self):
            return self.x_f, self.x_0 + 0.5 * (self.v_0 + self.v_f) * self.t

        @func
        def parse(self):
            if self.v_0 < 0:
                self.del_branch()

    # Identical equations as before, just with arbitrary parse function
    # Would be better applied with negative time, but this matches previous test
    k = Kinematic()

    k.x_0 = 100 * meter
    k.v_0 = 3 * meter / second
    k.a = -9.8 * meter / second ** 2
    k.t = 2 * second

    k.solve()

    # Calculated values are correct
    assert within_tolerance(k.x_f, 86.4 * meter)
    assert within_tolerance(k.v_f, -16.6 * meter / second)

    # Original values are maintained
    assert k.x_0 == 100 * meter
    assert k.v_0 == 3 * meter / second
    assert k.a == -9.8 * meter / second ** 2
    assert k.t == 2 * second

    # Create another object instead with unknown initial velocity and time
    k = Kinematic()

    k.x_0 = 100 * meter
    k.v_f = -16.6 * meter / second
    k.x_f = 86.4 * meter
    k.a = -9.8 * meter / second ** 2

    # Re-solve the equations
    k.solve()

    # Check that there are two solution branches
    assert k.num_branches == 1

    assert set(k.get_var_vals('v_0')) == {3.0 * meter / second}
    assert set(k.get_var_vals('t')) == {2.0 * second}


def test_auto_del_branch():
    class Problem(PyEquations):

        def __init__(self):
            super().__init__([
                'x', 'y'
            ])

        @eq
        def eq1(self):
            return self.x ** 2, 16

        @eq
        def eq2(self):
            return self.x + self.y, 6

        @eq
        def eq3(self):
            return self.y - self.x, -2

    # With this system, a^2 = 16 creates branches for a = 4 and a = -4
    # However, the second equation is only satisfied for a = 4
    # This tests that the branch for a = -4 is deleted

    p = Problem()

    p.solve()

    assert p.num_branches == 1


def test_multilevel_inheritance():

    # Also tests add_variables from context_stack
    class Base(PyEquations):

        def __init__(self):
            super().__init__([
                'x', 'y'
            ])

        @eq
        def eq1(self):
            return self.x + self.y, 6

        @eq
        def eq2(self):
            return self.x - self.y, 2

    class Child(Base):

        def __init__(self):
            super().__init__()
            self.add_variables([
                'z'
            ])


        @eq
        def eq3(self):
            return self.z, self.x * self.y

    class Grandchild(Child):

        def __init__(self):
            super().__init__()
            self.add_variables([
                'a'
            ])

        @eq
        def eq4(self):
            return self.a, self.z ** 2

    g = Grandchild()

    g.solve()

    expected = [{'a': 64, 'x': 4, 'y': 2, 'z': 8}]

    assert_dicts_equal(g.vars, expected)


def test_system_lock():

    class Problem(PyEquations):

        def __init__(self):
            super().__init__([
                'x', 'y'
            ])

        @eq
        def eq1(self):
            return self.x ** 2, 16

        @eq
        def eq2(self):
            return self.x + self.y, 6

        @eq
        def eq3(self):
            return self.y - self.x, -2

    p = Problem()

    p.solve()

    # Check that the system is locked
    assert p.locked

    # Check that a runtime error is raised when trying to add a variable
    with raises(RuntimeError):
        p.add_variables(['z'])

# Create another class that will only have one branch
    class Problem(PyEquations):

        def __init__(self):
            super().__init__([
                'x', 'y'
            ])

        @eq
        def eq1(self):
            return self.x, 10

        @eq
        def eq2(self):
            return self.y, 10

    p = Problem()

    p.solve()

    # Check that the system is not locked as there is only one branch
    assert not p.locked

    # Create a new object to avoid solving the same system twice (warning)
    p = Problem()

    # Check that we can add a variable
    # Note -- this is kind of useless since we cannot add a new function or equation -- noted in docs # TODO
    p.add_variables({'z': 'z position'})

    # Resolve the system
    p.solve()

    # Check that the system is still not locked
    assert not p.locked

    # Check that the variable description was added
    assert p.var_descriptions['z'] == 'z position'


def test_save_root_branch():
    class Problem(PyEquations):

        def __init__(self):
            super().__init__([
                'x', 'y'
            ])

        @eq
        def eq1(self):
            return self.x ** 2, 64

        @eq
        def eq2(self):
            return self.x - self.y, 2

        @eq
        def eq3(self):
            return self.x + self.y, 6

    # This test has two immediate branches, x = 8 and x = -8
    # The second equation has one solution, nether of which are x = -8 or x = 8
    # This tests that the root branch is saved so there is always at least one branch

    p = Problem()

    # The error ensure that it is known that there are no solutions; the branch is preserved
    with raises(RuntimeError):
        p.solve()


def test_var_descriptions():
    class Problem(PyEquations):

        def __init__(self):
            super().__init__({
                'x': 'x position',
                'y': 'y position',
                'z': 'z position'
            })

        @eq
        def eq1(self):
            return self.x - self.y, 2

        @eq
        def eq2(self):
            return self.x + self.y, 6

    p = Problem()

    expected = {'x': 'x position', 'y': 'y position', 'z': 'z position'}

    assert p.var_descriptions == expected


def test_num_branches():
    class Problem(PyEquations):

        def __init__(self):
            super().__init__([
                'x'
            ])

        @eq
        def eq1(self):
            return self.x ** 2, 16

    p = Problem()

    p.solve()

    assert p.num_branches == 2


def test_vars():
    class Problem(PyEquations):

        def __init__(self):
            super().__init__([
                'x'
            ])

        @eq
        def eq1(self):
            return self.x ** 2, 16

    p = Problem()

    p.solve()

    expected = [{'x': 4}, {'x': -4}]

    assert_dicts_equal(p.vars, expected)


def test_get_var_description():
    class Problem(PyEquations):

        def __init__(self):
            super().__init__({
                'x': 'x position',
                'y': 'y position',
                'z': 'z position'
            })

    p = Problem()

    assert p.var_description('x') == 'x position'
    assert p.var_description('y') == 'y position'
    assert p.var_description('z') == 'z position'


def test_complicated_solution_set_units():
    class Inherit(PyEquations):

        def __init__(self):
            super().__init__([
                'x', 'y', 'z', 'w'
            ])

        @eq
        def eq2(self):
            return self.y ** 2, self.z ** 2 + self.w

        @eq
        def eq3(self):
            return self.y, 8 * self.z

        @eq
        def eq4(self):
            return self.z, self.y + self.x

    inherit = Inherit()

    # Same as the previous test_complicated_solution_set, but with units
    # Chosen because the solution set is complicated and the units could be a source of error

    inherit.w = 64 * meter

    inherit.solve()

    assert inherit.num_branches == 2

    expected = [{'w': 64 * meter, 'x': 8 * sqrt(7) * sqrt(meter) / 3, 'y': -64 * sqrt(7) * sqrt(meter) / 21,
                 'z': -8 * sqrt(7) * sqrt(meter) / 21},
                {'w': 64 * meter, 'x': -8 * sqrt(7) * sqrt(meter) / 3, 'y': 64 * sqrt(7) * sqrt(meter) / 21,
                 'z': 8 * sqrt(7) * sqrt(meter) / 21}]

    assert_dicts_equal(expected, inherit.vars)


def test_vars_decimal():
    class Problem(PyEquations):

        def __init__(self):
            super().__init__([
                'x'
            ])

        @eq
        def eq1(self):
            return self.x ** 2, 15

    p = Problem()

    p.solve()

    expected = [{'x': -3.872983346207417022285041735}, {'x': 3.872983346207417022285041735}]

    actual = p.vars_decimal

    # Check that the values are within 1e-10 of the expected values and consider that the order could be different
    if abs(expected[0]['x'] - actual[0]['x']) > 1e-10:
        assert abs(expected[0]['x'] - actual[1]['x']) < 1e-10
        assert abs(expected[1]['x'] - actual[0]['x']) < 1e-10
    else:
        assert abs(expected[0]['x'] - actual[0]['x']) < 1e-10
        assert abs(expected[1]['x'] - actual[1]['x']) < 1e-10


def test_var_vals_decimal():
    class Kinematic(PyEquations):

        # Define our variables with optional descriptions
        def __init__(self):
            super().__init__({
                'x_0': 'initial position',
                'x_f': 'final position',
                'v_0': 'initial velocity',
                'v_f': 'final velocity',
                'a': 'acceleration',
                't': 'time'
            })

        # Define our equations by noting them with the eq decorator
        # An '=' sign is replaced with a ',' thereby returning a tuple
        @eq
        def calc_v_f(self):
            return self.v_f, self.v_0 + self.a * self.t

        @eq
        def calc_x_f(self):
            return self.x_f, self.x_0 + self.v_0 * self.t + 0.5 * self.a * self.t ** 2

        @eq
        def calc_v_f_2(self):
            return self.v_f ** 2, self.v_0 ** 2 + 2 * self.a * (self.x_f - self.x_0)

        @eq
        def calc_x_f_2(self):
            return self.x_f, self.x_0 + 0.5 * (self.v_0 + self.v_f) * self.t

    k = Kinematic()

    k.x_0 = 100 * meter
    k.v_0 = 3 * meter / second
    k.a = -10 * meter / second ** 2
    k.x_f = 0 * meter

    k.solve()

    assert k.num_branches == 2

    # Asserting that the dictionaries here is noq quite easy because the values are all decimals and I can only
    # represent finite precision decimals in the expected dictionary

    # Use get_var_vals to get the values of the variables in the solution set

    assert_set_values_within_tolerance(set(k.get_var_vals_decimal('x_0')), {100. * meter})
    assert_set_values_within_tolerance(set(k.get_var_vals_decimal('x_f')), {0.})
    assert_set_values_within_tolerance(set(k.get_var_vals_decimal('v_0')), {3. * meter / second})
    assert_set_values_within_tolerance(set(k.get_var_vals_decimal('v_f')),
                                       {44.8218696620299 * meter / second, -44.8218696620299 * meter / second})
    assert_set_values_within_tolerance(set(k.get_var_vals_decimal('a')), {-10. * meter / second ** 2})
    assert_set_values_within_tolerance(set(k.get_var_vals_decimal('t')),
                                       {4.78218696620299 * second, -4.18218696620299 * second})


def test_warn_if_resolve():
    class Problem(PyEquations):
        def __init__(self):
            super().__init__({
                'x': 'x',
                'y': 'y'
            })

        @eq
        def eq1(self):
            return self.x, self.y + 4

        @eq
        def eq2(self):
            return self.y, self.x ** 2 * 5 - 10

    p = Problem()

    p.solve()

    # Mess with solution
    with warns(UserWarning):
        p.x = 5.64532323 * meter

    # Should warn when we try to solve again
    with warns(UserWarning):
        p.solve()
