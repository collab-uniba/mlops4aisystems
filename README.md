# Replication package for the EMSE 2022 paper 

This is the replication package of the EMSE 2022 NIER track paper "A Preliminary Analysis of CI/CD for AI-enabled systems".

## Setup

Before running the scripts contained in this repository, you first need to create an `env.ini` file in the project root directory and populate it with the following entries:

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
DUMPS_DIR = path/to/dumps/dir
```

To install the dependencies, open a Poetry shell session and run:

```shell
poetry shell
make install
```

## Execution

Within an active Poetry shell session, run the scripts as follows:

```shell
python actions4DS/main.py
python actions4DS/analyze_workflows.py
```
