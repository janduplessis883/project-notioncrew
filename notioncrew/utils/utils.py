from datetime import datetime, timedelta


def get_next_working_day():
    # Get the current date and time
    current_date = datetime.now()
    current_time = current_date.time()

    # Check if the current time is after 16:00
    if current_time >= datetime.strptime("16:00", "%H:%M").time():
        current_date += timedelta(days=1)  # Move to the next day

    # Check if the resulting day is a weekend
    while current_date.weekday() in (5, 6):  # 5 = Saturday, 6 = Sunday
        current_date += timedelta(days=1)

    # If it's Monday, set time to 09:00
    if current_date.weekday() == 0:  # Monday
        current_date = current_date.replace(hour=9, minute=0, second=0, microsecond=0)

    return current_date.strftime("%A, %Y-%m-%d")
