#!/usr/bin/env python3
"""
Скрипт для тестирования отправки резервных копий
"""

import os
import sys
from dotenv import load_dotenv
from backup_service import BackupService

# Загружаем переменные окружения
load_dotenv()

def test_backup():
    """Тестирование отправки резервной копии"""
    
    # Получаем переменные окружения
    bot_token = os.getenv('BOT_TOKEN')
    backup_to_id = os.getenv('BACKUPTO')
    
    if not bot_token:
        print("❌ Не указан BOT_TOKEN в файле .env")
        return False
    
    if not backup_to_id:
        print("❌ Не указан BACKUPTO в файле .env")
        return False
    
    # Путь к файлу базы данных
    db_path = "/opt/telegram_bots/NaumovaDO_biznesscouch/naumovado.db"
    
    print(f"🔍 Проверка файла базы данных: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"❌ Файл базы данных не найден: {db_path}")
        return False
    
    # Получаем размер файла
    file_size = os.path.getsize(db_path)
    print(f"✅ Файл найден, размер: {file_size} байт")
    
    # Создаем сервис резервных копий
    print("🤖 Создание сервиса резервных копий...")
    backup_service = BackupService(bot_token, backup_to_id, db_path)
    
    # Тестируем отправку
    print("📤 Тестирование отправки резервной копии...")
    try:
        backup_service.send_backup()
        print("✅ Резервная копия успешно отправлена!")
        return True
    except Exception as e:
        print(f"❌ Ошибка при отправке: {e}")
        return False

def check_scheduler():
    """Проверка планировщика"""
    print("\n📅 Проверка планировщика резервных копий...")
    
    bot_token = os.getenv('BOT_TOKEN')
    backup_to_id = os.getenv('BACKUPTO')
    
    if bot_token and backup_to_id:
        backup_service = BackupService(bot_token, backup_to_id)
        backup_service.schedule_backup()
        print("✅ Планировщик настроен на отправку в 21:00 ежедневно")
    else:
        print("❌ Не удалось настроить планировщик - отсутствуют переменные окружения")

if __name__ == "__main__":
    print("🧪 Тестирование системы резервных копий")
    print("=" * 50)
    
    success = test_backup()
    
    if success:
        check_scheduler()
        print("\n✅ Все тесты пройдены успешно!")
    else:
        print("\n❌ Тесты не пройдены. Проверьте настройки.")
        sys.exit(1) 