from itertools import combinations
from sympy import symbols, Symbol, solve, Eq, Number, simplify, Mul, Add, Pow, Symbol, Number
from sympy.physics.units import Quantity


def get_symbols(equations: [Eq]) -> tuple:
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


def remove_units(expr: Symbol | Number) -> Symbol | Number:
    """
    Remove the units from a given expression
    :param expr: An expression
    :return: The expression with the units removed
    """
    if expr is None:
        return None
    if isinstance(expr, (int, float)):
        return expr
    if not expr.has(Quantity):
        return expr
    units = expr.subs({x: 1 for x in expr.args if not x.has(Quantity)})
    return expr / units


# TODO make __getattr__ in PyEquations that grabs the current context

# make it see if it exists, if not then go to context stack

class PyEquations:

    def __init__(self, var_descriptions: dict[str, str] | list[str]):

        # Create context stack variable
        self._context_stack = None
        # Sympy expressions to solve for
        self.eqs: list[callable] = []
        # User defined functions
        self.funcs: list[callable] = []

        if var_descriptions:
            if isinstance(var_descriptions, dict):
                self._context_stack = ContextStack(list(var_descriptions.keys()))
                self.variable_descriptions = var_descriptions
            elif isinstance(var_descriptions, list):
                self._context_stack = ContextStack(var_descriptions)
                self.variable_descriptions = {name: "" for name in var_descriptions}
        else:
            raise ValueError("Must have at least one variable description")

        # Get all methods defined in the class
        methods = [getattr(self, name) for name in dir(self) if callable(getattr(self, name))]

        # Add all methods that are decorated with @calc to the calculation_functions list
        for method in methods:
            if hasattr(method, '__equation__'):
                self.eqs.append(method)
            elif hasattr(method, '__user_func__'):
                self.funcs.append(method)

    @property
    def context_stack(self):
        return self._context_stack

    def __getattr__(self, name):
        """
        Get the attribute for the current branch
        :param name: the attribute name
        :return: the attribute value
        """

        print(f'accessing {name}')
        print(self._context_stack)

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
        Set the attribute for all branches, if the attribute does not exist and the value is an int, float, or complex
        :param name: the attribute name
        :param value: the attribute value
        :return: None
        """

        # If the attribute does not exist and the value is an int, float, or complex, set the value for all branches
        if not hasattr(self, name) and isinstance(value, int | float | complex):
            # Check if the variables is in the context stack
            if name in self.context_stack.variables:
                # If it is, set the value for all branches
                self.context_stack.set_value_all_contexts(name, value)
            # Otherwise, raise an exception as the variable cannot be added
            else:
                raise AttributeError(f'Variable {name} cannot be added after initialization')

        # Otherwise, use the default __setattr__ method for this branch
        else:
            super().__setattr__(name, value)



    def _eval_funcs(self) -> None:
        """
        Evaluate all the user defined functions for this branch
        :return: None
        """

        # TODO
        # Loop through all the user-defined functions and evaluate them
        for f in self.funcs:

            try:
                f()
            except TypeError as e:
                print(str(e))
                continue

    def context_switch(self, target_branch: int) -> None:
        """
        Switch the current branch to the specified branch
        :param target_branch: The branch number to switch to
        :return: None
        """

        # If the branch number is out of range, throw an exception
        if target_branch >= self.context_stack.num_contexts:
            raise IndexError(f'Branch {target_branch} does not exist')

        # Otherwise, set the current branch to the specified branch by moving it to the front of the list
        self.context_stack.context_idx = target_branch

    def rotate_context(self) -> None:
        """
        Rotate the current branch to the next branch
        :return: None
        """

        self.context_stack.rotate_context()

    # TODO get context by variable values

    def _verify_and_extract_solution(self, solution, target_variables) -> dict | None:
        """
        Check if the solution is a numeric solution
        If multiple solutions, branch the solution set by adding contexts
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

                    old_context_idx = self.context_stack.context_idx

                    # Create a new branch (context)
                    self.context_stack.add_context()

                    # Switch to the new branch
                    self.context_switch(self.context_stack.num_contexts - 1)

                    # Set the values for the new branch
                    for var, val in zip(target_variables, sol):
                        self.context_stack.set_value(var, val)

                    # Switch back to the old branch
                    self.context_switch(old_context_idx)

                    # TODO solve these contexts too

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

    def _retrieve_equations(self) -> list:
        """
        Retrieve all the equations from the calculation functions
        :return: A list of equations
        """

        equations = []

        print(f'CALLING FROM {self}')
        print(f'here are the equations {self.eqs}')

        for function in self.eqs:

            # Call the function from the context of the branch
            result = function()
            if len(result) == 2:
                resulting_eq = Eq(*result)
                equations.append(resulting_eq)
            else:
                raise ValueError("Function does not return two elements")

        # This is the major bottleneck in the code
        # However, it is necessary  to ensure that comparing them does not yield false inequalities
        return [simplify(e) for e in equations]

    def _run_solver_this_branch(self) -> None:
        """
        Solve the equations by substituting solutions in place of unknown variables
        Recursively attempts all combinations of equations
        :return: None
        """

        # Evaluate all the user defined functions
        self._eval_funcs()

        # Gather all the equations from the calculation functions that have an unknown variable
        # Remove any equations that are True as they are redundant
        equations = [e for e in self._retrieve_equations() if e != True]

        # Attempt to solve every subgroup of the equations
        for r in range(1, len(equations) + 1):
            for subgroup in combinations(equations, r):

                target_variables = get_symbols(subgroup)

                # Attempt to solve the subgroup of equations
                solution = solve(subgroup, *target_variables)

                # If solution == [], there is no solution for this subgroup, raise an exception
                if not solution:
                    raise RuntimeError(f'Equations have no solutions: {subgroup}')

                # Verify the solution is valid, handle solution branching
                sol = self._verify_and_extract_solution(solution, target_variables)

                # If a solution was found, set the variables to the solution in this branch
                if sol is not None:
                    for key, value in sol.items():
                        # Found a solution, set the variable to the solution
                        self.context_stack.set_value(key, value)

                    # If there are still unknown variables, attempt to solve again with the new information
                    self._run_solver_this_branch()

                    # Return to prevent further solving (want to utilize the most information possible)
                    return

        # Re-evaluate all the user defined functions in case of new information
        self._eval_funcs()

    def solve(self) -> None:
        """
        Trigger to solve the equations on all existing branches
        :return: None
        """

        old_context_idx = self.context_stack.context_idx

        # Iterate through all the branches and solve them
        # Iterate by rotating the context stack until we are back at where we started
        # This accounts for new branches being added during the solving process

        # Rotate off the first context
        self._run_solver_this_branch()
        self.context_stack.rotate_context_stack()

        # Wishing do-while loops were a thing in python...

        # Continue rotating until we are back at the first context
        while self.context_stack.context_idx != old_context_idx:
            self._run_solver_this_branch()
            self.context_stack.rotate_context_stack()

    def _clear_single_var(self, name: str) -> None:
        """
        Returns a variable to a variable (potentially from a value)
        Applies for all contexts
        Used for changing a value back to a variable
        :param name: The name of the variable
        :return: None
        """

        # Raise an exception if the variable does not exist
        if name not in self.context_stack.variables:
            raise KeyError(f'Variable {name} does not exist')

        # Set the variable to the symbol for all contexts
        for idx in range(self.context_stack.num_contexts):
            self.context_stack.set_value(name, Symbol(name), idx)

    def clear_var(self, *variables) -> None:
        """
        Used for changing values back to variables for all contexts
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
        pass  # TODO: Implement

    def get_branches_var(self, name: str) -> list[Symbol | Number]:
        pass  # TODO: Implement

    def _get_this_branch_vars(self):
        """
        Get all variables in the branch/context
        :return: A dictionary of all variables in the branch
        """

        # Return a dictionary of all variables in the branch
        return {name: self.context_stack.get_value(name) for name in sorted(self.variable_descriptions.keys())}

    def vars(self, decimal=False) -> list[dict[str, Symbol | Number]]:
        """
        Get all variables among all solution branches
        :return: A list of dictionaries of all variables for each solution branch
        """

        # Return a list of all variables for each solution branch
        ret = []

        for idx in range(self.context_stack.num_contexts):
            ret.append(
                {name: self.context_stack.get_value(name, idx) for name in sorted(self.variable_descriptions.keys())})

        if not decimal:
            return ret

        # Option for returning decimal values
        return [{key: value.evalf() for key, value in branch.items()} for branch in ret]

    def num_branches(self) -> int:
        """
        Get the number of solution branches
        :return: The number of solution branches
        """

        # Return the number of solution branches
        return self.context_stack.num_contexts

    def var_descriptions(self) -> dict[str: str]:
        """
        Get all variable descriptions
        :return: A list of all variable descriptions
        """

        # Return a dictionary of all variable descriptions sorted by variable name
        return {name: self.variable_descriptions[name] for name in sorted(self.variable_descriptions.keys())}

    def del_branch(self) -> None:
        """
        Delete the current branch of the current context
        :return: None
        """

        # Make note of the current context
        old_context_idx = self.context_stack.context_idx

        # Rotate to the next context
        self.context_stack.rotate_context_stack()

        # Delete the old context
        self.context_stack.remove_context(old_context_idx)

# TODO update dependencies

# TODO github workflow

# TODO note how we won't remove final branch
