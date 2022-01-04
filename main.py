import os

from dotenv import load_dotenv

from get_repo_list import get_repos_from_boa_dataset
from scrape_repos import GitHubScraper

# Load environment variables from .env file
load_dotenv()
GITHUB_PERSONAL_ACCESS_TOKEN = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")

if __name__ == "__main__":

    # STEP 1: get list of repo slugs
    slugs = get_repos_from_boa_dataset()

    # STEP 2: scrape repos to collect workflows
    github_scraper = GitHubScraper(GITHUB_PERSONAL_ACCESS_TOKEN)
    github_scraper.scrape_repos(slugs)
