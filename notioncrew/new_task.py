# Warning control
import warnings
warnings.filterwarnings('ignore')

import os
import json
import re
import yaml
import requests
from datetime import datetime, timedelta
from typing import ClassVar, Union, Dict, Any, List

import streamlit as st
import pandas as pd

from crewai import Agent, Task, Crew, LLM
from crewai.process import Process
from crewai_tools import BaseTool, SerperDevTool, WebsiteSearchTool, ScrapeWebsiteTool

from notionfier_main import append_markdown_to_notion_page

today = datetime.now()

search_tool = SerperDevTool()
web_rag_tool = WebsiteSearchTool()
scrape_web_tool = ScrapeWebsiteTool()

# Load environment variables from streamlit secrets
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
OPENAI_MODEL_NAME = st.secrets["OPENAI_MODEL_NAME"]
NOTION_ENDPOINT = st.secrets["NOTION_ENDPOINT"]
NOTION_VERSION = st.secrets["NOTION_VERSION"]
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
NOTION_DATABASE_ID = st.secrets["NOTION_DATABASE_ID"]
SERPER_API_KEY = st.secrets["SERPER_API_KEY"]

# Define file paths for YAML configurations
files = {
    'agents': 'notioncrew/config/agents.yaml',
    'tasks': 'notioncrew/config/tasks.yaml'
}

print(f"🅾️- {today}")


# Load configurations from YAML files
configs = {}
for config_type, file_path in files.items():
    with open(file_path, 'r') as file:
        configs[config_type] = yaml.safe_load(file)

# Assign loaded configurations to specific variables
agents_config = configs['agents']
tasks_config = configs['tasks']




# Validate if the variables are loaded correctly
if not NOTION_TOKEN or not OPENAI_API_KEY or not NOTION_ENDPOINT or not NOTION_DATABASE_ID:
    raise ValueError("One or more required environment variables are missing.")

class DatabaseDataFetcherTool(BaseTool):
    """
    Tool to fetch the structure and properties of a Notion Database.
    """
    name: str = "Notion Database Data Fetcher"
    description: str = "Fetches Notion Database structure and properties."

    headers: ClassVar[Dict[str, str]] = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }

    database_id: str = "136fdfd68a9780a3ae4be27f473bad08"

    def _run(self) -> Union[dict, str]:
        """
        Fetch all the properties and structure of a Notion database.

        Returns:
            Union[dict, str]: The database structure or an error message.
        """
        url = f"{NOTION_ENDPOINT}/databases/{self.database_id}"

        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            else:
                return f"Error {response.status_code}: {response.text}"
        except Exception as e:
            return f"An error occurred: {str(e)}"



class PageDataFetcherTool(BaseTool):
    """
    Tool to fetch all pages in a Notion database with their IDs and full schemas.
    """
    name: str = "Fetch Notion Pages Tool"
    description: str = (
        "Fetches all pages in a specified Notion database, "
        "returning their unique page IDs and full page schemas."
    )

    headers: ClassVar[Dict[str, str]] = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION
    }

    def _run(self, database_id: str) -> List[Dict[str, Any]]:
        """
        Fetches all pages in the specified Notion database.

        Args:
            database_id (str): The Notion database ID.

        Returns:
            List[Dict]: A list of dictionaries containing page IDs and full schemas.
        """
        from datetime import datetime, timedelta

        # Dynamic date calculation
        today = datetime.now()
        yesterday = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        next_week = (today + timedelta(days=7)).strftime("%Y-%m-%d")

        # Properly formatted filter with Status != Done
        filter_payload = {
            "filter": {
                "and": [
                    {
                        "property": "Due Date",
                        "date": {
                            "on_or_after": yesterday
                        }
                    },
                    {
                        "property": "Due Date",
                        "date": {
                            "before": next_week
                        }
                    },
                    {
                        "property": "Status",
                        "status": {
                            "does_not_equal": "Done"
                        }
                    }
                ]
            }
        }

        url = f"{NOTION_ENDPOINT}/databases/{database_id}/query"
        all_pages = []
        has_more = True
        next_cursor = None

        # Handle pagination to get all pages
        while has_more:
            payload = {"start_cursor": next_cursor} if next_cursor else {}
            payload.update(filter_payload)  # Add the filter to the payload
            response = requests.post(url, headers=self.headers, json=payload)

            if response.status_code == 200:
                data = response.json()
                for page in data.get("results", []):
                    all_pages.append({
                        "page_id": page.get("id"),
                        "full_schema": page
                    })

                has_more = data.get("has_more", False)
                next_cursor = data.get("next_cursor", None)
            else:
                return [{"error": response.text, "status_code": response.status_code}]

        return all_pages


