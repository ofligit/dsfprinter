#!/usr/bin/env python3
import array
import json
import logging
from threading import Condition, Event

from pydsfapi import pydsfapi
from pydsfapi.initmessages.clientinitmessages import SubscriptionMode

from octoprint.util import monotonic_time
from octoprint_dsfprinter.model.patch import patch


def command():
	"""Example of a command connection to send arbitrary commands to the machine"""
	command_connection = pydsfapi.CommandConnection(debug=False)
	command_connection.connect()

	try:
		# Perform a simple command and wait for its output
		res = command_connection.perform_simple_code('M115')
		print(res)
	finally:
		command_connection.close()


# noinspection PyBroadException
class Printer:
	logger = logging.getLogger("octoprint.plugins.dsfprinter.printer")
	logger.setLevel(logging.DEBUG)

	temp_logger = logging.getLogger("octoprint.plugins.dsfprinter.printer.temp")
	temp_logger.setLevel(logging.INFO)

	interval = .01

	def __init__(self, settings):
		self.logger.debug("+__init__")
		self.settings = settings
		self.model = None

		self.next_wait_timeout = monotonic_time() - self.interval
		self.subscribed = Event()
		self.subscribed.clear()

		self.connection_lock = Condition()
		self.tool_connection = pydsfapi.SubscribeConnection(SubscriptionMode.FULL, filter_str="tools")
		self.heater_connection = pydsfapi.SubscribeConnection(SubscriptionMode.FULL, filter_str="heat")

		self.heaters = array.array('i', [])
		self.bed_heaters = array.array('i', [])
		self.chamber_heaters = array.array('i', [])
		self.logger.debug("-__init__")

	def subscribe(self):
		self.logger.debug("+subscribe")
		with self.connection_lock:
			if not self.subscribed.is_set():
				self.tool_connection.connect()
				self.heater_connection.connect()
				self.model = self.tool_connection.get_machine_model()
				self.heaters = []
				for tool in self.model.__dict__['tools']:
					self.logger.debug("Printer.subscribe tool={}".format(tool))
					heaters = tool['heaters']
					self.logger.debug("Printer.subscribe tool={} heaters={}".format(tool, heaters))
					if len(heaters) > 0:
						self.heaters.append(tool['heaters'][0])
					self.logger.debug("Printer.subscribe heaters={}".format(heaters))

				heat = self.model.__dict__['heat']
				self.logger.debug("Printer.subscribe heat={}".format(heat))
				for bed_heater in heat['bedHeaters']:
					if bed_heater != -1:
						self.bed_heaters.append(bed_heater)
				self.logger.debug("subscribe bed_heaters={}".format(self.bed_heaters))
				for chamber_heater in heat['chamberHeaters']:
					if chamber_heater != -1:
						self.chamber_heaters.append(chamber_heater)
				self.logger.debug("subscribe chamber_heaters={}".format(self.chamber_heaters))
				self.subscribed.set()
			else:
				self.logger.warning("already subscribed")
		self.logger.debug("-subscribe")

	def update_temps(self):
		self.temp_logger.debug("+update_temps")
		with self.connection_lock:
			if self.subscribed.is_set() and monotonic_time() > self.next_wait_timeout:
				# get machine model update as a string
				mm_u_str = self.heater_connection.get_machine_model_patch()
				# convert to a  dict
				mm_update = json.loads(mm_u_str)
				# apply to the saved machine model
				patch(self.model.__dict__, mm_update)
				self.next_wait_timeout = monotonic_time() + self.interval
		self.temp_logger.debug("-update_temps")

	def temp(self, i):
		self.temp_logger.debug("+temp({})".format(i))
		if len(self.heaters) > i:
			self.update_temps()
			with self.connection_lock:
				heater = self.heaters[i]
				temp = self.model.__dict__["heat"]["heaters"][heater]["current"]
				self.temp_logger.debug("-temp({}, heater={})->{}".format(i, heater, temp))
				return temp
		else:
			self.temp_logger.debug("-temp()->0 (no tool heater)")
			return 0

	def bed_temp(self):
		self.temp_logger.debug("+bed_temp()")
		if len(self.bed_heaters) == 0:
			self.temp_logger.debug("-bed_temp()->0 (no bed heater)")
			return 0
		else:
			self.update_temps()
			with self.connection_lock:
				# return only first bed heater for now
				heater = self.bed_heaters[0]
				temp = self.model.__dict__["heat"]["heaters"][heater]["current"]
				self.temp_logger.debug("-bed_temp(heater={})->{}".format(heater, temp))
				return temp

	def chamber_temp(self):
		if len(self.chamber_heaters) == 0:
			self.temp_logger.debug("-chamber_temp()->0 (no chamber heater)")
			return 0
		else:
			self.update_temps()
			with self.connection_lock:
				# return only first chamber heater for now
				temp = self.model.__dict__["heat"]["heaters"][self.chamber_heaters[0]]["current"]
				self.temp_logger.debug("-chamber_temp()->{}".format(temp))
				return temp
