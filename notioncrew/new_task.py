__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')# Warning control


import warnings

warnings.filterwarnings("ignore")

import os
import json
import re
import yaml
import requests
from datetime import datetime, timedelta
from typing import ClassVar, Union, Dict, Any, List

import streamlit as st
import pandas as pd

from crewai import Agent, Task, Crew
from crewai.process import Process
from crewai_tools import BaseTool, SerperDevTool, WebsiteSearchTool, ScrapeWebsiteTool

from notionfier_main import append_markdown_to_notion_page
from utils import get_next_working_day
from tools.custom_tools import NewTaskCreationTool

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
    "agents": "notioncrew/config/agents.yaml",
    "tasks": "notioncrew/config/tasks.yaml",
}

print(f"🅾️- {today}")


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
    config=agents_config["task_creation_agent"], tools=[NewTaskCreationTool()]
)

research_agent = Agent(
    config=agents_config["research_agent"],
    tools=[search_tool, web_rag_tool, scrape_web_tool],
)

writer_agent = Agent(
    config=agents_config["writer_agent"],
)

# Creating Tasks
# data_collection = Task(
#   config=tasks_config['data_collection'],
#   agent=data_collection_agent
# )

create_new_tasks = Task(
    config=tasks_config["create_new_tasks"],
    agent=task_creation_agent,
    tools=[NewTaskCreationTool()],
)

online_research_tasks = Task(
    config=tasks_config["online_research_tasks"], agent=research_agent
)

writer_tasks = Task(config=tasks_config["writer_tasks"], agent=writer_agent)


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

    st.caption(f"🕒 **Current datetime**: {datetime_now}")
    st.caption(f"👨🏻‍💻 **Next Working Day**: {next_working_day}")

    inputs = {
        "prompt": prompt,
        "datetime_now": datetime_now,
        "next_working_day": next_working_day
    }

    # Run the crew
    result = crew.kickoff(inputs=inputs)

    st.json(result.raw)

    cleaned_string = re.sub(r"```.*?\n", "", result.raw, flags=re.DOTALL)

    # Step 3: Parse the cleaned string
    parsed_json = json.loads(cleaned_string)

    # Step 4: Access data

    parent_page_id = parsed_json.get("notion_page_id")
    markdown_text = parsed_json.get("markdown_report")

    st.write(f"**Notion Page ID**: {parent_page_id}")

    append_markdown_to_notion_page(NOTION_TOKEN, parent_page_id, markdown_text)
    st.write("🚀 Notion Page Creation Completed")

    import pandas as pd

    costs = (
        0.150
        * (crew.usage_metrics.prompt_tokens + crew.usage_metrics.completion_tokens)
        / 1_000_000
    )
    st.markdown(f"💷 **Total costs**: ${costs:.4f}")

    # Convert UsageMetrics instance to a DataFrame
    df_usage_metrics = pd.DataFrame([crew.usage_metrics.dict()])
    st.dataframe(df_usage_metrics)
    st.write("✅ Crew run successfully!")
