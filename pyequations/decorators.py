import copy


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
