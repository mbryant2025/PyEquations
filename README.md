# PyEquations

## Overview

A Python package for solving a bunch of equations with a bunch of unknowns.
PyEquations maximally solves with the given equations, functions, and variables. It internally uses SymPy
for symbolic math and supports it units on all variables.

The key advantage of this package is that you don't need to know what specific equations to use to solve for a certain value.
You can simply dump all the equations and the known values. PyEquations will figure out the rest.

## Installation

```bash
pip install pyequations
```

## Use Cases and Examples

### Basic Example

Suppose we on top of a 100-meter tall building, and we throw a ball up with an initial velocity.
How long does it take to hit the ground and at what velocity?

This is a simple problem if one has studied physics. Everything can be solved for using the kinematic equations (of constant acceleration):

---
$$
v_f = v_0 + at
$$


    x_f = x_0 + v_0 + \frac{1}{2}at^2

    v_f^2 = v_0^2 + 2a(x_f - x_0)

    x_f = x_0 + \frac{1}{2}(v_0 + v_f)t $