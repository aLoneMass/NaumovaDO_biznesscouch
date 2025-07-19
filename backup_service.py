import schedule
import time
import threading
import asyncio
import logging
from datetime import datetime
from telegram import Bot
from database import Database
import os

# Настройка логирования
logger = logging.getLogger(__name__)

class BackupService:
    def __init__(self, bot_token: str, backup_to_id: str, db_path: str = "naumovado.db"):
        self.bot = Bot(token=bot_token)
        self.backup_to_id = int(backup_to_id)
        self.db_path = db_path
        self.database = Database(db_path)
    
    def send_backup(self):
        """Отправка резервной копии базы данных"""
        logger.info("🔄 Начинаем отправку резервной копии...")
        try:
            if os.path.exists(self.db_path):
                logger.info(f"📁 Файл базы данных найден: {self.db_path}")
                with open(self.db_path, 'rb') as db_file:
                    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    filename = f"naumovado_backup_{timestamp}.db"
                    
                    logger.info(f"📤 Отправляем файл: {filename}")
                    
                    # Создаем новый event loop для асинхронной отправки
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    try:
                        loop.run_until_complete(
                            self.bot.send_document(
                                chat_id=self.backup_to_id,
                                document=db_file,
                                filename=filename,
                                caption=f"📊 Резервная копия базы данных\n📅 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                            )
                        )
                        logger.info(f"✅ Резервная копия успешно отправлена: {filename}")
                        print(f"Резервная копия отправлена: {filename}")
                    finally:
                        loop.close()
            else:
                logger.error(f"❌ Файл базы данных не найден: {self.db_path}")
                print("Файл базы данных не найден")
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке резервной копии: {e}")
            print(f"Ошибка при отправке резервной копии: {e}")
    
    def schedule_backup(self):
        """Планирование ежедневной отправки резервной копии в 21:00"""
        schedule.every().day.at("21:00").do(self.send_backup)
        # Также планируем на каждый час для тестирования
        schedule.every().hour.do(self.send_backup)
        logger.info("📅 Резервная копия запланирована на 21:00 ежедневно и каждый час")
        print("Резервная копия запланирована на 21:00 ежедневно и каждый час")
    
    def start_scheduler(self):
        """Запуск планировщика в отдельном потоке"""
        logger.info("🚀 Запуск планировщика резервных копий...")
        self.schedule_backup()
        
        def run_scheduler():
            logger.info("⏰ Планировщик запущен, ожидаем выполнения задач...")
            while True:
                try:
                    schedule.run_pending()
                    time.sleep(60)  # Проверка каждую минуту
                except Exception as e:
                    logger.error(f"❌ Ошибка в планировщике: {e}")
                    time.sleep(60)  # Продолжаем работу
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        logger.info("✅ Планировщик резервных копий запущен в отдельном потоке")
        print("Планировщик резервных копий запущен") 