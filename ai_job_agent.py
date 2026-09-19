import logging
import uuid
from jobspy import scrape_jobs
import pandas as pd
import json

def search_web_for_jobs(role, location, results_wanted=15):
    """Uses python-jobspy to fetch job listings from major job boards."""
    logging.info(f"JobSpy Agent: Searching for {role} in {location}")
    
    try:
        # Scrape jobs using jobspy
        jobs_df = scrape_jobs(
            site_name=["indeed", "linkedin", "glassdoor"],
            search_term=role,
            location=location,
            results_wanted=results_wanted,
            country_indeed='India', # Assuming India by default for NareshIT
            hours_old=72 # Filter for recent jobs
        )
        
        if jobs_df.empty:
            logging.warning("JobSpy Agent: No jobs found.")
            return []
            
        # Convert DataFrame to list of dictionaries
        raw_jobs = jobs_df.to_dict(orient='records')
        formatted_jobs = []
        
        for job in raw_jobs:
            # Handle NaN values and formatting
            def clean_val(val, default=""):
                if pd.isna(val) or val is None:
                    return default
                return str(val).strip()

            formatted_jobs.append({
                "id": str(uuid.uuid4()),
                "title": clean_val(job.get('title'), "Unknown Title"),
                "company": clean_val(job.get('company'), "Unknown Company"),
                "location": clean_val(job.get('location'), location),
                "description": clean_val(job.get('description'), "No description provided."),
                "job_url": clean_val(job.get('job_url'), "#"),
                "site": clean_val(job.get('site'), "jobspy")
            })
            
        logging.info(f"JobSpy Agent: Successfully mapped {len(formatted_jobs)} jobs.")
        return formatted_jobs[:results_wanted]
        
    except Exception as e:
        logging.error(f"JobSpy Extraction failed: {e}")
        return []

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Testing ai_job_agent directly with JobSpy...")
    jobs = search_web_for_jobs("data scientist", "hyderabad", 5)
    print(f"\nFound {len(jobs)} jobs:")
    print(json.dumps(jobs, indent=2))

