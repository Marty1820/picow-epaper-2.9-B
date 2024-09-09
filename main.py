import machine
import utime as time
import Secrets
import Network
import EventManager
import EPD_2in9_B as epd

# Global variables for display lines and their colors
lines = [""] * 28
line_color = ["black"] * 28
month_abbreviations = ["Jan", "Feb", "Mar", "Apr",
                       "May", "Jun", "Jul", "Aug",
                       "Sep", "Oct", "Nov", "Dec"]

# Function to format event data for display
def format_event_output(event_manager):
    # Format lines for the next fixed event or weekend
    if event_manager.next_fixed_event_time:
        lines[0] = 'RECURRING'
        lines[1] = f'{event_manager.format_timestamp(event_manager.next_fixed_event_time)}'
    else:
        lines[0] = 'HURRAY!'
        lines[1] = 'ITS THE WEEKEND'
    line_color[1] = "red"

    # Format lines for the next event if it exists
    if event_manager.next_event_time:
        event_time_tuple = time.localtime(event_manager.next_event_time)
        lines[3] = 'EVENTS'
        lines[4] = f'{event_manager.format_time(event_time_tuple)}'
        lines[5] = f'{event_manager.next_event_info}'
        line_color[4] = 'red'
        line_color[5] = 'red'
    else:
        lines[3] = 'NO EVENTS TODAY'
        line_color[3] = 'red'
        lines[4] = 'HAVE A'
        lines[5] = 'WONDERFUL DAY'

    # Get and format the current date and time
    get_current_datetime(local_timezone)

    return lines, line_color

# Function to update the e-paper display with the given lines and colors
def update_display(e_paper, lines, line_colors):
    e_paper.__init__() # Initialize e-paper display
    e_paper.Clear # Clear previous content

    # Map colors to e-paper image objects
    color_map = {
        "black": e_paper.imageblack,
        "red": e_paper.imagered
    }

    # Clear display
    e_paper.imageblack.fill(0xff)
    e_paper.imagered.fill(0xff)

    # Draw each line with its specified color
    for i, (line, color) in enumerate(zip(lines, line_colors)):
        image_obj = color_map.get(color, e_paper.imageblack) # Default to black
        image_obj.text(line, 5, 10 + i * 10, 0x00) # Text, x, y, color

    e_paper.display() # Update the display
    e_paper.sleep() # Put the display to sleep

# Function to formate current date and time, adjusting for the timezone offset
def get_current_datetime(timezone_offset):
    # Get the current local time
    local_time = time.localtime() # Return tuple

    # Adjust hours based on timezone offset
    adjusted_hour = (local_time[3] + timezone_offset) % 24
    day_adjustment = (local_time[3] + timezone_offset) // 24
    adjusted_day = local_time[2] + day_adjustment

    # Determine (AM/PM) period and adjust hour for 12-hour format
    hour = adjusted_hour % 12
    hour = 12 if hour == 0 else hour
    period = 'AM' if adjusted_hour < 12 else 'PM'

    # Get the month abbreviation
    month_abbr = month_abbreviations[local_time[1] -1]

    # Format date and time
    formatted_date = "{} {:02}".format(month_abbr, adjusted_day)
    formatted_time = "{:02}:{:02} {}".format(hour, local_time[4], period)

    # Print current date and time for debugging
    print("Current date:", formatted_date)
    print("Current local formatted time:", formatted_time)

    # Update lines with the formatted date and time
    lines[24] = 'TODAYS DATE'
    lines[25] = formatted_date
    line_color[25] = 'red'
    lines[26] = 'LAST REFRESH'
    lines[27] = formatted_time
    line_color[27] = 'red'

# Function to set a specific line of text and its color.
def set_line(index, text, color="black"):
    if 0 <= index < len(lines):
        lines[index] = text
        line_color[index] = color

# Function Center each line of text to a width of 15 characters.
def centered_lines(lines):
    return [s.center(15) for s in lines]

if __name__ == "__main__":
    # Configuration from Secrets.py
    country = Secrets.WiFiCOUNTRY
    ssid = Secrets.SSID
    password = Secrets.PASSWORD
    local_timezone = Secrets.TIMEZONE
    events_path = Secrets.EVENTS
    fixed_events_path = Secrets.RECURRING_EVENTS
    update_interval = Secrets.UPDATE_INTERVAL

    # Initialize network and e-paper objects
    NetworkManager = Network.NetworkManager
    NTPManager = Network.NTPManager
    network_manager = NetworkManager(country, ssid, password)
    ntp_manager = NTPManager()
    led = machine.Pin("LED", machine.Pin.OUT)
    e_paper = epd.E_paper()
    EventsSetup = EventManager.EventManager

    # Connect to network and synchronize time
    network_manager.connect()
    ntp_manager.sync()

    while True:
        led.on()
        # Initialize and format event data
        event_manager = EventsSetup(
            events_path, fixed_events_path, timezone_offset=local_timezone
        )
        formatted_lines = format_event_output(event_manager)

        # Set fixed messages
        set_line(7, "This is black")
        set_line(8, "This is red", color="red")
        set_line(9, "THIS MAX LENGTH")

        # Center and update display
        center_lines = centered_lines(lines)
        update_display(e_paper, center_lines, line_color)

        led.off()

        # Wait for next update
        print(f'Waiting {update_interval} seconds for next update')
        time.sleep(update_interval)
