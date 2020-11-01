"""
	Machine contains a generic implementation for the machine model.
"""

import logging
from octoprint_dsfprinter.pydsfapi.model.machinemodel import MachineModel


class Machine:
	"""
	Machine provides generic access to the machine model.
	"""

	patch_logger = logging.getLogger("octoprint.plugins.dsfprinter.model.machine.patch")
	patch_logger.setLevel(logging.INFO)

	def __init__(self, machine_model: MachineModel):
		self.machine_model = machine_model
		self._logger = logging.getLogger("octoprint.plugins.dsfprinter.model.machine")
		self._logger.setLevel(logging.DEBUG)

	def apply_patch(self, patch):
		self.patch(self.machine_model.__dict__, patch)

	def patch(self, a, b, path=None, debug=False):
		if path is None:
			path = []
		if len(path) == 0:
			self.patch_logger.debug("patch the machine model")
			self.patch_logger.debug(b)
		for key in b:
			# debug draws a sort of diagram indicating nesting depth
			if self.patch_logger.isEnabledFor(logging.DEBUG):
				s = "   "
				for _ in path:
					s += " > "
				s += key
				self.patch_logger.debug(s)

			if key in a:
				# the element in the patch already exists in the model
				if isinstance(a[key], dict) and isinstance(b[key], dict):
					# a[key] and b[key] are both dicts, recurse
					self.patch(a[key], b[key], path + [str(key)], debug)
				elif isinstance(a[key], list) and isinstance(b[key], list):
					# a[key] and b[key] are both list, enumerate
					for idx, value in enumerate(b[key]):
						# need new diagram line here for the enumerations
						if self.patch_logger.isEnabledFor(logging.DEBUG):
							s = "   "
							for _ in path:
								s += " > "
							# put [] around index to identify we're in a list
							s += " > [" + str(idx) + "]"
							self.patch_logger.debug(s)
						# initially assume it's a list of dicts / lists and recurse
						try:
							a[key][idx] = self.patch(a[key][idx], b[key][idx], path + [str(key), str(idx)], debug)
						except TypeError:
							# but if that didn't work treat it as a leaf
							if self.patch_logger.isEnabledFor(logging.DEBUG):
								s = ""
								for _ in path:
									s += "   "
								# put [] around index to identify we're in a list
								s += " > [" + str(idx) + "]"
								s += "       = " + str(b[key][idx])
								self.patch_logger.debug(s)
							a[key][idx] = b[key][idx]
				else:
					# treat as a leaf, but note either (but not both) could actually be a dict
					# e.g. a[key] could have been a single value and we now overwrite with a new dict
					# or it could have been a dict and now we've overwritten a single scalar
					if self.patch_logger.isEnabledFor(logging.DEBUG):
						s = ""
						for _ in path:
							s += "   "
						s += "    = " + str(b[key])
						self.patch_logger.debug(s)
					a[key] = b[key]
			else:
				# the key in the path is not yet in the model - just splice it in
				if self.patch_logger.isEnabledFor(logging.DEBUG):
					s = ""
					for _ in path:
						s += "   "
					s += "*** = " + str(b[key])
					self.patch_logger.debug(s)
				a[key] = b[key]
		return a
