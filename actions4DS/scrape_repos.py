import calendar
import json
import logging
import queue
import re
import threading
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path

from github import Github
from github.GithubException import UnknownObjectException
from models import GitHubSlug
from rich.progress import BarColumn, Progress, TaskID, TimeRemainingColumn
from ruamel.yaml import YAML


class GitHubScraper:
    """Base class for scraping GitHub repositories."""

    def __init__(
        self,
        experiment_settings: dict,
        token_list: list[str],
        dumps_dir: Path,
        slugs: list[GitHubSlug],
    ) -> None:

        # Set up the experiment settings
        self.experiment_settings = experiment_settings

        # Set up the dumps directory
        self.dumps_dir: Path = dumps_dir

        # Initialize scraping stats
        self.scraping_stats: dict = {
            "start_datetime": str(datetime.now()),
            "end_datetime": None,
        }

        # Initialize list of selected slugs
        self.selected_slugs: list[GitHubSlug] = []

        # Define dump filename upon the name of the class that produces it
        # and the current date
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.dump_path = self.dumps_dir / (
            current_time + "_" + self.__class__.__name__ + "_dump.json"
        )

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
            logging.info("Resuming after sleep...")

    def _dump_scraping_results(self) -> None:
        """Dump scraping results to a JSON file.

        The output file will contain:

        - the experiment settings
        - the scraping stats
        - the list of selected slugs

        The output file will be placed in `DUMPS_DIR/`.
        """
        # Prepare the dictionary to dump
        dump: dict = {}
        dump.update({"experiment_settings": self.experiment_settings})
        dump.update({"scraping_stats": self.scraping_stats})
        slug_list = [str(slug) for slug in self.selected_slugs]
        dump.update({"selected_slugs": slug_list})

        # Write the dump to disk as a JSON file
        with open(self.dump_path, "w") as dump_file:
            json.dump(dump, dump_file, indent=4)


