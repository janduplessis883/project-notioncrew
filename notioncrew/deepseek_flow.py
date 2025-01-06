from crewai.flow.flow import Flow, listen, start
from crewai.agent import Agent
from crewai.task import Task
from crewai_tools import FileReadTool, DirectoryReadTool, SerperDevTool

# Define the agents
file_reader_agent = Agent(
    role="File Reader",
    goal="Read local files containing site profile and recruitment strategy",
    backstory="An expert in reading and extracting information from local files.",
    tools=[FileReadTool(), DirectoryReadTool()],
    verbose=True
)

study_spec_reader_agent = Agent(
    role="Study Spec Reader",
    goal="Read the study specifications from a local file",
    backstory="An expert in reading and interpreting study specifications.",
    tools=[FileReadTool()],
    verbose=True
)

online_searcher_agent = Agent(
    role="Online Searcher",
    goal="Search online for recruitment strategies relevant to the clinical domain of the study",
    backstory="An expert in finding relevant recruitment strategies online.",
    tools=[SerperDevTool()],
    verbose=True
)

writer_agent = Agent(
    role="Report Writer",
    goal="Compile a comprehensive report based on the gathered information",
    backstory="An expert in writing detailed and structured reports.",
    verbose=True
)

auditor_agent = Agent(
    role="Report Auditor",
    goal="Score the report and provide feedback for improvement if necessary",
    backstory="An expert in evaluating reports and providing constructive feedback.",
    verbose=True
)

# Define the tasks
read_site_profile_task = Task(
    description="Read the site profile and recruitment strategy from local files",
    expected_output="Extracted information from the site profile and recruitment strategy",
    agent=file_reader_agent
)

read_study_specs_task = Task(
    description="Read the study specifications from a local file",
    expected_output="Extracted study specifications",
    agent=study_spec_reader_agent
)

search_recruitment_strategies_task = Task(
    description="Search online for recruitment strategies relevant to the clinical domain of the study",
    expected_output="List of relevant recruitment strategies",
    agent=online_searcher_agent
)

write_report_task = Task(
    description="Compile a comprehensive report based on the gathered information",
    expected_output="A detailed report on recruitment strategies and study specifications",
    agent=writer_agent
)

audit_report_task = Task(
    description="Score the report and provide feedback for improvement if necessary",
    expected_output="A score out of 10 and feedback for improvement if the score is less than 7",
    agent=auditor_agent
)

# Define the flow
class RecruitmentFlow(Flow):
    max_iterations = 3  # Exit after 3 iterations

    @start()
    def start_flow(self):
        print("Starting the recruitment flow...")
        return self.read_site_profile()

    @listen(start_flow)
    def read_site_profile(self):
        print("Reading site profile and recruitment strategy...")
        site_profile = read_site_profile_task.run()
        return site_profile

    @listen(read_site_profile)
    def read_study_specs(self, site_profile):
        print("Reading study specifications...")
        study_specs = read_study_specs_task.run()
        return {"site_profile": site_profile, "study_specs": study_specs}

    @listen(read_study_specs)
    def search_strategies(self, data):
        print("Searching for recruitment strategies...")
        strategies = search_recruitment_strategies_task.run()
        return {**data, "strategies": strategies}

    @listen(search_strategies)
    def write_report(self, data):
        print("Writing the report...")
        report = write_report_task.run(inputs=data)
        return report

    @listen(write_report)
    def audit_report(self, report):
        print("Auditing the report...")
        audit_result = audit_report_task.run(inputs={"report": report})
        if audit_result["score"] < 7:
            print(f"Report scored {audit_result['score']}. Sending back for revision...")
            return self.write_report(report)  # Send back to writer for revision
        else:
            print(f"Report scored {audit_result['score']}. Exiting flow.")
            return audit_result

# Instantiate and run the flow
flow = RecruitmentFlow()
result = flow.kickoff()
print("Final result:", result)
