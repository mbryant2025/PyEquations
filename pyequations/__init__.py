__version__ = '0.1.4'

# Define the epsilon value
# Used as a tolerance for floating point comparisons
# Tolerance is calculated as a percentage of the value
# For example, the two values need to be EPSILON% of each other to be considered equal
EPSILON = 1e-10

# The amount random numbers can vary from the base value
# Is an absolute value not a percentage
# See generate_units_subs.py for more information
RAND_RANGE = 0.2
