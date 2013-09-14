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
		self.textlocalUser = pluginPrefs.get("textlocalUser", "")
		self.textlocalPasswd = pluginPrefs.get("textlocalPasswd", "")
		self.textlocalFromValue = pluginPrefs.get("textlocalFromValue", "MyHome")
	
	########################################
	def __del__(self):
		indigo.PluginBase.__del__(self)
		
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
				indigo.server.log("Received an error from TextLocal: %s" % (jsonResponse['Error']))
			else:
				indigo.server.log("Message successfully sent via TextLocal")
		except IOError:
			indigo.server.log("Unable to contact TextLocal service.")
