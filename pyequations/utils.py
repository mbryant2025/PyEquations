from sympy import Eq, Symbol, Number, Expr, N, Mul, Add, Pow, simplify
from sympy.physics.units import Quantity, Unit

from pyequations import EPSILON
from pyequations.generate_units_subs import UnitSub


def _is_solved(var) -> bool:
    """
    Check if the variable is solved
    :param var: the attribute to check
    :return: Whether the variable is solved
    """

    return not isinstance(var, Symbol)


def solved(*variables) -> bool:
    """
    Check if all the variables are solved
    :param variables: The variables to check
    :return: Whether all the variables are solved
    """

    return all([_is_solved(var) for var in variables])


def get_symbols(equations: [Eq]) -> tuple:
    """
    Get all the symbols in an equation
    :param equations: The equations
    :return: A tuple of all the symbols
    """

    # Return a tuple of all the symbols in the equation
    # Cannot use sympy.atoms because that would return all the symbols PLUS the units
    return tuple({sym for e in equations if isinstance(e, Eq) for sym in e.free_symbols})


def remove_units(expr: Symbol | Number) -> Expr | Number | None:
    """
    Remove the units from a given expression
    :param expr: An expression
    :return: The expression with the units removed
    """
    if expr is None:
        return None
    if isinstance(expr, int | float | complex):
        return expr
    if not expr.has(Quantity):
        return expr
    units = expr.subs({x: 1 for x in expr.args if not x.has(Quantity)})
    return expr / units


def is_constant(expr) -> bool:
    """
    Check if the expression is constant
    For example, 2 * cm is constant, but x * cm is not
    Precondition: The expression must be simplified
    :param expr: The expression to check
    :return: Whether the expression is constant
    """

    # If the expression is a number, it is constant
    if isinstance(expr, int | float | complex):
        return True

    # If the expression is a symbol, it is not constant
    if isinstance(expr, Symbol):
        return False

    # If the expression is a unit, it is constant
    if isinstance(expr, Quantity):
        return True

    # If the expression is a number, it is constant
    if isinstance(expr, Number):
        return True

    # If calling N() on the expression is different from the expression, call is_constant on the result
    if (result := N(expr)) != expr:
        return is_constant(result)

    # If the expression is an expression, check if it is constant
    if isinstance(expr, Expr):

        # If the expression is a Mul, check if all the args are constant
        if isinstance(expr, Mul):
            return all(is_constant(arg) for arg in expr.args)

        # If the expression is an Add, check if all the args are constant
        if isinstance(expr, Add):
            return all(is_constant(arg) for arg in expr.args)

        # If the expression is a Pow, check if the base and exponent are constant
        if isinstance(expr, Pow):
            return is_constant(expr.base) and is_constant(expr.exp)

    # If the expression is not a number, symbol, or expression, it is not constant
    return False


def get_units(expr) -> set:
    """
    Get all the units in an expression
    :param expr: The expression
    :return: A set of all the units in the expression
    """

    if isinstance(expr, Expr):
        return expr.atoms(Unit)
    return set()


def get_quantities(expr) -> set:
    """
    Get all the numerical quantities in an expression (ex. 7)
    :param expr: The expression
    :return: A set of all the quantities in the expression
    """

    if isinstance(expr, Expr):
        return N(expr).atoms(Number)
    return set()


