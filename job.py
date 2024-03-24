import subprocess
import time

import schedule

def job():
    subprocess.run(["python", "main.py"])


# Schedule the job to run at 3 am
schedule.every().day.at("12:39").do(job)

while True:
    schedule.run_pending()
    time.sleep(60)
