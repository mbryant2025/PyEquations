from itertools import combinations
from sympy import symbols, Symbol, solve, Eq, Number
from copy import deepcopy


def _get_symbols(equations: [Eq]) -> tuple:
    """
    Get all the symbols in an equation
    :param equations: The equations
    :return: A tuple of all the symbols
    """

    # Return a tuple of all the symbols in the equation
    return tuple({sym for e in equations if isinstance(e, Eq) for sym in e.free_symbols})


def _is_solved(var) -> bool:
    """
    Check if the variable is solved
    :param var: the attribute to check
    :return: Whether the variable is solved
    """

    return not isinstance(var, Symbol)


class PyEquations:

    def __init__(self):
        self.variable_descriptions = {}
        # Sympy expressions to solve for
        self.eqs = []
        # User defined functions
        self.funcs = []
        # Branches for multiple solutions
        self.children_branches = {self}
        # Parent branch
        self.parent_link = None
        # Root branch
        self.root_link = self

        # Get all methods defined in the class
        methods = [getattr(self, name) for name in dir(self) if callable(getattr(self, name))]

        # Add all methods that are decorated with @calc to the calculation_functions list
        for method in methods:
            if hasattr(method, '__equation__'):
                self.eqs.append(method)
            elif hasattr(method, '__user_func__'):
                self.funcs.append(method)

    def _super_setattr(self, name, value):
        """
        Set the attribute for the class using the default __setattr__ method
        :param name: the attribute name
        :param value: the attribute value
        :return: None
        """
        super().__setattr__(name, value)

    def __setattr__(self, name, value):
        """
        Set the attribute for all branches
        :param name: the attribute name
        :param value: the attribute value
        :return: None
        """

        # If the attribute does not exist and the value is a sympy symbol, add it to the class for all branches
        if not hasattr(self, name) and isinstance(value, Symbol):
            for branch in self.children_branches:
                branch._super_setattr(name, value)

        # If the attribute exists and the value is a number, substitute the value into the sympy symbol for all branches
        elif hasattr(self, name) and isinstance(value, (int, float, complex)):
            for branch in self.children_branches:
                branch._super_setattr(name, getattr(self, name).subs(getattr(self, name), value))

        # Otherwise, if the value is a sympy symbol or a number, throw an exception as it was used incorrectly
        elif isinstance(value, Symbol):
            raise RuntimeError(f'Variable {name} already exists')

        elif isinstance(value, (int, float, complex)):
            raise Exception(f'Variable {name} does not exist and cannot be set to a number')

        # If the added attribute is a function, add it to all branches
        elif callable(value):
            for branch in self.children_branches:
                branch._super_setattr(name, value)

        # Otherwise, use the default __setattr__ method for this branch
        else:
            super().__setattr__(name, value)

    def _super_delattr(self, name):
        """
        Delete the attribute for the class using the default __delattr__ method
        :param name: the attribute name
        :return: None
        """
        super().__delattr__(name)

    def __delattr__(self, item):
        """
        Delete the attribute for all branches
        :param item: the attribute name
        :return: None
        """

        for branch in self.children_branches:
            branch._super_delattr(item)

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
                continue # TODO nmake custom exception

    def _verify_and_extract_solution(self, solution, target_variables) -> dict | None:
        """
        Check if the solution is a numeric solution
        If multiple solutions, branch the solution set
        :param solution: The solution to check
        :param target_variables: The corresponding variables to check, match the order of the solution
        :return: A dict containing the solution for the branch or None if the solution is not valid
        """

        if not bool(solution):
            return None

        symbol_names = [str(sym) for sym in target_variables]

        # If solution is a list, it is not an individual solution
        if isinstance(solution, list):
            # If the solution has multiple elements, there are multiple solutions
            # and a new solution branch should be created
            if len(solution) > 1:
                # [(solution 1), (solution 2), ...]
                valid_sols = []

                for sol in solution:
                    add_flag = True
                    # If the sol itself is composed of multiple variables, loop through them
                    if isinstance(sol, tuple):
                        # [(x, y, z), (x, y, z), ...]
                        for variable in sol:
                            # If the variable contains free symbols, it is not a numeric solution
                            if bool(variable.free_symbols):
                                add_flag = False
                                break

                    # Otherwise, for one variable, if the variable contains free symbols, it is not a numeric solution
                    elif bool(sol.free_symbols):
                        # [x, x, ...]
                        add_flag = False
                        break

                    if add_flag:
                        valid_sols.append(sol)

                if len(valid_sols) == 0:
                    return None

                # With the valid solutions, create a new solution branch for each solution after the first
                for sol in valid_sols[1:]:
                    # Want to make an exact copy of the current PyEquations object data, except for the parent indicator
                    # For each solution, create a new branch and propagate this new branch to the root

                    # Create a new solution branch
                    new_branch = deepcopy(self)
                    new_branch.parent_link = self

                    current_branch = new_branch
                    while current_branch.parent_link is not None:
                        current_branch.parent_link.children_branches.add(new_branch)
                        current_branch = current_branch.parent_link

                    # Add the solution to the new branch
                    for v, s in zip(symbol_names, sol):
                        new_branch.__setattr__(v, s)

                    # Continue solving the new branch with this sol
                    new_branch.solve()

                # Return the first solution
                # Create a dictionary to map the target variables to the solution
                return dict(zip(target_variables, valid_sols[0]))

            # If it is a list with one element, it is not a complete solution
            else:
                return None

        elif isinstance(solution, dict):
            # Trivial case, single solution for all variables
            # Loop through the variables in the solution
            for value in solution.values():
                # If the value contains free symbols, it is not a numeric solution
                if bool(value.free_symbols):
                    return None

            # In this case, we will already have a dictionary
            return solution

        else:
            # Unknown type, not a valid solution. Throw an exception
            raise RuntimeError(f'Unknown solution type {solution}')

    def _run_solver_this_branch(self) -> None:
        """
        Solve the equations by substituting solutions in place of unknown variables
        Recursively attempts all combinations of equations
        :return: None
        """

        # TODO call solve for all branches

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

        # If any of the equations are False, the system has no solution, throw an exception # TODO check for false
        # if false_equations := [e for e in equations if e == False]:
        #     # Locate the functions that created the false equations
        #     if (false_functions := [function for function in self.eqs if
        #                             Eq(*function()) in false_equations]):
        #         # Raise an exception with the functions that created the false equations
        #         raise RuntimeError(f'Equations have no solutions: {false_functions}')

        # Attempt to solve every subgroup of the equations
        for r in range(1, len(equations) + 1):
            for subgroup in combinations(equations, r):

                # If any of the equations are True, we can ignore the subgroup
                if any([e == True for e in subgroup]):
                    continue

                target_variables = _get_symbols(subgroup)

                # Attempt to solve the subgroup of equations
                solution = solve(subgroup, *target_variables)

                # Verify the solution is valid, handle solution branching
                sol = self._verify_and_extract_solution(solution, target_variables)

                # If a solution was found, set the variables to the solution in this branch
                if sol is not None:
                    for key, value in sol.items():
                        # Found a solution, set the variable to the solution
                        setattr(self, str(key), value)

                    # If there are still unknown variables, attempt to solve again with the new information
                    self.solve()

                    # Return to prevent further solving (want to utilize the most information possible)
                    return

        # Re-evaluate all the user defined functions in case of new information
        self._eval_funcs()

    def solve(self) -> None:
        """
        Trigger to solve the equations on all existing branches
        :return: None
        """

        for branch in [b for b in self.children_branches]:
            branch._run_solver_this_branch()

    def add_var(self, name: str, description: str = '') -> None:
        """
        Add a variable to the class (for all branches)
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

    def _clear_single_var(self, name) -> None:
        """
        Returns a variable to a variable (from a value, applies for all branches)
        Used for changing a value back to a variable
        :param name: The name of the variable
        :return: None
        """

        # Raise an exception if the variable does not exist
        if not hasattr(self, name):
            raise RuntimeError(f'Variable {name} does not exist')

        # Remove the variable from the class
        delattr(self, name)

        # Add the variable back to the class
        self.add_var(name)

    def clear_var(self, *variables) -> None:
        """
        Returns variables to variables
        Used for changing values back to variables
        :param variables: The names of the variables
        :return: None
        """

        # Loop through all the variables
        for variable in variables:
            # Clear the variable
            self._clear_single_var(variable)

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

    def _get_this_branch_var(self, name: str) -> Symbol | Number:
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

    def get_branches_var(self, name: str) -> list[Symbol | Number]:
        """
        Get the value of a variable for all branches
        :param name: The name of the variable
        :return: The value of the variable
        """

        # Return the value of the variable
        return list(set([branch._get_this_branch_var(name) for branch in self.children_branches]))

    def _get_this_branch_vars(self):
        """
        Get all variables in the branch
        :return: A dictionary of all variables in the branch
        """

        # Return a dictionary of all variables in the branch
        return {name: getattr(self, name) for name in sorted(self.variable_descriptions.keys())}

    def vars(self) -> list[dict[str, Symbol | Number]]:
        """
        Get all variables among all solution branches
        :return: A list of dictionaries of all variables for each solution branch
        """

        # Return a list of all variables for each solution branch
        return [branch._get_this_branch_vars() for branch in self.children_branches]

    def num_branches(self) -> int:
        """
        Get the number of solution branches
        :return: The number of solution branches
        """

        # Return the number of solution branches
        return len(self.children_branches)

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

    def del_branch(self) -> None:
        """
        Delete the current branch
        :return: None
        """

        # Return if only one branch (children includes self)
        # Return rather than raise exception because this is called potentially many times
        if len(self.root_link.children_branches) == 1:
            return

        # If the target branch is the root branch, reassign the root branch for all branches
        if self is self.root_link:
            # Since we know that there is at least 2 branches, reassign the root link
            new_root = None

            for b in self.root_link.children_branches:
                if b is not None:
                    new_root = b
                    break

            # List comprehension to get all branches (copy)
            all_branches = [b for b in self.root_link.children_branches]

            # For all branches, reassign root
            for branch in all_branches:
                branch.root_link = new_root
                branch.children_branches.add(self)

        all_branches = [b for b in self.root_link.children_branches]

        for branch in all_branches:
            if self in branch.children_branches:
                branch.children_branches.remove(self)

        del self


# TODO add threads to branches

# TODO update dependencies

# If no solution, kill branch TODO

# TODO add custom exception for when a variable is not numerically valued in func

# Set variables for all branches

# Throw warning when using .x when multiple branches (__setattr__)
