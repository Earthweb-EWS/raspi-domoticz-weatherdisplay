# -*- coding:utf-8 -*-

from luma.core.interface.serial import i2c, spi
from luma.core.render import canvas
from luma.core import lib

from luma.oled.device import sh1106
import RPi.GPIO as GPIO

import time
import subprocess
import thread

import locale

from datetime import datetime
from decimal import Decimal

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import urllib, json

import logging
import os

# Set to users preferred locale:
locale.setlocale(locale.LC_ALL, '')

# URL to Domoticz Device
# http://www.domoticz.com/wiki/Domoticz_API/JSON_URL%27s#Retrieve_status_of_specific_device
# http://www.domoticz.com/wiki/Domoticz_API/JSON_URL%27s#Base64_encode
#
# Don't forget to fill in Device Description because this is the header of the display.
#
liveurl = "https://URL/json.htm?username=USER==&password=PASS&type=devices&rid=<SENSORID>" # <SENSORID> as placeholder for sensorid variable.
dayurl = "https://URL/json.htm?username=USER==&password=PASS&type=graph&sensor=temp&idx=<SENSORID>&range=day" # <SENSORID> as placeholder for sensorid variable.

livedata = 0 # Placeholder for remote JSON file content.
daydata = 0 # Placeholder for remote JSON file content.
mode = 1 # Default Displaymode (1-3).
timer = 240 # x in seconds for refreshing data from Domoticz.
logPath = os.getcwd() # Path to logfile.
logfileName = "weatherdisplay" # Filename for logfile.
defaultDescription = "Weerstation" # Default Description if not filled in by Domoticz Description.
sensorid = [NUMBER1,NUMBER2,NUMBER3,ETC]
timer2max = 60 # x in seconds to switch back to startscreen.


# Program settings, do not change.
selectedsensor = 1 # Selected sensor from array of sensors. Starts with number one.
timer2 = 1 # x in seconds. Starts with number one.


logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
rootLogger = logging.getLogger()
rootLogger.setLevel(logging.ERROR)

fileHandler = logging.FileHandler("{0}/{1}.log".format(logPath, logfileName))
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)


# Get Remote Data from Domoticz.
def getlivedata():
	try:
		global liveurl
		tmpurl = liveurl
		tmpurl = tmpurl.replace("<SENSORID>", str(sensorid[selectedsensor - 1]))
		if urllib.urlopen(tmpurl).getcode() == 200:
			response = urllib.urlopen(tmpurl)
			return json.loads(response.read())
		else:
			logging.ERROR("URL kan niet worden geopend.")
	except Exception as e:
		logging.exception(e)
		return

# Get Remote Data from Domoticz.
def getdaydata():
	try:
		global dayurl
		tmpurl = dayurl
		tmpurl = tmpurl.replace("<SENSORID>", str(sensorid[selectedsensor - 1]))
		if urllib.urlopen(tmpurl).getcode() == 200:
			response = urllib.urlopen(tmpurl)
			return json.loads(response.read())
		else:
			logging.ERROR("URL kan niet worden geopend.")
	except Exception as e:
		logging.exception(e)
		return
		
def getdesc(obj):
	desc = (obj['result'][0]['Description'])
	if not desc:
		desc = defaultDescription
	return desc

def gettemp(obj):
	tmp = (Decimal(obj['result'][0]['Temp']))
	return ('{0:.3g}'.format(tmp))

def getdew(obj):
	tmp = (Decimal(obj['result'][0]['DewPoint']))
	return ('{0:.3g}'.format(tmp))

def gethum(obj):
	tmp = (Decimal(obj['result'][0]['Humidity']))
	return ('{0:.3g}'.format(tmp))

def gethumstat(obj):
	humstat = (obj['result'][0]['HumidityStatus'])
	if humstat == "Normal":
		humstatNL = "Normaal"
	elif humstat == "Comfortable":
		humstatNL = "Comfortabel"
	elif humstat == "Dry":
		humstatNL = "Droog"
	elif humstat == "Wet":
		humstatNL = "Vochtig"
	else:
		humstatNL = humstat

	return humstatNL

def getbatt(obj):
	return(obj['result'][0]['BatteryLevel'])

def getsunrise(obj):
	dt = datetime.strptime((obj['Sunrise']), "%H:%M")
	return(dt.strftime("%H:%M"))

