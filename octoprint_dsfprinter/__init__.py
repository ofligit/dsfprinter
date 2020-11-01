# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin


class DSFPrinterPlugin(octoprint.plugin.SettingsPlugin,
                       octoprint.plugin.AssetPlugin,
                       octoprint.plugin.StartupPlugin):

	##~~ StartupPlugin mixin

	def on_after_startup(self):
		self._logger.info("Loaded DSFPrinter Plugin")


	##~~ SettingsPlugin mixin

	def get_settings_defaults(self):
		return {
			"title": "DSF",
			"enabled": True,
			"okAfterResend": False,
			"forceChecksum": False,
			"numExtruders": 1,
			"pinnedExtruders": None,
			"includeCurrentToolInTemps": True,
			"includeFilenameInOpened": True,
			"hasBed": True,
			"hasChamber": False,
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
			"firmwareName": "DSF",
			"sharedNozzle": False,
			"sendBusy": False,
			"busyInterval": 2.0,
			"simulateReset": True,
			"resetLines": ['start', 'DSF: Virtual DSF!', '\x80', 'SD card ok'],
			"preparedOks": [],
			"okFormatString": "ok",
			"m115FormatString": "FIRMWARE_NAME:{firmware_name} PROTOCOL_VERSION:1.0",
			"m115ReportCapabilities": True,
			"capabilities": {
				"AUTOREPORT_TEMP": True,
				"AUTOREPORT_SD_STATUS": True,
				"EMERGENCY_PARSER": True
			},
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

	##~~ AssetPlugin mixin

	def get_assets(self):
		# Define your plugin's asset files to automatically include in the
		# core UI here.
		return dict(
			js=["js/dsfprinter.js"],
			css=["css/dsfprinter.css"],
			less=["less/dsfprinter.less"]
		)

	##~~ Softwareupdate hook

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
		self._logger.info("+DSFPrinterPlugin.dsfprinter_factory"+str(port))
		if not port == "DSF":
			return None

		import logging.handlers
		from octoprint.logging.handlers import CleaningTimedRotatingFileHandler

		seriallog_handler = CleaningTimedRotatingFileHandler(
			self._settings.get_plugin_logfile_path(postfix="serial"),
			when="D",
			backupCount=3)

		seriallog_handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
		seriallog_handler.setLevel(logging.DEBUG)

		from . import dsfprinter

		serial_obj = dsfprinter.DSFPrinter(self._settings,
										   seriallog_handler=seriallog_handler,
										   read_timeout=float(read_timeout),
										   faked_baudrate=baudrate)
		return serial_obj

	def get_additional_port_names(self, *args, **kwargs):
		try:
			self._logger.info("+DSFPrinterPlugin.get_additional_port_names")
			return ["DSF"]
		finally:
			self._logger.info("-DSFPrinterPlugin.get_additional_port_names")


__plugin_name__ = "DSFPrinter Plugin"
__plugin_pythoncompat__ = ">=3,<4" # only python 3

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
