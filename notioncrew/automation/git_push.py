import os
import subprocess
from datetime import datetime
from colorama import Fore, init, Back

init(autoreset=True)

from notioncrew.params import LOCAL_GIT_REPO


repo_path = LOCAL_GIT_REPO


def get_current_branch():
    """Returns the name of the current Git branch."""
    # Run the command 'git branch --show-current' and decode the output to get the current branch
    branch = (
        subprocess.check_output(["git", "branch", "--show-current"]).strip().decode()
    )
    return branch


def perform_git_operations(branch):
    # Print the git status
    print(f"{Fore.GREEN}[+] git status")
    subprocess.run(["git", "status", "."])

    # Add all the files in the current directory to the git repository
    print(f"{Fore.GREEN}[+] git add .")
    subprocess.run(["git", "add", "."])

    # Commit the changes with a timestamped message
    print(f"{Fore.GREEN}[+] git commit")
    current_timestamp = datetime.now()
    formatted_timestamp = current_timestamp.strftime("%Y-%m-%d %H:%M")
    message = f"Automated commit via Python script - {formatted_timestamp}"
    subprocess.run(["git", "commit", "-m", message])

    # Push the changes to the remote repository
    print(f"{Fore.GREEN}[+] git push origin {branch}")
    subprocess.run(["git", "push", "origin", branch])


def push_changes_to_github():
    os.chdir(repo_path)
    # Get the current branch
    current_branch = get_current_branch()

    # Pull the latest changes from the current branch of the remote repository
    print(f"{Fore.GREEN}[+] Pulling latest changes from origin/{current_branch}")
    subprocess.run(["git", "pull", "origin", current_branch])

    # Perform git operations (status, add, commit, push) on the current branch
    perform_git_operations(current_branch)


if __name__ == "__main__":
    push_changes_to_github()
