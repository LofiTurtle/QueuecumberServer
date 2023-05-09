from apscheduler.schedulers.background import BackgroundScheduler

from server.database.historytracker import save_all_user_recently_played


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=save_all_user_recently_played, trigger='interval', minutes=30)
    scheduler.start()
