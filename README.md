# raspi-domoticz-weatherdisplay
Raspberry Pi WeatherDisplay for Domoticz

Simple script to WeatherSensor data from Domoticz on a cheap Raspberry Pi Display. </br>

<p>
	Hardware requirements: </br>
	Raspberry Pi Zero W </br>
	<a href="https://nl.aliexpress.com/item/Frambozenpastei-1-3-inch-OLED-uitbreidingskaart-SH1106-module-SPI-I2C-Mini-Display/32849447496.html?spm=a2g0s.9042311.0.0.jQL6cq">Display</a>
</p>

<p>
	To setup follow documentation and run demo code.</br>
	<a href="https://www.waveshare.com/w/upload/4/46/1.3inch_OLED_HAT_User_Manual_EN.pdf">User Manual and Setup</a> </br>
	<a href="https://www.waveshare.com/wiki/1.3inch_OLED_HAT">Demo Code</a>
</p>

<p>
	Download weatherdisplay.py and execute: </br>
	sudo python /home/pi/Python/weatherdisplay.py </br>
</p>

<p>
	To start at startup: </br>
	Open: sudo nano /etc/rc.local </br>
	Add the line before the last line following text: </br>
	sudo python /home/pi/Python/weatherdisplay.py & </br>
</p>