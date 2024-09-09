# Original source
# https://github.com/waveshareteam/Pico_ePaper_Code/blob/main/python/Pico_ePaper-2.9-B.py
from machine import Pin, SPI
import framebuf
import utime

# Display resolution constants
EPD_WIDTH       = 128
EPD_HEIGHT      = 296

# Pin configuration constants
RST_PIN         = 12
DC_PIN          = 8
CS_PIN          = 9
BUSY_PIN        = 13

# Class to interface with the 2.9-inch e-paper display using SPI communication
class E_paper:
    # Initialize the e-paper display interface.
    def __init__(self):
        # Initialize pins
        self.reset_pin = Pin(RST_PIN, Pin.OUT)
        self.busy_pin = Pin(BUSY_PIN, Pin.IN, Pin.PULL_UP)
        self.cs_pin = Pin(CS_PIN, Pin.OUT)
        self.dc_pin = Pin(DC_PIN, Pin.OUT)

        # Display dimensions
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT

        # Initialize SPI communication
        self.spi = SPI(1)
        self.spi.init(baudrate=4000_000) # Set SPI baudrate to 4MHz

        # Framebuffers for storing image data
        self.buffer_black = bytearray(self.height * self.width // 8)
        self.buffer_red = bytearray(self.height * self.width // 8)
        self.imageblack = framebuf.FrameBuffer(self.buffer_black, self.width, self.height, framebuf.MONO_HLSB)
        self.imagered = framebuf.FrameBuffer(self.buffer_red, self.width, self.height, framebuf.MONO_HLSB)

        # Initialize the display
        self.init()

    # Set the digital value of a pin
    def digital_write(self, pin, value):
        pin.value(value)

    # Read a digital value of a pin
    def digital_read(self, pin):
        return pin.value()

    # Delay for a specified number of milliseconds
    def delay_ms(self, delaytime):
        utime.sleep(delaytime / 1000.0)

    # Write a byte of data to the SPI bus.
    def spi_writebyte(self, data):
        self.spi.write(bytearray(data))

    # Perform actions required to safetly exit and power down the module
    def module_exit(self):
        self.digital_write(self.reset_pin, 0)

    # Perform a hardware reset of the display
    def reset(self):
        self.digital_write(self.reset_pin, 1)
        self.delay_ms(50)
        self.digital_write(self.reset_pin, 0)
        self.delay_ms(2)
        self.digital_write(self.reset_pin, 1)
        self.delay_ms(50)

    # Send a command to the display
    def send_command(self, command):
        self.digital_write(self.dc_pin, 0) # Set DC pin low for command
        self.digital_write(self.cs_pin, 0) # Select the display
        self.spi_writebyte([command])
        self.digital_write(self.cs_pin, 1) # Deselct the display

    # Send data to the display
    def send_data(self, data):
        self.digital_write(self.dc_pin, 1) # Set DC pin high for data
        self.digital_write(self.cs_pin, 0) # Select the display
        self.spi_writebyte([data])
        self.digital_write(self.cs_pin, 1) # Deselect the display

    # Send a buffer of data to the display
    def send_data1(self, buf):
        self.digital_write(self.dc_pin, 1) # Set DC pin high for data
        self.digital_write(self.cs_pin, 0) # Select the display
        self.spi.write(bytearray(buf))
        self.digital_write(self.cs_pin, 1) # Deselect the display

    # Wait until the display is not busy
    def ReadBusy(self):
        print('busy')
        self.send_command(0x71) # Command to check busy status
        while(self.digital_read(self.busy_pin) == 0):
            self.send_command(0x71) # Check again if still busy
            self.delay_ms(10)
        print('busy release')

    # Send the command to turn on the display
    def TurnOnDisplay(self):
        self.send_command(0x12) # Command to update display
        self.ReadBusy() # Wait until the update is complete

    # Initialize the display settings and configuration
    def init(self):
        print('init')
        self.reset() # Performa a hardware reset
        self.send_command(0x04) # Command to start initialization
        self.ReadBusy() # Wat for initialization to complete

        # Panel Settings
        self.send_command(0x00)
        self.send_data(0x0f) # Set LUT from OTP, 128x296
        self.send_data(0x89) # Set temperature sensor, boost, and timing

        # Resolution setting
        self.send_command(0x61)
        self.send_data (0x80) # Width
        self.send_data (0x01) # Height
        self.send_data (0x28) # Resolution settings

        # VCOM and Data interval setting
        self.send_command(0X50)
        self.send_data(0x77) # Set VCOM and Data interval

        return 0

    # Update the display with the current image buffers
    def display(self):
        self.send_command(0x10) # Command to send black image data
        self.send_data1(self.buffer_black)

        self.send_command(0x13) # Command to send red image data
        self.send_data1(self.buffer_red)

        self.TurnOnDisplay() # Refresh the display to show the updated image

    # Clear the display with specified colors
    def Clear(self, colorblack, colorred):
        self.send_command(0x10) # Command the clear the black buffer
        self.send_data1([colorblack] * self.height * int(self.width / 8))

        self.send_command(0x13) # Command to clear the red buffer
        self.send_data1([colorred] * self.height * int(self.width / 8))

        self.TurnOnDisplay() # Refresh the display to show the cleared screen

    # Put the display into a deep sleep mode to save power
    def sleep(self):
        self.send_command(0X02) # Command to power off
        self.ReadBusy() # Wait for power-off to complete
        self.send_command(0X07) # Command to enter deep sleep
        self.send_data(0xA5) # Deep sleep command byte

        self.delay_ms(2000) # Wait for 2 seconds
        self.module_exit() # Perform any necessary cleanup
