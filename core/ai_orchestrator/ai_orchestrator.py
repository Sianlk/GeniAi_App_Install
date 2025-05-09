import subprocess

def run_all():
    subprocess.run(['python3', 'core/analytics/analytics_scraper.py'])
    subprocess.run(['python3', 'core/recommendation_engine/neuro_matcher.py'])
    subprocess.run(['python3', 'core/education/edu_module.py'])

if __name__ == "__main__":
    run_all()
