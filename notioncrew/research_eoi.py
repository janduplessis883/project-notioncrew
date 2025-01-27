import toml
import pandas as pd
import textwrap
import yaml
from crewai import Agent, Task, Crew, Process, LLM
from crewai.knowledge.source.string_knowledge_source import StringKnowledgeSource
from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource
from tools.custom_tools_terminal import ReadFile

# Create a knowledge source
from crewai_tools import (
    PDFSearchTool,
    SerperDevTool,
    WebsiteSearchTool,
    ScrapeWebsiteTool,
)
from md_to_notion import *


search_tool = SerperDevTool()
scrape_web_tool = ScrapeWebsiteTool()
website_rag = WebsiteSearchTool()

nihr_guidelines_rag = PDFSearchTool(pdf="knowledge/eoi_guidelines_nihr.pdf")
nihr_guidelines_content = ReadFile(
    name="nihr_guidelines_content", file_path="knowledge/eoi_guidelines_nihr.txt"
)

site_profile_rag = PDFSearchTool(pdf="knowledge/thechelseapractice.pdf")
site_profile_content = ReadFile(
    name="site_profile_content", file_path="knowledge/thechelseapractice.txt"
)

site_identification_questions = ReadFile(
    name="site_identification_questions",
    file_path="knowledge/site_identification_questions.txt",
)

recruitment_strategies = ReadFile(
    name="recruitment_strategies", file_path="knowledge/recruitment_strategies.txt"
)



# 🅾️ Identify Study documetnation further down


# Create an LLM with a temperature of 0 to ensure deterministic outputs
llm = LLM(model="gpt-4o-mini", temperature=0)

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
APPRAISAL_DATABASE_ID = config_secrets["APPRAISAL_DATABASE_ID"]


# Define file paths for YAML configurations
files = {
    "agents": "notioncrew/config/agents.yaml",
    "tasks": "notioncrew/config/tasks.yaml",
}


def run_my_crew(study_no, study_identifier):

    study_rag = PDFSearchTool(pdf=f"knowledge/study{study_no}.pdf")
    study_content = ReadFile(
        name="study_content", file_path=f"knowledge/study1.txt"
    )

    # Load configurations from YAML files
    configs = {}
    for config_type, file_path in files.items():
        with open(file_path, "r") as file:
            configs[config_type] = yaml.safe_load(file)

    # Assign loaded configurations to specific variables
    agents_config = configs["agents"]
    tasks_config = configs["tasks"]

    clinical_researcher_agent = Agent(
        config=agents_config["clinical_researcher_agent"],
        tools=[study_content],
    )

    research_recruitement_coordinator_agent = Agent(
        config=agents_config["research_recruitement_coordinator_agent"],
        tools=[search_tool, scrape_web_tool],
    )

    senior_research_writer_agent = Agent(
        config=agents_config["senior_research_writer_agent"],
        tools=[nihr_guidelines_content, site_identification_questions],
    )

    research_auditor_agent = Agent(
        config=agents_config["research_auditor_agent"],
        tools=[nihr_guidelines_content, nihr_guidelines_rag],
    )

    # TASKS
    review_study_specifications = Task(
        config=tasks_config["review_study_specifications"],
        agent=clinical_researcher_agent,
        output_file="01_the_study.md",
    )

    participant_recruitment_strategy = Task(
        config=tasks_config["participant_recruitment_strategy"],
        agent=research_recruitement_coordinator_agent,
        output_file="02_recruitment_strategy.md",
    )

    complete_site_identification_questionnaire = Task(
        config=tasks_config["complete_site_identification_questionnaire"],
        agent=senior_research_writer_agent,
        tools=[site_identification_questions],
        output_file="03_site_identification_questions.md",
    )

    audit_site_identification_questionnaire = Task(
        config=tasks_config["audit_site_identification_questionnaire"],
        agent=research_auditor_agent,
        output_file="04_submission_audit.md",
    )

    # Creating Crew
    crew = Crew(
        agents=[
            clinical_researcher_agent,
            research_recruitement_coordinator_agent,
            senior_research_writer_agent,
            research_auditor_agent,
        ],
        tasks=[
            review_study_specifications,
            participant_recruitment_strategy,
            complete_site_identification_questionnaire,
            audit_site_identification_questionnaire,
        ],
        process=Process.sequential,
        verbose=True,
    )
    print()
    print(f"🤖 Model: {OPENAI_MODEL_NAME}")
    print(f"💉 Study No: {study_no}")
    print(f"🆔 Study Identifier: {study_identifier}")
    print()

    inputs = {"study_identifier": study_identifier}
    result = crew.kickoff()

    costs = (
        0.150
        * (crew.usage_metrics.prompt_tokens + crew.usage_metrics.completion_tokens)
        / 1_000_000
    )
    print(f"💷 **Total costs**: ${costs:.4f}")

    # Convert UsageMetrics instance to a DataFrame
    df_usage_metrics = pd.DataFrame([crew.usage_metrics.dict()])
    print(df_usage_metrics)

    return result.raw


def write_output_to_notion(study_identifier):
    print("✏️ Writing Output files to Notion")
    notion_secret = NOTION_TOKEN
    notion_database_id = "16bfdfd68a978047b47dfe063a6a5407"
    new_page_id = create_new_notion_page(study_identifier)

    md_files = [
        "01_the_study.md",
        "02_recruitment_strategy.md",
        "02b_recruitment_retention.md",
        "03_site_identification_questions.md",
        "04_submission_audit.md",
    ]

    for file in md_files:
        print(file)
        md_content = read_md_file(file)
        append_markdown_to_notion_page(notion_secret, new_page_id, md_content)
    print("✅ Output files written to Notion")


if __name__ == "__main__":
    print("🅾️ CLINICAL RESEARCH EOI CREW 🅾️")
    print("Study 1: CN012-0023\nStudy 2: GlobalMinds\nStudy 3: J1I-MC-GZQB")
    print("-" * 100)

    study_no = input("💉 Study No: ")
    study_identifier = input("🆔 Study Identifier: ")
    print("-" * 100)
    run_my_crew(study_no, study_identifier)

    print("🚀 Crew Finished")

    write_output_to_notion(study_identifier)
