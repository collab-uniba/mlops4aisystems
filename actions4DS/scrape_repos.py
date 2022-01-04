import calendar
import time
from typing import List

from github import Github
from github.GithubException import UnknownObjectException
from models import GitHubSlug
from tqdm import tqdm


class GitHubScraper:
    def __init__(self, github_personal_access_token: str) -> None:
        self.github = Github(github_personal_access_token)
        self.scraping_stats = {
            "repos_with_at_least_one_workflow": 0,
            "total_number_of_workflows": 0,
        }

    def _update_pbar_description(self, pbar):
        pbar.set_description(
            f"Total workflows found = {self.scraping_stats['total_number_of_workflows']}"
        )

    def _check_rate_limit(self, g: Github):
        """Check the rate limit of the Github API.

        Args:
            g (Github): the Github API object.
        """
        core_rate_limit = g.get_rate_limit().core
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
                self._check_rate_limit(self.github)
                repo = self.github.get_repo(str(slug))
                contents = repo.get_contents(".github/workflows")

                # Update scraping stats
                self.scraping_stats["repos_with_at_least_one_workflow"] += 1
                self.scraping_stats["total_number_of_workflows"] += len(contents)

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
