import network
import ntptime
import rp2
import machine
import utime as time

# Initialize the LED pin for status indication
led = machine.Pin("LED", machine.Pin.OUT)

# Network Manager class for handling Wi-Fi network connections
class NetworkManager:
    # Initialize the Network Manager with Wi-Fi credentials and LED pin
    def __init__(self, country, ssid, password, led_pin="LED"):
        self.country = country
        self.ssid = ssid
        self.password = password
        self.led = machine.Pin(led_pin, machine.Pin.OUT)

    # Connect to Wi-Fi network and manage connection status
    def connect(self):
        rp2.country(self.country) # Set the country for Wi-Fi configuration
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True) # Activate the WLAN interface
        wlan.connect(self.ssid, self.password) # Connect to specified network

        self.led.on() # Turn on LED to indicate connection attempt
        max_wait = 20 # Timeout for connection attempt
        while max_wait > 0:
            # Check connection status
            if wlan.status() < 0 or wlan.status() >= 3:
                break
            max_wait -= 1
            print('waiting for connection...')
            time.sleep(2) # Wait before retrying

        self.led.off() # Turn off LED after connection attempt

        # Check if the connection was successful
        if wlan.status() != 3:
            raise RuntimeError('network connection failed')
        else:
            print('connected with ip = ' + wlan.ifconfig()[0])

# Class to handle NTP (Network Time Protocol) synchronization
class NTPManager:
    # Synchronize the device's time with an NTP server
    def sync(self):
        try:
            ntptime.settime() # Sync time with NTP server
            # Print the local time after synchronization
            print('Time Synced | UTC Time : %s' % str(time.localtime()))
        except Exception as e:
            # Print error message if synchronization fails
            print('Failed to sync time:', e)
