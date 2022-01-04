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
make install
```

## Execution

Open a poetry shell and then run the scripts as follows:

```shell
poetry shell
python actions4DS/main.py
```
