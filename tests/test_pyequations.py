from sympy import symbols, Eq, sqrt, I
from sympy.physics.units import cm, meter, second
from pyequations import __version__
from pyequations.inheritables import _get_symbols, PyEquations
from pyequations.utils import solved
from pyequations.decorators import eq, func
from pytest import raises


def within_tolerance(expected, actual, percent=0.001):
    return abs(expected - actual) <= abs(expected * percent / 100)


def assert_dicts_equal(expected, actual):
    expected_set = {frozenset(d.items()) for d in expected}
    actual_set = {frozenset(d.items()) for d in actual}

    assert expected_set == actual_set


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
            self.add_var('x')
            self.add_var('y')

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
            self.add_var('x')
            self.add_var('y')
            self.add_var('z')

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
            super().__init__()
            self.add_var('x')
            self.add_var('y')

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
            super().__init__()
            self.add_var('x')
            self.add_var('y')

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
            super().__init__()
            self.add_var('x')
            self.add_var('y')

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
            self.add_var('x')
            self.add_var('y')

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
            self.add_var('x')
            self.add_var('y')
            self.add_var('z')

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
            super().__init__()
            self.add_var('x')
            self.add_var('y')

        @eq
        def calc_x(self):
            return self.x ** 2, 4

        @eq
        def calc_y(self):
            return self.y ** 2, 16

    inherit = InheritedClass()

    inherit.solve()

    # For multiple solutions, should branch for each possible set of solutions
    assert inherit.num_branches() == 4

    assert_dicts_equal([{'x': 2, 'y': 4}, {'x': 2, 'y': -4}, {'x': -2, 'y': 4}, {'x': -2, 'y': -4}], inherit.vars())


def test_multiple_solutions_2():
    class Problem(PyEquations):

        def __init__(self):
            super().__init__()

            self.add_var('x')
            self.add_var('y')

        @eq
        def eq1(self):
            return 2 * self.x ** 2 + 3 * self.y ** 2, 1

        @eq
        def eq2(self):
            return self.x ** 2, self.y ** 2

    p = Problem()

    p.solve()

    # Should be four different solution branches
    assert p.num_branches() == 4

    expected = [{'x': -sqrt(5) / 5, 'y': -sqrt(5) / 5}, {'x': -sqrt(5) / 5, 'y': sqrt(5) / 5},
                {'x': sqrt(5) / 5, 'y': -sqrt(5) / 5}, {'x': sqrt(5) / 5, 'y': sqrt(5) / 5}]

    assert_dicts_equal(expected, p.vars())


def test_some_multiple_some_single_solution():
    class Problem(PyEquations):

        def __init__(self):
            super().__init__()

            self.add_var('x')
            self.add_var('y')
            self.add_var('z')

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
    assert p.num_branches() == 4

    expected = [{'x': -sqrt(5) / 5, 'y': -sqrt(5) / 5, 'z': 10}, {'x': -sqrt(5) / 5, 'y': sqrt(5) / 5, 'z': 10},
                {'x': sqrt(5) / 5, 'y': -sqrt(5) / 5, 'z': 10}, {'x': sqrt(5) / 5, 'y': sqrt(5) / 5, 'z': 10}]

    assert_dicts_equal(expected, p.vars())


def test_some_multiple_some_single_solution_2():
    class Problem(PyEquations):

        def __init__(self):
            super().__init__()

            self.add_var('x')
            self.add_var('y')
            self.add_var('a')
            self.add_var('b')
            self.add_var('c')

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

    assert p.num_branches() == 4

    print(p.vars())

    expected = [{'a': 1, 'b': 2, 'c': 3, 'x': -sqrt(5) / 5, 'y': sqrt(5) / 5},
                {'a': 1, 'b': 2, 'c': 3, 'x': sqrt(5) / 5, 'y': -sqrt(5) / 5},
                {'a': 1, 'b': 2, 'c': 3, 'x': -sqrt(5) / 5, 'y': -sqrt(5) / 5},
                {'a': 1, 'b': 2, 'c': 3, 'x': sqrt(5) / 5, 'y': sqrt(5) / 5}]

    assert_dicts_equal(expected, p.vars())


