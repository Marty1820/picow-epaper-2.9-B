import network
import ntptime
import rp2
import machine
import utime as time

led = machine.Pin("LED", machine.Pin.OUT)

# Network Manager class for handling Wi-Fi connection
class NetworkManager:
    def __init__(self, country, ssid, password, led_pin="LED"):
        self.country = country
        self.ssid = ssid
        self.password = password
        self.led = machine.Pin(led_pin, machine.Pin.OUT)

    def connect(self):
        rp2.country(self.country)
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wlan.connect(self.ssid, self.password)

        self.led.on()
        max_wait = 20
        while max_wait > 0:
            if wlan.status() < 0 or wlan.status() >= 3:
                break
            max_wait -= 1
            print('waiting for connection...')
            time.sleep(2)
        self.led.off()

        if wlan.status() != 3:
            raise RuntimeError('network connection failed')
        else:
            print('connected with ip = ' + wlan.ifconfig()[0])

# NTP Manager class to sync time
class NTPManager:
    def sync(self):
        try:
            ntptime.settime()
            print('Time Synced | UTC Time : %s' % str(time.localtime()))
        except Exception as e:
            print('Failed to sync time:', e)
