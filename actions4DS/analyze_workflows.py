import re
from collections import Counter
from pathlib import Path
from typing import Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup
from config import DATA_DIR, DUMPS_DIR
from mlxtend.frequent_patterns import apriori
from mlxtend.preprocessing import TransactionEncoder
from models import GitHubSlug
from rich import print
from ruamel.yaml import YAML


class Action:

    scraping_cache: dict = {}
    BASE_GITHUB_URL: str = "https://github.com"

    def __init__(
        self,
        slug: str,
    ) -> None:
        # Slug validation
        regex = re.compile(r"^(.*\/([^@\n]*))(@.*)?$")
        match = regex.match(slug)
        if match:
            self.slug = slug
        else:
            raise ValueError("Invalid action slug.")

        self.name = match.group(2)
        self.slug_without_tag = match.group(1)
        self.tag = match.group(3)

        self.cml_related = self._is_cml_related()
        self.docker_related = self._is_docker_related()

        self.parsed_marketplace_page: Optional[
            BeautifulSoup
        ] = self._get_parsed_marketplace_page()

        self.is_from_verified_creator = None
        self.categories = None
        if self.parsed_marketplace_page:
            self.is_from_verified_creator = self._is_from_verified_creator()
            self.categories = self._get_action_categories()

    def asdict(self) -> dict:
        return {
            "action_slug": self.slug,
            "action_name": self.name,
            "action_slug_noTag": self.slug_without_tag,
            "action_tag": self.tag,
            "cml_related_action": self.cml_related,
            "docker_related_action": self.docker_related,
            "available_in_marketplace": True if self.parsed_marketplace_page else False,
            "from_verified_creator": True if self.is_from_verified_creator else False,
            "category_1": self.categories[0] if self.categories else None,
            "category_2": self.categories[1]
            if self.categories and len(self.categories) > 1
            else None,
        }

    def __repr__(self) -> str:
        return f'Action("{self.slug}")'

    def __str__(self) -> str:
        return self.slug

    def _is_cml_related(self) -> bool:
        return True if re.search("cml", self.slug, re.IGNORECASE) else False

    def _is_docker_related(self) -> bool:
        return True if re.search("docker", self.slug, re.IGNORECASE) else False

    def _get_parsed_marketplace_page(self) -> Optional[BeautifulSoup]:

        cache = self.scraping_cache.get(self.slug_without_tag)
        if cache:
            if cache["available_in_marketplace"]:
                return cache["parsed_html"]
            else:
                return None
        else:
            URL = self.BASE_GITHUB_URL + "/" + self.slug_without_tag

            try:
                page = requests.get(URL)
                if page.status_code != 200:
                    raise Exception("GitHub repo not found.")
                repo_page_html = BeautifulSoup(page.content, "html.parser")
                view_on_marketplace_btn = repo_page_html.find(
                    "a", string="View on Marketplace"
                )
                if view_on_marketplace_btn:
                    marketplace_ref = view_on_marketplace_btn["href"]

                URL = self.BASE_GITHUB_URL + marketplace_ref
                page = requests.get(URL)
                if page.status_code != 200:
                    raise Exception("Marketplace page not found.")
                parsed_html = BeautifulSoup(page.content, "html.parser")
                self.scraping_cache.update(
                    {
                        self.slug_without_tag: {
                            "available_in_marketplace": True,
                            "parsed_html": parsed_html,
                            "from_verified_creator": None,
                            "categories": None,
                        }
                    }
                )
                return parsed_html
            except Exception:
                self.scraping_cache.update(
                    {
                        self.slug_without_tag: {
                            "available_in_marketplace": False,
                            "parsed_html": None,
                            "from_verified_creator": None,
                            "categories": None,
                        }
                    }
                )
                return None

    def _is_from_verified_creator(self) -> bool:
        cache = self.scraping_cache[self.slug_without_tag]["from_verified_creator"]
        if cache:
            return cache
        else:
            res = (
                True
                if self.parsed_marketplace_page
                and self.parsed_marketplace_page.find_all(
                    "svg", class_="octicon-verified"
                )
                else False
            )
            self.scraping_cache[self.slug_without_tag]["from_verified_creator"] = res
            return res

    def _get_action_categories(self) -> Optional[tuple]:
        cache = self.scraping_cache[self.slug_without_tag]["categories"]
        if cache:
            return cache
        elif self.parsed_marketplace_page:
            res = tuple(
                c.text.strip()
                for c in self.parsed_marketplace_page.find_all("a", class_="topic-tag")
            )
            self.scraping_cache[self.slug_without_tag]["categories"] = res
            return res
        else:
            return None


