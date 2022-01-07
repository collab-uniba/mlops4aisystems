import calendar
import json
import logging
import queue
import re
import threading
import time
from datetime import datetime
from pathlib import Path

from github import Github
from github.GithubException import UnknownObjectException
from models import GitHubSlug
from rich.progress import BarColumn, Progress, TaskID, TimeRemainingColumn
from ruamel.yaml import YAML


class GitHubScraper:
    """Base class for scraping GitHub repositories."""

    def __init__(
        self, token_list: list[str], dumps_dir: Path, slugs: list[GitHubSlug]
    ) -> None:

        # Set up the dumps directory
        self.dumps_dir: Path = dumps_dir

        # Initialize scraping stats
        self.scraping_stats: dict = {
            "start_datetime": str(datetime.now()),
            "end_datetime": None,
        }

        # Initialize list of selected slugs
        self.selected_slugs: list[GitHubSlug] = []

        # Initialize multithreading
        self.token_list = token_list
        self.queue: queue.Queue = queue.Queue()

        self.slugs = slugs
        for slug in self.slugs:
            self.queue.put(slug)
        for _ in range(len(token_list)):
            self.queue.put(None)

    def _check_rate_limit(self, github: Github):
        """Check the rate limit of the Github API."""
        core_rate_limit = github.get_rate_limit().core
        if core_rate_limit.remaining <= 5:
            logging.info("Rate limit reached...")
            reset_timestamp = calendar.timegm(core_rate_limit.reset.timetuple())
            # add 5 seconds to be sure the rate limit has been reset)
            sleep_time = reset_timestamp - calendar.timegm(time.gmtime()) + 5
            logging.info(f"Sleeping for {sleep_time} seconds...")
            time.sleep(sleep_time)

    def _dump_scraping_results(self) -> None:
        """Dump scraping results to a JSON file.

        The output file will contain:

        - the scraping stats
        - the selected list of slugs

        The output file will be placed in a `DATA_DIR` subfolder called `dumps`.
        """

        # Define dump filename upon the name of the class that is dumped
        dump_path = self.dumps_dir / (self.__class__.__name__ + "_dump.json")

        # Prepare the dictionary to dump
        dump: dict = self.scraping_stats
        slug_list = [str(slug) for slug in self.selected_slugs]
        slug_dict = {"selected_slugs": slug_list}
        dump.update(slug_dict)

        # Write the dump to disk as a JSON file
        with open(dump_path, "w") as dump_file:
            json.dump(dump, dump_file, indent=4)


