#!/usr/bin/env python3
"""
This script is used to backup the database of the NaumovaDO_biznesscouch bot.
"""
import os
import time
import requests
from datetime import datetime, date
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

DB_PATH = "/opt/telegram_bots/NaumovaDO_biznesscouch/naumovado.db"

class BackupService:
    """Сервис для создания и отправки резервных копий базы данных"""
    
    def __init__(self, bot_token, backup_to, db_path):
        self.bot_token = bot_token
        self.backup_to = backup_to
        self.db_path = db_path
        self.bot_url = f"https://api.telegram.org/bot{bot_token}"
    
    def send_backup(self):
        """Отправляет резервную копию базы данных"""
        try:
            # Проверяем существование файла базы данных
            if not os.path.exists(self.db_path):
                print(f"❌ Файл базы данных не найден: {self.db_path}")
                return False
            
            # Создаем имя файла с временной меткой
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"naumovado_backup_{timestamp}.db"
            
            # Отправляем файл через Telegram Bot API
            with open(self.db_path, 'rb') as db_file:
                files = {'document': (backup_filename, db_file, 'application/x-sqlite3')}
                data = {'chat_id': self.backup_to}
                
                response = requests.post(
                    f"{self.bot_url}/sendDocument",
                    files=files,
                    data=data
                )
                
                if response.status_code == 200:
                    print(f"✅ Резервная копия успешно отправлена: {backup_filename}")
                    return True
                else:
                    print(f"❌ Ошибка при отправке: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Ошибка при создании резервной копии: {e}")
            return False
    
    def start_scheduler(self):
        """Запускает планировщик резервных копий"""
        try:
            import schedule
            import threading
            import time
            
            def backup_job():
                """Задача для создания резервной копии"""
                if was_db_changed_today(self.db_path):
                    print("🔄 Создание автоматической резервной копии...")
                    self.send_backup()
                else:
                    print("ℹ️ База данных не изменялась сегодня, резервная копия не требуется")
            
            # Планируем резервное копирование каждый день в 23:00
            schedule.every().day.at("23:00").do(backup_job)
            
            # Запускаем планировщик в отдельном потоке
            def run_scheduler():
                while True:
                    schedule.run_pending()
                    time.sleep(60)  # Проверяем каждую минуту
            
            scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
            scheduler_thread.start()
            
            print("✅ Планировщик резервных копий запущен (ежедневно в 23:00)")
            return True
            
        except ImportError:
            print("⚠️ Библиотека schedule не установлена, планировщик не запущен")
            return False
        except Exception as e:
            print(f"❌ Ошибка при запуске планировщика: {e}")
            return False

def was_db_changed_today(db_path):
    """Проверяет, была ли база данных изменена сегодня"""
    if not os.path.exists(db_path):
        print("❌ Файл базы данных не найден")
        return False
    mtime = os.path.getmtime(db_path)
    mdate = datetime.fromtimestamp(mtime).date()
    today = date.today()
    print(f"Дата последнего изменения базы: {mdate}, сегодня: {today}")
    return mdate == today

def main():
    """Основная функция для запуска из командной строки"""
    if was_db_changed_today(DB_PATH):
        print("✅ База была изменена сегодня, отправляем бэкап...")
        
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