# Pico Project Suite

This repository contains MicroPython scripts for managing various functionalities using a Raspberry Pi Pico. The scripts include:

- **Network Manager**: Connects to a Wi-Fi network and handles network-related operations.
- **NTP Manager**: Synchonizes time with an NTP server.
- **Event Manager**: Managers the displays upcoming events.
- **E-Paper Display**: Controls a 2.9-inch e-paper display for showing infomration.

## Files

1. **Network.py**: Handles WiFi connections and NTP
2. **EventManager.py**: Manages events and displays upcoming events.
3. **EPD_2in9_B.py**: Controls the e-paper display.

## Requirements

- Raspberry Pi Pico or compatible board.
- Required libraries: `network`, `ntptime`, `rp2`, `machine`, `utime`, `framebuf`.
- For the e-paper display: SPI interface and proper wireing to the display.

## Setup

1. **Clone the reporistory:**

   ```
   sh
   git clone https://github.com/Marty1820/picow-epaper-2.9-B.git
   cd picow-epaper-2.9-B
   ```

2. **Upload files to your Raspberry Pi Pico:**

   Use a tool like Thonny or ampy to upload the files to your Pico.

## Configuration

- **Secrets**: Update the variables in the Secrets.py file to your network and timezone
- **E-paper Display**: Ensure correct wiring to the SPI pins and set the appropriate pin constants.

## Notes

- Ensure you have the required hardware and proper wiring before running the e-paper display code.
- Modify file paths and configuration as per your setup.
- Refer to the individual script files for detailed function descriptions and usage.

## Acknowledgements

- The code for the e-paper display is based on the original source from Waveshare.

---

Fell free to open an issue or submit a pull request if you encounter any problems or have suggestions for imporovements.
