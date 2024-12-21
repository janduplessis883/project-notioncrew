import streamlit as st
import streamlit_shadcn_ui as ui

from timeblocker import run_timeblocking
from new_task import *


st.set_page_config(
    page_title="NotionCrew",
    page_icon=":shark:",
    initial_sidebar_state="auto",
)

# Set the title of the Streamlit app
st.title(":material/robot_2: NotionCrew")

tab_selector = ui.tabs(
    options=[
        "Notion Task Scheduler",
        "Create New Smart Task",
    ],
    default_value="Notion Task Scheduler",
    key="pagetab",
)


if tab_selector == "Notion Task Scheduler":
    st.write(":material/update: **Task Sheduler** - Reschedule Notion Tasks with a crew of agents.")
    st.image("images/notioncrew2.png", width=300)
    with st.spinner('Rescheduling tasks...'):
        if st.button(":material/laps: Reschedule Notion Tasks"):
            run_timeblocking()
            st.write("✅ Crew run successfully")




elif tab_selector == "Create New Smart Task":

    st.write(":material/add_circle: **New Smart Task** - Schedules a new task and researches the topic on the internet.")
    st.caption("Priority and duration of tasks will be assigned an agent, if not specified.")
    with st.form(key='new_task_form', border=False):
        new_task = st.text_input("New Task prompt")
        submit_button = st.form_submit_button(label='Submit')

        if submit_button:
            st.write(f"New task submitted: {new_task}")

    st.image("images/notioncrew2.png", width=300)
