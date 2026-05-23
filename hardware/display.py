# Generic Waveshare 2.9" B/W e-paper display driver for MicroPython

from machine import Pin, SPI
import framebuf
import utime

# Display resolution constants
EPD_WIDTH = 128
EPD_HEIGHT = 296

# Hardware pin definitions (adjust for your hardware)
RST_PIN = 12
DC_PIN = 8
CS_PIN = 9
BUSY_PIN = 13


class EPD_2in9_B:
    """
    Waveshare 2.9 inch B/W e-paper driver.
    Manages SPI communication, buffers, and display commands.
    """

    def __init__(self):
        """Initialize the display"""
        # Initialize Pins
        self.reset_pin = Pin(RST_PIN, Pin.OUT)
        self.busy_pin = Pin(BUSY_PIN, Pin.IN, Pin.PULL_UP)
        self.cs_pin = Pin(CS_PIN, Pin.OUT)
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT

        # Initialize SPI
        self.spi = SPI(1)
        self.spi.init(baudrate=4_000_000)
        self.dc_pin = Pin(DC_PIN, Pin.OUT)

        # Initialize Buffers (Black and Red)
        # MONO_HLSB: Monochrome, LSB First
        self.buffer_black = bytearray(self.height * self.width // 8)
        self.buffer_red = bytearray(self.height * self.width // 8)
        self.imageblack = framebuf.FrameBuffer(
            self.buffer_black, self.width, self.height, framebuf.MONO_HLSB
        )
        self.imagered = framebuf.FrameBuffer(
            self.buffer_red, self.width, self.height, framebuf.MONO_HLSB
        )
        self.init()

    def _digital_write(self, pin, value):
        pin.value(value)

    def _digital_read(self, pin):
        return pin.value()

    def _delay_ms(self, delaytime):
        utime.sleep(delaytime / 1_000.0)

    def _spi_writebyte(self, data):
        self.spi.write(bytearray(data))

    def _module_exit(self):
        self._digital_write(self.reset_pin, 0)

    # Hardware reset
    def reset(self):
        self._digital_write(self.reset_pin, 1)
        self._delay_ms(50)
        self._digital_write(self.reset_pin, 0)
        self._delay_ms(2)
        self._digital_write(self.reset_pin, 1)
        self._delay_ms(50)

    def _send_command(self, command):
        self._digital_write(self.dc_pin, 0)
        self._digital_write(self.cs_pin, 0)
        self._spi_writebyte([command])
        self._digital_write(self.cs_pin, 1)

    def _send_data(self, data):
        self._digital_write(self.dc_pin, 1)
        self._digital_write(self.cs_pin, 0)
        self._spi_writebyte([data])
        self._digital_write(self.cs_pin, 1)

    def _send_data_block(self, buf):
        self._digital_write(self.dc_pin, 1)
        self._digital_write(self.cs_pin, 0)
        self.spi.write(bytearray(buf))
        self._digital_write(self.cs_pin, 1)

    def _read_busy(self):
        """Wait until the display is not busy."""
        print("[DISPLAY] busy")
        self._send_command(0x71)
        while self._digital_read(self.busy_pin) == 0:
            self._send_command(0x71)
            self._delay_ms(10)
        print("[DISPLAY] busy release")

    def _turn_on_display(self):
        self._send_command(0x12)
        self._read_busy()

    def init(self):
        """Initialize the display panel."""
        print("[DISPLAY] Init")
        self.reset()
        self._send_command(0x04)  # Power on
        self._read_busy()  # wait for epaper IC to release idle signal

        self._send_command(0x00)  # Panel setting
        self._send_data(0x0F)  # LUT from OTP, 128x296
        self._send_data(0x89)  # Temp sensor, boost, timing

        self._send_command(0x61)  # Resolution setting
        self._send_data(0x80)  # Width (128)
        self._send_data(0x01)  # Height High byte (296 >> 8)
        self._send_data(0x28)  # Height Low byte (296 & 0xFF)

        self._send_command(0x50)  # VCOM and Data Interval
        self._send_data(0x77)  # WB mode settings

        return 0

    def display(self):
        """Send buffers to display and refresh."""
        self._send_command(0x10)
        self._send_data_block(self.buffer_black)

        self._send_command(0x13)
        self._send_data_block(self.buffer_red)

        self._turn_on_display()

    def clear(self, color_black=0xFF, color_red=0xFF):
        """
        Clear the display with specified colors

        Args:
            color_black: Color for black buffer (0xFF=White, 0x00=Black)
            color_red: Color for red buffer (0xFF=White, 0x00=Red)
        """
        self._send_command(0x10)
        self._send_data_block([color_black] * self.height * int(self.width / 8))

        self._send_command(0x13)
        self._send_data_block([color_red] * self.height * int(self.width / 8))

        self._turn_on_display()

    def sleep(self):
        """Put display into deep sleep."""
        self._send_command(0x02)  # Power off
        self._read_busy()
        self._send_command(0x07)  # Deep sleep
        self._send_data(0xA5)

        self._delay_ms(2_000)
        self._module_exit()
        print("[DISPLAY] Sleeping")

    # --- Generic Drawing Primitives ---

    def clear_area(self, x, y, width, height):
        """Clear a rectangular area on both buffers."""
        self.imageblack.fill_rect(x, y, width, height, 0xFF)
        self.imagered.fill_rect(x, y, width, height, 0xFF)

    def draw_text_black(self, text, x, y):
        """Draw text in black on the black buffer."""
        self.imageblack.text(text, x, y, 0x00)

    def draw_text_red(self, text, x, y):
        """Draw text in red on the red buffer."""
        self.imagered.text(text, x, y, 0x00)

    def draw_text_conditional(self, text, x, y, is_high=False):
        """
        Draw text conditionally in black or red based on flag.

        Args:
            text: String to draw
            x: X coordinate
            y: Y coordinate
            is_high: If True, draw in red; otherwise black
        """
        if is_high:
            self.draw_text_red(text, x, y)
        else:
            self.draw_text_black(text, x, y)

    def draw_line(self, x1, y1, x2, y2, color="black"):
        """
        Draw a line between two points.

        Args:
            x1, y1: Start coordinates
            x2, y2: End coordinates
            color: 'black' or 'red'
        """
        buffer = self.imageblack if color == "black" else self.imagered
        buffer.line(x1, y1, x2, y2, 0x00)

    def draw_rect(self, x, y, w, h, color="black", filled=False):
        """
        Draw a rectangle.

        Args:
            x, y: Top-left coordinates
            w, h: Width and height
            color: 'black' or 'red'
            filled: If True, fill the rectangle
        """
        buffer = self.imageblack if color == "black" else self.imagered
        if filled:
            buffer.fill_rect(x, y, w, h, 0x00)
        else:
            buffer.rect(x, y, w, h, 0x00)

    def render(self):
        """Refresh the display with current buffer contents."""
        self.display()
