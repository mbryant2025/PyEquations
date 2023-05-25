===========
PyEquations
===========

Overview
========

A Python package for solving a bunch of equations with a bunch of unknowns.
Maximally solves with given equations, functions, and variables. Utilizes SymPy
for symbolic math and supports units on all variables.

Installation
============

::

    pip install pyequations


Use Cases and Examples
======================

Basic Example
-------------

.. math::

   a = b + c


latex examples

.. math::

   \frac{ \sum_{t=0}^{N}f(t,k) }{N}

python example

    ```python
    from pyequations import Equation, Variable, Function, solve
    python```

:code:`a = b + c`

:math:`a = b + c`

This is `interpreted text` using the default role.


My amazing code here::

    def my_function():
        print("Hello World!")


Wow go me


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