class NewTaskCreationTool(BaseTool):
    name: str = "Create New Task Tool"
    description: str = "Creates a new task in the calendar database with user-specified properties like Priority, Title, and Due Dates."

    database_id: str = "136fdfd68a9780a3ae4be27f473bad08"
    headers: ClassVar[Dict[str, str]] = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"  # Use the correct Notion API version
    }

    def _run(self, name: str, status: str, priority: str, start_datetime: str, end_datetime: str, duration_in_minutes: int) -> Dict[str, Any]:
        """
        Create a new task in the Notion database with specified properties.

        Args:
            title (str): The name of the task.
            status (str): The status of the task (e.g., "Not started", "In progress", "Done", default="Not started").
            priority (str): Priority of the task ("High", "Medium", "Low").
            start_datetime (str): Start date and time in ISO 8601 format.
            end_datetime (str): End date and time in ISO 8601 format.
            duration_in_minutes (int): How many minutes the task will take to complete, if not in the imput prompt default=30

        Returns:
            dict: The response from the Notion API.
        """
        task_data = {
            "parent": {"database_id": "136fdfd68a9780a3ae4be27f473bad08"},
            "properties": {
                "Name": {
                    "title": [{"text": {"content": f"🤖 {name}"}}]
                },
                "Status": {
                    "status": {"name": status}
                },
                "Duration (minutes)":{
                "number": duration_in_minutes
                },
                "Priority": {
                    "select": {"name": priority}
                },
                "Due Date": {
                    "date": {"start": start_datetime, "end": end_datetime}
                }
            }
        }

        # Make the API request to Notion
        url = f"{NOTION_ENDPOINT}/pages"
        response = requests.post(url, headers=self.headers, json=task_data)

        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.text}


class RescheduleExcistingTasks(BaseTool):
    name: str = "Reschedule Existing Task Tool"
    description: str = "Reschedules a single existing task, identified by page_id, with a new start date time and end date time. This tool cannot process multiple tasks at once."

    headers: ClassVar[Dict[str, str]] = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"  # Use the correct Notion API version
    }

    def _run(self, page_id: str, start_datetime: str, end_datetime: str) -> Dict[str, Any]:
        """
        Update the start_datetime and end_datetime properties for an excisting Task or database page, identified by the page_id.

        Args:
            page_id (str): Notioh Page ID of page to be updated or rescheduled.
            start_datetime (str): Start date and time in ISO 8601 format.
            end_datetime (str): End date and time in ISO 8601 format.

        Returns:
            dict: The response from the Notion API.
        """
        task_data = {
            "parent": {"database_id": NOTION_DATABASE_ID},
            "properties": {
                "Due Date": {
                    "date": {"start": start_datetime, "end": end_datetime}
                }
            }
        }

        # Make the API request to Notion
        url = f"{NOTION_ENDPOINT}/pages/{page_id}"
        response = requests.patch(url, headers=self.headers, json=task_data)

        if response.status_code == 200:
            data = response.json()
            print(data)

            page_id = data['id']
            print(f"Page ID: {page_id}")
            os.environ["NOTION_PARENT_PAGE_ID"] = page_id
            print("🧡 Notion Page ID Exported as enviromental variable.")
            return page_id
        else:
            return {"error": response.text}


# Creating Agents


# data_collection_agent = Agent(
#   config=agents_config['data_collection_agent'],
#   tools=[DatabaseDataFetcherTool(), PageDataFetcherTool()]

# )

task_creation_agent = Agent(
  config=agents_config['task_creation_agent'],
  tools=[NewTaskCreationTool()]
)

research_agent = Agent(
  config=agents_config['research_agent'],
  tools=[search_tool, web_rag_tool, scrape_web_tool]
)

writer_agent = Agent(
  config=agents_config['writer_agent'],
)

# Creating Tasks
# data_collection = Task(
#   config=tasks_config['data_collection'],
#   agent=data_collection_agent
# )

create_new_tasks = Task(
  config=tasks_config['create_new_tasks'],
  agent=task_creation_agent,
  tools=[NewTaskCreationTool()]
)

online_research_tasks = Task(
  config=tasks_config['online_research_tasks'],
  agent=research_agent
)

writer_tasks = Task(
  config=tasks_config['writer_tasks'],
  agent=writer_agent
)


# Creating Crew
crew = Crew(
  agents=[
    task_creation_agent,
    research_agent,
    writer_agent
  ],
  tasks=[
    create_new_tasks,
    online_research_tasks,
    writer_tasks
  ],
  process=Process.sequential,
  verbose=True
)


if __name__ == "__main__":
    datetime_n = datetime.now()
    datetime_now = datetime_n.strftime('%A, %Y-%m-%d %H:%M')

    # The given Python dictionary
    inputs = {
    'prompt': input("🆕 New Task Creation prompt:"),
    'datetime_now': datetime_now
    }
    # 🅾️ Train and Test runs
    # crew.train(n_iterations=1, filename='training2.pkl', inputs=inputs)
    # crew.test(1, inputs=inputs)

    # Run the crew
    result = crew.kickoff(
    inputs=inputs
    )

    print("Printing 'result' from crew.kickoff() method:")
    print(type(result.raw))
    print(result.raw)

    cleaned_string = re.sub(r"```.*?\n", "", result.raw, flags=re.DOTALL)

    # Step 3: Parse the cleaned string
    parsed_json = json.loads(cleaned_string)

    # Step 4: Access data




    parent_page_id = parsed_json.get('notion_page_id')
    markdown_text = parsed_json.get('markdown_report')

    print("Notion Page ID:", parent_page_id)

    append_markdown_to_notion_page(NOTION_TOKEN, parent_page_id, markdown_text)
    print("🚀 Notion Page Creation Completed")


    import pandas as pd

    costs = 0.150 * (crew.usage_metrics.prompt_tokens + crew.usage_metrics.completion_tokens) / 1_000_000
    print(f"💷 Total costs: ${costs:.4f}")

    # Convert UsageMetrics instance to a DataFrame
    df_usage_metrics = pd.DataFrame([crew.usage_metrics.dict()])
    print(df_usage_metrics)
    print()
    print("Completging this run:")
    print(result.raw)
