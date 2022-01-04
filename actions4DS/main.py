import os
from pathlib import Path

from dotenv import load_dotenv
from get_repo_list import get_repos_from_boa_dataset, get_repos_from_reporeaper
from scrape_repos import GitHubScraper

# Load environment variables from .env file
load_dotenv()
GITHUB_PERSONAL_ACCESS_TOKEN = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
DATA_DIR = Path(os.getenv("DATA_DIR", "data"))

if __name__ == "__main__":
    # Ensure the data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # STEP 1: get list of repo slugs
    boa_slugs = get_repos_from_boa_dataset()
    reaper_slugs = get_repos_from_reporeaper(DATA_DIR)
    slugs = boa_slugs + reaper_slugs

    # STEP 2: scrape repos to collect workflows
    github_scraper = GitHubScraper(GITHUB_PERSONAL_ACCESS_TOKEN, DATA_DIR)
    github_scraper.scrape_repos(slugs)
