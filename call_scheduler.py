# call_scheduler.py
import os
from asana import Client as AsanaClient
from twilio.rest import Client as TwilioClient
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta

# Ініціалізація клієнтів
asana = AsanaClient.access_token(os.getenv("ASANA_TOKEN"))
twilio = TwilioClient(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
scheduler = BackgroundScheduler()
scheduler.start()

PROJECT_ID      = os.getenv("ASANA_PROJECT_ID")
PHONE_FLD       = os.getenv("PHONE_FIELD_GID")
MODE_FLD        = os.getenv("MODE_FIELD_GID")
ATTEMPTS_FLD    = os.getenv("ATTEMPTS_FIELD_GID")
CALLER_NUMBER   = os.getenv("TWILIO_CALLER_NUMBER")
BASE_URL        = os.getenv("BASE_URL")

def schedule_call(task_id, delay_minutes=0):
    run_time = datetime.utcnow() + timedelta(minutes=delay_minutes)
    scheduler.add_job(lambda: make_call(task_id), 'date', run_date=run_time)

def make_call(task_id):
    # Отримуємо таск
    task = asana.tasks.get_task(task_id, opt_fields=f"custom_fields.{PHONE_FLD},custom_fields.{MODE_FLD},custom_fields.{ATTEMPTS_FLD}")
    phone = next(f['text_value'] for f in task['custom_fields'] if f['gid']==PHONE_FLD)
    mode  = next(f['enum_value']['name'] for f in task['custom_fields'] if f['gid']==MODE_FLD)
    attempts = int(next(f['number_value'] for f in task['custom_fields'] if f['gid']==ATTEMPTS_FLD) or 0)

    if attempts >= 3:
        # Переносимо у Customer Unavailable
        asana.tasks.update_task(task_id, {"completed": False, "custom_fields": {ATTEMPTS_FLD: attempts, /* статус-поле */}})
        return

    # Ініціюємо дзвінок через Twilio
    call = twilio.calls.create(
        to=phone,
        from_=CALLER_NUMBER,
        url=f"{BASE_URL}/voice?task_id={task_id}"
    )
    # Нічого не робимо тут далі — обробка через webhook /status

def poll_asana():
    # Вибираємо таски зі статусом “Needs Confirmation”
    tasks = asana.tasks.get_tasks_for_project(PROJECT_ID, opt_fields="gid,completed")
    for t in tasks:
        # Тут перевіряємо тег або статус-поле — що сигналізує про потребу дзвінка
        # Ініціюємо перший дзвінок одразу
        schedule_call(t['gid'], delay_minutes=0)

if __name__ == "__main__":
    poll_asana()
    # Далі зупинки немає — scheduler тримає процес живим
