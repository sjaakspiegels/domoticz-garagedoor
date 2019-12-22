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
        <param field="Port" label="MQTT Port" width="150px" required="true" default="1883"/>
        <param field="Username" label="MQTT Username" width="150px" required="true" default=""/>
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
import paho.mqtt.client as mqtt

class BasePlugin:
 
    mqttClient = None
    mqttserveraddress = 'localhost'
    mqttserverport = 1883
    mqttusername = ''
    mqttpassword = ''

    def __init__(self):
        return

    def onStart(self):
        Domoticz.Debug("onStart called")
        if Parameters["Mode6"] == "Debug":
            Domoticz.Debugging(1)        
            Domoticz.Log("Debugging ON")
        if ('GarageDoorClosed'  not in Images): Domoticz.Image('GarageDoorClosed.zip').Create()
        if ('GarageDoorOpen' not in Images): Domoticz.Image('GarageDoorOpen.zip').Create()
        if ('GarageDoorHalfOpen' not in Images): Domoticz.Image('GarageDoorHalfOpen.zip').Create()

        self.mqttserveraddress = Parameters["Address"].strip()
        self.mqttserverport = Parameters["Port"].strip()
        self.mqttusername = Parameters["Username"].strip()
        self.mqttpassword = Parameters["Password"].strip()

        self.mqttClient = mqtt.Client()
        self.mqttClient.on_connect = onMQTTConnect
        self.mqttClient.username_pw_set(username=self.mqttusername, password=self.mqttpassword)
        Domoticz.Debug("Before connect MQTT")
        self.mqttClient.connect(self.mqttserveraddress, int(self.mqttserverport), 60)
        Domoticz.Debug("After connect MQTT")
#        self.mqttClient.loop_start()
#        self.mqttClient = MqttClientSH2(self.mqttserveraddress, self.mqttserverport, "", self.onMQTTConnected, self.onMQTTDisconnected, self.onMQTTPublish, self.onMQTTSubscribed)
# username_pw_set(username=”roger”,password=”password”)

        if (len(Devices) == 0):
            Options = {"LevelActions": "|","LevelNames": "Open|Sluit","LevelOffHidden": "false","SelectorStyle": "1"}
            Domoticz.Device(Name="garage-door-status", Unit=1, TypeName="Selector Switch", Switchtype=18, Image=13, Options=Options).Create()
            Domoticz.Log("Devices created.")

        if (1 in Devices):
            UpdateImage(1, 'GarageDoorHalfOpen')
 
    def onStop(self):
        Domoticz.Debug("onStop called")

    def onConnect(self, Connection, Status, Description):
        Domoticz.Debug("onConnect called")

    def onMQTTConnect(self, client, userdata, flags, rc):
        Domoticz.Debug("onMQTTConnect called")

    def onMessage(self, Connection, Data):
        Domoticz.Debug("onMessage called")

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Debug("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Debug("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Debug("onDisconnect called")

    def onDeviceModified(self, Unit):
        Domoticz.Debug("onDeviceModified called for Unit " + str(Unit))

    def onHeartbeat(self):
        Domoticz.Debug("onHeartbeat called")
        if (1 in Devices):
            Domoticz.Debug("Device 1 exists")
        if ('GarageDoorClosed' in Images):
            Domoticz.Debug("Image closed exists")

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

def onDeviceModified(Unit):
    global _plugin
    _plugin.onDeviceModified(Unit)

def onMQTTConnect(client, userdata, flags, rc):
    global _plugin
    _plugin.onMQTTConnect(client, userdata, flags, rc)


# Synchronise images to match parameter in hardware page
def UpdateImage(Unit, StateIcon):
    if (Unit in Devices) and (StateIcon in Images):
        Domoticz.Debug("Device Image update")
        if (Devices[Unit].Image != Images[StateIcon].ID):
            Devices[Unit].Update(nValue=Devices[Unit].nValue, sValue=str(Devices[Unit].sValue), Image=Images[StateIcon].ID)
    return