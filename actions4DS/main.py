from config import DATA_DIR, DUMPS_DIR, EXPERIMENT_SETTINGS, TOKEN_LIST
from get_repo_list import get_repos_cml
from scrape_repos import WorkflowScraper

if __name__ == "__main__":

    # STEP 1: get list of repo slugs
    slugs = get_repos_cml()

    # STEP 2: scrape repos to collect workflows
    wf_scraper = WorkflowScraper(
        EXPERIMENT_SETTINGS, TOKEN_LIST, DUMPS_DIR, DATA_DIR, slugs
    )
    wf_scraper.scrape_repos()
