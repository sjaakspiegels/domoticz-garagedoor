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
        <param field="Mode1" label="MQTT State Topic" width="150px" required="true" default=""/>
        <param field="Mode2" label="Button# open" width="150px" required="true" default="1"/>
        <param field="Mode3" label="Button# close" width="150px" required="true" default="2"/>
        <param field="Mode4" label="Switch# opened" width="150px" required="true" default="3"/>
        <param field="Mode5" label="Switch# closed" width="150px" required="true" default="4"/>
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
    mqttserveraddress = "localhost"
    mqttserverport = 1883
    mqttusername = ""
    mqttpassword = ""
    mqttstatetopic = ""
    mqttbuttonopen = ""
    mqttbuttonclose = ""
    mqttswitchopen = ""
    mqttswitchclosed = ""
    garagedoorstate = "GarageDoorHalfOpen"
    garagedoor_is_open = False
    garagedoor_is_closed = False

    def __init__(self):
        return

    def onStart(self):
        Domoticz.Debug("onStart called")
        if Parameters["Mode6"] == "Debug":
            Domoticz.Debugging(1)        
            Domoticz.Log("Debugging ON")
        if ("GarageDoorClosed"  not in Images): Domoticz.Image("GarageDoorClosed.zip").Create()
        if ("GarageDoorOpen" not in Images): Domoticz.Image("GarageDoorOpen.zip").Create()
        if ("GarageDoorHalfOpen" not in Images): Domoticz.Image("GarageDoorHalfOpen.zip").Create()

        if (len(Devices) == 0):
            Options = {"LevelActions": "||","LevelNames": "Off|Open|Sluit","LevelOffHidden": "true","SelectorStyle": "0"}
            Domoticz.Device(Name="garage-door-status", Unit=1, TypeName="Selector Switch", Switchtype=18, Options=Options).Create()
            Domoticz.Log("Devices created.")

        self.updateGarageDoorState(None, None)

        self.mqttserveraddress = Parameters["Address"].strip()
        self.mqttserverport = Parameters["Port"].strip()
        self.mqttusername = Parameters["Username"].strip()
        self.mqttpassword = Parameters["Password"].strip()
        self.mqttstatetopic = Parameters["Mode1"].strip()
        self.mqttbuttonopen = Parameters["Mode2"].strip()
        self.mqttbuttonclose = Parameters["Mode3"].strip()
        self.mqttswitchopen = Parameters["Mode4"].strip()
        self.mqttswitchclosed = Parameters["Mode5"].strip()

        self.mqttClient = mqtt.Client()
        self.mqttClient.on_connect = onMQTTConnect
        self.mqttClient.on_subscribe = onMQTTSubscribe
        self.mqttClient.on_message = onMQTTmessage
        self.mqttClient.username_pw_set(username=self.mqttusername, password=self.mqttpassword)
        self.mqttClient.connect(self.mqttserveraddress, int(self.mqttserverport), 60)        
        self.mqttClient.loop_start()

    def onStop(self):
        Domoticz.Debug("onStop called")
        self.mqttClient.unsubscribe(self.mqttstatetopic)
        self.mqttClient.disconnect()

    def onConnect(self, Connection, Status, Description):
        Domoticz.Debug("onConnect called")

    def onMQTTConnect(self, client, userdata, flags, rc):
        Domoticz.Debug("onMQTTConnect called")
        Domoticz.Debug("Connected to " + self.mqttserveraddress + " with result code {}".format(rc))
        self.mqttClient.subscribe("tele/" + self.mqttstatetopic,1)
        self.mqttClient.subscribe("cmnd/" + self.mqttstatetopic,1)

    def onMQTTSubscribe(self, client, userdata, mid, granted_qos):
        Domoticz.Debug("onMQTTSubscribe called")

    def onMQTTmessage(self, client, userdata, message):
        Domoticz.Debug("message topic=" + message.topic)
        payload = str(message.payload.decode("utf-8"))
        Domoticz.Debug("message received " + payload)

        if message.topic == "cmnd/" + self.mqttstatetopic.replace("#",'POWER' + self.mqttswitchclosed):
            Domoticz.Debug("Power Close switch")
            self.updateGarageDoorState(payload == 'ON', None)

        if message.topic == "cmnd/" + self.mqttstatetopic.replace("#","POWER" + self.mqttswitchopen):
            Domoticz.Debug("Power Open switch")
            self.updateGarageDoorState(None, payload == "ON")

        if message.topic == "tele/" + self.mqttstatetopic.replace("#",'SENSOR'):
            json_msg = json.loads(payload)
            Domoticz.Debug("Sensor message: " + str(json_msg))
            self.updateGarageDoorState(json_msg["Switch" + self.mqttswitchclosed] == "ON", json_msg["Switch" + self.mqttswitchopen] == "ON")

    def updateGarageDoorState(self, GarageDoorClosed, GarageDoorOpen):
        Domoticz.Debug("Update garage door state " + str(GarageDoorClosed) + ", " + str(GarageDoorOpen))
        if GarageDoorClosed is not None:
            if GarageDoorClosed:
                self.garagedoor_is_open = False
                self.garagedoor_is_closed = True
            else:
                self.garagedoor_is_closed = False

        if GarageDoorOpen is not None:
            if GarageDoorOpen:
                self.garagedoor_is_open = True
                self.garagedoor_is_closed = False
            else:
                self.garagedoor_is_open = False

        Domoticz.Debug("Garage door current state: " + self.garagedoorstate)

        state = self.garagedoorstate
        if self.garagedoor_is_closed:
            self.garagedoorstate = 'GarageDoorClosed'    
        elif self.garagedoor_is_open:
            self.garagedoorstate = 'GarageDoorOpen'    
        else:
            self.garagedoorstate = 'GarageDoorHalfOpen'    

        Domoticz.Debug("Garage door new state: " + self.garagedoorstate)

        if state != self.garagedoorstate:
            Domoticz.Log("Garage door " + state + " => " + self.garagedoorstate)
            UpdateImage(1, self.garagedoorstate)

    def onMessage(self, Connection, Data):
        Domoticz.Debug("onMessage called")

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Debug("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))
        if Level == 10:
            Domoticz.Log("Garage door open")
            self.mqttClient.publish("cmnd/" + self.mqttstatetopic.replace("#","power" + self.mqttbuttonopen), payload = "on", qos=1)
        elif Level == 20:
            Domoticz.Log("Garage door close")
            self.mqttClient.publish("cmnd/" + self.mqttstatetopic.replace("#","power" + self.mqttbuttonclose), payload = "on", qos=1)


    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Debug("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Debug("onDisconnect called")

    def onDeviceModified(self, Unit):
        Domoticz.Debug("onDeviceModified called for Unit " + str(Unit))

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

def onDeviceModified(Unit):
    global _plugin
    _plugin.onDeviceModified(Unit)

def onMQTTConnect(client, userdata, flags, rc):
    global _plugin
    _plugin.onMQTTConnect(client, userdata, flags, rc)

def onMQTTSubscribe(client, userdata, mid, granted_qos):
    global _plugin
    _plugin.onMQTTSubscribe(client, userdata, mid, granted_qos)

def onMQTTmessage(client, userdata, message):
    global _plugin
    _plugin.onMQTTmessage(client, userdata, message)

# Synchronise images to match parameter in hardware page
def UpdateImage(Unit, StateIcon):
    if (Unit in Devices) and (StateIcon in Images):
        Domoticz.Debug("Device Image update to " + StateIcon)
        if (Devices[Unit].Image != Images[StateIcon].ID):
            Devices[Unit].Update(nValue=Devices[Unit].nValue, sValue=StateIcon, Image=Images[StateIcon].ID)
    else:
        Domoticz.Debug("Error update icon")
    return