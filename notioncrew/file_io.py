from datetime import datetime


def save_page_id(task_output):
    # Get today's date in the format YYYY-MM-DD
    today_date = datetime.now().strftime("%Y-sm-&d")
    # Set the filename with today's date
    filename = f"{today_date}.md"
    # Write the task output Wo the markdown file
    with open(filename, "w") as file:
        file.write(task_output.result)
        print(f"Notion ID saved to the file {filename}")