def composes_equation(lhs, rhs, min_float=1e-5) -> int:
    """
    Check if the two elements compose an equation
    If there are no free symbols, it is not an equation
    Otherwise, we check that the sides are 'close enough' to be considered equal
    Precondition: The expressions must be simplified
    :param lhs: The left hand side of the equation
    :param rhs: The right hand side of the equation
    :param min_float: The minimum float value observed elsewhere in the system. Used as a reference to zero.
    :return: 1 if the elements compose an equation, 0 if they do not, or -1 if a contradiction is found
    """

    valid, invalid, contradiction = 1, 0, -1

    lhs_constant = is_constant(lhs)
    rhs_constant = is_constant(rhs)

    # If both sides are expressions, check if they are equal
    if not lhs_constant and not rhs_constant:
        equal = False
        # Need to simplify if either side contains units, otherwise the previous simplification is enough
        if get_units(lhs) or get_units(rhs):
            equal = simplify(lhs - rhs) == 0
        else:
            equal = lhs - rhs == 0
        return invalid if equal else valid

    # If either side contains free symbols, check if they are equal
    elif not lhs_constant or not rhs_constant:
        # Still need to check if they are equal
        # Flip the sides if the rhs is an expression
        if lhs_constant:
            lhs, rhs = rhs, lhs
        equal = False
        # Need to simplify if either side contains units, otherwise the previous simplification is enough
        if get_units(lhs) or get_units(rhs):
            equal = simplify(lhs - rhs) == 0
        else:
            equal = lhs - rhs == 0
        return invalid if equal else valid

    # Final case: numeric values on both sides
    # Check if the sides are 'close enough' to be considered equal
    # This includes checking for unit correctness
    # If lhs and rhs are both numbers, check if they are equal
    else:

        # The main things to be careful with here is units
        # The workaround is to substitute all the units with random numbers around 1
        # This is to avoid confusing the epsilon check
        # Note that these random numbers are not the same for each unit

        # Using randomness does have the potential to cause false positives
        # However, this is unlikely to happen in practice and an incorrect result here will likely not cause issues
        # This is because the system will likely be able to solve the system to the same extent, even if one equation is
        # incorrectly considered to be not usable
        # But, just to be sure, we check twice with two different mappings

        # Get all the units in the lhs and rhs
        lhs_units = get_units(lhs)
        rhs_units = get_units(rhs)

        # Make a list of the units, checking for None (no units)
        units = []
        if lhs_units is not None:
            units.extend(lhs_units)
        if rhs_units is not None:
            units.extend(rhs_units)

        # Reference the dictionaries of the units to substitute
        for unit_dict in UnitSub.get_mappings():
            # Test twice since there is the slightest probability that the random numbers will cause a false positive

            # Substitute the units if they exist
            if lhs_units:
                lhs = lhs.subs(unit_dict)

            if rhs_units:
                rhs = rhs.subs(unit_dict)

            sub = float(lhs - rhs)

            # If one of the sides is 0, we can compare with the minimum float found elsewhere
            if lhs == 0 or rhs == 0:
                equal = abs(sub) <= min_float * EPSILON
            else:
                # Otherwise, re-check if the values are equal, scaled by the epsilon and the sum of the values
                # This helps in the case when the numbers are smaller than the epsilon
                equal = abs(sub) <= EPSILON * abs(lhs + rhs)

            # This will only cause false positives -- i.e. we need to recheck only if the values are equal
            if not equal:
                break

        return invalid if equal else contradiction


class BoolWrapper:
    """
    A wrapper for a boolean value
    This exists because we cannot re-initialize without the superclass in PyEquations
    Provides simple functionality to set and get the value
    """

    def __init__(self, val: bool):
        self.val = val

    def __bool__(self):
        return self.val

    def set(self, val: bool):
        self.val = val

    def __repr__(self):
        return str(self.val)


class IntWrapper:
    """
    A wrapper for an integer value
    This exists because we cannot re-initialize without the superclass in PyEquations
    Provides simple functionality to set and get the value
    """

    def __init__(self, val: int):
        self.val = val

    @property
    def value(self):
        return self.val

    def set(self, val: int):
        self.val = val

    def increment(self):
        self.val += 1

    def __repr__(self):
        return str(self.val)


class MinFloatTracker:
    """
    A wrapper for a float value representing the minimum (nonzero) value seen
    """

    def __init__(self):
        self.val = float('inf')

    @property
    def value(self):
        return self.val

    def add(self, val: float):
        """
        Add a value to the tracker
        :param val: The value to add
        :return: None
        """
        if val != 0:
            self.val = min(self.val, val)

    def __repr__(self):
        return str(self.val)
