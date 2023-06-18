![Tests](https://github.com/mbryant2025/PyEquations/actions/workflows/python-package.yml/badge.svg)

# PyEquations

## Table of Contents
1. [Overview](#overview)
2. [Installation](#installation)
3. [Example](#example)
4. [Additional Features](#additional-features)
    * [Multi-Level Inheritance](#multi-level-inheritance)
    * [No-Solution Handling](#no-solution-handling)
    * [Recursive Branching](#recursive-branching)
    * [Exact Solution Form](#exact-solution-form)
    * [No Need for Initial Values](#no-need-for-initial-values)
    * [Automatic Branch Deletion for Invalid Values](#automatic-branch-deletion-for-invalid-values)
5. [API](#api)
6. [Additional Notes](#additional-notes)

## Overview

PyEquations is a Python package for solving a bunch of equations with a bunch of unknowns.
PyEquations maximally solves with the given equations, functions, and variables. It internally uses SymPy
for symbolic math and supports units on all variables.

The key advantage of this package is that you don't need to know what specific equations to use to solve for a certain value.
You can simply dump all the equations and the known values. PyEquations will figure out the rest.

## Installation

```bash
pip install pyequations
```

## Example

Suppose we on top of a 100-meter tall building, and we throw a ball up with an initial velocity of 3 meters/second.
After how long does the ball hit the ground and with what velocity?

This is a simple problem if one has studied physics. Everything can be solved for using the kinematic equations (of constant acceleration):


$$ v_f = v_0 + at $$

$$ x_f = x_0 + v_0t + \frac{1}{2}at^2 $$

$$ v_f^2 = v_0^2 + 2a(x_f - x_0) $$

$$ x_f = x_0 + \frac{1}{2}(v_0 + v_f)t $$


Let's demonstrate how to solve this problem with PyEquations.

```python
# Import PyEquations dependencies
from pyequations.inheritables import PyEquations
from pyequations.decorators import eq

# Create a class that inherits from PyEquations
class Kinematic(PyEquations):
    def __init__(self):
        # Initialize the PyEquations class with the variables
        # Also supports a list of variable names if descriptions are not needed
        super().__init__({
            'x_0': 'Initial position',
            'x_f': 'Final position',
            'v_0': 'Initial velocity',
            'v_f': 'Final velocity',
            'a': 'Acceleration',
            't': 'Time'
        })

    # Define the equations as methods with the @eq decorator
    # Reference variables as class attributes
    # Every @eq method must return two-element tuple, with the comma representing an '='
    @eq
    def calc_v_f(self):
        # v_f = v_0 + at
        return self.v_f, self.v_0 + self.a * self.t

    @eq
    def calc_x_f(self):
        # x_f = x_0 + v_0t + 0.5at^2
        return self.x_f, self.x_0 + self.v_0 * self.t + 0.5 * self.a * self.t ** 2

    @eq
    def calc_v_f_2(self):
        # v_f^2 = v_0^2 + 2a(x_f - x_0)
        return self.v_f ** 2, self.v_0 ** 2 + 2 * self.a * (self.x_f - self.x_0)

    @eq
    def calc_x_f_2(self):
        # x_f = x_0 + 0.5(v_0 + v_f)t
        return self.x_f, self.x_0 + 0.5 * (self.v_0 + self.v_f) * self.t
```

Now, we can use the class to solve for a given set of known values.

```python
# Import SymPy units if you want to use units
from sympy.physics.units import meter, second

# Create an instance of the class
k = Kinematic()

# Set the known values
k.x_0 = 100 * meter
k.v_0 = 3 * meter / second
k.a = -9.8 * meter / second ** 2
k.x_f = 0 * meter

# Call the solver
k.solve()

# Print the results
print(k.vars)
```

The output of this code is:

```bash
[{'x_0': 100*meter, 'x_f': 0, 'v_0': 3*meter/second, 'v_f': -44.3734154646676*meter/second, 'a': -9.8*meter/second**2, 't': 4.83402198619057*second},
 {'x_0': 100*meter, 'x_f': 0, 'v_0': 3*meter/second, 'v_f': 44.3734154646676*meter/second, 'a': -9.8*meter/second**2, 't': -4.22177708823138*second}]
```

And just like that, PyEquations figured out the rest of the unknowns for us.

But, if you look carefully at the output, you'll notice that there are two solution branches.
PyEquations figured out that there are two possible solutions with the given equations and known values.
One of them has negative time, which we do not want for out ball-off-building example.

Let's fix this problem while also showcasing another feature of PyEquations.

```python
# Import the func decorator
from pyequations.decorators import func

class Kinematic(PyEquations):

    # ... rest of the code

    # Add a function decorated with @func
    # This function is called during solving
    # It can access and set variables, and even delete solution branches
    @func
    def parse(self):
        if self.t < 0:
            self.del_branch()

    # ... rest of the code
```

The above code adds a parsing function that deletes the solution branch if the time is negative.

The output of the updated code is:

```bash
[{'x_0': 100*meter, 'x_f': 0, 'v_0': 3*meter/second, 'v_f': -44.3734154646676*meter/second, 'a': -9.8*meter/second**2, 't': 4.83402198619057*second}]
```

Now, we have only one solution, which is the correct one.

If we want to access the solution values, we can do so as follows:

```python
print(k.get_var_vals('t'))
print(k.get_var_vals('v_f'))
```

The output of this code is:

```bash
[4.83402198619057*second]
[-44.3734154646676*meter/second]
```

Invoking `get_var_vals` with a variable name returns a list of all the values of that variable in the solution branches.

However, in a case like this where there is only one solution branch,
we can jut directly use the class attribute

```python
print(k.t)
print(k.v_f)
```

The output of this code is:

```bash
4.83402198619057*second
-44.3734154646676*meter/second
```

The reason we can directly access the attributes is due to how PyEquations handles multiple solutions.
It uses a technique very similar to context switching in order to handle multiple solution branches.
This means that the class attributes are always set to the values of the current context.


Furthermore, if you want to know how many solution branches there are, you can use the `num_branches` attribute.

```python
print(k.num_branches)
```

The output of this code is:

```bash
1
```

## Additional Features

    

### Multi-Level Inheritance
PyEquations supports multi-level inheritance. This is useful for creating a hierarchy of equations.
A sample use case is having a parent class called Silicon that contains all the equations for silicon.
A child class called SiliconDiode can inherit from Silicon and add the equations for a diode while maintaining the equations for silicon.

Here is a basic example of the syntax and how it works:

```python
class Base(PyEquations):

    def __init__(self):
        super().__init__([
            'x', 'y'
        ])

    @eq
    def eq1(self):
        return self.x + self.y, 6

    @eq
    def eq2(self):
        return self.x - self.y, 2

class Child(Base):

    def __init__(self):
        super().__init__()
        self.add_variables([
            'z'
        ])


    @eq
    def eq3(self):
        return self.z, self.x * self.y

class Grandchild(Child):

    def __init__(self):
        super().__init__()
        self.add_variables([
            'a'
        ])

    @eq
    def eq4(self):
        return self.a, self.z ** 2

g = Grandchild()

g.solve()

print(g.vars)
```

The output of this code is:

```bash
[{'a': 64, 'x': 4, 'y': 2, 'z': 8}]
```

Note how PyEquations was able to solve for all the variables in the hierarchy.
Furthermore, all variables are alphabetically sorted in the output.


### No-Solution Handling

Let's say you input the following system into PyEquations:

$$ y = x + 1 $$

$$ y = x + 2 $$

Or rather, if you enter any system with no solution, PyEquations will
raise a `RunTimeError` while noting that no consistent solutions exist..

### Recursive Branching

PyEquations systems of equations can branch infinitely. 
If multiple variables have multiple solutions, all valid solutions will be accounted for.
This includes imaginary solutions. If these are unwanted, a `@func` decorated method can be used to delete branches
with imaginary solutions, similar to the example above. 
For example, the output of PyEquations solving this system:

$$ x^3 + 2x^2 + 4x + 2 = 0$$

is:

```bash
[{'x': -2/3 + (-1/2 - sqrt(3)*I/2)*(1/27 + sqrt(57)/9)**(1/3) - 8/(9*(-1/2 - sqrt(3)*I/2)*(1/27 + sqrt(57)/9)**(1/3))}, {'x': -2/3 - 8/(9*(-1/2 + sqrt(3)*I/2)*(1/27 + sqrt(57)/9)**(1/3)) + (-1/2 + sqrt(3)*I/2)*(1/27 + sqrt(57)/9)**(1/3)}, {'x': -8/(9*(1/27 + sqrt(57)/9)**(1/3)) - 2/3 + (1/27 + sqrt(57)/9)**(1/3)}]
```

Wow, that's a mess. Note that you can also use the `vars_decimal` attribute to get the decimal values of the variables:

```bash
[{'x': -0.680551540264324 - 1.63317024091524*I}, {'x': -0.680551540264324 + 1.63317024091524*I}, {'x': -0.638896919471353}]
```

### Exact Solution Form

As demonstrated above, PyEquations can solve systems of equations and return the exact solution form.

### No Need for Initial Values

Also, as demonstrated in the Recursive Branching section, PyEquations does not require initial values to solve a system.

### Automatic Branch Deletion for Invalid Values

Let's say you were working with this system

$$ x^2 = 16 $$

$$ x + y = 10 $$

$$ x - y = -2 $$

Looking at the first equation, PyEquations would branch into two branches, one with $x = 4$ and one with $x = -4$.
However, the second and third equations together are only valid for $x = 4$ and $y = 6$.

PyEquations will automatically delete the branch with $x = -4$ because it is invalid in this system.
If neither $x = 4$ nor $x = -4$ were valid, PyEquations would raise a `RuntimeError` noting that no consistent solutions exist.


## API
* `@eq` 
  * Function decorator used for notifying PyEquations that a method is an equation
  * The method must return a tuple of the form (expression, expression), with the comma symbolizing an equality
* `@func`
  * Function decorator used for notifying PyEquations that a method is a function
  * The method will be run during solving
  * Can access/modify variables and delete branches
* `solve() -> None`
  * Used for running the solver
* `vars` 
  * Property used for getting the solution in exact form
  * The solution is returned as a list of dictionaries
* `vars_decimal`
  * Property used for getting the solution in decimal form
  * The solution is returned as a list of dictionaries
* `num_branches`
  * Property used for getting the number of solution branches
  * Returns an int
* `locked`
  * Property used for getting the locked status of the object
  * Returns a bool
  * Locks from changing or adding variables
  * Automatically locked after branching
* `add_variables(var_descriptions: dict[str, str] | list[str]) -> None`
  * Used for adding variables to the system
  * Must be called before branching
* `context_switch(self, target_branch: int) -> None`
  * Used for switching to a different branch
  * Mostly used internally, but can be used to switch contexts manually to easily access variables
* `rotate_context(self) -> None`
  * Mostly used internally, but can be used to rotate contexts manually to easily access variables
* `delete_branch(self, branch: int) -> None` used for deleting a branch
  * Used in `@func` decorated methods
* `var_description(self, name: str) -> str` 
  * Used for getting the description of a variable
* `get_var_vals(self, name: str) -> list`
  * Used for getting the values of a variable spanning all branches
* `get_var_vals_decimal(self, name: str) -> list`
  * Used for getting the decimal values of a variable spanning all branches
* `solved(*variables) -> bool`
  * Used for checking if all the provided variables has been solved
  * Example usage: `solved(self.x, self.y, self.z)` would return `True` if all three variables have been solved in the 
    current branch


## Additional Notes

* Systems can only be solved once
  * A given object that inherits from PyEquations can only be solved once
  * This is to avoid manually setting values resulting in invalid states
  * Doing so will result in a `RuntimeError`
  * If you want to solve with different values, create a new object or re-run with different values
* Variables can only be added/set before the system branches
  * Doing so will result in a `RuntimeError`
  * This is to avoid ambiguity in setting when there could be potentially multiple branches to set
* `@eq` and `@func` decorated methods must be present at instantiation
  * These functions are gathered and processed at instantiation, inefficient (and unnecessary) to check for them later

