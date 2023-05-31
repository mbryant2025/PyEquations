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


class ContextStack:
    """
    A class to manage the context stack for branching systems
    """

    def __init__(self):
        self.contexts: list[dict] = []
        self._context_idx: int = 0

    @property
    def context_idx(self):
        return self._context_idx

    @context_idx.setter
    def context_idx(self, value):
        if 0 <= value < len(self.contexts):
            self._context_idx = value
        else:
            raise IndexError("Invalid context_idx")

    def __getattr__(self, key):
        if 0 <= self._context_idx < len(self.contexts):
            return self.contexts[self._context_idx].get(key)
        else:
            raise IndexError("Invalid context_idx")


# TODO make __getattr__ in PyEquations that grabs the current context

# make it see if it exists, if not then go to context stack

class PyEquations:

    def __init__(self):

        # Text-base descriptions inputted by user (optional to have one, empty string by default)
        self.variable_descriptions: dict[str, str] = {}
        # Sympy expressions to solve for
        self.eqs: list[callable] = []
        # User defined functions
        self.funcs: list[callable] = []
        # Branches for multiple solutions
        # Current branch is the first branch
        self.context_stack: list[dict] = []

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
            for branch in self.context_stack:
                branch[name] = value

        # If the attribute exists and the value is a number, substitute the value into the sympy symbol for all branches
        elif hasattr(self, name) and isinstance(value, (int, float, complex)) and not isinstance(value, bool):
            for branch in self.branches:
                branch._super_setattr(name, getattr(self, name).subs(getattr(self, name), value))

        # Otherwise, if the value is a sympy symbol or a number, throw an exception as it was used incorrectly
        elif isinstance(value, Symbol):
            raise RuntimeError(f'Variable {name} already exists')

        elif isinstance(value, (int, float, complex)) and not isinstance(value, bool):
            raise Exception(f'Variable {name} does not exist and cannot be set to a number')

        # If the added attribute is a function, add it to all branches
        elif callable(value):
            for branch in self.branches:
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

        for branch in self.root_link.branches:
            branch._super_delattr(item)

    def _eval_funcs(self) -> None:
        """
        Evaluate all the user defined functions for this branch
        :return: None
        """

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
        if target_branch >= len(self.context_stack):
            raise IndexError(f'Branch {target_branch} does not exist')

        # Otherwise, set the current branch to the specified branch by moving it to the front of the list
        self.context_stack.insert(0, self.context_stack.pop(target_branch))


    def rotate_context(self) -> None:
        """
        Rotate the current branch to the next branch
        :return: None
        """

        # If there are no branches, throw an exception
        if len(self.context_stack) == 0:
            raise IndexError('No branches exist')

        # Otherwise, move the current branch to the back of the list
        self.context_stack.append(self.context_stack.pop(0))


    # TODO get context by variable values


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
                    print('BRANCHING')
                    # Want to make an exact copy of the current PyEquations object data, except for the parent indicator
                    # For each solution, create a new branch and propagate this new branch to the root

                    # Create a new solution branch
                    new_branch = copy(self)

                    # Need to deepcopy the eqs and funcs
                    new_branch.eqs = deepcopy(self.eqs)
                    new_branch.funcs = deepcopy(self.funcs)

                    # Add a new branch to the root
                    self.root_link.branches.add(new_branch)

                    # Add the solution to the new branch
                    for v, s in zip(symbol_names, sol):
                        new_branch.__setattr__(v, s)

                    # Add this new branch to the queue of new branches to solve
                    self.root_link.new_branches.append(new_branch)

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

        print(f'self is {self}')

        # Gather all the equations from the calculation functions that have an unknown variable
        # Remove any equations that are True as they are redundant
        equations = [e for e in self._retrieve_equations() if e != True]

        print(f'running solver for a BRANCH {self}')

        print(f'our value of x is {self.x} and our value of y is {self.y} and self is {self}')

        print(self._retrieve_equations())

        # Attempt to solve every subgroup of the equations
        for r in range(1, len(equations) + 1):
            for subgroup in combinations(equations, r):

                target_variables = get_symbols(subgroup)

                # Attempt to solve the subgroup of equations
                solution = solve(subgroup, *target_variables)

                print(subgroup)

                # If solution == [], there is no solution for this subgroup, raise an exception
                if not solution:
                    raise RuntimeError(f'Equations have no solutions: {subgroup}')

                # Verify the solution is valid, handle solution branching
                sol = self._verify_and_extract_solution(solution, target_variables)

                # If a solution was found, set the variables to the solution in this branch
                if sol is not None:
                    for key, value in sol.items():
                        # Found a solution, set the variable to the solution
                        setattr(self, str(key), value)

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

        # List comprehension to run the solver on current branches and not have concurrent modification issues
        # Could use multiprocessing here, but would require to serialize the PyEquations object
        for branch in [b for b in self.root_link.branches]:
            branch._run_solver_this_branch()

        print('AFTER SOLVING EXISTING')

        print(self.vars(decimal=True))

        while len(self.root_link.new_branches) > 0:
            print()
            print('popping')
            # Get the first branch in the queue
            branch = self.new_branches.pop(0)

            print(f'branch y is {branch.y}')

            # Run the solver on the branch
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
        return list(set([branch._get_this_branch_var(name) for branch in self.root_link.branches]))

    def _get_this_branch_vars(self):
        """
        Get all variables in the branch
        :return: A dictionary of all variables in the branch
        """

        # Return a dictionary of all variables in the branch
        return {name: getattr(self, name) for name in sorted(self.variable_descriptions.keys())}

    def vars(self, decimal=False) -> list[dict[str, Symbol | Number]]:
        """
        Get all variables among all solution branches
        :return: A list of dictionaries of all variables for each solution branch
        """

        # Return a list of all variables for each solution branch
        ret = [branch._get_this_branch_vars() for branch in self.root_link.branches]

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
        return len(self.root_link.branches)

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

        print('deleting branch')
        print(f'we have {len(self.root_link.branches)} branches')

        # Return if only one branch (children includes self)
        # Return rather than raise exception because this is called potentially many times
        if len(self.root_link.branches) == 1:
            return

        # If the target branch is the root branch, we need to switch all the data between the target branch and another
        # This also means we need to modify the children of the branches and the parent links
        if self is self.root_link:
            print('I AM ROOT')
        else:
            print('I AM NOT ROOT')

        return

























        # # If the target branch is the root branch, reassign the root branch for all branches
        # if self is self.root_link:
        #     # Since we know that there is at least 2 branches, reassign the root link
        #     new_root = None
        #
        #     for b in self.root_link.branches:
        #         if b is not None:
        #             new_root = b
        #             break
        #
        #     for b in self.root_link.branches:
        #         # For the branches that had the old root as their parent, reassign to the new one
        #         if b.parent_link is self.root_link:
        #             b.parent_link = new_root
        #         # Need to ensure that the new_root has the correct children_branches by adding all from old root
        #         new_root.children_branches.add(b)
        #
        #
        #     # List comprehension to get all branches (copy)
        #     all_branches = [b for b in self.root_link.branches]
        #
        #     # For all branches, reassign root
        #     for branch in all_branches:
        #         branch.root_link = new_root
        #         branch.branches.add(self)
        #
        # all_branches = [b for b in self.root_link.branches]
        #
        # for branch in all_branches:
        #     if self in branch.branches:
        #         branch.branches.remove(self)
        #
        # del self


# TODO update dependencies

# TODO github workflow

# TODO note how we won't remove final branch