class RunCommand:
    def __init__(self, command: str) -> None:
        self.command: str = command

        self.cml_related: bool = self._is_cml_related()
        self.cml_commands: list[str] = (
            self._get_cml_commands() if self.cml_related else []
        )

        self.docker_related: bool = self._is_docker_related()
        self.docker_commands: list[str] = (
            self._get_docker_commands() if self.docker_related else []
        )

    def asdict(self) -> dict:
        return {
            "cml_related_run_command": self.cml_related,
            "cml_commands": self.cml_commands,
            "docker_related_run_command": self.docker_related,
            "docker_commands": self.docker_commands,
        }

    def _is_cml_related(self) -> bool:
        return True if re.search("cml", self.command, re.IGNORECASE) else False

    def _get_cml_commands(self) -> list[str]:
        return re.findall(
            r"cml[ -]([^ \n]*)([ -].*)?",
            self.command,
            re.IGNORECASE,
        )

    def _is_docker_related(self) -> bool:
        return True if re.search("docker", self.command, re.IGNORECASE) else False

    def _get_docker_commands(self) -> list[str]:
        return re.findall(
            r"docker(?: --?\S*)* (\S*) .*",
            self.command,
            re.IGNORECASE,
        )

    def _is_dvc_related(self) -> bool:
        return True if re.search("dvc", self.command, re.IGNORECASE) else False

    def _get_dvc_commands(self) -> list[str]:
        return re.findall(
            r"dvc(?: --?\S*)* (\S*) .*",
            self.command,
            re.IGNORECASE,
        )


class Workflow:
    def __init__(self, data_dir: Path, local_path: Path) -> None:
        self._data_dir: Path = data_dir
        self._local_path: Path = local_path

        self._yaml: dict = self._parse_yaml()

        self.name: Optional[str] = self._yaml.get("name")
        self.events: list[str] = self._get_triggering_events()

        raw_actions, raw_commands = self._get_raw_components()
        self.actions: list[Action] = [Action(a) for a in raw_actions]
        self.commands: list[RunCommand] = [RunCommand(c) for c in raw_commands]
        self.cml_commands: Counter = Counter()
        self.docker_commands: Counter = Counter()
        for run_command in self.commands:
            self.cml_commands.update(run_command.cml_commands)
            self.docker_commands.update(run_command.docker_commands)

    @property
    def filename(self) -> str:
        return self._local_path.name

    @property
    def repository(self) -> GitHubSlug:
        relative_path: Path = self._local_path.relative_to(str(self._data_dir))
        repo_slug_string: Path = relative_path.parent

        return GitHubSlug(str(repo_slug_string))

    def asdict(self) -> dict:
        d = {
            "repository": str(self.repository),
            "filename": self.filename,
            "name": self.name,
            "trigger_events": self.events,
            "n_of_actions": len(self.actions),
            "cml_related_actions": any([a.cml_related for a in self.actions]),
            "docker_related_actions": any([a.docker_related for a in self.actions]),
            "n_of_run_commands": len(self.commands),
            "cml_related_commands": any([c.cml_related for c in self.commands]),
            "cml_commands": list(self.cml_commands.keys()),
            "docker_related_commands": any([c.docker_related for c in self.commands]),
            "docker_commands": list(self.docker_commands.keys()),
        }
        return d

    def __repr__(self) -> str:
        return f'Workflow("{str(self._local_path)}")'

    def __str__(self) -> str:
        return str(self._local_path.relative_to(self._data_dir))

    def _parse_yaml(self) -> dict:
        yaml_parser = YAML(typ="safe", pure=True)
        return yaml_parser.load(self._local_path)

    def _get_triggering_events(self) -> list[str]:
        events_raw = self._yaml["on"]
        if type(events_raw) is dict:
            events = list(events_raw.keys())
        elif type(events_raw) is list:
            events = events_raw
        elif type(events_raw) is str:
            events = [events_raw]
        return events

    def _get_raw_components(self) -> tuple[list[str], list[str]]:
        actions = []
        run_commands = []

        for job in self._yaml["jobs"].keys():
            for step in self._yaml["jobs"][job]["steps"]:
                action = step.get("uses")
                if action:
                    action = str(action)
                    actions.append(action)

                run_command = step.get("run")
                if run_command:
                    run_command = str(run_command)
                    run_commands.append(run_command)

        return actions, run_commands