def test_multiple_multiple_solutions():
    class Problem(PyEquations):

        def __init__(self):
            super().__init__()

            self.add_var('x')
            self.add_var('y')
            self.add_var('a')
            self.add_var('b')
            self.add_var('c')

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

    assert p.num_branches() == 8

    expected = [{'a': -2, 'b': -2, 'c': 0, 'x': -sqrt(5) / 5, 'y': -sqrt(5) / 5},
                {'a': -2, 'b': -2, 'c': 0, 'x': -sqrt(5) / 5, 'y': sqrt(5) / 5},
                {'a': 2, 'b': 2, 'c': 0, 'x': -sqrt(5) / 5, 'y': sqrt(5) / 5},
                {'a': -2, 'b': -2, 'c': 0, 'x': sqrt(5) / 5, 'y': -sqrt(5) / 5},
                {'a': 2, 'b': 2, 'c': 0, 'x': sqrt(5) / 5, 'y': -sqrt(5) / 5},
                {'a': -2, 'b': -2, 'c': 0, 'x': sqrt(5) / 5, 'y': sqrt(5) / 5},
                {'a': 2, 'b': 2, 'c': 0, 'x': sqrt(5) / 5, 'y': sqrt(5) / 5},
                {'a': 2, 'b': 2, 'c': 0, 'x': -sqrt(5) / 5, 'y': -sqrt(5) / 5}]

    assert_dicts_equal(expected, p.vars())


def test_multiple_multiple_solutions_2():
    class Problem(PyEquations):

        def __init__(self):
            super().__init__()

            self.add_var('x')
            self.add_var('y')
            self.add_var('a')
            self.add_var('b')
            self.add_var('c')
            self.add_var('m')

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

    assert p.num_branches() == 16

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

    assert_dicts_equal(expected, p.vars())


def test_complex_solutions():
    class ComplexSystem(PyEquations):

        def __init__(self):
            super().__init__()

            self.add_var('x')

        @eq
        def eq1(self):
            return self.x ** 2 + 4, 0

    # This is a system with complex solutions

    c = ComplexSystem()

    c.solve()

    assert c.num_branches() == 2

    expected = [{'x': -2 * I}, {'x': 2 * I}]

    assert_dicts_equal(expected, c.vars())


def test_infinite_solutions():
    class InheritedClass(PyEquations):

        def __init__(self):
            super().__init__()
            self.add_var('x')
            self.add_var('y')

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
            super().__init__()

            self.add_var('w')
            self.add_var('x')
            self.add_var('y')
            self.add_var('z')

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

    assert inherit.num_branches() == 2

    expected = [{'w': 64, 'x': 8 * sqrt(7) / 3, 'y': -64 * sqrt(7) / 21, 'z': -8 * sqrt(7) / 21},
                {'w': 64, 'x': -8 * sqrt(7) / 3, 'y': 64 * sqrt(7) / 21, 'z': 8 * sqrt(7) / 21}]

    assert_dicts_equal(expected, inherit.vars())


def test_func():
    class InheritedClass(PyEquations):

        def __init__(self):
            super().__init__()
            self.add_var('x')
            self.add_var('y')

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


def test_del_branch():
    class Problem(PyEquations):

        def __init__(self):
            super().__init__()

            self.add_var('x')

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

    assert problem.num_branches() == 1


def test_get_branches_var():
    class Problem(PyEquations):

        def __init__(self):
            super().__init__()

            self.add_var('x')
            self.add_var('y')

        @eq
        def eq1(self):
            return self.x ** 2, 4

        @eq
        def eq2(self):
            return self.y, 2

    # Check all possible values for a single variable given the solution branches
    problem = Problem()

    problem.solve()

    assert problem.num_branches() == 2

    assert problem.get_branches_var('x') == [2, -2]
    assert problem.get_branches_var('y') == [2]


def test_get_branches_var2():
    class Problem(PyEquations):

        def __init__(self):
            super().__init__()

            self.add_var('x')
            self.add_var('y')
            self.add_var('a')
            self.add_var('b')
            self.add_var('c')

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

    assert problem.num_branches() == 8

    assert set(problem.get_branches_var('x')) == {sqrt(5) / 5, -sqrt(5) / 5}
    assert set(problem.get_branches_var('y')) == {sqrt(5) / 5, -sqrt(5) / 5}
    assert problem.get_branches_var('a') == [2, -2]
    assert problem.get_branches_var('b') == [2, -2]
    assert problem.get_branches_var('c') == [0]


