import logging


class Gcode:

	logger = logging.getLogger(__name__)
	logger.setLevel(logging.INFO)

	def __init__(self, line: str = None):
		self._code = None
		self._command = None
		self._args: dict[str, str] = dict()
		self._comment = None
		self._checksum = 0
		self._words: list[str] = []
		if line is not None:
			self._parse_line(line)

	@property
	def code(self) -> str:
		return self._code

	@property
	def command(self):
		return self._command

	@property
	def args(self):
		return self._args

	@property
	def comment(self):
		return self._comment

	@property
	def checksum(self):
		return self._checksum

	def _parse_line(self, line):
		self.logger.debug("parse_line line='{}'".format(line))
		line_words = line.split(';', maxsplit=1)
		self.logger.debug("parse_line line_words='{}'".format(line_words))
		if len(line_words) > 1:
			self._comment = ";{}".format(line_words[1])
			self.logger.debug("parse_line found comment '{}'".format(self._comment))

		checksum_words = line_words[0].split('*', maxsplit=1)
		self.logger.debug("parse_line checksum_words='{}'".format(checksum_words))
		if len(checksum_words) > 1:
			self._checksum = int(checksum_words[1].strip())
			self.logger.debug("parse_line found checksum {}".format(self._checksum))

		self.logger.debug("parse_words words='{}'".format(checksum_words[0]))
		for word in checksum_words[0].split():
			self.logger.debug("parse_words word='{}'".format(word))
			if word[0] in ['M', 'G', 'F', 'T']:
				self.logger.debug("parse_words word in [MGFT]")
				self._code = word[0]
				self._command = word
			else:
				self.logger.debug("parse_words other word")
				self._args[word[0]] = word[1:]

	def __str__(self) -> str:
		return "Gcode(code={}, command={}, args{}, comment={}, checksum={})".format(
			self._code, self._command, self._args, self._comment, self._checksum)

if __name__ == '__main__':
	logging.basicConfig(level=logging.DEBUG)
	print(Gcode("M115"))
