from itertools import combinations
from sympy import solve, Eq, simplify, Mul, Add, Pow, Symbol, Number, N, Expr
from warnings import warn
from pyequations.context_stack import ContextStack
from pyequations.utils import get_symbols, composes_equation, BoolWrapper, IntWrapper, MinFloatTracker
from copy import deepcopy


class PyEquations:

    def _super_setattr(self, name, value):
        """
        Set the attribute for the class using the default __setattr__ method
        :param name: the attribute name
        :param value: the attribute value
        :return: None
        """
        super(PyEquations, self).__setattr__(name, value)

    def __init__(self, var_descriptions: dict[str, str] | list[str]):

        # Set attributes using super to avoid recursion
        #  would spawn from the overriden __getattr__ method

        # Sympy expressions to solve for
        self._super_setattr('eqs', [])
        # User defined functions
        self._super_setattr('funcs', [])

        # Branches marked for pruning
        self._super_setattr('contexts_to_prune', {})
        # Advance branch flag -- used when a branch is pruned, and we need to advance to the next branch
        self._super_setattr('advance_branch', BoolWrapper(False))
        # Number of deletions for a current solve
        # Important for determining if there are any valid solutions
        self._super_setattr('deletions', IntWrapper(0))

        # If the object has been solved
        self._super_setattr('solved', BoolWrapper(False))

        # If a bad solution was found
        self._super_setattr('bad_solution', BoolWrapper(False))

        # The minimum numerical quantity handled in the system
        # Used to use as a reference if a value is compared to zero
        # Ex. if the minimum number dealt ith is 5e-20, then technically 5e-15 is within the margin of error
        self._super_setattr('min_float', MinFloatTracker())

        if var_descriptions:
            if isinstance(var_descriptions, dict):
                self._super_setattr('context_stack', ContextStack(list(var_descriptions.keys())))
                self._super_setattr('var_descriptions', var_descriptions)
            elif isinstance(var_descriptions, list):
                self._super_setattr('context_stack', ContextStack(var_descriptions))
                self._super_setattr('var_descriptions', {name: '' for name in var_descriptions})
        else:
            raise ValueError('Must have at least one variable description')

        # Get all methods defined in the class
        methods = [getattr(self, name) for name in dir(self) if callable(getattr(self, name))]

        # Add all methods that are decorated with @calc to the calculation_functions list
        for method in methods:
            if hasattr(method, '__equation__'):
                self.eqs.append(method)
            elif hasattr(method, '__user_func__'):
                self.funcs.append(method)

    @property
    def num_branches(self) -> int:
        """
        Get the number of branches
        :return: The number of branches
        """

        return self.context_stack.num_contexts

    @property
    def vars(self) -> list[dict[str, Symbol | Number]]:
        """
        Get the variables for all branches
        :return: A list of dictionaries containing the variables for each branch
        """

        return self.context_stack.contexts

    @property
    def vars_decimal(self) -> list[dict[str, float]]:
        """
        Get the variables for all branches
        Understandably could have this and the above be a function, but since these are used so often, it is
        better to have them as a property
        :return: A list of dictionaries containing the variables for each branch
        """

        non_decimal = self.vars
        return [{key: N(value) for key, value in branch.items()} for branch in non_decimal]

    @property
    def locked(self) -> bool:
        """
        Get if the object is locked
        :return: True if the object is locked, False otherwise
        """

        return self.context_stack.locked

    def __getattr__(self, name):
        """
        Get the attribute for the current branch
        This function is called when the attribute is not found, and therefore we should check the context stack
        :param name: the attribute name
        :return: the attribute value
        """

        # If the attribute is not in the context stack, raise an error
        if name not in self.context_stack.variables:
            raise AttributeError(f'Variable {name} does not exist')
        else:
            # Return the value of the attribute
            return self.context_stack.get_value(name)

    def __setattr__(self, name, value):
        """
        Set the attribute for all branches, if the attribute does not exist and the value is an int, float, or complex
        :param name: the attribute name
        :param value: the attribute value
        :return: None
        """

        # If we have already solved the equations, raise a warning and do not set the attribute
        if self.solved:
            warn('Equations have already been solved. Cannot add new variables')
            return

        # If the value is an int, float, or complex, set the value for all branches
        # (Also include the sympy types)
        if isinstance(value, int | float | complex | Mul | Add | Pow | Symbol | Number):
            # Check if the variables is in the context stack
            if name in self.context_stack.variables:
                # If it is, set the value for all branches
                self.context_stack.set_value_all_contexts(name, value)
            # Otherwise, raise an exception as the variable cannot be added
            else:
                raise AttributeError(f'Variable {name} cannot be added after initialization')

        # Otherwise, use the default __setattr__ method for this branch
        else:
            self._super_setattr(name, value)

    def add_variables(self , var_descriptions: dict[str, str] | list[str]) -> None:
        """
        Add variables to the context stack
        Cannot be done after the context stack has branched
        In this case, an exception will be raised
        :param var_descriptions: The variable descriptions to add
        :return: None
        """

        # If the variable descriptions are a dictionary, add them to the context stack
        if isinstance(var_descriptions, dict):
            self.context_stack.add_variables(list(var_descriptions.keys()))
            self.var_descriptions.update(var_descriptions)
        # Otherwise, if the variable descriptions are a list, add them to the context stack
        elif isinstance(var_descriptions, list):
            self.context_stack.add_variables(var_descriptions)
            self.var_descriptions.update({name: '' for name in var_descriptions})

    def _eval_funcs(self) -> None:
        """
        Evaluate all the user defined functions for the current branch
        :return: None
        """

        # Loop through all the user-defined functions and evaluate them
        for f in self.funcs:
            try:
                f()
            except TypeError:
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
                        self.context_stack.set_value(str(var), val)

                    # Switch back to the old branch
                    self.context_switch(old_context_idx)

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

    def _mark_for_pruning(self, equations: list) -> None:
        """
        Mark the current context for pruning by adding a hash to the list of hashes to prune
        Also carry the offending equation with the hash, so it can be printed if an exception is thrown
        :return: None
        """

        # Generate a hash for the current context
        current_context = self.context_stack.contexts[self.context_stack.context_idx]
        # Specifically, we want to hash the values of the context, not the keys
        context_hash = hash(tuple(sorted(current_context.items())))
        print(f'this is the context hash: {context_hash}')
        # Add the context hash to the list of contexts to prune
        # Also have the value be the equation that caused the contradiction, so it can be printed
        # if an exception is thrown
        self.contexts_to_prune[context_hash] = equations
        # Mark that we can now advance to the next context
        self.advance_branch.set(True)

    def observe_floats(self, equations: list) -> None:
        """
        Observe the specified floats and add them to the list of floats to observe
        :param equations: The equations to observe
        :return: None
        """

        for equation in equations:
            print(f'OBSERVING {N(equation)}')
            # Extract the floats from the equation and add observe them
            for num in Expr(equation).atoms(Number):
                self.min_float.add(abs(num))

    def _retrieve_equations(self) -> set:
        """
        Retrieve all the equations from the calculation functions
        :return: A set of equations
        """

        equations = set()

        for function in self.eqs:

            # Call the function from the context of the branch
            result = function()
            if len(result) == 2:
                # Simplify the results here to make all other operations faster
                result = [simplify(e) for e in result]
                # Check if the result is an equation that could produce a valid solution
                # Also, handle the case where there is a contradiction (return -1)
                can_compose = composes_equation(*result, self.min_float.value)
                print(f'can {result} compose? {can_compose}')
                match can_compose:
                    # Valid equation
                    case 1:
                        # Also observe the floats here
                        self.observe_floats(result) # TODO observe better
                        resulting_eq = Eq(*result)
                        equations.add(resulting_eq)
                    # Invalid equation
                    case 0:
                        continue
                    # Contradiction
                    case -1:
                        print(f'Contradiction found in {result}')
                        print(f'the current context is {self.context_stack.contexts[self.context_stack.context_idx]}')
                        # Mark the current context for pruning
                        # Note how a list type is passed, this is because this same function can be called elsewhere
                        # with a list of equations that are all contradictory (but not necessarily on their own)
                        self._mark_for_pruning([result])
                        print('------------------------')
                        # TODO terminate branch solving for now -- not necessary, but will speed up the process
            else:
                raise ValueError(f'Function does not return two elements {function}')

        return equations

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
        equations = self._retrieve_equations()

        # If the advance_branch flag is set, return
        # This means that a contradiction was found and the branch should be pruned
        if self.advance_branch:
            return

        print(f'equations: {equations}')

        # Attempt to solve every subgroup of the equations
        for r in range(1, len(equations) + 1):
            for subgroup in combinations(equations, r):

                target_variables = get_symbols(subgroup)

                # Attempt to solve the subgroup of equations
                solution = solve(subgroup, *target_variables)

                print(f'solution: {solution}')

                # If solution == [], there is no solution for this subgroup
                if not solution:
                    # This branch shouldn't necessarily be pruned, but we need to throw special flag
                    # Specifically, if the vars before solving and the vars after solving are the same, then
                    # we should throw the flag. This is because some solutions may have branches that lead to this point
                    # and we don't want to prune those branches because that set of equations could spawn a valid
                    # solution. So, we need to check if the variables are the same before and after solving.
                    # This would indicate that the equations are not solvable, and we should throw an exception.
                    self.bad_solution.set(True)

                # Verify the solution is valid; handle solution branching
                sol = self._verify_and_extract_solution(solution, target_variables)

                # If a solution was found, set the variables to the solution in this branch
                if sol is not None:
                    for key, value in sol.items():
                        # Found a solution, set the variable to the solution
                        self.context_stack.set_value(str(key), value)

                    # If there are still unknown variables, attempt to solve again with the new information
                    self._run_solver_this_branch()

                    # Return to prevent further solving (want to utilize the most information possible)
                    return

        # Re-evaluate all the user defined functions in case of new information
        self._eval_funcs()

    def _prune_branches(self) -> None:
        """
        Prune the branches that are marked for pruning
        :return: None
        """
        # return  # TODO
        print(f'we found {len(self.contexts_to_prune)} to prune they are {self.contexts_to_prune}')

        # If there are as many branches as there are contexts, raise an exception because there are no solutions
        # Also need to offset the number of branches by the number of deletions
        if self.num_branches - self.deletions.value == len(self.contexts_to_prune):  # TODO

            print(f'here are the vars {self.vars}')

            # Make quick-and-dirty pretty_equation function for use in just this exception throwing
            # (Cannot have the second string be an f-string because that would mean nested f-strings)
            def pretty_equation(equations):
                s = ''
                for eqn in equations:
                    s += f'{eqn[0]} = {eqn[1]}, '
                return s[:-2]

            print(self.contexts_to_prune)

            raise RuntimeError('Given equations have no consistent solutions. '
                               'Please check your equations and try again. '
                               'Contradiction(s) found: '
                               f'{[pretty_equation(equations) for equations in self.contexts_to_prune.values()]}')

        # Otherwise, prune the branches by finding the branches that match the hash
        # Also, ensure that the context idx is not greater than the number of contexts
        for context_hash, equation in self.contexts_to_prune.items():
            for branch_idx, branch in enumerate(self.context_stack.contexts):
                # If the branch matches the hash, prune it
                if hash(tuple(sorted(branch.items()))) == context_hash:
                    # Remove the context
                    self.context_stack.remove_context(branch_idx)
                    # Break out of the inner loop as we have found the branch to prune
                    break

        # Ensure that the actual idx pointer is not greater than the number of contexts
        self.context_stack.context_idx = min(self.context_stack.context_idx, self.context_stack.num_contexts - 1)

        # Reset the prune branches dictionary
        self.contexts_to_prune.clear()

    def solve(self) -> None:
        """
        Trigger the solver on all existing branches
        Solver could branch into additional branches, of which the solver will also be triggered on
        :return: None
        """

        # If the object has been solved before, throw a warning
        if self.solved:
            warn('This object has already been solved. '
                 'Please create a new object to solve again.'
                 'Solving multiple times could cause undetermined behavior in the branching behavior'
                 'if variables are changed after the first solve.')

        # Clear contexts_to_prune dictionary
        self.contexts_to_prune.clear()

        # Reset the bad_solution flag
        self.bad_solution.set(False)

        # Store the current context idx
        old_context_idx = self.context_stack.context_idx

        # Store the current solution as a copy of self.vars
        old_solution = deepcopy(self.vars)

        # Iterate through all the branches and solve them
        # Iterate by rotating the context stack until we are back at where we started
        # This accounts for new branches being added during the solving process

        # Local function to run the solver on the current branch
        def run_single():
            # Run the solver on the current branch
            self._run_solver_this_branch()
            # Rotate off the first context
            self.context_stack.rotate_context()
            # Reset the advance_branch flag
            self.advance_branch.set(False)
            # Reset the number of deleted branches
            self.deletions.set(0)

        run_single()

        # Wishing do-while loops were a thing in python...

        # Continue rotating until we are back at the first context
        while self.context_stack.context_idx != old_context_idx:
            run_single()

        # After solving, prune any branches that are marked for pruning
        # Also check if there are no solutions and throw an exception accordingly
        self._prune_branches()

        # If the solution is bad and the branches did not change, throw an exception
        if self.bad_solution and old_solution == self.vars:
            raise RuntimeError('Given equations have no consistent solutions. '
                               'Please check your equations and try again.')

        # Mark the object as solved
        self.solved.set(True)

    def var_description(self, name: str) -> str:
        """
        Get the description of a variable
        :param name: The name of the variable
        :return: The description of the variable
        """

        # Raise an exception if the variable does not exist
        if name not in self.var_descriptions:
            raise KeyError(f'Variable {name} does not exist')

        # Return the description of the variable
        return self.var_descriptions[name]

    def get_var_vals(self, name: str) -> list:
        """
        Get the value of a variable for each branch
        :param name: The name of the variable
        :return: A list of the values of the variable for each branch
        """

        # Raise an exception if the variable does not exist
        if name not in self.context_stack.variables:
            raise KeyError(f'Variable {name} does not exist')

        # Return a list of the value of the variable for each branch
        return list({self.context_stack.get_value(name, idx) for idx in range(self.context_stack.num_contexts)})

    def get_var_vals_decimal(self, name: str) -> list:
        """
        Get the decimal value of a variable for each branch
        :param name: The name of the variable
        :return: A list of the values of the variable for each branch
        """

        # Raise an exception if the variable does not exist
        if name not in self.context_stack.variables:
            raise KeyError(f'Variable {name} does not exist')

        # Return a list of the value of the variable for each branch
        return list({N(self.context_stack.get_value(name, idx)) for idx in range(self.context_stack.num_contexts)})

    def del_branch(self) -> None:
        """
        Delete the current branch of the current context
        :return: None
        """

        # Delete the old context
        # This handles updating the context idx
        self.context_stack.remove_context(self.context_stack.context_idx)
        # Note that we have deleted a branch
        self.deletions.increment()
#
# # TODO update dependencies
#
# # TODO github workflow

# TODO get context by variable values
