from sympy import Symbol


class ContextStack:
    """
    A class to manage the context stack for branching systems
    Must be initialized with a list of variables to track
    """

    def __init__(self, var_names: list[str] = None):
        self._contexts = [{name: Symbol(name) for name in var_names} if var_names else {}]
        self._context_idx: int = 0

    @property
    def context_idx(self):
        return self._context_idx

    @property
    def contexts(self):
        return self._contexts

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

    def set_value(self, name, value) -> None:
        if 0 <= self._context_idx < len(self._contexts):
            self._contexts[self._context_idx][name] = value
        else:
            raise IndexError("Invalid context_idx")

    def add_context(self, reference: int = 0) -> None:
        """
        Adds a new context to the stack, copying all values from the reference context at the index `reference`
        """
        if 0 <= reference < len(self._contexts):
            self._contexts.append(self._contexts[reference].copy())
        else:
            raise IndexError("Invalid context_idx")

    @property
    def num_contexts(self):
        return len(self._contexts)
