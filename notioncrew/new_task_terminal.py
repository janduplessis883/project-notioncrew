import warnings

warnings.filterwarnings("ignore")
import toml
import os
import json
import re
import yaml
import requests
from datetime import datetime, timedelta
from typing import ClassVar, Union, Dict, Any, List
from pydantic import BaseModel, Field
import pandas as pd


from crewai import Agent, Task, Crew
from crewai.process import Process
from crewai_tools import BaseTool, SerperDevTool, WebsiteSearchTool, ScrapeWebsiteTool

from notionfier_main import append_markdown_to_notion_page
from utils import get_next_working_day
from tools.custom_tools_terminal import NewTaskCreationTool
from file_io import save_page_id

today = datetime.now()

search_tool = SerperDevTool()
web_rag_tool = WebsiteSearchTool()
scrape_web_tool = ScrapeWebsiteTool()
new_task_tool = NewTaskCreationTool()

with open("notioncrew/config_secrets.toml", "r") as f:
    config_secrets = toml.load(f)

# Load environment variables from streamlit secrets
OPENAI_API_KEY = config_secrets["OPENAI_API_KEY"]
OPENAI_MODEL_NAME = config_secrets["OPENAI_MODEL_NAME"]
NOTION_ENDPOINT = config_secrets["NOTION_ENDPOINT"]
NOTION_VERSION = config_secrets["NOTION_VERSION"]
NOTION_TOKEN = config_secrets["NOTION_TOKEN"]
NOTION_DATABASE_ID = config_secrets["NOTION_DATABASE_ID"]
SERPER_API_KEY = config_secrets["SERPER_API_KEY"]


class NotionInfo(BaseModel):
    page_id: str = Field(..., description="page_id of newly created Notion page")
    markdown_output: str = Field(..., description="markdown output from writer")


# Define file paths for YAML configurations
files = {
    "agents": "notioncrew/config/agents.yaml",
    "tasks": "notioncrew/config/tasks.yaml",
}


# Load configurations from YAML files
configs = {}
for config_type, file_path in files.items():
    with open(file_path, "r") as file:
        configs[config_type] = yaml.safe_load(file)

# Assign loaded configurations to specific variables
agents_config = configs["agents"]
tasks_config = configs["tasks"]


# Validate if the variables are loaded correctly
if (
    not NOTION_TOKEN
    or not OPENAI_API_KEY
    or not NOTION_ENDPOINT
    or not NOTION_DATABASE_ID
):
    raise ValueError("One or more required environment variables are missing.")

# Creating Agents

task_creation_agent = Agent(
    config=agents_config["task_creation_agent"], tools=[new_task_tool]
)

research_agent = Agent(
    config=agents_config["research_agent"],
    tools=[search_tool, web_rag_tool, scrape_web_tool],
)

writer_agent = Agent(
    config=agents_config["writer_agent"],
)

create_new_tasks = Task(
    config=tasks_config["create_new_tasks"],
    agent=task_creation_agent,
    tools=[NewTaskCreationTool()],
)

online_research_tasks = Task(
    config=tasks_config["online_research_tasks"], agent=research_agent
)

writer_tasks = Task(
    config=tasks_config["writer_tasks"], agent=writer_agent, output_pydantic=NotionInfo
)


# Creating Crew
crew = Crew(
    agents=[task_creation_agent, research_agent, writer_agent],
    tasks=[create_new_tasks, online_research_tasks, writer_tasks],
    process=Process.sequential,
    verbose=True,
)


def new_task_creation(prompt: str):

    datetime_now = datetime.now().strftime("%A, %Y-%m-%d %H:%M")
    next_working_day = get_next_working_day()

    print(f"🕒 **Current datetime**: {datetime_now}")
    print(f"👨🏻‍💻 **Next Working Day**: {next_working_day}")

    inputs = {
        "prompt": prompt,
        "datetime_now": datetime_now,
        "next_working_day": next_working_day,
    }

    # Run the crew
    result = crew.kickoff(inputs=inputs)

    # Step 4: Access data

    parent_page_id = result.pydantic.dict()["page_id"]
    markdown_text = result.pydantic.dict()["markdown_output"]

    with open("notioncrew/page_id.txt", "r") as f:
        parent_page_id = f.read().strip()

    print(f"Notion Page ID: {parent_page_id}")
    print(f"Markdown Report: {markdown_text}")

    append_markdown_to_notion_page(NOTION_TOKEN, parent_page_id, markdown_text)
    print("🚀 Notion Page Creation Completed")

    import pandas as pd

    costs = (
        0.150
        * (crew.usage_metrics.prompt_tokens + crew.usage_metrics.completion_tokens)
        / 1_000_000
    )
    print(f"💷 **Total costs**: ${costs:.4f}")

    # Convert UsageMetrics instance to a DataFrame
    df_usage_metrics = pd.DataFrame([crew.usage_metrics.dict()])
    print(df_usage_metrics)


if __name__ == "__main__":
    prompt = input("New task creation prompt: ")
    new_task_creation(prompt)
