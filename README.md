# Replication package for the CAIN 2022 experimentation

This is the replication package of the CAIN 2022 paper on the use of GitHub Actions in data science projects.

## Setup

Before running the scripts contained in this repository, you first need to create a `.env` file in the project root directory and populate it with the following entries.

```shell
GITHUB_PERSONAL_ACCESS_TOKEN=<your-personal-GitHub-access-token>
DATA_DIR=<data/directory/path>
```

To install the dependencies, run:

```shell
poetry install
```

## Execution

Open a poetry shell and then run the scripts as follows:

```ini
[GITHUB]
TOKEN_LIST = [
        "faketoken1",
        "faketoken2",
        "faketoken3",
        "faketoken4",
        "faketoken5",
    ]

[PATHS]
DATA_DIR = path/to/data/dir
LOGS_DIR = path/to/logs/dir
```
