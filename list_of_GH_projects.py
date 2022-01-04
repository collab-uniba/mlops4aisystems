import requests
import re
import os
from tqdm import tqdm
from github import Github
from github.GithubException import UnknownObjectException

# Download `info.txt` form the paper's GitHub repository (boalang/MSR19-DataShowcase)
URL = "https://raw.githubusercontent.com/boalang/MSR19-DataShowcase/master/info.txt"
r = requests.get(URL)
lines = r.text.splitlines()
regex = re.compile("^lib\[(.*)\] = (.*)$")
slugs = [match.group(1) for line in lines if (match := regex.match(line))]

personal_access_token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
g = Github(personal_access_token)

repos_with_workflow = 0
total_number_of_workflows = 0
pbar = tqdm(slugs)
for slug in pbar:
    try:
        contents = g.get_repo(slug).get_contents(".github/workflows")
        pbar.set_description(f"Total workflows found = {total_number_of_workflows}")
        repos_with_workflow += 1
        total_number_of_workflows += len(contents)
    except UnknownObjectException:
        pbar.set_description(f"Total workflows found = {total_number_of_workflows}")

print("Repos with at least one workflow =", repos_with_workflow)
print("Total number of workflows =", total_number_of_workflows)
