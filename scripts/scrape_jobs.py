import os, sys
# Bridge to backend/scripts/scrape_jobs.py
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.insert(0, backend_dir)
from scripts.scrape_jobs import run_scraper

if __name__ == '__main__':
    run_scraper()
