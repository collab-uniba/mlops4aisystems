# Replication package for the CAIN 2022 experimentation

This is the replication package of the CAIN 2022 paper on the use of GitHub Actions in data science projects.

## Setup

Before running the scripts contained in this repository, you first need to create a `config.ini` file in the project root directory and populate it with the following entries:

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

To install the dependencies, run:

```shell
make install
```

## Execution

Open a poetry shell and then run the scripts as follows:

```shell
poetry shell
python actions4DS/main.py
```
