import configparser
import json
import os
from pathlib import Path

from get_repo_list import get_repos_from_boa_dataset, get_repos_from_reporeaper
from scrape_repos import GitHubScraper

# Load configuration from config.ini file
config = configparser.ConfigParser()
config.read(Path("config.ini"))

DATA_DIR = Path(config["PATHS"]["DATA_DIR"])
TOKEN_LIST = json.loads(config["GITHUB"]["TOKEN_LIST"])

if __name__ == "__main__":

    # STEP 1: get list of repo slugs
    boa_slugs = get_repos_from_boa_dataset()
    reaper_slugs = get_repos_from_reporeaper(DATA_DIR)
    slugs = boa_slugs + reaper_slugs

    # STEP 2: scrape repos to collect workflows
    github_scraper = GitHubScraper(TOKEN_LIST, DATA_DIR)
    github_scraper.scrape_repos(slugs)
