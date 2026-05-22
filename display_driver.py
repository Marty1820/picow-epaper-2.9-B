# Handles e-paper display initialization, buffer management, and rendering logic

from machine import Pin, SPI
import framebuf
import utime
import time
from config import (
    THRESHOLDS,
    TOTAL_AQI_THRESHOLD,
)

# Display resolution constants
EPD_WIDTH = 128
EPD_HEIGHT = 296

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
        utime.sleep(delaytime / 1000.0)

    def _spi_writebyte(self, data):
        self.spi.write(bytearray(data))

    def _module_exit(self):
        self._digital_write(self.reset_pin, 0)

    def reset(self):
        """Hardware reset sequence."""
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
        print("busy")
        self._send_command(0x71)
        while self._digital_read(self.busy_pin) == 0:
            self._send_command(0x71)
            self._delay_ms(10)
        print("busy release")

    def _turn_on_display(self):
        self._send_command(0x12)
        self._read_busy()

    def init(self):
        """Initialize the display panel."""
        print("init")
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
        """Clear the display with specified colors (0xFF=White, 0x00=Black/Red)."""
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
        self._delay_ms(2000)
        self._module_exit()

    # --- High Level Drawing Helpers ---

    def draw_metric_line(self, label, value, threshold, x, y):
        """
        Draws a single metric line.
        If value >= threshold, draws in Red. Otherwise Black.
        Clears the area on both buffers first to prevent ghosting.
        """
        is_high = value is not None and value >= threshold

        # Format text
        if value is None:
            text = label + "N/A"
            is_high = False
        else:
            text = (
                f"{label}{value:.1f}"
                if isinstance(value, float)
                else f"{label}{int(value)}"
            )

        # Calculate width to clear (approx 6px per char + padding)
        text_width = len(text) * 6 + 10
        # Ensure we don't go off screen
        if x + text_width > self.width:
            text_width = self.width - x

        # Clear area on BOTH buffers
        self.imageblack.fill_rect(x, y, text_width, 12, 0xFF)
        self.imagered.fill_rect(x, y, text_width, 12, 0xFF)

        # Draw text on correct buffer
        if is_high:
            self.imagered.text(text, x, y, 0x00)
        else:
            self.imageblack.text(text, x, y, 0x00)

    def render_full_screen(self, weather_data, aqi_data, offset_hours):
        """
        Renders the entire weather and AQI screen.
        Takes raw JSON data and draws it to the buffers.
        """
        # Clear buffers
        self.imageblack.fill(0xFF)
        self.imagered.fill(0xFF)

        # --- Header ---
        self.imageblack.text("WEATHER STATION", 5, 10, 0x00)

        # --- Weather Section ---
        try:
            temp = weather_data["current"]["temp"]
            desc = weather_data["current"]["weather"][0]["description"]
            feels_like = weather_data["current"]["feels_like"]
            humidity = weather_data["current"]["humidity"]
            wind_speed = weather_data["current"]["wind_speed"]

            self.imageblack.text(desc[:18], 5, 25, 0x00)
            self.imageblack.text(f"TEMP  : {int(temp)}F", 5, 40, 0x00)
            self.imageblack.text(f"FEELS : {int(feels_like)}F", 5, 55, 0x00)
            self.imageblack.text(f"HUMID : {humidity}%", 5, 70, 0x00)
            self.imageblack.text(f"WIND  : {round(wind_speed)}m/s", 5, 85, 0x00)
        except KeyError as e:
            self.imageblack.text(f"Weather Error: {e}", 5, 25, 0x00)

        # --- AQI Section ---
        self.imageblack.text("AIR QUALITY", 5, 115, 0x00)

        try:
            aqi_data_inner = aqi_data.get("data")
            if not isinstance(aqi_data_inner, dict):
                raise TypeError("AQI 'data' field is not a dictionary")

            total_aqi = aqi_data_inner.get("aqi", 0)
            self.draw_metric_line("AQI    : ", total_aqi, TOTAL_AQI_THRESHOLD, 10, 130)

            iaqi = aqi_data_inner.get("iaqi", {})
            if not isinstance(iaqi, dict):
                iaqi = {}

            y_offset = 145

            for key, cfg in THRESHOLDS.items():
                val_data = iaqi.get(key)
                value = None
                if val_data:
                    value = (
                        val_data.get("v") if isinstance(val_data, dict) else val_data
                    )

                self.draw_metric_line(
                    cfg["label"], value, cfg["threshold"], 10, y_offset
                )
                y_offset += 15

        except KeyError as e:
            self.imageblack.text(f"AQI Error: {e}", 5, 115, 0x00)

        # --- Timestamp ---
        try:
            t = time.localtime()
            utc_seconds = time.mktime(t)
            local_seconds = utc_seconds + (offset_hours * 3600)
            local_t = time.localtime(local_seconds)

            daystamp = f"{local_t[0]}-{local_t[1]:02d}-{local_t[2]:02d}"
            timestamp = f"{local_t[3]:02d}:{local_t[4]:02d}"

            self.imageblack.text("Last Update:", 10, 240, 0x00)
            self.imageblack.text(daystamp, 10, 255, 0x00)
            self.imageblack.text(timestamp, 10, 270, 0x00)
        except Exception:
            self.imageblack.text("Time Error", 10, 240, 0x00)

        # Refresh
        self.display()
        print("[Display] Render complete.")
