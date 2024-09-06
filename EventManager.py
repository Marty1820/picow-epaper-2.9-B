import utime as time
import json

# Event Manager class for managing and finding events
class EventManager:
    month_map = {
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
        'may': 5, 'jun': 6, 'jul': 7, 'aug': 8,
        'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
    }

    def __init__(self, file_path, fixed_events_path, timezone_offset=0):
        self.file_path = file_path
        self.fixed_events_path = fixed_events_path
        self.timezone_offset = timezone_offset
        self.events = []
        self.fixed_event_times = []
        self.next_event_time = None
        self.next_event_info = None
        self.next_fixed_event_time = None

        self.load_events()
        self.load_fixed_events()
        self.find_next_event()
        self.find_next_fixed_event()

    def parse_datetime(self, date_str, time_str):
        month_str, day = date_str.split('-')
        month = self.month_map.get(month_str.lower())
        if month is None:
            raise ValueError(f"Unknown month abbreviation: {month_str}")
        day = int(day)
        hour, minute = map(int, time_str.split(':'))

        now = time.localtime()
        current_year = now[0]
        local_time = (current_year, month, day, hour, minute, 0, 0, 0, -1)

        # Convert local time to timestamp
        return time.mktime(local_time)

    def load_events(self):
        try:
            with open(self.file_path, 'r') as file:
                events_data = json.load(file)
                for event in events_data:
                    date_str = event['date']
                    time_str = event['time']
                    info = event['info']
                    event_time = self.parse_datetime(date_str, time_str)
                    self.events.append((event_time, info.strip()))
        except (OSError, ValueError) as e:
            print(f"Error loading events: {e}")

    def load_fixed_events(self):
        try:
            with open(self.fixed_events_path, 'r') as file:
                fixed_events_data = json.load(file)
                now = time.localtime()
                current_year = now[0]
                current_month = now[1]
                current_day = now[2]
                current_weekday = now[6] # Monday is 0 and Sunday is 6

            day_map = {
                'Mon': 0, 'Tue': 1, 'Wed': 2,
                'Thu': 3, 'Fri': 4, 'Sat': 5, 'Sun': 6
            }

            for day_entry in fixed_events_data:
                for day_name, times in day_entry.items():
                    if day_name not in day_map:
                        continue
                    target_day = day_map[day_name]

                    for time_of_day, time_str in times.items():
                        hour, minute = map(int, time_str.split(':'))
                        days_until_target = (target_day - current_weekday + 7) % 7
                        days_until_target = max(days_until_target, 0) # Ensure non-negative

                        event_date_local = time.mktime((
                            current_year, current_month,
                            current_day + days_until_target,
                            hour, minute, 0, 0, 0, -1
                        ))
                        self.fixed_event_times.append(event_date_local)

            self.fixed_event_times.sort()

        except (OSError, ValueError) as e:
            print(f"Error loading fixed events: {e}")

    def find_next_event(self):
        now = time.localtime()
        current_time = time.mktime((
            now[0], now[1], now[2], now[3], now[4], 0, 0, 0, -1
        )) + (self.timezone_offset * 3600)

        today_events = [
            event for event in self.events if event[0] >= current_time and
            time.localtime(event[0])[0:3] == (now[0], now[1], now[2])
        ]

        if today_events:
            self.next_event_time, self.next_event_info = min(today_events, key=lambda x: x[0])
        print(f'Next Event: {self.next_event_info}')
        print(f'Next Event Time: {self.next_event_time}')

    def find_next_fixed_event(self):
        now = time.localtime()
        current_time = time.mktime((
            now[0], now[1], now[2], now[3], now[4], 0, 0, 0, -1
        )) + (self.timezone_offset * 3600)

        today_events = [event for event in self.fixed_event_times if current_time <= event < current_time + 86400]

        self.next_fixed_event_time = min(today_events, default=None)
        print(f'Next Fixed Event Time: {self.next_fixed_event_time}')

    def format_time(self, time_tuple):
        hour = time_tuple[3]
        minute = time_tuple[4]
        period = 'AM' if hour < 12 else 'PM'
        hour = hour % 12
        hour = 12 if hour == 0 else hour
        return "{:02}:{:02} {}".format(hour, minute, period)

    def format_timestamp(self, timestamp):
        if not isinstance(timestamp, int):
            raise TypeError(f"Expected integer timestamp, got: {timestamp}")
        return self.format_time(time.localtime(timestamp))

    def print_upcoming_events(self):
        if self.next_event_time:
            event_time_tuple = time.localtime(self.next_event_time)
            print("Next event time:", self.format_time(event_time_tuple))
            print("Next event info:", self.next_event_info)

        if self.next_fixed_event_time:
            fixed_event_time_tuple = time.localtime(self.next_fixed_event_time)
            print(f"Next fixed event time: {self.format_time(fixed_event_time_tuple)}")