def getsunset(obj):
	dt = datetime.strptime((obj['Sunset']), "%H:%M")
	return(dt.strftime("%H:%M"))

def getstatus(obj):
	return(obj['status'])

def getservertime():
	dt = datetime.strptime(str(datetime.now()), "%Y-%m-%d %H:%M:%S.%f")
	return(dt.strftime("%d-%m-%Y %H:%M"))

def getlastupdate(obj):
	dt = datetime.strptime((obj['result'][0]['LastUpdate']), "%Y-%m-%d %H:%M:%S")
	return(dt.strftime("%d-%m-%Y %H:%M"))

def getavetempperiod1(obj):
	value = 0
	for x in range(len(obj['result']) - 3, len(obj['result'])):
		value = (value + (obj['result'][x]['te']))
	value = (value/3)
	return(value)

def getavetempperiod2(obj):
	value = 0
	for x in range(len(obj['result']) - 12, len(obj['result']) - 4):
		value = (value + (obj['result'][x]['te']))
	value = (value/8)
	return(value)

def gettrend():
	value = 1
	if getavetempperiod1(daydata) > getavetempperiod2(daydata):
		value = 2
	if getavetempperiod1(daydata) < getavetempperiod2(daydata):
		value = 0
	return value

def make_font(name, size):
    font_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 'fonts', name))
    return ImageFont.truetype(font_path, size)

# Define new thread for timer.
def starttimer(threadName, delay):
	try:
		while True:
			#print ("%s" % (threadName))
			global livedata
			global daydata
			livedata=getlivedata()
			daydata=getdaydata()
			time.sleep(delay)
	except Exception as e:
		logging.exception(e)

# Define new thread for timer2.
def starttimer2(threadName, delay):
	try:
		while True:
			#print ("%s" % (threadName))
			global mode
			global selectedsensor
			if not mode == 1:
				global livedata
				global daydata
				mode = 1
				selectedsensor = 1
				livedata=getlivedata()
				daydata=getdaydata()
			else:
				selectedsensor = 1
			time.sleep(delay)
	except Exception as e:
		logging.exception(e)

# Get first time data before the timer kicks in.
try:
	livedata=getlivedata()
	daydata=getdaydata()
except Exception as e:
	logging.exception(e)

# Print Timer Value and start it.
try:
	print ("Refresh data from Domoticz: " + str(timer) + " seconds")
	thread.start_new_thread(starttimer, ("Refresh data Domoticz", timer, ) )

	print ("Refresh data on Screen: " + str(timer2max) + " seconds")
	thread.start_new_thread(starttimer2, ("Refresh data Screen", timer2max, ) )
except Exception as e:
	logging.exception(e)
  
# Print Sensor Status.
if not livedata or not daydata:
	print("{0}: Fout met ophalen data!".format(defaultDescription))
else:
	print("{0}: {1}".format(getdesc(livedata), getstatus(livedata)))


# Load default font.
font = ImageFont.load_default()
fontbig = make_font("code2000.ttf", 36)

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = 128
height = 64
image = Image.new('1', (width, height))

# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height-padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0

#GPIO define
RST_PIN        = 25
CS_PIN         = 8
DC_PIN         = 24
KEY_UP_PIN     = 6 
KEY_DOWN_PIN   = 19
KEY_LEFT_PIN   = 5
KEY_RIGHT_PIN  = 26
KEY_PRESS_PIN  = 13
KEY1_PIN       = 21
KEY2_PIN       = 20
KEY3_PIN       = 16

#SPI or IIC
USER_I2C = 0
if  USER_I2C == 1:
	GPIO.setup(RST_PIN,GPIO.OUT)	
	GPIO.output(RST_PIN,GPIO.HIGH)
	
	serial = i2c(port=1, address=0x3c)
else:
	serial = spi(device=0, port=0, bus_speed_hz = 8000000, transfer_size = 4096, gpio_DC = DC_PIN, gpio_RST = RST_PIN)

device = sh1106(serial, rotate=0) #sh1106

