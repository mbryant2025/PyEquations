from pyequations.inheritables import PyEquations
from pyequations.decorators import eq, func
from sympy.physics.units import meter, second
from sympy import symbols
from copy import deepcopy, copy


class Problem(PyEquations):

    def __init__(self):
        super().__init__()

        self.add_var('x')
        self.add_var('y')

    @eq
    def eq1(self):
        print(f'running eq 1 with x = {self.x} and y = {self.y}')
        print(f'the id of y is {id(self.y)}')
        return self.x ** 2, 4

    @eq
    def eq2(self):
        print(f'running eq 2 with x = {self.x} and y = {self.y} and SELF is {self}')
        print(f'the id of y is {id(self.y)}')
        return self.y, 2 * self.x

    # @func
    # def constraint(self):
    #     print(f'running constraint with x = {self.x}')
    #     if self.x > 0:
    #         print(f'{self.x} triggered')
    #         self.del_branch()


# Check for func that deletes branch if a condition is met
problem = Problem()

problem.solve()

print('--------------')

branches = problem.root_link.branches

branch1, branch2 = branches
print(branch1)
print(branch1.__dict__)
print(branch1.vars(decimal=True))
print('--------------')
print(branch2)
print(branch2.__dict__)
print(branch2.vars(decimal=True))


# class Test:
#
#     def __init__(self):
#         self.x = symbols('x')
#
#     def calc(self):
#         print(self.x)
#
#
#
# a = Test()
#
# b = copy(a)
#
# # Substitute in 2 for x in b
# b.x = b.x.subs(b.x, 2)
#
# print(a.x)
# print(b.x)
#
# a.calc()
# b.calc()

# The problem is that each branch has its own x and y but when calling the methods it calls methods from the root branch and gets its variab;es