class DataScienceScraper(GitHubScraper):
    """Scraper for data science repositories.

    Extends: GitHubScraper
    """

    def __init__(
        self,
        token_list: list[str],
        dumps_dir: Path,
        keywords: list[str],
        slugs: list[GitHubSlug],
    ) -> None:
        super().__init__(token_list, dumps_dir, slugs)

        # Set filtering keywords
        self.KEYWORDS = keywords

        # Initialize scraping stats
        self.scraping_stats.update(
            {
                "repos_not_found": 0,
                "repos_with_keywords_in_topics": 0,
                "repos_with_keywords_in_description": 0,
                "selected_repos": 0,
            }
        )

        # Initialize progress bar
        self.progress: Progress = Progress(
            "[progress.description]{task.description}",
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%",
            "[progress.completed_ratio]{task.completed}/{task.total}",
            "[progress.selected_repos][bright_black]Selected: {task.fields[selected]}",
            TimeRemainingColumn(),
        )
        self.task: TaskID = self.progress.add_task(
            "Filtering GitHub Repos...", total=len(self.slugs), selected=0
        )

    def __str__(self) -> str:
        summary = "SUMMARY\n"
        summary += "  - Repositories with at least one matching keyword = "
        summary += f"{self.scraping_stats['selected_repos'] };\n"
        summary += "  - Repositories with matching keyword(s) in topics = "
        summary += f"{self.scraping_stats['repos_with_keywords_in_topics'] };\n"
        summary += "  - Repositories with matching keyword(s) in description = "
        summary += f"{self.scraping_stats['repos_with_keywords_in_description'] };\n"
        summary += "  - Repositories not found = "
        summary += f"{self.scraping_stats['repos_not_found'] }\n"

        return summary

    def _decide_on_repo(self, github: Github) -> None:
        """Decide whether each repo should be kept or excluded from the study.

        Target function to be run inside each thread.
        The scraper will run one instance of this function for each available
        GitHub token.
        """

        # Using the pattern suggested in this SO answer for queue termination:
        # https://stackoverflow.com/a/31905997/4178082
        while True:

            slug = self.queue.get()

            # `None` is used as a sentinel to mark the end of the queue
            if slug is None:
                self.queue.task_done()
                break

            # Check GitHub API rate limit: wait if needed
            self._check_rate_limit(github)

            try:
                repo = github.get_repo(str(slug))

                try:
                    topics = " ".join(repo.get_topics())
                except UnknownObjectException:
                    topics = ""
                description = repo.description or ""

                for keyword in self.KEYWORDS:
                    keywords_in_topics = re.search(keyword, topics, re.IGNORECASE)
                    keywords_in_description = re.search(
                        keyword, description, re.IGNORECASE
                    )
                    if keywords_in_topics or keywords_in_description:
                        self.selected_slugs.append(slug)
                        self.progress.console.log(
                            f':thumbs_up: Data science repo found: "{slug}".',
                        )

                        # Update scraping stats
                        if keywords_in_topics:
                            self.scraping_stats["repos_with_keywords_in_topics"] += 1
                        if keywords_in_description:
                            self.scraping_stats[
                                "repos_with_keywords_in_description"
                            ] += 1
                        self.scraping_stats["selected_repos"] += 1

            except UnknownObjectException:
                self.scraping_stats["repos_not_found"] += 1
                self.progress.console.log(
                    f':cross_mark: Repository not found: "{slug}".',
                )
            finally:
                self.progress.update(
                    self.task,
                    advance=1,
                    selected=self.scraping_stats["selected_repos"],
                )

            self.queue.task_done()

    def scrape_repos(self) -> list[GitHubSlug]:
        """Scrape GitHub repos for data science.

        Args:
            github (Github): main class of the PyGithub library
            slugs (list(GitHubSlug)): list of GitHub slugs

        Returns:
            list[GitHubSlug]: list of GitHub slugs with data science keywords
        """
        LOGGING_CONTEXT = "[Filtering slugs from RepoReaper] "

        # Start progress bar
        self.progress.start()

        # Spawn the threads (one for each GitHub token)
        for token in self.token_list:
            g = Github(token)
            threading.Thread(target=self._decide_on_repo, args=(g,)).start()

        # Block until all items in the queue have been gotten and processed
        self.queue.join()

        # Stop progress bar
        self.progress.stop()

        # Complete scraping_stats and dump the scraping results
        self.scraping_stats["end_datetime"] = str(datetime.now())
        self._dump_scraping_results()
        logging.info(LOGGING_CONTEXT + "Filtering completed.")
        logging.info(LOGGING_CONTEXT + str(self))
        return self.selected_slugs


