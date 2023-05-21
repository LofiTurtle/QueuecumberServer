from apscheduler.schedulers.background import BackgroundScheduler

from server.database.historytracker import save_all_user_recently_played


def start_scheduler():
    """
    Starts running the background tasks to check for new songs in users' listening history every 30 minutes
    """
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=save_all_user_recently_played, trigger='interval', minutes=30)
    scheduler.start()
