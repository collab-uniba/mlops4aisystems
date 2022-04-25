"""
Generate a list of GitHub repositories containing data science projects.
"""

import logging
from pathlib import Path

from models import GitHubSlug


# Method 1
# Get repositories which use CML
def get_repos_cml() -> list[GitHubSlug]:
    """Get the list of repo slugs from an input file, 
       which contains the list of repositories with CML.

    Returns:
        list: the list of GitHub slugs for the projects referenced in the
              file.
    """

    LOGGING_CONTEXT = "[Getting slugs for CML dataset]"
    BASE_DIR = Path(__file__).parent.parent.absolute()

    filepath = Path(BASE_DIR, "cml-repos.txt")
    with open(filepath, mode="r", encoding="UTF-8") as f:
        urls = f.read().splitlines()
    logging.info(LOGGING_CONTEXT + f"Total number of CML repositories: {len(urls)}.")

    slugs = []
    for url in urls:
        slug = url.replace("https://github.com/", "")
        slugs.append(GitHubSlug(slug))

    return slugs