class DataScienceScraper(GitHubScraper):
    """Scraper for data science repositories.

    INCLUSION CRITERIA
    - The last commit in the repo must have been done `self.OFFSET_MONTHS` past
      the release date of GitHub Actions.
    - The description or the topics of the repo must contain at least one of
      the keywords in `self.KEYWORDS`

    Extends: GitHubScraper
    """

    def __init__(
        self,
        experiment_settings: dict,
        token_list: list[str],
        dumps_dir: Path,
        slugs: list[GitHubSlug],
    ) -> None:
        super().__init__(experiment_settings, token_list, dumps_dir, slugs)

        # Set GitHub Actions release date and offset months
        self.gh_actions_release_condition: bool = self.experiment_settings[
            "githubActionsReleaseCondition"
        ]
        if self.gh_actions_release_condition:
            GITHUB_ACTIONS_RELEASE_DATE: datetime = datetime(2019, 11, 1)
            OFFSET_MONTHS: int = int(
                self.experiment_settings["githubActionsRelease-offset-months"]
            )
            self.ACCEPTANCE_DATE = GITHUB_ACTIONS_RELEASE_DATE + timedelta(
                days=(OFFSET_MONTHS * 30)
            )

        # Set filtering keywords
        self.KEYWORDS: list[str] = self.experiment_settings["keywords"]

        # Initialize scraping stats
        self.scraping_stats.update(
            {
                "repos_not_available": 0,
                "repos_inactive_before_GHA_release": 0,
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
        summary += "  - Selected repositories = "
        summary += f"{self.scraping_stats['selected_repos'] };\n"
        summary += "  - Repositories inactive before GitHub Actions release = "
        summary += f"{self.scraping_stats['repos_inactive_before_GHA_release'] };\n"
        summary += "  - Repositories not found = "
        summary += f"{self.scraping_stats['repos_not_available'] }\n"

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

            try:

                # Check GitHub API rate limit: wait if needed
                self._check_rate_limit(github)

                try:
                    repo = github.get_repo(str(slug))  # API request (+1)

                    if self.gh_actions_release_condition:
                        # Decide based on last-commit date
                        is_last_commit_date_ok = False
                        commits = repo.get_commits(since=self.ACCEPTANCE_DATE)

                        try:
                            commits[0]  # API request (+1)
                            is_last_commit_date_ok = True
                        except IndexError:
                            self.scraping_stats[
                                "repos_inactive_before_GHA_release"
                            ] += 1
                            self.progress.console.log(
                                f':cross_mark: Repo inactive before GHA release: "{slug}".',
                            )

                    if (
                        not self.gh_actions_release_condition
                    ) or is_last_commit_date_ok:

                        # Decide based on keywords presence in repo topics or description
                        try:
                            topics = " ".join(repo.get_topics())  # API request (+1)
                        except UnknownObjectException:
                            topics = ""
                        description = repo.description or ""

                        keyword_found = False
                        for keyword in self.KEYWORDS:
                            keyword_in_topics = re.search(
                                keyword, topics, re.IGNORECASE
                            )
                            keyword_in_description = re.search(
                                keyword, description, re.IGNORECASE
                            )
                            if keyword_in_topics or keyword_in_description:
                                keyword_found = True
                                break

                        if keyword_found:
                            self.selected_slugs.append(slug)
                            self.progress.console.log(
                                f':thumbs_up: Data science repo found: "{slug}".',
                            )
                            self.scraping_stats["selected_repos"] += 1
                            self._dump_scraping_results()

                except Exception:
                    self.scraping_stats["repos_not_available"] += 1
                    self.progress.console.log(
                        f':cross_mark: Repository not available: "{slug}".',
                    )
                finally:
                    self.progress.update(
                        self.task,
                        advance=1,
                        selected=self.scraping_stats["selected_repos"],
                    )
            except Exception:
                logging.info("THREAD_EXCEPTION")
                logging.info(traceback.format_exc())
                time.sleep(10)
            finally:
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
        experiment_settings: dict,
        token_list: list[str],
        dumps_dir: Path,
        data_dir: Path,
        slugs: list[GitHubSlug],
    ) -> None:
        super().__init__(experiment_settings, token_list, dumps_dir, slugs)

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

            try:

                # Check GitHub API rate limit: wait if needed
                self._check_rate_limit(github)

                try:
                    repo = github.get_repo(str(slug))

                    try:
                        workflows = repo.get_contents(".github/workflows")

                        # Update scraping stats
                        self.selected_slugs.append(slug)

                        # Download workflows
                        self.progress.console.log(
                            f':down_arrow: Downloading workflows from "{slug}"...',
                        )
                        local_repo_path = Path(
                            self.data_dir, slug.repo_owner, slug.repo_name
                        )
                        if not local_repo_path.exists():
                            local_repo_path.mkdir(parents=True)

                            number_of_workflows_in_current_repo = 0
                            for workflow in workflows:

                                workflow_path = Path(workflow.path)
                                if workflow_path.suffix in [".yml", ".yaml"]:

                                    self.scraping_stats[
                                        "total_number_of_workflows"
                                    ] += 1
                                    number_of_workflows_in_current_repo += 1

                                    try:
                                        workflow_filename = workflow_path.name
                                        local_workflow_path = (
                                            local_repo_path / workflow_filename
                                        )
                                        yaml_string = workflow.decoded_content.decode(
                                            "utf8"
                                        )
                                        yaml_object = yaml_parser.load(yaml_string)
                                        yaml_parser.dump(
                                            yaml_object, local_workflow_path
                                        )
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
                            if number_of_workflows_in_current_repo > 0:
                                self.scraping_stats[
                                    "repos_with_at_least_one_workflow"
                                ] += 1

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
                except Exception:
                    self.scraping_stats["repos_not_found"] += 1
                    self.progress.console.log(
                        f':cross_mark: Error while accessing the repo: "{slug}".',
                    )
                    self.progress.console.log(traceback.format_exc())
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
            except Exception:
                logging.info("THREAD_EXCEPTION")
                logging.info(traceback.format_exc())
                time.sleep(10)
            finally:
                self.queue.task_done()

    def scrape_repos(self) -> list[GitHubSlug]:
        """Scrape GitHub repos.

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
