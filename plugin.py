# Domoticz garage door
# Works with domoticz and MQTT
# Author: Sjaak Spiegels
#
# Based on code from: 
#
#
"""
<plugin key="Garagedoor" name="Garagedoor" version="1.0.0" author="Sjaak" wikilink="" externallink="">
    <params>
        <param field="Address" label="MQTT Server" width="200px" required="true" default=""/>
        <param field="Port" label="MQTT Port" width="150px" required="true" default=""/>
        <param field="Username" label="MQTT Username" width="150px" required="true" default="1883"/>
        <param field="Password" label="MQTT Password" width="150px" required="true" default="" password="true"/>
        <param field="Mode1" label="MQTT Topic" width="150px" required="true" default=""/>
        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug" default="true"/>
                <option label="False" value="Normal" />
            </options>
      </param>
  </params>
  </plugin>
"""

import Domoticz
import http.client
import base64
import json

class BasePlugin:
 
    def __init__(self):
        return

    def onStart(self):
        Domoticz.Debug("onStart called")
        if Parameters["Mode6"] == "Debug":
            Domoticz.Debugging(1)        
            Domoticz.Log("Debugging ON")
            DumpConfigToLog()

    def onStop(self):
        Domoticz.Debug("onStop called")
        self.connection.close()

    def onConnect(self, Connection, Status, Description):
        Domoticz.Debug("onConnect called")

    def onMessage(self, Connection, Data):
        Domoticz.Debug("onMessage called")

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Debug("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Debug("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Debug("onDisconnect called")

    def onHeartbeat(self):
        Domoticz.Debug("onHeartbeat called")
 

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

    # Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return

def get_sensor_triggered(sensor):
    if sensor is not None:
        Domoticz.Debug("Device: " + sensor["name"] + " status = " + sensor["status"] )
        if sensor['status'].upper() == "DOOR OPEN":
            return True
        elif sensor['status'].upper() == "DOOR CLOSE":
            return False
    else:
        return None

def get_panel_state(panel):
    if panel is not None:
        status = panel['updates']['mode_a1']
        return status.upper()
    else:
        return None

def parse_to_json(sensor_data):
    import json
    import re
    sensor_data = sensor_data.replace("/*-secure-","")
    sensor_data = sensor_data.replace("*/","")
    sensor_data = sensor_data.replace('{	senrows : [','{"senrows":[')
    property_names_to_fix = ["no","type","type_f","area", "zone", "name", "attr", "cond", "cond_ok", "battery", "battery_ok", "tamp", "tamper", "tamper_ok", "bypass", "rssi", "status", "id","su"]
    for p in property_names_to_fix:
        sensor_data = sensor_data.replace(p+' :','"'+p+'":')
    data = json.loads(sensor_data, strict=False)
    return data

def UpdateDevice(Unit, nValue, sValue):
# Make sure that the Domoticz device still exists (they can be deleted) before updating it 
    if (Unit in Devices):
        if (Devices[Unit].nValue != nValue) or (Devices[Unit].sValue != sValue):
            Devices[Unit].Update(nValue=nValue, sValue=str(sValue))
            Domoticz.Debug("Update "+str(nValue)+":'"+str(sValue)+"' ("+Devices[Unit].Name+")")
    return