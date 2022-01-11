import json
from pathlib import Path
from typing import OrderedDict

from config import DATA_DIR, DUMPS_DIR
from models import Action, GitHubSlug, RepoWithWorkflows, RunCommand, Workflow
from ruamel.yaml import YAML


class WorkflowAnalyzer:
    def __init__(self, data_dir: Path) -> None:
        self.DATA_DIR = data_dir

        yaml_parser = YAML(typ="safe", pure=True)

        for workflow_path in data_dir.glob("**/*.y*ml"):

            # Events
            workflow = yaml_parser.load(workflow_path)
            events_raw = workflow["on"]
            if type(events_raw) is dict:
                events = list(events_raw.keys())
            elif type(events_raw) is list:
                events = events_raw
            elif type(events_raw) is str:
                events = [events_raw]
            print(events)

    def analyze_workflows(self):
        pass


if __name__ == "__main__":

    w = WorkflowAnalyzer(DATA_DIR)
    w.analyze_workflows()
