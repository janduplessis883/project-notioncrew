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
from tools.custom_tools import DatabaseDataFetcherTool, AppraisalPageDataFetcherTool

database_tool = DatabaseDataFetcherTool()
appraisal_pages_tool = AppraisalPageDataFetcherTool()
search_tool = SerperDevTool()
scrape_web_tool = ScrapeWebsiteTool()

# Load environment variables from streamlit secrets
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
OPENAI_MODEL_NAME = st.secrets["OPENAI_MODEL_NAME"]
NOTION_ENDPOINT = st.secrets["NOTION_ENDPOINT"]
NOTION_VERSION = st.secrets["NOTION_VERSION"]
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
APPRAISAL_DATABASE_ID = st.secrets["APPRAISAL_DATABASE_ID"]
SERPER_API_KEY = st.secrets["SERPER_API_KEY"]

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
    or not APPRAISAL_DATABASE_ID
):
    raise ValueError("One or more required environment variables are missing.")

from typing import List
from pydantic import BaseModel, Field

class Resource(BaseModel):
    resource_name: str = Field(..., description="Name of the resource found")
    summary: float = Field(..., description="Summary of the online resourse found")
    relevance: float = Field(..., description="Why it is relevant to the employee")
    url: List[str] = Field(..., description="URL of the onlline resource")



appraisal_data_collection_agent = Agent(
    config=agents_config["appraisal_data_collection_agent"],
    tools=[database_tool, appraisal_pages_tool],
)

appraisal_research_agent = Agent(
    config=agents_config["appraisal_research_agent"],
    tools=[search_tool, scrape_web_tool],
    output_pydantic=Resource
)

appraisal_analysis_agent = Agent(
    config=agents_config["appraisal_analysis_agent"],
    output_pydantic=Resource
)



# Creating Tasks

appraisal_data_collection = Task(
    config=tasks_config["appraisal_data_collection"],
    agent=appraisal_data_collection_agent,
    tools=[database_tool, appraisal_pages_tool],
)

appraisal_research_task = Task(
    config=tasks_config["appraisal_research_task"], agent=appraisal_research_agent
)

appraisal_report_task = Task(config=tasks_config["appraisal_report_task"], agent=appraisal_analysis_agent)


# Creating Crew
crew = Crew(
    agents=[appraisal_data_collection_agent, appraisal_research_agent, appraisal_analysis_agent],
    tasks=[appraisal_data_collection, appraisal_research_task, appraisal_report_task],
    process=Process.sequential,
    verbose=True,
)


def appraisal():
    print(f"🅾️- Appraisal Tool")
    inputs = {
        "employee_name": input("Enter the employee's name: "),
    }

    # Run the crew
    result = crew.kickoff(inputs=inputs)

    print(result.raw)
    print(result.pydantic.dict())



    # Step 4: Access data


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
    appraisal()
