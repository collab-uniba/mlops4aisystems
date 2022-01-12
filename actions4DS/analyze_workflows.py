import re
from collections import Counter
from pathlib import Path
from typing import Optional

import pandas as pd
from config import DATA_DIR
from mlxtend import frequent_patterns
from mlxtend.frequent_patterns import apriori
from mlxtend.preprocessing import TransactionEncoder
from models import GitHubSlug
from rich import print
from ruamel.yaml import YAML


class Action:
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

        self.docker_related = self._is_docker_related()

    def asdict(self) -> dict:
        return {
            "action_slug": self.slug,
            "action_name": self.name,
            "action_slug_noTag": self.slug_without_tag,
            "action_tag": self.tag,
            "docker_related_action": self.docker_related,
        }

    def __repr__(self) -> str:
        return f'Action("{self.slug}")'

    def __str__(self) -> str:
        return self.slug

    def _is_docker_related(self) -> bool:
        return True if re.search("docker", self.slug, re.IGNORECASE) else False


class RunCommand:
    def __init__(self, command: str) -> None:
        self.command: str = command
        self.docker_related: bool = self._is_docker_related()
        self.docker_commands: list[str] = (
            self._get_docker_commands() if self.docker_related else []
        )

    def asdict(self) -> dict:
        return {
            "docker_related_run_command": self.docker_related,
            "docker_commands": self.docker_commands,
        }

    def _is_docker_related(self) -> bool:
        return True if re.search("docker", self.command, re.IGNORECASE) else False

    def _get_docker_commands(self) -> list[str]:
        return re.findall(
            r"docker(?: --?\S*)* (\S*) .*",
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
        self.docker_commands: Counter = Counter()
        for run_command in self.commands:
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
            "docker_related_actions": any([a.docker_related for a in self.actions]),
            "n_of_run_commands": len(self.commands),
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

        # FREQUENT PATTERN MINING
        # Actions
        self.frequent_actions_df = self._get_frequently_cooccurring_actions(
            support=0.05, include_tags=True
        )
        self.frequent_actions_noTags_df = self._get_frequently_cooccurring_actions(
            support=0.05, include_tags=False
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


if __name__ == "__main__":
    wa = WorkflowAnalyzer(DATA_DIR)

    workflows_df = pd.DataFrame.from_records(
        [workflow.asdict() for workflow in wa.workflows]
    )