class WorkflowScraper(GitHubScraper):
    """Scraper for GitHub repositories with Actions workflows.

    Extends: GitHubScraper
    """

    def __init__(
        self,
        token_list: list[str],
        dumps_dir: Path,
        data_dir: Path,
        slugs: list[GitHubSlug],
    ) -> None:
        super().__init__(token_list, dumps_dir, slugs)

        # Initialize scraping stats
        self.scraping_stats.update(
            {
                "repos_not_found": 0,
                "repos_with_at_least_one_workflow": 0,
                "total_number_of_workflows": 0,
                "total_number_of_valid_workflows": 0,  # Valid YAML file
                "total_number_of_invalid_workflows": 0,  # Invalid YAML file
            }
        )

        # Set up the data directory
        if not data_dir.exists:
            raise ValueError("The specified data directory does not exist.")
        if not data_dir.is_dir:
            raise ValueError("The specified data directory is not a folder.")
        else:
            self.data_dir = data_dir

        # Initialize progress bar
        self.progress: Progress = Progress(
            "[progress.description]{task.description}",
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%",
            "[progress.completed_ratio]{task.completed}/{task.total}",
            "[progress.with_workflows][bright_black]\
                W/ workflows: {task.fields[repos_with_workflows]}",
            "[progress.tot_workflows][bright_black]\
                Valid workflows: {task.fields[valid_workflows]}",
            TimeRemainingColumn(),
        )
        self.task: TaskID = self.progress.add_task(
            "Downloading workflows...",
            total=len(slugs),
            repos_with_workflows=0,
            valid_workflows=0,
        )

    def __str__(self) -> str:
        summary = "SUMMARY\n"
        summary += "  - Repositories with at least one workflow = "
        summary += f"{self.scraping_stats['repos_with_at_least_one_workflow'] };\n"
        summary += "  - Total number of workflows = "
        summary += f"{self.scraping_stats['total_number_of_workflows'] };\n"
        summary += "  - Total number of valid workflows (valid YAML) = "
        summary += f"{self.scraping_stats['total_number_of_valid_workflows'] };\n"
        summary += "  - Total number of invalid workflows (invalid YAML) = "
        summary += f"{self.scraping_stats['total_number_of_invalid_workflows'] };\n"
        summary += "  - Repositories not found = "
        summary += f"{self.scraping_stats['repos_not_found'] }\n"

        return summary

    def _download_repo_workflows(self, github: Github) -> None:
        """Downloads GitHub Actions workflows contained in a repository (if any)."""

        # Set up the yaml parser
        yaml_parser = YAML()

        # Using the pattern suggested in this SO answer for queue termination:
        # https://stackoverflow.com/a/31905997/4178082
        while True:

            slug = self.queue.get()

            # `None` is used as a sentinel to mark the end of the queue
            if slug is None:
                self.queue.task_done()
                break

            # Check GitHub API rate limit: wait if needed
            self._check_rate_limit(github)

            try:
                repo = github.get_repo(str(slug))

                try:
                    workflows = repo.get_contents(".github/workflows")

                    # Update scraping stats
                    self.selected_slugs.append(slug)
                    self.scraping_stats["repos_with_at_least_one_workflow"] += 1
                    self.scraping_stats["total_number_of_workflows"] += len(workflows)

                    # Download workflows
                    self.progress.console.log(
                        f':down_arrow: Downloading workflows from "{slug}"...',
                    )
                    local_repo_path = Path(
                        self.data_dir, slug.repo_owner, slug.repo_name
                    )
                    if not local_repo_path.exists():
                        local_repo_path.mkdir(parents=True)

                        for workflow in workflows:

                            workflow_filename = Path(workflow.path).name
                            local_workflow_path = local_repo_path / workflow_filename

                            try:
                                yaml_string = workflow.decoded_content.decode("utf8")
                                yaml_object = yaml_parser.load(yaml_string)
                                yaml_parser.dump(yaml_object, local_workflow_path)
                                self.scraping_stats[
                                    "total_number_of_valid_workflows"
                                ] += 1
                            except Exception as e:
                                self.scraping_stats[
                                    "total_number_of_invalid_workflows"
                                ] += 1
                                self.progress.console.log(
                                    f':cross_mark: Invalid YAML file: \
                                        "{workflow_filename}".\
                                            Exception: "{repr(e)}"',
                                )

                        self.progress.console.log(
                            f':thumbs_up: Downloaded workflows from "{slug}".',
                        )
                    else:
                        self.progress.console.log(
                            "Target directory already exists. Download canceled.",
                        )

                except UnknownObjectException:
                    self.progress.console.log(
                        f'No workflows found in "{slug}". Skipping...',
                    )

            except UnknownObjectException:
                self.scraping_stats["repos_not_found"] += 1
                self.progress.console.log(
                    f':cross_mark: Repository not found: "{slug}".',
                )
            finally:
                self.progress.update(
                    self.task,
                    advance=1,
                    repos_with_workflows=self.scraping_stats[
                        "repos_with_at_least_one_workflow"
                    ],
                    valid_workflows=self.scraping_stats[
                        "total_number_of_valid_workflows"
                    ],
                )

            self.queue.task_done()

    def scrape_repos(self) -> list[GitHubSlug]:
        """Scrape GitHub repos for GitHub Actions workflows.

        Args:
            github (Github): main class of the PyGithub library
            slugs (set(GitHubSlug)): set of GitHub slugs
        """
        LOGGING_CONTEXT = "[WorkflowScraper] "
        logging.info(LOGGING_CONTEXT + "Downloading workflows from selected slugs...")

        # Start progress bar
        self.progress.start()

        # Spawn the threads (one for each GitHub token)
        for token in self.token_list:
            g = Github(token)
            threading.Thread(target=self._download_repo_workflows, args=(g,)).start()

        # Block until all items in the queue have been gotten and processed
        self.queue.join()

        # Stop progress bar
        self.progress.stop()

        # Complete scraping_stats and dump the scraping results
        self.scraping_stats["end_datetime"] = str(datetime.now())
        self._dump_scraping_results()
        logging.info(LOGGING_CONTEXT + "Download completed.")
        logging.info(LOGGING_CONTEXT + str(self))
        return self.selected_slugs
