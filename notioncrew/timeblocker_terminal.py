import os
import json
import yaml
import requests
import warnings
from datetime import datetime, timedelta
from typing import ClassVar, Union, Dict, Any, List
import pandas as pd
from crewai import Agent, Task, Crew
from crewai.process import Process
from crewai_tools import BaseTool
import toml
# from crewai.llm import LLM

# llm = LLM(model="ollama/nezahatkorkmaz/deepseek-v3:latest", base_url="http://localhost:11434", temprature=0)

warnings.filterwarnings("ignore")

from notioncrew.tools.custom_tools_terminal import (
    DatabaseDataFetcherTool,
    PageDataFetcherTool,
    UpdateExcistingTasks,
)
from utils import get_next_working_day


database_fetcher = DatabaseDataFetcherTool()
page_fetcher = PageDataFetcherTool()
updater = UpdateExcistingTasks()

# Load the TOML file
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
data_collection_agent = Agent(
    config=agents_config["data_collection_agent"],

)

calendar_scheduler_agent = Agent(
    config=agents_config["calendar_scheduler_agent"],

)

notion_database_updater_agent = Agent(
    config=agents_config["notion_database_updater_agent"],

)


# Creating Tasks
data_collection = Task(
    config=tasks_config["data_collection"],
    agent=data_collection_agent,
    tools=[database_fetcher, page_fetcher],
)

reschedule_tasks = Task(
    config=tasks_config["reschedule_tasks"],
    agent=calendar_scheduler_agent,
)

update_notion_database = Task(
    config=tasks_config["update_notion_database"],
    agent=notion_database_updater_agent,
    tools=[updater],
)


# Creating Crew
crew = Crew(
    agents=[
        data_collection_agent,
        calendar_scheduler_agent,
        notion_database_updater_agent,
    ],
    tasks=[data_collection, reschedule_tasks, update_notion_database],
    process=Process.sequential,
    verbose=True,
)


def run_timeblocking():

    datetime_now = datetime.now().strftime("%A, %Y-%m-%d %H:%M")
    next_working_day = get_next_working_day()
    print(f"🤖 Model: {OPENAI_MODEL_NAME}")
    print(f"🕒 **Current datetime**: {datetime_now}")
    print(f"👨🏻‍💻 **Next Working Day**: {next_working_day}")
    # The given Python dictionary
    inputs = {"datetime_now": datetime_now, "next_working_day": next_working_day}
    # Run the crew
    result = crew.kickoff(inputs=inputs)

    costs = (
        0.150
        * (crew.usage_metrics.prompt_tokens + crew.usage_metrics.completion_tokens)
        / 1_000_000
    )

    # Convert UsageMetrics instance to a DataFrame
    df_usage_metrics = pd.DataFrame([crew.usage_metrics.dict()])
    print(df_usage_metrics)
    print(f"💷 Total costs: ${costs:.4f}")

    print(result.raw)
    return result.raw


if __name__ == "__main__":
    run_timeblocking()
