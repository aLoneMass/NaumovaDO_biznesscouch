#!/usr/bin/env python3
"""
This script is used to backup the database of the NaumovaDO_biznesscouch bot.
"""
import os
import time
from datetime import datetime, date
from dotenv import load_dotenv
from backup_service import BackupService

# Загрузка переменных окружения
load_dotenv()

DB_PATH = "/opt/telegram_bots/NaumovaDO_biznesscouch/naumovado.db"

def was_db_changed_today(db_path):
    if not os.path.exists(db_path):
        print("❌ Файл базы данных не найден")
        return False
    mtime = os.path.getmtime(db_path)
    mdate = datetime.fromtimestamp(mtime).date()
    today = date.today()
    print(f"Дата последнего изменения базы: {mdate}, сегодня: {today}")
    return mdate == today

def main():
    if was_db_changed_today(DB_PATH):
        print("✅ База была изменена сегодня, отправляем бэкап...")
        from backup_service import BackupService
        import os
        bot_token = os.getenv('BOT_TOKEN')
        backup_to = os.getenv('BACKUPTO')
        if not bot_token or not backup_to:
            print("❌ Не заданы переменные окружения BOT_TOKEN или BACKUPTO")
            return
        backup_service = BackupService(bot_token, backup_to, DB_PATH)
        backup_service.send_backup()
    else:
        print("ℹ️ База не менялась сегодня, бэкап не отправляется.")

if __name__ == "__main__":
    main()