def test_incorrect_functions():
    class InheritedClass(PyEquations):

        def __init__(self):
            super().__init__()
            self.add_var('x')
            self.add_var('y')

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
            super().__init__()
            self.add_var('Si_type', 'Silicon type')
            self.add_var('N_a', 'Acceptor concentration')
            self.add_var('N_d', 'Donor concentration')
            self.add_var('n_oN', 'Thermal equilibrium electron concentration in n-type silicon')
            self.add_var('p_oP', 'Thermal equilibrium hole concentration in p-type silicon')
            self.add_var('n_oP', 'Thermal equilibrium electron concentration in p-type silicon')
            self.add_var('p_oN', 'Thermal equilibrium hole concentration in n-type silicon')

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
            super().__init__()
            self.add_var('x_0', 'Initial position')
            self.add_var('x_f', 'Final position')
            self.add_var('v_0', 'Initial velocity')
            self.add_var('v_f', 'Final velocity')
            self.add_var('a', 'Acceleration')
            self.add_var('t', 'Time')

        @eq
        def calc_v_f(self):
            return self.v_f, self.v_0 + self.a * self.t

        @eq
        def calc_x_f(self):
            return self.x_f, self.x_0 + self.v_0 * self.t + 0.5 * self.a * self.t ** 2

        @eq
        def calc_v_f2(self):
            return self.v_f ** 2, self.v_0 ** 2 + 2 * self.a * (self.x_f - self.x_0)

        @eq
        def calc_x_f2(self):
            return self.x_f, self.x_0 + 0.5 * (self.v_0 + self.v_f) * self.t

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

    # Clear the inital position and time
    k.clear_var('x_0', 't')

    # Check that the initial position and time are cleared
    assert k.x_0 == symbols('x_0')
    assert k.t == symbols('t')

    # Re-solve the equations
    k.solve()

    # Calculated values are correct
    assert within_tolerance(k.x_0, 100.0 * meter)
    assert within_tolerance(k.t, 2.0 * second)

    # Original values are maintained
    assert within_tolerance(k.x_f, 86.4 * meter)
    assert within_tolerance(k.v_f, -16.6 * meter / second)
    assert within_tolerance(k.v_0, 3.0 * meter / second)
    assert within_tolerance(k.a, -9.8 * meter / second ** 2)

    # Clear the initial velocity and time
    k.clear_var('v_0', 't')

    # Check that the initial velocity and time are cleared
    assert k.v_0 == symbols('v_0')
    assert k.t == symbols('t')

    # Re-solve the equations
    k.solve()

    # Check that there are two solution branches
    assert k.num_branches() == 2

    print(k.get_branches_var('v_0'))

    assert set(k.get_branches_var('v_0')) == {3.0 * meter / second, -3.0 * meter / second}
    assert set(k.get_branches_var('t')) == {2.0 * second, 68 / 49 * second}


def test_kinematic_parse():
    class Kinematic(PyEquations):

        def __init__(self):
            super().__init__()
            self.add_var('x_0', 'Initial position')
            self.add_var('x_f', 'Final position')
            self.add_var('v_0', 'Initial velocity')
            self.add_var('v_f', 'Final velocity')
            self.add_var('a', 'Acceleration')
            self.add_var('t', 'Time')

        @eq
        def calc_v_f(self):
            return self.v_f, self.v_0 + self.a * self.t

        @eq
        def calc_x_f(self):
            return self.x_f, self.x_0 + self.v_0 * self.t + 0.5 * self.a * self.t ** 2

        @eq
        def calc_v_f2(self):
            return self.v_f ** 2, self.v_0 ** 2 + 2 * self.a * (self.x_f - self.x_0)

        @eq
        def calc_x_f2(self):
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

    # Clear the initial velocity and time
    k.clear_var('v_0', 't')

    # Check that the initial velocity and time are cleared
    assert k.v_0 == symbols('v_0')
    assert k.t == symbols('t')

    # Re-solve the equations
    k.solve()

    # Check that there are two solution branches
    assert k.num_branches() == 1

    assert set(k.get_branches_var('v_0')) == {3.0 * meter / second}
    assert set(k.get_branches_var('t')) == {2.0 * second}

# TODO test more with units

# TODO test get_var_vals

# TODO test one branch fails

# TODO test change propagates

# TODO test getter functions

# TODO note how we won't remove final branch
