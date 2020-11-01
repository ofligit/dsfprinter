#!/usr/bin/env python3
import json
import logging
import sys
import threading
import time
from pydsfapi import pydsfapi
from pydsfapi.commands import code
from pydsfapi.initmessages.clientinitmessages import InterceptionMode, SubscriptionMode

from octoprint_dsfprinter.model.machine import Machine


# noinspection PyBroadException
def intercept():
	"""Example of intercepting and interacting with codes"""
	intercept_connection = pydsfapi.InterceptConnection(InterceptionMode.PRE, debug=True)
	intercept_connection.connect()

	try:
		while True:

			# Wait for a code to arrive
			cde = intercept_connection.receive_code()

			# Flush the code's channel to be sure we are being in sync with the machine
			success = intercept_connection.flush(cde.channel)

			# Flushing failed so we need to cancel our code
			if not success:
				print('Flush failed')
				intercept_connection.cancel_code()
				continue

			# Check for the type of the code
			if cde.type == code.CodeType.MCode:
				# Do whatever needs to be done if this is the right code
				print(cde, cde.flags)

			# We here ignore it so it will be continued to be processed
			intercept_connection.ignore_code()
	except:
		e = sys.exc_info()[0]
		print("Closing connection: ", e)
		intercept_connection.close()


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

	def __init__(self):
		try:
			self.subscribe_connection = pydsfapi.SubscribeConnection(
				SubscriptionMode.PATCH,
				debug=self.logger.isEnabledFor(logging.DEBUG))

			self.subscriptionThread = threading.Thread(
				target=self._process_machine_model(),
				name="octoprint.plugins.dsfprinter.subscription_thread")

			self.machine = None
		except:
			self.logger.exception("Exception creating printer")

	def subscribe(self):
		try:
			self.subscribe_connection.connect()
			self.machine = Machine(self.subscribe_connection.get_machine_model())
			self.logger.debug(self.machine.machine_model.__dict__)
			self.subscriptionThread.start()
		except:
			self.machine = None
			self.logger.exception("Exception creating subscriber")

	def _process_machine_model(self):
		while self.machine is not None:
			try:
				patch = self.subscribe_connection.get_machine_model_patch()
				self.logger.debug(patch)
				self.machine.apply_patch(json.loads(patch))
				self.logger.debug(self.machine.machine_model)
			except:
				self.logger.exception("Exception in processMachineModel loop")
			time.sleep(1.0)
		self.subscribe_connection.close()

# intercept()
# command()
# subscribe()
