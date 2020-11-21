# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin

from octoprint_dsfprinter import simple_serial, simple_printer


class DSFPrinterPlugin(
	octoprint.plugin.SettingsPlugin,
	octoprint.plugin.AssetPlugin,
	octoprint.plugin.StartupPlugin):

	# StartupPlugin mixin

	def __init__(self):
		super().__init__()
		self.comm_instance = None
		self.printer = None

	def on_after_startup(self):
		self._logger.info("Loaded DSFPrinter Plugin")

	# SettingsPlugin mixin

	def get_settings_defaults(self):
		return {
			"title": "DSF",
			"enabled": True,
			"okAfterResend": False,
			"forceChecksum": False,
			"numExtruders": 1,
			"pinnedExtruders": None,
			"includeFilenameInOpened": True,
			"okBeforeCommandOutput": False,
			"reprapfwM114": False,
			"extendedSdFileList": False,
			"throttle": 0.01,
			"sendWait": True,
			"waitInterval": 1.0,
			"rxBuffer": 64,
			"commandBuffer": 4,
			"supportM112": True,
			"echoOnM117": True,
			"brokenM29": True,
			"brokenResend": False,
			"supportF": False,
			"sharedNozzle": False,
			"sendBusy": False,
			"busyInterval": 2.0,
			"preparedOks": [],
			"m115FormatString": "FIRMWARE_NAME:{firmware_name} PROTOCOL_VERSION:1.0",
			"m114FormatString": "X:{x} Y:{y} Z:{z} E:{e[current]} Count: A:{a} B:{b} C:{c}",
			"ambientTemperature": 21.3,
			"errors": {
				"checksum_mismatch": "Checksum mismatch",
				"checksum_missing": "Missing checksum",
				"lineno_mismatch": "expected line {} got {}",
				"lineno_missing": "No Line Number with checksum, Last Line: {}",
				"maxtemp": "MAXTEMP triggered!",
				"mintemp": "MINTEMP triggered!",
				"command_unknown": "Unknown command {}"
			}
		}

	def get_settings_version(self):
		return 1

	def on_settings_migrate(self, target, current):
		if current is None:
			config = self._settings.global_get(["devel", "dsfprinter"])
			if config:
				self._logger.info("Migrating settings from devel.dsfprinter to plugins.dsfprinter...")
				self._settings.global_set(["plugins", "dsfprinter"], config, force=True)
				self._settings.global_remove(["devel", "dsfprinter"])

	# AssetPlugin mixin

	def get_assets(self):
		# Define your plugin's asset files to automatically include in the
		# core UI here.
		return dict(
			js=["js/dsfprinter.js"],
			css=["css/dsfprinter.css"],
			less=["less/dsfprinter.less"]
		)

	# Softwareupdate hook

	def get_update_information(self):
		# Define the configuration for your plugin to use with the Software Update
		# Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
		# for details.
		return dict(
			dsfprinter=dict(
				displayName="DSFPrinter Plugin",
				displayVersion=self._plugin_version,

				# version check: github repository
				type="github_release",
				user="ofligit",
				repo="dsfprinter",
				current=self._plugin_version,

				# update method: pip
				pip="https://github.com/ofligit/dsfprinter/archive/{target_version}.zip"
			)
		)

	def dsfprinter_printer_factory(self, comm_instance, port, baudrate, read_timeout):
		self._logger.info("+DSFPrinterPlugin.dsfprinter_factory port=" + str(port))
		if not port == "DSF":
			return None

		self.comm_instance = comm_instance
		self.printer = simple_printer.SimplePrinter(self._settings)

		import logging.handlers
		from octoprint.logging.handlers import CleaningTimedRotatingFileHandler

		serial_log_handler = CleaningTimedRotatingFileHandler(
			self._settings.get_plugin_logfile_path(postfix="serial"),
			when="D",
			backupCount=3)

		serial_log_handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
		serial_log_handler.setLevel(logging.DEBUG)

		from . import simple_serial

		serial_obj = simple_serial.Serial(
			self.printer,
			self._settings,
			serial_log_handler=serial_log_handler,
			read_timeout=float(read_timeout),
			faked_baudrate=baudrate)

		self._logger.info("-DSFPrinterPlugin.dsfprinter_factory port=" + str(port))
		return serial_obj

	def get_additional_port_names(self, *args, **kwargs):
		try:
			self._logger.info("+DSFPrinterPlugin.get_additional_port_names")
			return ["DSF"]
		finally:
			self._logger.info("-DSFPrinterPlugin.get_additional_port_names")


__plugin_name__ = "DSFPrinter Plugin"
__plugin_pythoncompat__ = ">=3,<4"  # only python 3


def __plugin_load__():
	plugin = DSFPrinterPlugin()

	global __plugin_implementation__
	__plugin_implementation__ = plugin

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
		"octoprint.comm.transport.serial.factory": plugin.dsfprinter_printer_factory,
		"octoprint.comm.transport.serial.additional_port_names": plugin.get_additional_port_names
	}
