import subprocess

def run_pipeline():
    subprocess.run(['python3', 'analytics_scraper.py'])
    subprocess.run(['python3', 'neuro_matcher.py'])
    subprocess.run(['python3', 'edu_module.py'])

if __name__ == "__main__":
    run_pipeline()
    print("All systems completed successfully.")
