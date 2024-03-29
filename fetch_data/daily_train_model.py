from fetch_data.modeling.calc_ai import test_train_pipeline, get_train_config
from scrape_nadlan.utils_insert import send_telegram_msg

if __name__ == '__main__':
    job_name = "Training regression models"
    iterations = 5_000
    n_folds = 5
    try:
        cfg = get_train_config()
        send_telegram_msg(f"⚪ Starting {job_name}, {n_folds=}, {iterations=}")
        cfg['iterations'] = iterations
        test_train_pipeline("forsale", n_folds, cfg)
        test_train_pipeline("rent", n_folds, cfg)

        send_telegram_msg(f"🟢 FINISHED JOB in {job_name}")
    except Exception as e:
        send_telegram_msg(f"🔴 ERROR in {job_name}")
        send_telegram_msg(str(e))
        raise e
