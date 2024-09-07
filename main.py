import machine
import utime as time
import Secrets
import Network
import EventManager
import EPD_2in9_B as epd

# Initialize lines and line color globally
lines = [""] * 28
line_color = ["black"] * 28
month_abbreviations = ["Jan", "Feb", "Mar", "Apr",
                       "May", "Jun", "Jul", "Aug",
                       "Sep", "Oct", "Nov", "Dec"]

# Function to format event output
def format_event_output(event_manager):
    if event_manager.next_fixed_event_time:
        lines[0] = 'RECURRING'
        lines[1] = f'{event_manager.format_timestamp(event_manager.next_fixed_event_time)}'
    else:
        lines[0] = 'HURRAY!'
        lines[1] = 'ITS THE WEEKEND'
    line_color[1] = "red"

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

    get_current_datetime(local_timezone)

    return lines, line_color

# Function to display on the e-ink screen
def update_display(e_paper, lines, line_colors):
    e_paper.__init__()
    e_paper.Clear
    color_map = {
        "black": e_paper.imageblack,
        "red": e_paper.imagered
    }

    # Clear display
    e_paper.imageblack.fill(0xff)
    e_paper.imagered.fill(0xff)

    for i, (line, color) in enumerate(zip(lines, line_colors)):
        image_obj = color_map.get(color, e_paper.imageblack) # Default to black
        image_obj.text(line, 5, 10 + i * 10, 0x00) # Text, x, y, color

    e_paper.display() # Update the display
    e_paper.sleep() # Put the display to sleep

# Function to get the current datetime formatted
def get_current_datetime(timezone_offset):
    current_time = time.localtime()
    adjusted_hour = (current_time[3] + timezone_offset) % 24
    hour = adjusted_hour % 12
    hour = 12 if hour == 0 else hour
    period = 'AM' if adjusted_hour < 12 else 'PM'

    # Get the month abbreviation
    month_abbr = month_abbreviations[current_time[1] -1]

    # Format date with month abbreviation
    formatted_date = "{} {:02}".format(month_abbr, current_time[2])
    formatted_time = "{:02}:{:02} {}".format(hour, current_time[4], period)

    print("Current date:", formatted_date)
    print("Current local formatted time:", formatted_time)
    #return formatted_time, formatted_date

    lines[24] = 'TODAYS DATE'
    lines[25] = formatted_date
    line_color[25] = 'red'
    lines[26] = 'LAST REFRESH'
    lines[27] = formatted_time
    line_color[27] = 'red'

# Function to set a specific line
def set_line(index, text, color="black"):
    if 0 <= index < len(lines):
        lines[index] = text
        line_color[index] = color

def centered_lines(lines):
    centered_strings = []
    for s in lines:
        # Center each string to a width of 15 characters
        centered = s.center(15)
        centered_strings.append(centered)
    return centered_strings

if __name__ == "__main__":
    # Configuration
    country = Secrets.WiFiCOUNTRY
    ssid = Secrets.SSID
    password = Secrets.PASSWORD
    local_timezone = Secrets.TIMEZONE
    events_path = Secrets.EVENTS
    fixed_events_path = Secrets.RECURRING_EVENTS
    update_interval = Secrets.UPDATE_INTERVAL

    # Initialize objects
    NetworkManager = Network.NetworkManager
    NTPManager = Network.NTPManager
    network_manager = NetworkManager(country, ssid, password)
    ntp_manager = NTPManager()
    led = machine.Pin("LED", machine.Pin.OUT)
    e_paper = epd.E_paper()
    EventsSetup = EventManager.EventManager

    # Connect to network and set local time
    network_manager.connect()
    ntp_manager.sync()

    while True:
        led.on()
        # Recalculate events and display data
        event_manager = EventsSetup(
            events_path, fixed_events_path, timezone_offset=local_timezone
        )
        formatted_lines = format_event_output(event_manager)

        # Lines 6-23 can be used
        # Max length of 15 characters or it runs off display
        # ex `set_line(LINE_NUMBER, "TEXT", color="COLOR")`
        set_line(7, "This is black")
        set_line(8, "This is red", color="red")
        set_line(9, "THIS MAX LENGTH")

        # Center text at 15 characters
        center_lines = centered_lines(lines)
        # Send data to display for update
        update_display(e_paper, center_lines, line_color)

        led.off()

        # Setup sleep interval
        print(f'Waiting {update_interval} seconds for next update')
        time.sleep(update_interval)
