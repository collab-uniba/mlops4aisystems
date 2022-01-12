"""
Generate a list of GitHub repositories containing data science projects.
"""

import logging
import re
from pathlib import Path

import pandas as pd
import requests
from models import GitHubSlug
from scrape_repos import DataScienceScraper


# Method 1
# Get repositories from the dataset: “Boa Meets Python: A Boa Dataset of
# Data Science Software in Python Language”
def get_repos_from_boa_dataset() -> list[GitHubSlug]:
    """Get the list of repo slugs from the "Boa Meets Python" dataset.

    In [1], Biswas et al. present a dataset of 1,558 mature data science projects
    from GitHub, written in the Python programming language.

    The list of GitHub projects referenced in the dataset is available in the paper's
    [companion repository](https://github.com/boalang/MSR19-DataShowcase/),
    in the `info.txt` file specifically.

    This funcion downloads `info.txt` and returns the list of repository slugs,
    extracted by means of a regular expression.

    [1]S. Biswas, M. J. Islam, Y. Huang, and H. Rajan,
    “Boa Meets Python: A Boa Dataset of Data Science Software in Python Language,”
    in 2019 IEEE/ACM 16th International Conference on Mining Software Repositories
    (MSR), Montreal, QC, Canada, May 2019, pp. 577–581. doi: 10.1109/MSR.2019.00086.

    Returns:
        list: the list of GitHub slugs for the projects referenced in the
            "Boa Meets Python" dataset [1].
    """

    LOGGING_CONTEXT = "[Getting slugs from Boa] "

    URL = "https://raw.githubusercontent.com/boalang/MSR19-DataShowcase/master/info.txt"
    logging.info(LOGGING_CONTEXT + f"Downloading {URL}...")
    r = requests.get(URL)
    logging.info(LOGGING_CONTEXT + "Download completed.")

    lines = r.text.splitlines()
    regex = re.compile(r"^lib\[(.*)\] = (.*)$")
    slugs = [
        GitHubSlug(match.group(1)) for line in lines if (match := regex.match(line))
    ]
    logging.info(
        LOGGING_CONTEXT + f"Slug extraction completed, total slugs: {len(slugs)}."
    )
    return slugs


def _filter_datascience_repos(
    experiment_settings: dict,
    token_list: list[str],
    dumps_dir: Path,
    all_slugs: list[GitHubSlug],
) -> list[GitHubSlug]:
    """Filter the list of GitHub slugs to only include data science repositories.

    Args:
        token_list (list[str]): list of GitHub API tokens
        all_slugs (list[GitHubSlug]): list of GitHub slugs

    Returns:
        list : the list of GitHub slugs for data science repositories
    """
    ds_scraper = DataScienceScraper(
        experiment_settings, token_list, dumps_dir, all_slugs
    )
    slugs = ds_scraper.scrape_repos()
    return slugs


def get_repos_from_reporeaper(
    experiment_settings: dict, token_list: list[str], dumps_dir: Path
) -> list[GitHubSlug]:
    """Get the list of repo slugs from the
    [RepoReaper](https://reporeapers.github.io) dataset.

    Args:
        token_list (list[str]): list of GitHub tokens
        dumps_dir (Path): path to the dumps directory

    Returns:
        list: the list of data-science GitHub slugs for the projects from
              the "RepoReaper" dataset.
    """

    LOGGING_CONTEXT = "[Getting slugs from RepoReaper] "

    dataset_gzip = Path(dumps_dir, "dataset.csv.gz")
    if not dataset_gzip.exists():
        URL = "https://reporeapers.github.io/static/downloads/dataset.csv.gz"
        logging.info(LOGGING_CONTEXT + f"Downloading '{URL}'...")
        try:
            with requests.get(URL, stream=True) as response:
                with open(dataset_gzip, "wb") as f:
                    for chunk in response.raw.stream(1024, decode_content=False):
                        if chunk:
                            f.write(chunk)
        except Exception as e:
            logging.error(e)

    else:
        logging.info(LOGGING_CONTEXT + "GZip file already exists. Skipping download.")

    dataset = Path(dumps_dir, "reporeaper.csv")
    if not dataset.exists():
        logging.info(LOGGING_CONTEXT + f"Unzipping '{dataset_gzip}' to '{dataset}'...")
        df = pd.read_csv(
            dataset_gzip, compression="gzip", header=0, sep=",", dtype={"stars": object}
        )
        df.to_csv(dataset, index=False)
    else:
        logging.info(LOGGING_CONTEXT + "CSV file already exists. Skipping unzipping.")
        df = pd.read_csv(dataset, header=0, sep=",", dtype={"stars": object})

    slugs = df.query("randomforest_utl == 1")["repository"]
    logging.info(
        LOGGING_CONTEXT
        + f"Total number of engineered sw projects with 2+ stars: {len(slugs)}."
    )

    logging.info(LOGGING_CONTEXT + "Filtering data science repositories...")

    slugs = _filter_datascience_repos(experiment_settings, token_list, dumps_dir, slugs)
    logging.info(
        LOGGING_CONTEXT + f"Total number of data science repositories: {len(slugs)}."
    )

    return [GitHubSlug(slug) for slug in slugs]
