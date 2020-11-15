"""
# update dictionary-of-dicts-and-lists a with a merge patch b
# values in b overwrite values with same key tree in a
"""


# note this function recurses
# note pydsfapi patches are just a json string so need to be turned into a dict
# before feeding to this function
# if a and b are both lists and b is shorter than a, a will be truncated
# this behaviour can be changed below - search 'truncated'
# debug=True draws a diagram
# debug=True and verbose=True reports input to the function on every entry
def patch(a, b, path=None, debug=False, verbose=False):
	if path is None:
		path = []
	if debug and (len(path) == 0 or verbose):
		print('patch: ' + str(b))
		if verbose:
			print(' into: ' + str(a))
			print(' at :  ' + str(path))

	# if both a and b are dicts work through the keys
	if isinstance(a, dict) and isinstance(b, dict):
		for key in b:
			if debug:
				# debug draws a sort of diagram indicating nesting depth
				print('   ', end='')
				for _ in path:
					print(' > ', end='')
				print(key)
			if key in a:
				# the element in the patch already exists in the original
				if ((isinstance(a[key], dict) and isinstance(b[key], dict))
						or (isinstance(a[key], list) and isinstance(b[key], list))):
					# a[key] and b[key] are both dicts or both lists, recurse
					a[key] = patch(a[key], b[key], path + [str(key)], debug, verbose)
				else:
					# mixed types, so treat as leaf
					if debug:
						for _ in path:
							print('   ', end='')
						print('    = ' + str(b[key]))
					a[key] = b[key]
			else:
				# the element in the patch is not in the original
				# treat as a leaf, but note either could actually be a dict or list
				# e.g. a[key] could have been a single value and we now overwrite with a new dict
				# or it could have been a dict and now we've overwritten a single scalar
				if debug:
					for _ in path:
						print('   ', end='')
					print('    = ' + str(b[key]))
				a[key] = b[key]

	# if both a and b are lists we enumerate and work through the values
	elif isinstance(a, list) and isinstance(b, list):
		# if b is shorter than a, should a be truncated or should the trailing values be unaltered?
		# The following line assumes that trailing values nopt found in b are truncated from a
		# remove this line if desired behaviour is that trailing values in a are left in place
		# note that would mean that a list will grow but never shrink
		a = a[0:len(b)]
		# if b is longer than a you could use a try: except IndexError: below
		# but that requires putting an entire recursion of this function inside the try
		# which makes it difficult to track where teh exception occurs, so instead
		# a is padded to be as long as b in advance
		a.extend([None] * (len(b) - len(a)))
		for idx, value in enumerate(b):
			# need a new diagram nesting line
			if debug:
				print('   ', end='')
				for _ in path:
					print(' > ', end='')
				# put [] around index to identify we're in a list
				print('[' + str(idx) + ']')
			a[idx] = patch(a[idx], b[idx], path + [str(idx)], debug, verbose)

	else:
		# a and b are different types, replace a with b
		if debug:
			for _ in path:
				print('   ', end='')
			print(' = ' + str(b))
		a = b

	# all done
	return a
