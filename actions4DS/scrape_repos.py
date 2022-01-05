import calendar
import time
from pathlib import Path
from typing import List

from github import Github
from github.GithubException import UnknownObjectException
from models import GitHubSlug
from ruamel.yaml import YAML
from tqdm import tqdm


class GitHubScraper:
    def __init__(self, token_list: List[str], data_dir: Path) -> None:

        # Set up the GitHub instance
        self.github = Github(token_list[0])

        # Set up the yaml parser
        self.yaml_parser = YAML()

        # Set up the data directory
        if not data_dir.exists:
            raise ValueError("The specified data directory does not exist.")
        if not data_dir.is_dir:
            raise ValueError("The specified data directory is not a folder.")
        else:
            self.data_dir = data_dir

        # Initialize scraping stats
        self.scraping_stats = {
            "repos_with_at_least_one_workflow": 0,
            "total_number_of_workflows": 0,
        }

    def _update_pbar_description(self, pbar):
        """Update the total number of workflows displayed in the progress bar."""
        pbar.set_description(
            f"Total workflows found = {self.scraping_stats['total_number_of_workflows']}"
        )

    def _check_rate_limit(self):
        """Check the rate limit of the Github API."""
        core_rate_limit = self.github.get_rate_limit().core
        if core_rate_limit.remaining <= 5:
            print("Rate limit reached...")
            reset_timestamp = calendar.timegm(core_rate_limit.reset.timetuple())
            # add 5 seconds to be sure the rate limit has been reset)
            sleep_time = reset_timestamp - calendar.timegm(time.gmtime()) + 5
            print(f"Sleeping for {sleep_time} seconds...")
            time.sleep(sleep_time)

    def scrape_repos(self, slugs: List[GitHubSlug]) -> None:
        """Scrape GitHub repos for GitHub Actions workflows.

        Args:
            github (Github): main class of the PyGithub library
            slugs (List(GitHubSlug)): list of GitHub slugs
        """

        pbar = tqdm(slugs)
        for slug in pbar:
            try:
                self._check_rate_limit()
                repo = self.github.get_repo(str(slug))
                workflows = repo.get_contents(".github/workflows")

                local_repo_path = Path(self.data_dir) / slug.repo_owner / slug.repo_name

                if not local_repo_path.exists():

                    local_repo_path.mkdir(parents=True)

                    for workflow in workflows:

                        workflow_filename = Path(workflow.path).name
                        local_workflow_path = local_repo_path / workflow_filename

                        yaml_string = workflow.decoded_content.decode("utf8")
                        yaml_object = self.yaml_parser.load(yaml_string)
                        self.yaml_parser.dump(yaml_object, local_workflow_path)

                # Update scraping stats
                self.scraping_stats["repos_with_at_least_one_workflow"] += 1
                self.scraping_stats["total_number_of_workflows"] += len(workflows)

            except UnknownObjectException:
                self._update_pbar_description(pbar)
            else:
                self._update_pbar_description(pbar)

        print(self)

    def __str__(self) -> str:
        summary = "\nSCRAPING SUMMARY\n"
        summary += "  - Repositories with at least one workflow = "
        summary += f"{self.scraping_stats['repos_with_at_least_one_workflow'] };\n"
        summary += "  - Total number of scraped workflows = "
        summary += f"{self.scraping_stats['total_number_of_workflows']}."

        return summary
