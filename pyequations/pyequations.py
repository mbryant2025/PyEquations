from itertools import combinations

from sympy import symbols, Symbol, solve, Eq, Number, N
from sympy.physics.units import cm


def calc(func: callable) -> callable:
    """
    Decorator to mark a function as a calculation function
    :param func: The function to decorate
    :return: The decorated function
    """

    # Throw exception if the decorated function does not return a sympy expression TODO
    # if not isinstance(func(), Symbol):
    #     raise Exception(f'Function {func.__name__} must return a sympy expression')

    setattr(func, '__calc__', True)
    return func


def _get_symbols(eqs: [Eq]) -> tuple:
    """
    Get all the symbols in an equation
    :param eqs: The equations
    :return: A tuple of all the symbols
    """

    # Return a tuple of all the symbols in the equation
    return tuple({sym for eq in eqs if isinstance(eq, Eq) for sym in eq.free_symbols})


def _is_solution(solution) -> bool:
    """
    Check if the solution is a numeric solution
    :param solution: The solution to check
    :return: Whether the solution is consistent
    """

    if not bool(solution):
        return False

    # If solution is not a dictionary or if any of the values are lists, there are multiple solutions
    if not isinstance(solution, dict) or any([isinstance(value, list) for value in solution.values()]):
        raise Exception(f'Equations have multiple solutions: {solution}')
        # TODO add consider adding positive, real, or @func

    # Loop through the values in the solution
    for value in solution.values():
        # If the value contains free symbols, it is not a numeric solution
        if bool(value.free_symbols):
            return False

    return True


class PyEquations:

    def __init__(self):
        self.variable_descriptions = {}
        self.calculation_functions = []

        # Get all methods defined in the class
        methods = [getattr(self, name) for name in dir(self) if callable(getattr(self, name))]

        # Add all methods that are decorated with @calc to the calculation_functions list
        for method in methods:
            if hasattr(method, '__calc__'):
                self.calculation_functions.append(method)

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

    def solve(self) -> None:
        """
        Solve the equations by substituting solutions in place of unknown variables
        Recursively attempts all combinations of equations
        :return: None
        """

        # Gather all the equations from the calculation functions that have an unknown variable
        equations = [Eq(*function()) for function in self.calculation_functions]

        # If any of the equations are False, the system has no solution, throw an exception
        if false_equations := [eq for eq in equations if eq == False]:
            # Locate the functions that created the false equations
            if (false_functions := [function for function in self.calculation_functions if
                                    Eq(*function()) in false_equations]):
                # Raise an exception with the functions that created the false equations
                raise Exception(f'Equations have no solutions: {false_functions}')

        # TODO check for invalid functions made by the user

        # Attempt to solve every subgroup of the equations
        for r in range(1, len(equations) + 1):
            for subgroup in combinations(equations, r):

                # If any of the equations are True, we can ignore the subgroup
                if any([eq == True for eq in subgroup]):
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

    def add_variable(self, name: str, description: str = '') -> None:
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
        self.variable_descriptions[name] = description

    def get_variable_description(self, name: str) -> str:
        """
        Get the description of a variable
        :param name: The name of the variable
        :return: The description of the variable
        """

        # Raise an exception if the variable does not exist
        if not hasattr(self, name) and name not in self.variable_descriptions:
            raise Exception(f'Variable {name} does not exist')

        # Return the description of the variable
        return self.variable_descriptions[name]

    def get_variable_value(self, name: str) -> Symbol | Number:
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

    from sympy import Number, Symbol

    def all_variables(self) -> dict[str, Symbol | Number]:
        """
        Get all variable
        :return: A dictionary of all variables
        """

        variables = {name: getattr(self, name) for name in sorted(self.variable_descriptions.keys())}

        return variables

    def get_all_variable_descriptions(self):  # TODO type hint
        """
        Get all variable descriptions
        :return: A list of all variable descriptions
        """

        # Return a dictionary of all variable descriptions
        return sorted(self.variable_descriptions.copy())

    def get_all_variables_and_descriptions(self) -> dict[str, Symbol | Number]:
        """
        Get all variables and descriptions
        :return: A list of all variables and descriptions
        """

        # Have the key be "variable_name - description"
        return {f'{name} - {self.variable_descriptions[name]}': getattr(self, name) for name in
                sorted(self.variable_descriptions.keys())}
