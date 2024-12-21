import dataclasses
import mistune
import notion_client

import notionfier.plugins.footnotes


def append_markdown_to_notion_page(token: str, page_id: str, markdown_content: str):
    """
    Appends Markdown content as blocks to an existing Notion page.

    Args:
        token (str): The Notion auth token.
        page_id (str): The ID of the Notion page where blocks will be appended.
        markdown_content (str): The Markdown content to be processed.

    """
    # Create a Mistune Markdown renderer with plugins
    md = mistune.create_markdown(
        renderer=notionfier.MyRenderer(),
        plugins=[
            mistune.plugins.plugin_task_lists,
            mistune.plugins.plugin_table,
            mistune.plugins.plugin_url,
            mistune.plugins.plugin_def_list,
            mistune.plugins.plugin_strikethrough,
            notionfier.plugins.plugin_footnotes,
        ],
    )
    # Render Markdown content to Notion blocks
    result = md(markdown_content)

    # Convert blocks to the format expected by the Notion API
    children = [
        dataclasses.asdict(
            x, dict_factory=lambda x: {k: v for (k, v) in x if v is not None}
        )
        for x in result
    ]

    # Initialize Notion client
    client = notion_client.Client(auth=token)

    # Append blocks to the specified Notion page
    client.blocks.children.append(block_id=page_id, children=children)


# Example usage
if __name__ == "__main__":
    # Replace these with your own values
    NOTION_TOKEN = "secret_AUqFdk1kzS6qe7iw0LVlPDQXJ1TrDxnM7n9ZIB5fOlB"
    PAGE_ID = "161fdfd68a9780a5a564c87358ffea07"

    # Markdown content received from an LLM or other source
    markdown_content = """### Notion Task Scheduler with CrewAI
![Notion-Agent](https://github.com/janduplessis883/notion-agent/blob/master/images/timeblocking.png?raw=true)



This project leverages **CrewAI** to create a custom, intelligent tool for interacting with a **Notion** Database to manage and optimize task scheduling. Designed for seamless integration with Notion’s API, this solution automates key scheduling operations such as fetching task data, rescheduling tasks based on priority, and ensuring tasks are effectively organized using time-blocking techniques.

## Overview

The project includes a suite of CrewAI agents working collaboratively to achieve the following goals:
1.	**Data Collection**: Retrieve the Notion Database schema and fetch all tasks, identifying each task with its corresponding page_id.
2.	**Task Scheduling**: Analyze task priorities and reschedule incomplete tasks efficiently using time-blocking. Tasks are scheduled sequentially within working hours to avoid overlap.
3.	**Task Updates**: Update existing tasks or create new ones based on user-defined requirements. Tasks are always assigned a Due Date (defaulted to today) and a Status of “Not Started.”

The agents are designed to follow clear logic, ensuring no duplication of tasks and preventing changes to critical events such as meetings.

## Key Features
- **CrewAI Integration**: Agents collaborate effectively to divide and conquer tasks like data fetching, analysis, and updates.
- **Notion API Compatibility**: Seamless interaction with the Notion Database using Notion’s REST API for querying, creating, and updating tasks.
- **Time-Blocking Optimization**: Tasks are scheduled using the time-blocking method, prioritizing high-priority tasks while adhering to defined working hours (e.g., 9:00 AM - 4:00 PM).
- **Dynamic Filters**: Tasks are filtered dynamically to exclude completed tasks (Status != Done) and ensure dates fall within a valid range (e.g., yesterday to the next 7 days).

### Technologies Used
- CrewAI: For orchestrating agents to perform specific roles.
- Python: Core programming language for developing custom tools.
- Notion API: To interact with the Notion database for task management.
- Datetime Module: For calculating dynamic date ranges (e.g., today, yesterday, next week).
- Requests Library: For making HTTP requests to the Notion API.

### How It Works
1. Data Collection Agent:
 - Fetches the database schema and all tasks with their unique page_id.
 - Outputs data in a user-friendly format (e.g., Markdown table).
2. Data Update Agent:
 - Updates existing tasks with new start and end times.
 - Creates new tasks as per user input, ensuring correct priority and Due Date settings.
3. Calendar Scheduler Agent:
 - Reschedules tasks based on priority and availability.
 - Prevents overlapping tasks and ensures all updates occur within working hours.

### Use Cases
- Automate task rescheduling and updates in a Notion project management database.
- Optimize workflows using intelligent time-blocking strategies.
- Integrate with CrewAI to expand scheduling capabilities across multiple Notion databases.

This project is a robust foundation for automating task management workflows using AI-powered agents and Notion’s versatile API. 🚀

---

This report is designed to be a comprehensive, polished, and actionable document, providing essential insights and recommendations for stakeholders involved in clinical research within the NHS framework.
"""

    append_markdown_to_notion_page(NOTION_TOKEN, PAGE_ID, markdown_content)
