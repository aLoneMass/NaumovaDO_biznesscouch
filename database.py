import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Tuple

class Database:
    def __init__(self, db_path: str = "naumovado.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных и создание таблиц"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    first_name TEXT,
                    last_name TEXT,
                    phone TEXT,
                    registration_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    request TEXT,
                    request_type TEXT,
                    file_id TEXT
                )
            ''')
            conn.commit()
    
    def add_user(self, telegram_id: int, first_name: str, last_name: str, phone: str) -> bool:
        """Добавление нового пользователя"""
        try:
            print(f"Попытка добавления пользователя: ID={telegram_id}, Имя={first_name}, Фамилия={last_name}, Телефон={phone}")
            print(f"Путь к БД: {os.path.abspath(self.db_path)}")
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO users (telegram_id, first_name, last_name, phone)
                    VALUES (?, ?, ?, ?)
                ''', (telegram_id, first_name, last_name, phone))
                conn.commit()
                print(f"Пользователь успешно добавлен/обновлен: {telegram_id}")
                return True
        except Exception as e:
            print(f"Ошибка при добавлении пользователя: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def update_user_request(self, telegram_id: int, request: str, request_type: str = None, file_id: str = None) -> bool:
        """Обновление запроса пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users SET request = ?, request_type = ?, file_id = ? WHERE telegram_id = ?
                ''', (request, request_type, file_id, telegram_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Ошибка при обновлении запроса: {e}")
            return False
    
    def get_user(self, telegram_id: int) -> Optional[Tuple]:
        """Получение пользователя по telegram_id"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM users WHERE telegram_id = ?
                ''', (telegram_id,))
                return cursor.fetchone()
        except Exception as e:
            print(f"Ошибка при получении пользователя: {e}")
            return None
    
    def get_all_users(self) -> List[Tuple]:
        """Получение всех пользователей"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM users ORDER BY registration_timestamp DESC
                ''')
                return cursor.fetchall()
        except Exception as e:
            print(f"Ошибка при получении всех пользователей: {e}")
            return []
    
    def get_today_registrations(self) -> List[Tuple]:
        """Получение регистраций за сегодня"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM users 
                    WHERE DATE(registration_timestamp) = DATE('now')
                    ORDER BY registration_timestamp DESC
                ''')
                return cursor.fetchall()
        except Exception as e:
            print(f"Ошибка при получении сегодняшних регистраций: {e}")
            return []
    
    def get_db_file_path(self) -> str:
        """Получение пути к файлу базы данных"""
        return os.path.abspath(self.db_path) 