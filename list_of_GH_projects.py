import os
from dotenv import load_dotenv
from tqdm import tqdm
from github import Github
from github.GithubException import UnknownObjectException
from get_repo_list import get_repos_from_boa_dataset

# Load environment variables from .env file
load_dotenv()
GITHUB_PERSONAL_ACCESS_TOKEN = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")

slugs = get_repos_from_boa_dataset()

g = Github(GITHUB_PERSONAL_ACCESS_TOKEN)

repos_with_workflow = 0
total_number_of_workflows = 0
pbar = tqdm(slugs)
for slug in pbar:
    try:
        contents = g.get_repo(str(slug)).get_contents(".github/workflows")
        pbar.set_description(f"Total workflows found = {total_number_of_workflows}")
        repos_with_workflow += 1
        total_number_of_workflows += len(contents)
    except UnknownObjectException:
        pbar.set_description(f"Total workflows found = {total_number_of_workflows}")

print("Repos with at least one workflow =", repos_with_workflow)
print("Total number of workflows =", total_number_of_workflows)
