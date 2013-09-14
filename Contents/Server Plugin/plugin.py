#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################
# Copyright (c) 2013, Kieran J. Broadfoot. All rights reserved.
#

################################################################################
# Imports
################################################################################
import sys
import os
import re
import urllib
import simplejson as json

################################################################################
# Globals
################################################################################
kTriggerType_CreditLow = "lowCredit"
kTriggerType_CreditExpired = "expiredCredit"

########################################
def updateVar(name, value, folder=0):
	if name not in indigo.variables:
		indigo.variable.create(name, value=value, folder=folder)
	else:
		indigo.variable.updateValue(name, value)

################################################################################
class Plugin(indigo.PluginBase):
	########################################
	# Class properties
	########################################
	
	########################################
	def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs): 
		indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
		self.events = dict()
		self.events[kTriggerType_CreditLow] = dict()
		self.events[kTriggerType_CreditExpired] = dict()
		self.textlocalUser = pluginPrefs.get("textlocalUser", "")
		self.textlocalPasswd = pluginPrefs.get("textlocalPasswd", "")
		self.textlocalFromValue = pluginPrefs.get("textlocalFromValue", "MyHome")
		self.textlocalCreditWarning = pluginPrefs.get("textlocalCreditWarning", "10")
	
	########################################
	def __del__(self):
		indigo.PluginBase.__del__(self)
		
	def triggerStartProcessing(self, trigger):
		if (trigger.pluginTypeId == kTriggerType_CreditLow) or (trigger.pluginTypeId == kTriggerType_CreditExpired):
			self.events[trigger.pluginTypeId][trigger.id] = trigger

	def triggerStopProcessing(self, trigger):
		if trigger.pluginTypeId in self.events:
			if (trigger.pluginTypeId == kTriggerType_CreditLow) or (trigger.pluginTypeId == kTriggerType_CreditExpired):
				if trigger.id in self.events[trigger.pluginTypeId]:
					del self.events[trigger.pluginTypeId][trigger.id]
	
	def sendTextLocalMessage(self, action, dev):
		if not self.textlocalUser or not self.textlocalPasswd:
			indigo.server.log("No valid user/password combination provided.")
		if not action.props.get("tlPhoneNumber",""):
			indigo.server.log("No phone number provided.")
		if not action.props.get("tlMessage",""):
			indigo.server.log("No message provided.")

		phoneNumbers = []
		for number in action.props.get("tlPhoneNumber","").split(","):
			phoneNumbers.append(indigo.variables[number].value)

		params = {'uname': self.textlocalUser, 
			'pword': self.textlocalPasswd, 
			'selectednums': ",".join(phoneNumbers),
			'message' : action.props.get("tlMessage",""), 
			'from': self.textlocalFromValue,
			'json': 1}

		try:
			handle = urllib.urlopen('https://www.txtlocal.co.uk/sendsmspost.php?' + urllib.urlencode(params))
			jsonResponse = json.loads(handle.read())
			if 'Error' in jsonResponse:
				if jsonResponse['Error'] == "No credit" or jsonResponse['Error'] == "Not enough credit":
					for trigger in self.events[kTriggerType_CreditExpired]:
						indigo.trigger.execute(trigger)
				indigo.server.log("Received an error from TextLocal: %s" % (jsonResponse['Error']))
			else:
				# check for current credit value.  if number = 10 then fire lowcredit message, if 0 then error
				if 'CreditsRemaining' in jsonResponse and int(jsonResponse['CreditsRemaining']) <= int(self.textlocalCreditWarning):
					indigo.server.log("Credit warning for your TextLocal account")
					for trigger in self.events[kTriggerType_CreditLow]:
						indigo.trigger.execute(trigger)
				indigo.server.log("Message successfully sent via TextLocal")
		except IOError:
			indigo.server.log("Unable to contact TextLocal service.")
