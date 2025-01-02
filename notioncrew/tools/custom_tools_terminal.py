import toml
from crewai_tools import BaseTool
from typing import ClassVar, Union, Dict, Any, List
import requests

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
APPRSAIAL_DATABASE_ID = config_secrets["APPRAISAL_DATABASE_ID"]


class DatabaseDataFetcherTool(BaseTool):
    """
    Tool to fetch the structure and properties of a Notion Database.
    """

    name: str = "Notion Database Data Fetcher"
    description: str = "Fetches Notion Database structure and properties."

    headers: ClassVar[Dict[str, str]] = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }

    def _run(self) -> Union[dict, str]:
        """
        Fetch all the properties and structure of a Notion database.

        Returns:
            Union[dict, str]: The database structure or an error message.
        """
        url = f"{NOTION_ENDPOINT}/databases/{NOTION_DATABASE_ID}"

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
        "Notion-Version": NOTION_VERSION,
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
        next_week = (today + timedelta(days=4)).strftime("%Y-%m-%d")

        # Properly formatted filter with Status != Done
        filter_payload = {
            "filter": {
                "and": [
                    {"property": "Due Date", "date": {"on_or_after": yesterday}},
                    {"property": "Due Date", "date": {"before": next_week}},
                    {"property": "Status", "status": {"does_not_equal": "Done"}},
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
                    all_pages.append({"page_id": page.get("id"), "full_schema": page})

                has_more = data.get("has_more", False)
                next_cursor = data.get("next_cursor", None)
            else:
                return [{"error": response.text, "status_code": response.status_code}]

        return all_pages


class NewTaskCreationTool(BaseTool):
    name: str = "Create New Task Tool"
    description: str = (
        "Creates a new task in the calendar database with user-specified properties like Priority, Title, and Due Dates."
    )

    headers: ClassVar[Dict[str, str]] = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,  # Use the correct Notion API version
    }

    def _run(
        self,
        name: str,
        status: str,
        priority: str,
        start_datetime: str,
        end_datetime: str,
        duration_in_minutes: int,
    ) -> Dict[str, Any]:
        """
        Create a new task in the Notion database with specified properties.

        Args:
            title (str): The name of the task.
            status (str): The status of the task (e.g., "Not Started", "In progress", "Done").
            priority (str): Priority of the task ("High", "Medium", "Low").
            duration_in_minutes (int): Duration of the task in minutes.
            start_datetime (str): Start date and time in ISO 8601 format.
            end_datetime (str): End date and time in ISO 8601 format.

        Returns:
            dict: The response from the Notion API.
        """
        task_data = {
            "parent": {"database_id": NOTION_DATABASE_ID},
            "properties": {
                "Name": {"title": [{"text": {"content": f"🅾️ {name}"}}]},
                "Status": {"status": {"name": status}},
                "Duration (minutes)": {"number": duration_in_minutes},
                "Priority": {"select": {"name": priority}},
                "Due Date": {"date": {"start": start_datetime, "end": end_datetime}},
            },
        }

        # Make the API request to Notion
        url = f"{NOTION_ENDPOINT}/pages"
        response = requests.post(url, headers=self.headers, json=task_data)

        if response.status_code == 200:
            output_data = response.json()
            page_id = output_data["id"]
            with open("notioncrew/page_id.txt", "w") as f:
                f.write(page_id)

            print(f"✅ Page ID {page_id} has been written to page_id.txt")
            return response.json()
        else:
            return {"error": response.text}


class UpdateExcistingTasks(BaseTool):
    name: str = "Reschedule Existing Task Tool"
    description: str = (
        "Reschedules a single existing task, identified by page_id, with a new start date time and end date time. This tool cannot process multiple tasks at once."
    )

    headers: ClassVar[Dict[str, str]] = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,  # Use the correct Notion API version
    }

    def _run(
        self, page_id: str, start_datetime: str, end_datetime: str
    ) -> Dict[str, Any]:
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
                "Due Date": {"date": {"start": start_datetime, "end": end_datetime}}
            },
        }

        # Make the API request to Notion
        url = f"{NOTION_ENDPOINT}/pages/{page_id}"
        response = requests.patch(url, headers=self.headers, json=task_data)

        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.text}


class AppraisalDatabaseDataFetcherTool(BaseTool):
    """
    Tool to fetch the structure and properties of a Notion Database.
    """

    name: str = "Notion Database Data Fetcher"
    description: str = "Fetches Notion Database structure and properties."

    headers: ClassVar[Dict[str, str]] = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }

    def _run(self) -> Union[dict, str]:
        """
        Fetch all the properties and structure of a Notion database.

        Returns:
            Union[dict, str]: The database structure or an error message.
        """
        url = f"{NOTION_ENDPOINT}/databases/{APPRSAIAL_DATABASE_ID}"

        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            else:
                return f"Error {response.status_code}: {response.text}"
        except Exception as e:
            return f"An error occurred: {str(e)}"


class AppraisalPageDataFetcherTool(BaseTool):
    """
    Tool to fetch Notion pages in a database containing a specific employee's name.
    """

    name: str = "Fetch Notion Pages by Employee Name Tool"
    description: str = (
        "Fetches pages from a specified Notion database that contain the name of a specific employee."
    )

    headers: ClassVar[Dict[str, str]] = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }

    def _run(self, employee_name: str) -> List[Dict[str, Any]]:
        """
        Fetches pages from the specified Notion database that contain the name {employee_name}.

        Args:
            database_id (str): The Notion database ID.
            employee_name (str): The name of the employee to search for.

        Returns:
            List[Dict]: A list of dictionaries containing page IDs and full schemas.
        """
        url = f"{NOTION_ENDPOINT}/databases/{APPRSAIAL_DATABASE_ID}/query"
        all_pages = []
        has_more = True
        next_cursor = None

        # Filter for pages where a property contains the employee's name
        filter_payload = {
            "filter": {
                "property": "Name",  # Replace "Name" with the property name where employee names are stored
                "rich_text": {"contains": employee_name},
            }
        }

        # Handle pagination to fetch all relevant pages
        while has_more:
            payload = {"start_cursor": next_cursor} if next_cursor else {}
            payload.update(filter_payload)  # Add the filter to the payload
            response = requests.post(url, headers=self.headers, json=payload)

            if response.status_code == 200:
                data = response.json()
                for page in data.get("results", []):
                    all_pages.append({"page_id": page.get("id"), "full_schema": page})

                has_more = data.get("has_more", False)
                next_cursor = data.get("next_cursor", None)
            else:
                return [{"error": response.text, "status_code": response.status_code}]

        output_data = all_pages[0]
        page_id = output_data["page_id"]
        with open("notioncrew/appraisal_page_id.txt", "w") as f:
            f.write(page_id)

        print(f"✅ Page ID {page_id} has been written to appraisal_page_id.txt")

        return all_pages


from crewai_tools import BaseTool

class ReadFile(BaseTool):
    """
    Tool to Read txt file content.
    """

    file_path: str = "Specify the file_path of the txt file to read."
    description: str = (
        "Fetches the content of a txt file. Provide the file_path as an argument."
    )

    def _run(self) -> str:
        """
        Fetch content of a txt file.

        Returns:
            str: Content string or an error message.
        """
        try:
            # Ensure the file path is provided
            if not self.file_path or self.file_path == "Specify the file_path of the txt file to read.":
                return "Error: No valid file_path provided."

            # Open and read the file content
            with open(self.file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            return content

        except FileNotFoundError:
            return f"Error: File not found at {self.file_path}."
        except Exception as e:
            return f"Error: An unexpected error occurred: {str(e)}"
