# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

__author__ = "Oliver Bruckauf <dsfprinter@bruckauf.net>"
__license__ = 'GNU Affero General Public License http://www.gnu.org/licenses/agpl.html'

import logging
import threading
import queue

from octoprint.util import to_bytes, to_unicode

# noinspection PyBroadException
from pydsfapi.pydsfapi import TaskCanceledException, InternalServerException

from octoprint_dsfprinter.simple_printer import SimplePrinter


class Serial(object):
	logger = logging.getLogger(__name__)
	logger.setLevel(logging.DEBUG)

	serial_log = logging.getLogger("{}.serial".format(__name__))
	serial_log.setLevel(logging.DEBUG)
	serial_log.propagate = False

	def __init__(
			self, printer: SimplePrinter, settings, serial_log_handler=None,
			read_timeout=5.0, write_timeout=10.0, faked_baudrate=115200):
		self.logger.debug("+__init__")

		self._settings = settings
		self._fake_baudrate = faked_baudrate

		if serial_log_handler is not None:
			import logging.handlers
			self.serial_log.addHandler(serial_log_handler)
			self.serial_log.setLevel(logging.INFO)
		self.serial_log.info(u"-" * 78)

		self._read_timeout = read_timeout
		self._write_timeout = write_timeout

		self.queue = queue.Queue()
		# self._queue_lock = threading.Condition()

		self._printer = printer
		self._printer.subscribe()

		buffer_thread = threading.Thread(target=self._process_queue, name="octoprint.plugins.dsfprinter.read_thread")
		buffer_thread.start()

		self.logger.debug("-__init__")

	def __str__(self):
		return "DSF(read_timeout={read_timeout},write_timeout={write_timeout},options={options})" \
			.format(read_timeout=self._read_timeout, write_timeout=self._write_timeout, options=self._settings.get([]))

	@property
	def timeout(self):
		self.logger.debug("timeout -> {}s".format(self._read_timeout))
		return self._read_timeout

	@timeout.setter
	def timeout(self, value):
		self.logger.debug("timeout({}s)".format(value))
		self._read_timeout = value

	@property
	def write_timeout(self):
		self.logger.debug("write_timeout -> {}s".format(self._write_timeout))
		return self._write_timeout

	@write_timeout.setter
	def write_timeout(self, value):
		self.logger.debug("write_timeout({}s)".format(value))
		self._write_timeout = value

	@property
	def port(self):
		self.logger.debug("port -> {}s".format("DSF"))
		return "DSF"

	@property
	def baudrate(self):
		self.logger.debug("baudrate -> {}s".format(self._fake_baudrate))
		return self._fake_baudrate

	def write(self, data):
		# type: (bytes) -> int
		# data = data.strip()
		self.logger.debug("+write({})".format(data))
		self.serial_log.info(">> {}".format(data.strip()))
		b = to_bytes(data, errors="replace")
		u_bytes = to_unicode(b, errors="replace")
		try:
			res = self._printer.command(u_bytes)
			self._publish(res)
		except(TaskCanceledException, InternalServerException) as e:
			self.logger.exception("Exception", exc_info=e)
			self._publish("// {}".format(e))
		self.logger.debug("-write()->{}".format(len(b)))
		return len(b)

	def readline(self):
		# type: () -> bytes
		self.logger.debug("+readline()")
		try:
			# fetch a line from the queue, wait no longer than timeout
			line = to_unicode(self.queue.get(timeout=self._read_timeout), errors="replace")
			self.queue.task_done()
			self.serial_log.info(u"<< {}".format(line.strip()))
			self.logger.debug("-readline()->{}".format(line))
			return to_bytes(line)
		except queue.Empty:
			# queue empty? return empty line
			self.logger.debug("-readline()->Empty")
			return b""

	def close(self):
		self.logger.debug("+close()")
		self.queue = None
		self._printer.close()
		self.logger.debug("-close()")

	def _publish(self, line):
		# type: (str) -> None
		self.logger.debug("+_publish line={}".format(line))
		if self.queue is not None:
			self.queue.put(line)
		self.logger.debug("-_publish len(queue)={}".format(self.queue.qsize()))

	# noinspection PyBroadException
	def _process_queue(self):
		while self.queue is not None:
			self.logger.debug("+_process_queue qsize={}".format(self.queue.qsize()))
			try:
				cde = self._printer.intercept()
				if cde is not None:
					data = to_unicode(cde.__str__(), encoding="ascii", errors="replace").strip()
					self.logger.debug("process_queue data={}".format(data))
					# self._publish(data)
				else:
					self.logger.debug("process_queue cde was None")
			except (InternalServerException, BrokenPipeError, TaskCanceledException) as e:
				self.logger.exception("Exception on intercept", exc_info=e)
			except ConnectionResetError:
				self.close()
			finally:
				self.logger.debug("+_process_queue qsize={}".format(self.queue.qsize()))
