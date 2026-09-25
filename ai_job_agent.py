import logging
import uuid
import json
import subprocess
import os

def run_bun_cli(cli_path, cmd_args):
    bun_exec = os.path.join(os.path.dirname(__file__), ".bun", "bin", "bun")
    if not os.path.exists(bun_exec):
        bun_exec = os.path.expanduser("~/.bun/bin/bun")
    try:
        cmd = [bun_exec, "run", "src/cli.ts", "search"] + cmd_args + ["--format", "json"]
        result = subprocess.run(cmd, cwd=cli_path, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except Exception as e:
        logging.error(f"Failed to run bun CLI in {cli_path}: {e}")
        return []

def search_web_for_jobs(role, location, results_wanted=15):
    """Uses ai-job-search skills to fetch job listings."""
    logging.info(f"Agent: Searching for {role} in {location}")
    
    formatted_jobs = []
    
    # 1. LinkedIn Search
    linkedin_path = os.path.join(os.path.dirname(__file__), "ai-job-search", ".agents", "skills", "linkedin-search", "cli")
    linkedin_args = ["-q", role, "-l", location, "-n", str(results_wanted)]
    linkedin_jobs = run_bun_cli(linkedin_path, linkedin_args)
    if isinstance(linkedin_jobs, dict) and "results" in linkedin_jobs:
        linkedin_jobs = linkedin_jobs["results"]
    
    # 2. Freehire Search (freehire doesn't use -l for generic location, use -q or omit)
    freehire_path = os.path.join(os.path.dirname(__file__), "ai-job-search", ".agents", "skills", "freehire-search", "cli")
    freehire_query = f"{role} {location}"
    freehire_args = ["-q", freehire_query, "-n", str(results_wanted)]
    freehire_jobs = run_bun_cli(freehire_path, freehire_args)
    if isinstance(freehire_jobs, dict) and "results" in freehire_jobs:
        freehire_jobs = freehire_jobs["results"]
        
    all_raw_jobs = []
    if isinstance(linkedin_jobs, list):
        all_raw_jobs.extend(linkedin_jobs)
    if isinstance(freehire_jobs, list):
        all_raw_jobs.extend(freehire_jobs)
    
    if not all_raw_jobs:
        logging.warning("Agent: No jobs found.")
        return []

    for job in all_raw_jobs:
        def clean_val(val, default=""):
            if val is None:
                return default
            return str(val).strip()

        formatted_jobs.append({
            "id": str(uuid.uuid4()),
            "title": clean_val(job.get('title'), "Unknown Title"),
            "company": clean_val(job.get('company'), "Unknown Company"),
            "location": clean_val(job.get('location'), location),
            "description": clean_val(job.get('description') or job.get('snippet'), "No description provided."),
            "job_url": clean_val(job.get('url') or job.get('job_url'), "#"),
            "site": clean_val(job.get('source') or "ai-job-search", "ai-job-search")
        })
        
    logging.info(f"Agent: Successfully mapped {len(formatted_jobs)} jobs.")
    return formatted_jobs

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Testing ai_job_agent directly with ai-job-search...")
    jobs = search_web_for_jobs("data scientist", "hyderabad", 5)
    print(f"\nFound {len(jobs)} jobs:")
    print(json.dumps(jobs, indent=2))