class WorkflowAnalyzer:
    def __init__(self, data_dir: Path) -> None:

        self.workflows: list[Workflow] = []

        for workflow_path in data_dir.glob("**/*.y*ml"):
            self.workflows.append(Workflow(data_dir, workflow_path))

        # DATAFRAMES
        # Workflows
        self.workflows_df = pd.DataFrame.from_records(
            [workflow.asdict() for workflow in self.workflows]
        )

        # Actions
        dataset_actions = []
        for workflow in self.workflows:
            workflow_actions = []
            for action in workflow.actions:
                action_dict = action.asdict()
                action_dict["workflow"] = str(workflow)
                workflow_actions.append(action_dict)
            dataset_actions.extend(workflow_actions)
        self.actions_df = pd.DataFrame.from_records(dataset_actions)

        # FREQUENT PATTERN MINING
        # Actions
        self.frequent_actions_df = self._get_frequently_cooccurring_actions(
            support=0.05, include_tags=True
        )
        self.frequent_actions_noTags_df = self._get_frequently_cooccurring_actions(
            support=0.05, include_tags=False
        )

        # CML commands
        self.frequent_cml_commands_subsample_df = (
            self._get_frequently_cooccurring_cml_commands(
                support=0.05, include_workflows_without_cml_commands=False
            )
        )

        # Docker commands
        self.frequent_docker_commands_subsample_df = (
            self._get_frequently_cooccurring_docker_commands(
                support=0.05, include_workflows_without_docker_commands=False
            )
        )

    def _mine_frequent_patterns(
        self, transactions_df: pd.DataFrame, support: float
    ) -> pd.DataFrame:
        te = TransactionEncoder()
        encoding = te.fit(transactions_df).transform(transactions_df)
        encoding_df = pd.DataFrame(encoding, columns=te.columns_)
        frequent_itemsets = apriori(encoding_df, min_support=support, use_colnames=True)
        frequent_itemsets["length"] = frequent_itemsets["itemsets"].apply(
            lambda x: len(x)
        )
        return frequent_itemsets

    def _get_frequently_cooccurring_actions(
        self, support: float, include_tags: bool = True
    ) -> pd.DataFrame:
        actions_per_workflow = []
        if include_tags:
            for workflow in self.workflows:
                actions_per_workflow.append(
                    [action.slug for action in workflow.actions]
                )
        else:
            for workflow in self.workflows:
                actions_per_workflow.append(
                    [action.slug_without_tag for action in workflow.actions]
                )
        return self._mine_frequent_patterns(actions_per_workflow, support=support)

    def _get_frequently_cooccurring_docker_commands(
        self, support: float, include_workflows_without_docker_commands: bool = True
    ) -> pd.DataFrame:
        docker_commands_per_workflow = []
        for workflow in self.workflows:
            workflow_docker_commands = workflow.docker_commands.keys()
            if (
                include_workflows_without_docker_commands
                or len(workflow_docker_commands) > 0
            ):
                docker_commands_per_workflow.append(workflow_docker_commands)
        return self._mine_frequent_patterns(docker_commands_per_workflow, support)

    def _get_frequently_cooccurring_cml_commands(
        self, support: float, include_workflows_without_cml_commands: bool = True
    ) -> pd.DataFrame:
        cml_commands_per_workflow = []
        for workflow in self.workflows:
            workflow_cml_commands = workflow.cml_commands.keys()
            if include_workflows_without_cml_commands or len(workflow_cml_commands) > 0:
                cml_commands_per_workflow.append(workflow_cml_commands)
        return self._mine_frequent_patterns(cml_commands_per_workflow, support)


if __name__ == "__main__":
    wa = WorkflowAnalyzer(DATA_DIR)

    # Serializing dataframes
    wa.workflows_df.to_pickle(str(DUMPS_DIR / "workflows_df.pkl"))
    wa.actions_df.to_pickle(str(DUMPS_DIR / "actions_df.pkl"))
    wa.frequent_actions_df.to_pickle(str(DUMPS_DIR / "frequent_actions_df.pkl"))
    wa.frequent_actions_noTags_df.to_pickle(
        str(DUMPS_DIR / "frequent_actions_noTags_df.pkl")
    )
    wa.frequent_cml_commands_subsample_df.to_pickle(
        str(DUMPS_DIR / "frequent_cml_commands_subsample_df.pkl")
    )
    wa.frequent_docker_commands_subsample_df.to_pickle(
        str(DUMPS_DIR / "frequent_docker_commands_subsample_df.pkl")
    )

    print("Done.")
