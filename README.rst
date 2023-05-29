===========
PyEquations
===========

Overview
========

A Python package for solving a bunch of equations with a bunch of unknowns.
Maximally solves with given equations, functions, and variables. Internally uses SymPy
for symbolic math and supports units on all variables.

The key advantage of this package is that you don't need to know what specific equations to use to solve for a certain value.
You can simply dump all of the equations and the known values. PyEquations will figure out the rest.

Installation
============

::

    pip install pyequations


Use Cases and Examples
======================

Basic Example
-------------

Suppose we on top of a 100 meter tall building and we throw a ball up with an initial velocity.
How long does it take to hit the ground and at what velocity?

This is a simple problem if one has studied physics. Everything can be solved for using the kinematic equations (of constant acceleration):

.. math::

   v_f = v_0 + at

    x_f = x_0 + v_0 + \frac{1}{2}at^2

    v_f^2 = v_0^2 + 2a(x_f - x_0)

    x_f = x_0 + \frac{1}{2}(v_0 + v_f)t



Let's demonstrate how to solve this problem with PyEquations.::

    from pyequations.inheritables import PyEquations
    from pyequations.utils import solved
    from pyequations.decorators import eq, func
    from sympy.physics.units import meter


    # Create a new class that inherits from PyEquations
    class Kinematic(PyEquations):

        # Define our variables with optional descriptions
        def __init__(self):
            super().__init__()
            self.add_var('x_0', 'Initial position')
            self.add_var('x_f', 'Final position')
            self.add_var('v_0', 'Initial velocity')
            self.add_var('v_f', 'Final velocity')
            self.add_var('a', 'Acceleration')
            self.add_var('t', 'Time')

        # Define our equations by noting them with the eq decorator
        # An '=' sign is replaced with a ',' thereby returning a tuple
        @eq
        def calc_v_f(self):
            return self.v_f, self.v_0 + self.a * self.t

        @eq
        def calc_x_f(self):
            return self.x_f, self.x_0 + self.v_0 * self.t + 0.5 * self.a * self.t ** 2

        @eq
        def calc_v_f2(self):
            return self.v_f ** 2, self.v_0 ** 2 + 2 * self.a * (self.x_f - self.x_0)

        @eq
        def calc_x_f2(self):
            return self.x_f, self.x_0 + 0.5 * (self.v_0 + self.v_f) * self.t

This has set us up to solve the problem. Let's create an instance of our class and set our variables: ::

    k = Kinematic()

    k.x_0 = 100 * meter
    k.v_0 = 10 * meter / second
    k.a = -9.8 * meter / second ** 2

Now running the solver: ::

    k.solve()

    print(k.vars())

Output: ::

Feature List
============


Dependencies
============
* Python 3.10+
* SymPy 1.12+




set up github workflow

inheritance

list dependencies

test more

note support for changing and then resolving clear_var

Test clear_var

Maybe keep multiple solutions and point to dependency and let user choose
Or recursively make instances

complex?

note that __ names are reserved for python