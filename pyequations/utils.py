from pyequations.inheritables import _is_solved


def solved(*variables) -> bool:
    """
    Check if all the variables are solved
    :param variables: The variables to check
    :return: Whether all the variables are solved
    """

    return all([_is_solved(var) for var in variables])
