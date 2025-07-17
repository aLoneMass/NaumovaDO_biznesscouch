#!/usr/bin/env python3
import os
import sqlite3
from database import Database

def check_database():
    """Проверка состояния базы данных"""
    print("=== Проверка базы данных ===")
    
    # Проверяем текущую директорию
    print(f"Текущая директория: {os.getcwd()}")
    
    # Проверяем файл базы данных
    db_path = "naumovado.db"
    print(f"Путь к БД: {os.path.abspath(db_path)}")
    
    if os.path.exists(db_path):
        print(f"✅ Файл БД существует")
        print(f"Размер файла: {os.path.getsize(db_path)} байт")
        print(f"Права доступа: {oct(os.stat(db_path).st_mode)[-3:]}")
    else:
        print(f"❌ Файл БД не существует")
    
    # Проверяем права на запись в директорию
    try:
        test_file = "test_write.tmp"
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        print("✅ Есть права на запись в директорию")
    except Exception as e:
        print(f"❌ Нет прав на запись в директорию: {e}")
    
    # Пробуем подключиться к БД
    try:
        db = Database()
        print("✅ Подключение к БД успешно")
        
        # Проверяем таблицу
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            if cursor.fetchone():
                print("✅ Таблица 'users' существует")
                
                # Проверяем количество записей
                cursor.execute("SELECT COUNT(*) FROM users")
                count = cursor.fetchone()[0]
                print(f"Количество пользователей в БД: {count}")
            else:
                print("❌ Таблица 'users' не существует")
                
    except Exception as e:
        print(f"❌ Ошибка при работе с БД: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_database() 