from config import DATA_DIR, DUMPS_DIR, KEYWORDS, TOKEN_LIST
from get_repo_list import get_repos_from_boa_dataset, get_repos_from_reporeaper
from scrape_repos import WorkflowScraper

if __name__ == "__main__":

    # STEP 1: get list of repo slugs
    boa_slugs = get_repos_from_boa_dataset()
    reaper_slugs = get_repos_from_reporeaper(TOKEN_LIST, DUMPS_DIR, DATA_DIR, KEYWORDS)
    slugs = set(reaper_slugs)

    # STEP 2: scrape repos to collect workflows
    wf_scraper = WorkflowScraper(TOKEN_LIST, DUMPS_DIR, DATA_DIR, slugs)
    wf_scraper.scrape_repos()
