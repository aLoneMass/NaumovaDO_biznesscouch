#!/usr/bin/env python3
"""
Скрипт для экспорта данных из базы в Google Sheets
Запускается по команде или по расписанию
"""
import os
import sys
import logging
from dotenv import load_dotenv
from database import Database
from google_sheets_service import GoogleSheetsService

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Основная функция экспорта"""
    try:
        # Загружаем переменные окружения
        load_dotenv()
        
        # Проверяем наличие необходимых переменных
        sheets_id = os.getenv('GoogleSheetsID')
        if not sheets_id:
            logger.error("❌ Не задан GoogleSheetsID в переменных окружения")
            return False
        
        # Путь к базе данных
        db_path = os.getenv('DB_PATH', 'naumovado.db')
        if not os.path.exists(db_path):
            logger.error(f"❌ Файл базы данных не найден: {db_path}")
            return False
        
        logger.info("🚀 Начинаем экспорт данных в Google Sheets...")
        
        # Инициализируем сервисы
        db = Database(db_path)
        sheets_service = GoogleSheetsService()
        
        # Получаем информацию о таблице
        sheet_info = sheets_service.get_sheet_info()
        if sheet_info:
            logger.info(f"📊 Таблица: {sheet_info.get('title', 'Неизвестно')}")
            logger.info(f"🔗 Ссылка: {sheet_info.get('url', 'Недоступна')}")
        
        # Получаем всех пользователей из базы
        users = db.get_all_users()
        logger.info(f"👥 Найдено {len(users)} пользователей в базе данных")
        
        if not users:
            logger.info("ℹ️ Нет пользователей для экспорта")
            return True
        
        # Экспортируем данные
        success = sheets_service.export_users_to_sheets(users)
        
        if success:
            logger.info("✅ Экспорт завершен успешно!")
            return True
        else:
            logger.error("❌ Ошибка при экспорте данных")
            return False
            
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        return False

def test_connection():
    """Тестирование подключения к Google Sheets"""
    try:
        load_dotenv()
        sheets_service = GoogleSheetsService()
        sheet_info = sheets_service.get_sheet_info()
        
        if sheet_info:
            print("✅ Подключение к Google Sheets успешно!")
            print(f"📊 Таблица: {sheet_info.get('title')}")
            print(f"🔗 Ссылка: {sheet_info.get('url')}")
            return True
        else:
            print("❌ Не удалось получить информацию о таблице")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

def show_help():
    """Показать справку по использованию"""
    print("""
📊 Экспорт данных в Google Sheets

Использование:
  python export_to_sheets.py          - Экспорт всех данных
  python export_to_sheets.py test     - Тест подключения
  python export_to_sheets.py help     - Показать эту справку

Требования:
  - Файл .env с переменной GoogleSheetsID
  - Файл endless-codex.json с учетными данными сервисного аккаунта
  - Установленные зависимости (см. requirements.txt)

Пример .env:
  GoogleSheetsID=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms
""")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "test":
            test_connection()
        elif command == "help":
            show_help()
        else:
            print(f"❌ Неизвестная команда: {command}")
            show_help()
    else:
        # Основной экспорт
        success = main()
        sys.exit(0 if success else 1)
