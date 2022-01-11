import re
from collections import Counter
from pathlib import Path
from typing import Optional

import pandas as pd
from config import DATA_DIR
from models import GitHubSlug
from rich import print
from ruamel.yaml import YAML


class Action:
    def __init__(
        self,
        slug: str,
    ) -> None:
        self.slug = slug
        self.docker_related = self._is_docker_related()

    @property
    def owner(self) -> str:
        owner, _ = self.slug.split("/")
        return owner

    @property
    def name(self) -> str:
        _, name_with_tag = self.slug.split("/")
        try:
            name, _ = name_with_tag.split("@")
        except ValueError:
            name = name_with_tag
        return name

    @property
    def tag(self) -> str:
        _, name_with_tag = self.slug.split("/")
        try:
            _, tag = name_with_tag.split("@")
        except ValueError:
            tag = ""
        return tag

    def asdict(self) -> dict:
        return {"action_slug": self.slug, "docker_related_action": self.docker_related}

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


if __name__ == "__main__":
    wa = WorkflowAnalyzer(DATA_DIR)

    workflows_df = pd.DataFrame.from_records(
        [workflow.asdict() for workflow in wa.workflows]
    )

    print(workflows_df)
