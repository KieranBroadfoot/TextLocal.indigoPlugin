TextLocal.indigoPlugin
======================

A [Indigo Domotics Indigo 7](http://www.indigodomo.com) plugin for sending SMS messages via TextLocal.com

Setup
-----

1. Create a [TextLocal](http://www.textlocal.com/signup) account
2. Download and install the TextLocal indigo plugin
3. Enter your username/password for your TextLocal account and specify a short name value from which your text messages will appear to originate

Usage
-----

The plugin offers two events for low credit and expired credit to which you can react.  For normal activity however simply choose the "Send a TextLocal message" action.  This takes a variable name which contains a mobile phone number and a text string.

Finally, there is a *very* simple templating engine in the plugin to interpolate indigo state into your text messages.  Simply wrap your python expression in ${}.  An example text message might be: "Temp: ${indigo.devices["Bathroom"].states["temperatureInput1"]}C"