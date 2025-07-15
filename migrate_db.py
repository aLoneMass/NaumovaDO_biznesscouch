#!/usr/bin/env python3
"""
Скрипт для миграции существующей базы данных
Добавляет новые поля request_type и file_id
"""

import sqlite3
import os

def migrate_database():
    """Миграция базы данных"""
    db_path = "naumovado.db"
    
    if not os.path.exists(db_path):
        print("База данных не найдена. Создастся новая база при первом запуске бота.")
        return
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Проверяем, есть ли уже новые поля
            cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'request_type' not in columns:
                print("Добавляем поле request_type...")
                cursor.execute("ALTER TABLE users ADD COLUMN request_type TEXT")
            
            if 'file_id' not in columns:
                print("Добавляем поле file_id...")
                cursor.execute("ALTER TABLE users ADD COLUMN file_id TEXT")
            
            conn.commit()
            print("✅ Миграция базы данных завершена успешно!")
            
    except Exception as e:
        print(f"❌ Ошибка при миграции базы данных: {e}")

if __name__ == "__main__":
    migrate_database() 