#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################
# Copyright (c) 2016, Kieran J. Broadfoot. All rights reserved.
#

import sys
import os
import re
import urllib
import simplejson as json

kTriggerType_CreditLow = "lowCredit"
kTriggerType_CreditExpired = "expiredCredit"

class Plugin(indigo.PluginBase):

	def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs): 
		indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
		self.events = dict()
		self.events[kTriggerType_CreditLow] = dict()
		self.events[kTriggerType_CreditExpired] = dict()
		self.textlocalUser = pluginPrefs.get("textlocalUser", "")
		self.textlocalPasswd = pluginPrefs.get("textlocalPasswd", "")
		self.textlocalFromValue = pluginPrefs.get("textlocalFromValue", "MyHome")
		self.textlocalCreditWarning = pluginPrefs.get("textlocalCreditWarning", "10")

	def __del__(self):
		indigo.PluginBase.__del__(self)

	def startup(self):
		self.logger.info("starting textlocal plugin")

	def validatePrefsConfigUi(self, valuesDict):
		self.textlocalUser = valuesDict["textlocalUser"]
		self.textlocalPasswd = valuesDict["textlocalPasswd"]
		self.textlocalFromValue = valuesDict["textlocalFromValue"]
		try:
			int(valuesDict["textlocalCreditWarning"])
			self.textlocalCreditWarning = valuesDict["textlocalCreditWarning"]
		except ValueError:
			errorDict = indigo.Dict()
			errorDict["textlocalCreditWarning"] = "Must be a whole number"
			return (False, valuesDict, errorDict)
		return True
		
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
			self.logger.info("No valid user/password combination provided.")
			return
		if not action.props.get("tlPhoneNumber",""):
			self.logger.info("No phone number provided.")
			return
		if not action.props.get("tlMessage",""):
			self.logger.info("No message provided.")
			return

		phoneNumbers = []
		for number in action.props.get("tlPhoneNumber","").split(","):
			phoneNumbers.append(indigo.variables[number].value)

		params = {'uname': self.textlocalUser, 
			'pword': self.textlocalPasswd, 
			'selectednums': ",".join(phoneNumbers),
			'message' : self.generateMessage(action.props.get("tlMessage","")),
			'from': self.textlocalFromValue,
			'json': 1}

		try:
			handle = urllib.urlopen('https://www.txtlocal.co.uk/sendsmspost.php?' + urllib.urlencode(params))
			jsonResponse = json.loads(handle.read())
			if 'Error' in jsonResponse:
				if jsonResponse['Error'] == "No credit" or jsonResponse['Error'] == "Not enough credit":
					for trigger in self.events[kTriggerType_CreditExpired]:
						indigo.trigger.execute(trigger)
				self.logger.info("received an error from TextLocal: %s" % (jsonResponse['Error']))
			else:
				# check for current credit value.  if number = 10 then fire lowcredit message, if 0 then error
				if 'CreditsRemaining' in jsonResponse and int(jsonResponse['CreditsRemaining']) <= int(self.textlocalCreditWarning):
					self.logger.warn("credit warning for your TextLocal account")
					for trigger in self.events[kTriggerType_CreditLow]:
						indigo.trigger.execute(trigger)
				self.logger.info("message successfully sent via TextLocal")
		except IOError:
			self.logger.info("unable to contact TextLocal service.")

	def generateMessage(self, text):
		# a very simple templating engine to extract IOM expressions
		potential = False
		evaluate = False
		result = ""
		evalstr = ""
		for char in text:
			if char == "$":
				potential = True
			elif char == "{" and potential:
				evaluate = True
			elif char == "}":
				if evaluate:
					result = result + str(eval(evalstr))
					evalstr = ""
					potential = False
					evaluate = False
				else:
					# found } but not in eval state
					result = result + char
			else:
				if evaluate:
					evalstr = evalstr+char
				else:
					result = result + char
					potential = False
		return result
