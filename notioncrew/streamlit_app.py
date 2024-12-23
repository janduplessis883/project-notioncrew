import streamlit as st
import streamlit_shadcn_ui as ui

from timeblocker import run_timeblocking
from new_task import new_task_creation

st.set_page_config(
    page_title="NotionCrew",  # Title of the app
    page_icon="📝",          # Optional icon for the app
    layout="wide",           # Set the layout to wide
)

# Set the title of the Streamlit app
st.title(":material/robot_2: NotionCrew")


tab_selector = ui.tabs(
    options=[
        "Notion Task Scheduler",
        "Create New Smart Task",
        "ID Extractor",
        "Appriasal Tool",
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

            run_timeblocking()
            st.write("✅ Crew run successfully")



elif tab_selector == "Create New Smart Task":

    st.write(
        ":material/add_circle: **New Smart Task** - Schedules a new task and researches the topic on the internet."
    )

    st.image("images/notioncrew2.png", width=300)

    with st.form(key="new_task_form", border=False):
        new_task = st.text_input("New Task prompt")
        submit_button = st.form_submit_button(label="Submit")
        with st.spinner("Creating new task..."):
            if submit_button:
                st.write(f"New task submitted: {new_task}")

                new_task_creation(new_task)
                st.write("✅ Crew run successfully")


elif tab_selector == "ID Extractor":
    link_type = st.radio(
        "Select the Notion link type:",
        ("Database URL", "Page URL")
    )

    if link_type == "Database URL":

        db_url = st.text_input("Enter the **Database** URL")
        database_id = db_url.split('/')[-1].split('?')[0]
        st.code(database_id, language="json")
    else:
        page_url = st.text_input("Enter the **Page** URL")
        page_id = page_url.split('-')[-1].split('?')[0]
        st.code(page_id, language="json")





elif tab_selector == "Appriasal Tool":
    pass
