from io import StringIO
import logging


class CaptureLogger:
	"""Context manager to capture `logging` streams
	Args:
		- logger: 'logging` logger object
	Results:
		The captured output is available via `self.out`
	"""

	def __init__(self, logger):
		self.logger = logger
		self.io = StringIO()
		self.sh = logging.StreamHandler(self.io)
		self.out = ''

	def __enter__(self):
		self.logger.addHandler(self.sh)
		return self

	def __exit__(self, *exc):
		self.logger.removeHandler(self.sh)
		self.out = self.io.getvalue()

	def __repr__(self):
		return f"captured: {self.out}\n"
