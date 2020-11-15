#!/usr/bin/env python3
import array
import json
import logging
from threading import Condition, Event

from pydsfapi import pydsfapi
from pydsfapi.initmessages.clientinitmessages import SubscriptionMode

from octoprint.util import monotonic_time
from octoprint_dsfprinter.model.patch import patch


# noinspection PyBroadException
class Printer:
	logger = logging.getLogger("octoprint.plugins.dsfprinter.printer")
	logger.setLevel(logging.DEBUG)

	temp_logger = logging.getLogger("octoprint.plugins.dsfprinter.printer.current_temp")
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

		self.command_connection = pydsfapi.CommandConnection(debug=True)
		self.command_connection.connect()

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

	def tool_temps(self):
		all_temps = []
		for i in range(len(self.heaters)):
			all_temps.append((i, self.current_temp(i), self.target_temp(i)))
		return all_temps

	def current_temp(self, i):
		self.temp_logger.debug("+current_temp({})".format(i))
		if len(self.heaters) > i:
			self.update_temps()
			with self.connection_lock:
				heater = self.heaters[i]
				temp = self.model.__dict__["heat"]["heaters"][heater]["current"]
				self.temp_logger.debug("-current_temp({}, heater={})->{}".format(i, heater, temp))
				return temp
		else:
			self.temp_logger.debug("-current_temp()->0 (no tool heater)")
			return 0

	def target_temp(self, i):
		self.temp_logger.debug("+target_temp({})".format(i))
		if len(self.heaters) > i:
			self.update_temps()
			with self.connection_lock:
				heater_num = self.heaters[i]
				heater = self.model.__dict__["heat"]["heaters"][heater_num]
				temp = 0
				if heater['state'] == "active":
					temp = heater['active']
				if heater['state'] == "standby":
					temp = heater['standby']
				self.temp_logger.debug("-target_temp({}, heater={})->{}".format(i, heater_num, temp))
				return temp
		else:
			self.temp_logger.debug("-target_temp()->0 (no tool heater)")
			return 0

	@property
	def has_bed_heater(self):
		return len(self.bed_heaters) > 0

	def current_bed_temp(self):
		self.temp_logger.debug("+current_bed_temp()")
		if not self.has_bed_heater:
			self.temp_logger.debug("-current_bed_temp()->0 (no bed heater)")
			return 0
		else:
			self.update_temps()
			with self.connection_lock:
				# return only first bed heater for now
				heater = self.bed_heaters[0]
				temp = self.model.__dict__["heat"]["heaters"][heater]["current"]
				self.temp_logger.debug("-current_bed_temp(heater={})->{}".format(heater, temp))
				return temp

	def target_bed_temp(self):
		self.temp_logger.debug("+target_bed_temp()")
		if not self.has_bed_heater:
			self.temp_logger.debug("-target_bed_temp()->0 (no bed heater)")
			return 0
		else:
			self.update_temps()
			with self.connection_lock:
				# return only first bed heater for now
				heater_num = self.bed_heaters[0]
				heater = self.model.__dict__["heat"]["heaters"][heater_num]
				temp = 0
				if heater['state'] == "active":
					temp = heater['active']
				if heater['state'] == "standby":
					temp = heater['standby']
				self.temp_logger.debug("-target_bed_temp(heater={})->{}".format(heater_num, temp))
				return temp

	@property
	def has_chamber_heater(self):
		return len(self.chamber_heaters) > 0

	def current_chamber_temp(self):
		if not self.has_chamber_heater:
			self.temp_logger.debug("-current_chamber_temp()->0 (no chamber heater)")
			return 0
		else:
			self.update_temps()
			with self.connection_lock:
				# return only first chamber heater for now
				temp = self.model.__dict__["heat"]["heaters"][self.chamber_heaters[0]]["current"]
				self.temp_logger.debug("-current_chamber_temp()->{}".format(temp))
				return temp

	def target_chamber_temp(self):
		if not self.has_chamber_heater:
			self.temp_logger.debug("-target_chamber_temp()->0 (no chamber heater)")
			return 0
		else:
			self.update_temps()
			with self.connection_lock:
				# return only first chamber heater for now
				heater = self.model.__dict__["heat"]["heaters"][self.chamber_heaters[0]]
				temp = 0
				if heater['state'] == "active":
					temp = heater['active']
				if heater['state'] == "standby":
					temp = heater['standby']
				self.temp_logger.debug("-target_chamber_temp()->{}".format(temp))
				return temp

	def command(self, command_str):
		# type: (str) -> str
		try:
			res = self.command_connection.perform_simple_code(command_str)
			print(res)
			return res
		except:
			return 'Not OK, something went wrong'

