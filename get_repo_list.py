"""
Generate a list of GitHub repositories containing data science projects.
"""

import requests
import re

from models import GitHubSlug

# Method 1
# Get repositories from the dataset: “Boa Meets Python: A Boa Dataset of Data Science Software in Python Language”
def get_repos_from_boa_dataset() -> GitHubSlug:
    """Get the list of repo slugs from the "Boa Meets Python" dataset.

    In [1], Biswas et al. present a dataset of 1,558 mature data science projects from GitHub, written in the Python programming language.

    The list of GitHub projects referenced in the dataset is available in the paper's [companion repository](https://github.com/boalang/MSR19-DataShowcase/), in the `info.txt` file specifically.

    This funcion downloads `info.txt` and returns the list of repository slugs, extracted by means of a regular expression.

    [1]S. Biswas, M. J. Islam, Y. Huang, and H. Rajan, “Boa Meets Python: A Boa Dataset of Data Science Software in Python Language,” in 2019 IEEE/ACM 16th International Conference on Mining Software Repositories (MSR), Montreal, QC, Canada, May 2019, pp. 577–581. doi: 10.1109/MSR.2019.00086.

    Returns:
        list: the list of GitHub slugs for the projects referenced in the "Boa Meets Python" dataset [1].
    """

    # URL to the raw `info.txt` file from https://www.github.com/boalang/MSR19-DataShowcase
    URL = "https://raw.githubusercontent.com/boalang/MSR19-DataShowcase/master/info.txt"

    r = requests.get(URL)
    lines = r.text.splitlines()
    regex = re.compile("^lib\[(.*)\] = (.*)$")
    slugs = [
        GitHubSlug(match.group(1)) for line in lines if (match := regex.match(line))
    ]

    return slugs
