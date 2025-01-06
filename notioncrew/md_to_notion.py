from notionfier_main import append_markdown_to_notion_page
from notion_api.notionhelper import *


def create_new_notion_page(cpms_id):
    nh = NotionHelper()

    properties = {
        "Sponsor": {"title": [{"text": {"content": cpms_id}}]},
        "CPMS ID": {"rich_text": [{"text": {"content": cpms_id}}]},
    }

    response = nh.new_page_to_db(
        "16bfdfd68a978047b47dfe063a6a5407", page_properties=properties
    )
    return response["id"]


def read_md_file(file_path):
    # Get page content from MardDown File
    with open(file_path, "r", encoding="utf-8") as file:
        text_01 = file.read()

    # Check Format of downloaded Text
    text_01 = text_01.replace("```markdown", "").replace("```", "")

    return text_01


if __name__ == "__main__":
    notion_secret = "secret_AUqFdk1kzS6qe7iw0LVlPDQXJ1TrDxnM7n9ZIB5fOlB"
    notion_database_id = "16bfdfd68a978047b47dfe063a6a5407"
    new_page_id = create_new_notion_page(notion_database_id)

    md_files = [
        "01_the_study.md",
        "02_site_profile.md",
        "03_site_identification_questions.md",
        "04_submission_audit.md",
    ]

    for file in md_files:
        print(file)
        md_content = read_md_file(file)
        append_markdown_to_notion_page(notion_secret, new_page_id, md_content)
