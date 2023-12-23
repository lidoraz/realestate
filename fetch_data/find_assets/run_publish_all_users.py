from ext.env import load_vault
# cd /home/ec2-user/realestate;
# export PYTHONPATH=.;
# sleep 120
# /usr/local/bin/python3.11 fetch_data/find_assets/run_publish_all_users.py >> ~/published_users.log 2>&1;

load_vault()  # load env to prod
from fetch_data.find_assets.publish_ai_assets_all import find_and_publish_for_all_users
from scrape_nadlan.utils_insert import send_telegram_msg
from datetime import datetime

if __name__ == '__main__':
    job_name = "run_publish_all_users"
    # print(os.environ['PRODUCTION'])
    print(f"{datetime.now()} Started {job_name}")
    # send_telegram_msg(f"⚪ Starting {job_name}")
    try:
        find_and_publish_for_all_users()
        # send_telegram_msg(f"🟢 FINISHED JOB in {job_name}")
    except Exception as e:
        send_telegram_msg(f"🔴 ERROR in {job_name}")
        send_telegram_msg(str(e))
        raise e
