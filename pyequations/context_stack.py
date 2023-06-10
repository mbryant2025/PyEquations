from sympy import Symbol


def verify_names(var_names: list[str]) -> None:
    """
    Checks that the variable names are valid
    :param var_names: The variable names
    :return: None. Throws an error if the variable names are invalid
    """

    # Check that the variable names are unique
    if len(var_names) != len(set(var_names)):
        raise ValueError("var_names must be unique")

    for name in var_names:
        # Check that the variable names are strings
        if not isinstance(name, str):
            raise TypeError("var_names must be a list of strings")

        # Check that the variables names can all be identified as attributes
        if not name.isidentifier():
            raise ValueError("var_names must be valid identifiers")


class ContextStack:
    """
    A class to manage the context stack for branching systems
    Must be initialized with a list of variables to track
    """

    def __init__(self, var_names: list[str] = None):

        # Validate the variable names
        if var_names is not None:
            verify_names(var_names)

        self._contexts = [{name: Symbol(name) for name in var_names} if var_names else {}]
        """
        A list of dictionaries containing the variables in each context
        """
        self._context_idx: int = 0
        """
        The index of the current context
        """
        self._locked: bool = False
        """
        A flag to indicate if the context stack is locked
        """

    def add_variables(self, var_names: list[str]) -> None:
        """
        Adds variables to the current context
        Can only be done before the context stack is locked
        Locking happens when any operation is done on the stack to compute or branch
        :param var_names: the names of the variables to add
        :return: None
        """

        # Check that the context stack is not locked
        if self._locked:
            raise RuntimeError("Context stack is locked. Variables can only be added before the system branches.")

        verify_names(var_names)

        # Add the variables to the current context
        self._contexts[self._context_idx].update({name: Symbol(name) for name in var_names})

    @property
    def context_idx(self):
        return self._context_idx

    @property
    def contexts(self):
        return self._contexts

    @property
    def locked(self):
        return self._locked

    @context_idx.setter
    def context_idx(self, value):
        if 0 <= value < len(self._contexts):
            self._context_idx = value
        else:
            raise IndexError("Invalid context_idx")

    def __getattr__(self, key):
        if 0 <= self._context_idx < len(self._contexts):
            return self._contexts[self._context_idx].get(key)
        else:
            raise IndexError("Invalid context_idx")

    def set_value(self, name: str, value, context: int = None) -> None:
        """
        Sets the value of a variable in the given context
        :param name: the name of the variable
        :param value: the value to set the variable to
        :param context: the index of the context to set the value in. If None, the current context is used
        :return: None
        """

        # If name is not a string, raise an error
        if not isinstance(name, str):
            raise TypeError('Name must be a string')

        if context is not None:
            self._context_idx = context

        if 0 <= self._context_idx < len(self._contexts):
            self._contexts[self._context_idx][name] = value
        else:
            raise IndexError('Invalid context_idx')

    def get_value(self, name, context: int = None):
        """
        Gets the value of a variable in the current context
        :param context: the index of the context to get the value from
        :param name: the name of the variable
        :return: the value of the variable
        """

        if context is None:
            context = self._context_idx

        if 0 <= context < len(self._contexts):
            return self._contexts[context].get(name)
        else:
            raise IndexError("Invalid context_idx")

    def set_value_all_contexts(self, name: str, value) -> None:
        """
        Sets the value of a variable in all contexts
        :param name:
        :param value:
        :return:
        """

        # If name is not a string, raise an error
        if not isinstance(name, str):
            raise TypeError('Name must be a string')

        for context in self._contexts:
            context[name] = value

    def add_context(self, reference: int = None) -> None:
        """
        Adds a new context to the stack, copying all values from the current context
        If no reference is given, the new context is a copy of the current context
        """

        # Lock the context stack to prevent adding variables
        self._locked = True

        if reference is None:
            reference = self._context_idx

        if 0 <= reference < len(self._contexts):
            self._contexts.append(self._contexts[reference].copy())
        else:
            raise IndexError("Invalid context_idx")

    def remove_context(self, index: int) -> None:
        """
        Removes a context from the stack
        """

        # Lock the context stack to prevent adding variables
        self._locked = True

        if 0 <= index < len(self._contexts):
            self._contexts.pop(index)
            # Need to ensure that the current context index is not greater than the index of the context to remove
            self._context_idx = min(self._context_idx, len(self._contexts) - 1)
        else:
            raise IndexError("Invalid context_idx")

    @property
    def num_contexts(self) -> int:
        return len(self._contexts)

    @property
    def variables(self) -> list[str]:
        return list(self._contexts[self._context_idx].keys())

    def rotate_context(self) -> None:
        """
        Rotates the context stack by one
        """
        self._context_idx = (self._context_idx + 1) % len(self._contexts)

    def has_variable(self, variable) -> bool:
        """
        Returns True if the current context has a variable
        """
        return variable in self._contexts[self._context_idx]
