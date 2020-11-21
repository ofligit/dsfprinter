import logging
from unittest import TestCase

from octoprint_dsfprinter.capture_logger import CaptureLogger
from octoprint_dsfprinter.gcode import Gcode


class TestGcode(TestCase):

	def setUp(self) -> None:
		super().setUp()
		logging.basicConfig(level=logging.DEBUG)

	def test_code1(self):
		with CaptureLogger(Gcode.logger):
			gcode = Gcode("N-1 M115 X10*13 ; Comments should be allowed to include * and other stuff")
		self.assertEqual("M", gcode.code)
		self.assertEqual("M115", gcode.command)
		self.assertEqual(13, gcode.checksum)
		self.assertEqual("; Comments should be allowed to include * and other stuff", gcode.comment)

	def test_code2(self):
		with CaptureLogger(Gcode.logger):
			gcode = Gcode("M114")
		self.assertEqual("M", gcode.code)
		self.assertEqual("M114", gcode.command)
		self.assertEqual(0, gcode.checksum)
		self.assertIsNone(gcode.comment)

	def test_code3(self):
		with CaptureLogger(Gcode.logger):
			gcode = Gcode("N-1 M110 N0*125\n")
		self.assertEqual("M", gcode.code)
		self.assertEqual("M110", gcode.command)
		self.assertEqual(125, gcode.checksum)
		self.assertIsNone(gcode.comment)
