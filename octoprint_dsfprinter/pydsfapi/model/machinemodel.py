"""
	MachineModel contains a generic implementation for the machine model.

    Python interface to DuetSoftwareFramework
    Copyright (C) 2020 Duet3D

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""


class MachineModel:
	"""
    MachineModel provides generic access to the machine model.
    """

	@classmethod
	def from_json(cls, data):
		"""Deserialize an instance of this class from JSON deserialized dictionary"""
		return cls(**data)

	def __init__(self, **kwargs):
		for key, value in kwargs.items():
			self.__dict__[key] = value

	def apply_patch(self, patch):
		self.patch(__dict__, patch)

	def patch(a, b, path=None, debug=False):
		if path is None: path = []
		if debug and len(path)==0:
			print("patch the machine model")
			print(b)
		for key in b:
			if debug:
				# debug draws a sort of diagram indicating nesting depth
				print("   ",end="")
				for i in path: print(" > ", end="")
				print(key)
			if key in a:
				# the element in the patch already exists in the model
				if isinstance(a[key], dict) and isinstance(b[key], dict):
					# a[key] and b[key] are both dicts, recurse
					patch(a[key], b[key], path + [str(key)], debug)
				elif isinstance(a[key], list) and isinstance(b[key], list):
					# a[key] and b[key] are both list, enumerate
					for idx, value in enumerate(b[key]):
						# need new diagram line here for the enumerations
						if debug:
							print("   ",end="")
							for i in path: print(" > ",end="")
							# put [] around index to identify we're in a list
							print(" > ["+str(idx)+"]")
						# initially assume it's a list of dicts / lists and recurse
						try:
							a[key][idx] = patch(a[key][idx], b[key][idx], path + [str(key), str(idx)], debug)
						except TypeError:
							# but if that didn't work treat it as a leaf
							if debug:
								for i in path: print("   ",end="")
								print("       = "+str(b[key][idx]))
							a[key][idx] = b[key][idx]
				else:
					# treat as a leaf, but note either (but not both) could actually be a dict
					# e.g. a[key] could have been a single value and we now overwrite with a new dict
					# or it could have been a dict and now we've overwritten a single scalar
					if debug:
						for i in path: print("   ",end="")
						print("    = " + str(b[key]))
					a[key]=b[key]
			else:
				# the key in the path is not yet in the model - just splice it in
				if debug:
					for i in path: print("   ", end="")
					print("*** = " + str(b[key]))
				a[key] = b[key]
		return a

'''
#!/usr/bin/env python3
# subscribe to the machine model and report the temperature each heater

# this is frequency of logging (seconds)
interval=3

# this is duration over which to log (seconds)
duration=90

import json
import sys
import time
from pydsfapi import pydsfapi
from pydsfapi.commands import basecommands, code
from pydsfapi.initmessages.clientinitmessages import InterceptionMode, SubscriptionMode


# establish the connection
subscribe_connection = pydsfapi.SubscribeConnection(SubscriptionMode.PATCH, debug=False)
subscribe_connection.connect()

# decide when to stop logging
endat = time.time() + duration

try:
    # Get the complete model once
    machine_model = subscribe_connection.get_machine_model()

    # Get updates
    while time.time() < endat:
        time.sleep(interval - time.time()%interval)
        # get machine model update as a string
        mm_u_str = subscribe_connection.get_machine_model_patch()
        # convert to a  dict
        mm_update=json.loads(mm_u_str)
        # apply to the saved machine model
        patch(machine_model,mm_update)

        # do something with the machine model
        # in this case just print out heater setpoints and current values
        print (time.strftime('%H:%M:%S'), end="")
        for heater in machine_model['heat']['heaters']:
            print (" {:5.1f} {:5.1f}".format(heater['active'],heater['current']), end="")
        print()
finally:
    subscribe_connection.close()
'''
