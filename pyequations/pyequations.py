from itertools import combinations

from sympy import symbols, Symbol, solve, Eq, Number
from sympy.physics.units import cm


def eq(f: callable) -> callable:
    """
    Decorator to mark a function as a calculation function
    :param f: The function to decorate
    :return: The decorated function
    """

    setattr(f, '__equation__', True)
    return f


def func(f: callable) -> callable:
    """
    Decorator to mark a function as a func
    :param f: The function to decorate
    :return: The decorated function
    """

    setattr(f, '__user_func__', True)
    return f


def _get_symbols(equations: [Eq]) -> tuple:
    """
    Get all the symbols in an equation
    :param equations: The equations
    :return: A tuple of all the symbols
    """

    # Return a tuple of all the symbols in the equation
    return tuple({sym for e in equations if isinstance(e, Eq) for sym in e.free_symbols})


def _is_solution(solution) -> bool:
    """
    Check if the solution is a numeric solution
    :param solution: The solution to check
    :return: Whether the solution is consistent
    """

    if not bool(solution):
        return False

    # If solution is a list, not a valid solution
    if isinstance(solution, list):
        # If the solution has multiple elements, there are multiple solutions and an exception should be thrown
        if len(solution) > 1:
            raise RuntimeError(f'Equations have multiple solutions: {solution}. Considering using a @func decorated'
                               f' function to solve for the remaining variables.')
        # If the solution has one element, the solution is not fully determined and is not a valid solution
        else:
            return False

    # Loop through the values in the solution
    for value in solution.values():
        # If the value contains free symbols, it is not a numeric solution
        if bool(value.free_symbols):
            return False

    return True


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


class PyEquations:

    def __init__(self):
        self.variable_descriptions = {}
        # Sympy expressions to solve for
        self.eqs = []
        # User defined functions
        self.funcs = []

        # Get all methods defined in the class
        methods = [getattr(self, name) for name in dir(self) if callable(getattr(self, name))]

        # Add all methods that are decorated with @calc to the calculation_functions list
        for method in methods:
            if hasattr(method, '__equation__'):
                self.eqs.append(method)
            elif hasattr(method, '__user_func__'):
                self.funcs.append(method)

    def __setattr__(self, name, value):
        # If the attribute does not exist and the value is a sympy symbol, add it to the class
        if not hasattr(self, name) and isinstance(value, Symbol):
            super().__setattr__(name, value)

        # If the attribute exists and the value is a number, substitute the value into the sympy symbol
        elif hasattr(self, name) and isinstance(value, (int, float, complex)):
            super().__setattr__(name, getattr(self, name).subs(getattr(self, name), value))

        # Otherwise, if the value is a sympy symbol or a number, throw an exception as it was used incorrectly
        elif isinstance(value, Symbol):
            raise Exception(f'Variable {name} already exists')

        elif isinstance(value, (int, float, complex)):
            raise Exception(f'Variable {name} does not exist and cannot be set to a number')

        # Otherwise, use the default __setattr__ method
        else:
            super().__setattr__(name, value)

    def _eval_funcs(self) -> None:
        """
        Evaluate all the user defined functions
        :return: None
        """

        # Loop through all the user defined functions and evaluate them
        for f in self.funcs:
            # Evaluate the function
            try:
                f()
            except Exception:
                continue

    def solve(self) -> None:
        """
        Solve the equations by substituting solutions in place of unknown variables
        Recursively attempts all combinations of equations
        :return: None
        """

        # Evaluate all the user defined functions
        self._eval_funcs()

        # Gather all the equations from the calculation functions that have an unknown variable
        equations = []
        for function in self.eqs:
            result = function()
            if len(result) == 2:
                equations.append(Eq(*result))
            else:
                raise ValueError("Function does not return two elements")

        # If any of the equations are False, the system has no solution, throw an exception
        if false_equations := [e for e in equations if e == False]:
            # Locate the functions that created the false equations
            if (false_functions := [function for function in self.eqs if
                                    Eq(*function()) in false_equations]):
                # Raise an exception with the functions that created the false equations
                raise RuntimeError(f'Equations have no solutions: {false_functions}')

        # Attempt to solve every subgroup of the equations
        for r in range(1, len(equations) + 1):
            for subgroup in combinations(equations, r):

                # If any of the equations are True, we can ignore the subgroup
                if any([e == True for e in subgroup]):
                    continue

                # Attempt to solve the subgroup of equations
                solution = solve(subgroup, *_get_symbols(subgroup))

                # If a solution was found, set the variables to the solution
                if _is_solution(solution):

                    for key, value in solution.items():
                        # Found a solution, set the variable to the solution
                        setattr(self, str(key), value)

                    # If there are still unknown variables, attempt to solve again with the new information
                    self.solve()

                    # Return to prevent further solving (want to utilize the most information possible)
                    return

        # Re-evaluate all the user defined functions in case of new information
        self._eval_funcs()

    def add_var(self, name: str, description: str = '') -> None:
        """
        Add a variable to the class
        :param name: The name of the variable
        :param description: A description of the variable
        :return: None
        """

        # Raise an exception if the variable already exists
        if hasattr(self, name):
            raise Exception(f'Variable {name} already exists')

        # Raise an exception if the name is not a string
        if not isinstance(name, str):
            raise Exception(f'Variable name must be a string')

        # Raise an exception if the name is not a valid attribute name
        if not name.isidentifier():
            raise Exception(f'Variable name must be a valid attribute name')

        # Create a sympy symbol and use setattr to add it to the class
        setattr(self, name, symbols(name))

        # Add the description to the variable
        if isinstance(description, str):
            self.variable_descriptions[name] = description

    def get_var_description(self, name: str) -> str:
        """
        Get the description of a variable
        :param name: The name of the variable
        :return: The description of the variable
        """

        # Raise an exception if the variable does not exist
        if not hasattr(self, name) and name not in self.variable_descriptions:
            raise KeyError(f'Variable {name} does not exist')

        # Return the description of the variable
        return self.variable_descriptions[name]

    def get_var_val(self, name: str) -> Symbol | Number:
        """
        Get the value of a variable
        :param name: The name of the variable
        :return: The value of the variable
        """

        # Raise an exception if the variable does not exist
        if not hasattr(self, name) and name not in self.variable_descriptions:
            raise Exception(f'Variable {name} does not exist')

        # Return the value of the variable
        return getattr(self, name)

    def vars(self) -> dict[str, Symbol | Number]:
        """
        Get all variable
        :return: A dictionary of all variables
        """

        variables = {name: getattr(self, name) for name in sorted(self.variable_descriptions.keys())}

        return variables

    def var_descriptions(self) -> dict[str: str]:
        """
        Get all variable descriptions
        :return: A list of all variable descriptions
        """

        # Return a dictionary of all variable descriptions sorted by variable name
        return {name: self.variable_descriptions[name] for name in sorted(self.variable_descriptions.keys())}

    def solved_vars(self) -> dict[str, Symbol | Number]:
        """
        Get all known variables
        :return: A dictionary of all known variables
        """

        # Return a dictionary of all known variables
        return {name: getattr(self, name) for name in sorted(self.variable_descriptions.keys()) if
                getattr(self, name) != symbols(name)}
