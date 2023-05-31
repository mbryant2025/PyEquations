


cs = ContextStack(['x', 'y'])

print(cs.num_contexts)

cs.add_context(reference=0)

print(cs.num_contexts)

cs.set_value('x', 5)

print(cs.x)

cs.context_idx = 1

print(cs.x)





# cs.context_idx = 1
#
# print(cs.context_idx)
