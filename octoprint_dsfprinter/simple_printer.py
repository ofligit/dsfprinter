#!/usr/bin/env python3
import logging
import re
from threading import Condition, Event
from typing import Optional

from pydsfapi import pydsfapi
from pydsfapi.commands import codechannel, basecommands
from pydsfapi.commands.code import Code
from pydsfapi.initmessages.clientinitmessages import InterceptionMode

from octoprint_dsfprinter.gcode import Gcode


class SimplePrinter:
	logger = logging.getLogger(__name__)
	logger.setLevel(logging.DEBUG)

	def __init__(self, settings):
		self.logger.debug("__init__")
		self.settings = settings

		self.subscribed = Event()
		self.subscribed.clear()

		self.connection_lock = Condition()
		with self.connection_lock:
			self.command_connection = pydsfapi.CommandConnection(debug=True)
			self.command_connection.connect()
			self.intercept_connection = pydsfapi.InterceptConnection(
				interception_mode=InterceptionMode.PRE,
				debug=self.logger.isEnabledFor(logging.DEBUG))
			self.intercept_connection.connect()
		self.logger.debug("-__init__")

	def subscribe(self):
		self.logger.debug("+subscribe")
		with self.connection_lock:
			if self.subscribed.is_set():
				raise ConnectionError("already subscribed")

			self.subscribed.set()
		self.logger.debug("-subscribe")

	def close(self):
		self.logger.debug("+close")
		with self.connection_lock:
			if not self.subscribed.is_set():
				self.logger.error("already closed")
				return

			self.intercept_connection.close()
			self.command_connection.close()
			self.subscribed.clear()
		self.logger.debug("-close")

	# noinspection PyBroadException
	def command(self, cde: str, channel: codechannel.CodeChannel = codechannel.CodeChannel.DEFAULT_CHANNEL):
		self.logger.debug("+command(cde={}, channel={})".format(cde.strip(), channel))
		with self.connection_lock:
			if not self.subscribed.is_set():
				return "// Error, not subscribed"
			self.logger.debug("command gcode={}".format(Gcode(cde)))
			self.parse_gcode(code_str=cde)
			if cde.strip() == "M21":  # ignore M21 as it is not supported / required on Duet 3 with SBC
				return "ok"
			simple_code = basecommands.simple_code(cde, channel)
			res = self.command_connection.perform_command(simple_code)
			self.logger.debug("-command()->{} res={}".format(res.result, res))
			return_string = "ok" if res.success else "!!"
			if len(res.result) > 0:
				return_string += " {}".format(res.result)
			return return_string

	def intercept(self):
		# type: () -> Optional[Code]
		self.logger.debug("+intercept")
		if not self.subscribed.is_set():
			self.logger.debug("not subscribed in intercept")
			return None

		# Wait for a code to arrive
		cde = self.intercept_connection.receive_code()
		# Flush the code's channel to be sure we are being in sync with the machine
		self.logger.debug("+flush")
		success = self.intercept_connection.flush(cde.channel)
		self.logger.debug("+flush")
		# Flushing failed so we need to cancel our code
		if not success:
			self.intercept_connection.cancel_code()
			raise BufferError('Flush failed')
		self.intercept_connection.ignore_code()
		self.logger.debug("-intercept code={}".format(cde))
		return cde

	def parse_gcode(self, code_str: str):
		word_map = {'G': "G", 'M': "M"}
		regexp = r'^.*?(?P<letter>[%s])' % ''.join(word_map.keys())
		self.logger.debug("parse_gcode regexp={}".format(regexp))
		next_word = re.compile(regexp, re.IGNORECASE)
		index = 0
		while True:
			letter_match = next_word.search(code_str[index:])
			if letter_match:
				# Letter
				letter = letter_match.group('letter').upper()
				index += letter_match.end()  # propagate index to start of value

				# Value
				# value_regex = word_map[letter].value_regex
				# value_match = value_regex.search(code_str[index:])
				# if value_match is None:
				# 	raise GCodeWordStrError("word '%s' value invalid" % letter)
				# value = value_match.group() # matched text
				value_match = code_str[index:]

				# yield Word(letter, value)

				self.logger.debug("parse_gcode letter={} value={}".format(letter, value_match.strip()))
				index += len(value_match)  # propagate index to end of value
			else:
				break
