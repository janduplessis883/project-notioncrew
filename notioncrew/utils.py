from datetime import datetime, timedelta

def get_next_working_day():
    # Get the current date
    current_date = datetime.now()

    # Check if today is a working day (Monday to Friday)
    if current_date.weekday() < 5:  # 0 = Monday, 4 = Friday
        return current_date.strftime("%A, %Y-%m-%d")

    # Otherwise, find the next working day
    next_day = current_date + timedelta(days=1)
    while next_day.weekday() in (5, 6):  # 5 = Saturday, 6 = Sunday
        next_day += timedelta(days=1)

    return next_day.strftime("%A, %Y-%m-%d")