#init GPIO
GPIO.setmode(GPIO.BCM) 
GPIO.setup(KEY_UP_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)    # Input with pull-up
GPIO.setup(KEY_DOWN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Input with pull-up
GPIO.setup(KEY_LEFT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Input with pull-up
GPIO.setup(KEY_RIGHT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up
GPIO.setup(KEY_PRESS_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up
GPIO.setup(KEY1_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)      # Input with pull-up
GPIO.setup(KEY2_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)      # Input with pull-up
GPIO.setup(KEY3_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)      # Input with pull-up

try:
	while True:
		with canvas(device) as draw:

			# Detecting with button is pressed.
			if not GPIO.input(KEY1_PIN): #A button is released
				mode = 1
	 
			if not GPIO.input(KEY2_PIN): #B button is released
				mode = 2
				
			if not GPIO.input(KEY3_PIN): #C button is released
				mode = 3

			if not GPIO.input(KEY_UP_PIN): #Up button is released
				mode = 8
	 
			if not GPIO.input(KEY_LEFT_PIN): #left button is released
				if selectedsensor == len(sensorid):
					selectedsensor = (selectedsensor - (len(sensorid)) + 1)
				else:
					selectedsensor = (selectedsensor + 1)
				livedata=getlivedata()
				daydata=getdaydata()
			
			if not GPIO.input(KEY_RIGHT_PIN): #right button is released
				if selectedsensor == 1:
					selectedsensor = (selectedsensor + (len(sensorid)) -1)
				else:
					selectedsensor = (selectedsensor - 1)
				livedata=getlivedata()
				daydata=getdaydata()
	 
			if not GPIO.input(KEY_DOWN_PIN): #down button is released
				livedata=getlivedata()
				daydata=getdaydata()
	 
			if not GPIO.input(KEY_PRESS_PIN): #center button is released
				mode = 1
				selectedsensor = 1
				livedata=getlivedata()
				daydata=getdaydata()


			# Write text on screen.
			if not livedata or not daydata:
				draw.text((x, top),       defaultDescription,  font=font, fill=255)
				draw.text((x, top+16),    "Fout met ophalen data!", font=font, fill=255)
			else:
				if mode == 2:
					draw.text((x, top),       str(getdesc(livedata)),  font=font, fill=255)
					draw.text((x, top+16),    "Temperatuur: " + str(gettemp(livedata)) + u"\u00b0C", font=font, fill=255)
					draw.text((x, top+24),    "Dauwpunt: " + str(getdew(livedata)) + u"\u00b0C",  font=font, fill=255)
					draw.text((x, top+32),    "Luchtvochtigheid: " + str(gethum(livedata)) + "%",  font=font, fill=255)
					draw.text((x, top+40),    "Weertype: " + str(gethumstat(livedata)),  font=font, fill=255)
				elif mode == 3:
					draw.text((x, top),       str(getdesc(livedata)),  font=font, fill=255)
					draw.text((x, top+16),    "Zonsopkomst: " + str(getsunrise(livedata)), font=font, fill=255)
					draw.text((x, top+24),    "Zonsondergang: " + str(getsunset(livedata)),  font=font, fill=255)
					draw.text((x, top+40),    "Bijgewerkt op: ",  font=font, fill=255)
					draw.text((x, top+48),    "" + str(getlastupdate(livedata)),  font=font, fill=255)
				elif mode == 8:
					draw.text((x, top),       str(getdesc(livedata)),  font=font, fill=255)
					draw.text((x, top+16),    "Status: " + str(getstatus(livedata)), font=font, fill=255)
					draw.text((x, top+24),    "Batterij: " + str(getbatt(livedata)) + "%",  font=font, fill=255)
					draw.text((x, top+40),    "Huidige datum & tijd: ",  font=font, fill=255)
					draw.text((x, top+48),    "" + str(getservertime()),  font=font, fill=255)
				else:
					draw.text((x, top),       str(getdesc(livedata)),  font=font, fill=255)
					draw.text((x, top+16),    str(gettemp(livedata)) + u"\u00b0C", font=fontbig, fill=255)

					if gettrend() == 2: # Temperature rising
						draw.text((x+110, top+16),       u"\u2191",  font=fontbig, fill=255)
					elif gettrend() == 0: # Temperature falling
						draw.text((x+110, top+16),       u"\u2193",  font=fontbig, fill=255)
					else: # Temperature is the same
						draw.text((x+110, top+16),       "=",  font=fontbig, fill=255)

except Exception as e:
	logging.exception(e)


GPIO.cleanup()
