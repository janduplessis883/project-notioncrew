import streamlit as st
import streamlit_shadcn_ui as ui

from timeblocker import run_timeblocking
from new_task import new_task_creation

import sys
from io import StringIO

# Set the title of the Streamlit app
st.title(":material/robot_2: NotionCrew")

class StreamlitLogger:
    def __init__(self, container):
        self.output = StringIO()
        self.container = container

    def write(self, message):
        # Write the message to the StringIO buffer
        self.output.write(message)
        # Update the container's content with the current output
        self.container.text_area("Terminal Output", self.output.getvalue(), height=300)

    def flush(self):
        # Required for compatibility with `sys.stdout`
        pass

tab_selector = ui.tabs(
    options=[
        "Notion Task Scheduler",
        "Create New Smart Task",
    ],
    default_value="Notion Task Scheduler",
    key="pagetab",
)


if tab_selector == "Notion Task Scheduler":
    st.write(
        ":material/update: **Task Sheduler** - Reschedule Notion Tasks with a crew of agents."
    )
    st.image("images/notioncrew2.png", width=300)
    with st.spinner("Rescheduling tasks..."):
        if st.button(":material/laps: Reschedule Notion Tasks"):

            # Create a placeholder container for the terminal output
            output_container = st.empty()

            # Create a logger instance and pass the container
            logger = StreamlitLogger(output_container)

            # Redirect stdout to the custom logger
            sys.stdout = logger
            run_timeblocking()
            st.write("✅ Crew run successfully")

            # Reset stdout when done
            sys.stdout = sys.__stdout__


elif tab_selector == "Create New Smart Task":

    st.write(
        ":material/add_circle: **New Smart Task** - Schedules a new task and researches the topic on the internet."
    )
    st.caption(
        "Priority and duration of tasks will be assigned an agent, if not specified."
    )
    st.image("images/notioncrew2.png", width=300)

    with st.form(key="new_task_form", border=False):
        new_task = st.text_input("New Task prompt")
        submit_button = st.form_submit_button(label="Submit")

        if submit_button:
            st.write(f"New task submitted: {new_task}")

             # Create a placeholder container for the terminal output
            output_container = st.empty()

            # Create a logger instance and pass the container
            logger = StreamlitLogger(output_container)

            # Redirect stdout to the custom logger
            sys.stdout = logger

            new_task_creation(new_task)
