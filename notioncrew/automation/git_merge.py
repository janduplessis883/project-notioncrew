import os
import subprocess
from datetime import datetime
from colorama import Fore, init

init(autoreset=True)

from notioncrew.params import LOCAL_GIT_REPO

repo_path = LOCAL_GIT_REPO

def get_current_branch():
    """Returns the name of the current Git branch."""
    # Run the command 'git branch --show-current' to get the current branch name
    branch = (
        subprocess.check_output(["git", "branch", "--show-current"]).strip().decode()
    )
    return branch


def do_git_merge():
    # Change the current working directory to the path of the local Git repository
    os.chdir(repo_path)
    # Get the name of the current branch
    current_branch = get_current_branch()

    # Check if the current branch is 'master'
    if current_branch == "master":
        # Perform Git operations for 'master' branch
        perform_git_operations("master")
    else:
        # Perform Git operations for the current branch
        perform_git_operations(current_branch)
        # Pull the latest changes from 'master' before merging
        subprocess.run(["git", "checkout", "master"])
        print(f"{Fore.BLUE}[+] Pulling latest changes from master")
        subprocess.run(["git", "pull", "origin", "master"])
        # Merge the current branch into 'master'
        print(f"{Fore.BLUE}[+] Merging {current_branch} into master")
        subprocess.run(["git", "merge", current_branch])
        # Push the merged changes to 'master'
        print(f"{Fore.BLUE}[+] Pushing merged changes to master")
        subprocess.run(["git", "push", "origin", "master"])
        # Switch back to the original branch
        print(f"{Fore.BLUE}[+] Switching back to {current_branch}")
        subprocess.run(["git", "checkout", current_branch])


def perform_git_operations(branch):
    # Display the status of the Git repository
    print(f"{Fore.RED}[+] git status")
    subprocess.run(["git", "status", "."])

    # Add all changes to the Git repository
    print(f"{Fore.RED}[+] git add .")
    subprocess.run(["git", "add", "."])

    # Commit the changes with a timestamp
    print(f"{Fore.RED}[+] git commit")
    current_timestamp = datetime.now()
    formatted_timestamp = current_timestamp.strftime("%Y-%m-%d %H:%M")
    message = f"Automated commit via Python script - {formatted_timestamp}"
    subprocess.run(["git", "commit", "-m", message])

    # Push the changes to the remote repository
    print(f"{Fore.RED}[+] git push origin {branch}")
    subprocess.run(["git", "push", "origin", branch])


if __name__ == "__main__":
    # Execute the do_git_merge function when the script is run directly
    do_git_merge()
