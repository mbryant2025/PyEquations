from pyequations.context_stack import ContextStack
from sympy import Symbol
from pytest import raises


def test_create_stack():
    cs = ContextStack(['x', 'y'])

    # Check that the stack has been initialized with the correct number of contexts
    assert cs.num_contexts == 1

    # Check that the context has been initialized with the correct variables
    assert cs.x == Symbol('x')
    assert cs.y == Symbol('y')

    # Check that the context index is correct
    assert cs.context_idx == 0


def test_add_context():
    cs = ContextStack(['x', 'y'])

    # Add a new context
    cs.add_context()

    # Check that the stack has been initialized with the correct number of contexts
    assert cs.num_contexts == 2

    # Check that the context has been initialized with the correct variables
    assert cs.x == Symbol('x')
    assert cs.y == Symbol('y')

    # Check that the context index is correct
    assert cs.context_idx == 0


def test_set_value():
    cs = ContextStack(['x', 'y'])

    # Add a new context
    cs.add_context(reference=0)

    # Set the value of x in the first context
    cs.set_value('x', 5)

    # Check that the value of x is correct in the first context
    assert cs.x == 5

    # Check that the value of x is correct in the second context
    cs.context_idx = 1
    assert cs.x == Symbol('x')


def test_set_value_invalid_context_idx():
    cs = ContextStack(['x', 'y'])

    # Add a new context
    cs.add_context(reference=0)

    # Try to set the value of x to an invalid context
    with raises(IndexError):
        cs.context_idx = 2


def test_copy_value_from_context():
    cs = ContextStack(['x', 'y'])

    # Add a new context
    cs.add_context(reference=0)

    # Switch to the second context
    cs.context_idx = 1

    # Set the value of x in the second context
    cs.set_value('x', 5)

    # Create a new context with reference to the second context
    cs.add_context(reference=1)

    # Check that the value of x is correct in the first context
    cs.context_idx = 0
    assert cs.x == Symbol('x')

    # Check that the value of x is correct in the second context
    cs.context_idx = 1
    assert cs.x == 5

    # Check that the value of x is correct in the third context
    cs.context_idx = 2
    assert cs.x == 5

    # Create a new context with reference to the first context
    cs.add_context(reference=0)

    # Switch to the first context
    cs.context_idx = 0

    # Set the value of x in the first context
    cs.set_value('x', 10)

    # Check that the value of x is correct in the first context
    assert cs.x == 10

    # Check that the value of x is correct in the second context
    cs.context_idx = 1
    assert cs.x == 5

    # Check that the value of x is correct in the third context
    cs.context_idx = 2
    assert cs.x == 5

    # Check that the value of x is correct in the fourth context
    cs.context_idx = 3
    assert cs.x == Symbol('x')


def test_variables():
    cs = ContextStack(['x', 'y'])

    # Add a new context
    cs.add_context()

    # Check that the variables are correct
    assert cs.variables == ['x', 'y']


def test_remove_context():
    cs = ContextStack(['x', 'y'])

    # Add a new context
    cs.add_context()

    # Remove the context
    cs.remove_context(1)

    # Check that the stack has been initialized with the correct number of contexts
    assert cs.num_contexts == 1

    # Check that the context has been initialized with the correct variables
    assert cs.x == Symbol('x')
    assert cs.y == Symbol('y')

    # Check that the context index is correct
    assert cs.context_idx == 0


def test_remove_context_invalid_context_idx():
    cs = ContextStack(['x', 'y'])

    # Add a new context
    cs.add_context()

    # Try to remove an invalid context
    with raises(IndexError):
        cs.remove_context(2)


def test_rotate_context():
    cs = ContextStack(['x', 'y'])

    # Add a new context
    cs.add_context()

    # Rotate the contexts
    cs.rotate_context()

    # Check that the stack has been initialized with the correct number of contexts
    assert cs.num_contexts == 2

    # Check that the context has been initialized with the correct variables
    assert cs.x == Symbol('x')
    assert cs.y == Symbol('y')

    # Check that the context index is correct
    assert cs.context_idx == 1


def test_get_value():
    cs = ContextStack(['x', 'y'])

    # Add a new context
    cs.add_context()

    # Set the value of x in the first context
    cs.set_value('x', 5)

    # Check that the value of x is correct in the first context
    assert cs.get_value('x') == 5

    # Check that the value of x is correct in the second context
    cs.context_idx = 1
    assert cs.get_value('x') == Symbol('x')


def test_has_variable():
    cs = ContextStack(['x', 'y'])

    # Add a new context
    cs.add_context()

    # Check that the variable x exists
    assert cs.has_variable('x')

    # Check that the variable z does not exist
    assert not cs.has_variable('z')
