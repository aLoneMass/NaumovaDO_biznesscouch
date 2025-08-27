#!/usr/bin/env python3
"""
Сервис для работы с Google Sheets API
Позволяет выгружать данные из базы в Google таблицы
"""
import os
import logging
from typing import List, Tuple, Optional
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleSheetsService:
    def __init__(self, credentials_file: str = "endless-codex.json"):
        """
        Инициализация сервиса Google Sheets
        
        Args:
            credentials_file: Путь к файлу с учетными данными сервисного аккаунта
        """
        self.credentials_file = credentials_file
        self.service = None
        self.sheets_id = os.getenv('GoogleSheetsID')
        
        if not self.sheets_id:
            raise ValueError("Не задан GoogleSheetsID в переменных окружения")
        
        self._authenticate()
    
    def _authenticate(self):
        """Аутентификация в Google API"""
        try:
            if not os.path.exists(self.credentials_file):
                raise FileNotFoundError(f"Файл учетных данных не найден: {self.credentials_file}")
            
            # Области доступа для Google Sheets
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # Загрузка учетных данных
            credentials = Credentials.from_service_account_file(
                self.credentials_file, 
                scopes=scopes
            )
            
            # Создание сервиса
            self.service = build('sheets', 'v4', credentials=credentials)
            logger.info("✅ Успешная аутентификация в Google Sheets API")
            
        except Exception as e:
            logger.error(f"❌ Ошибка аутентификации: {e}")
            raise
    
    def get_sheet_data(self, range_name: str = "A:Z") -> Optional[List[List]]:
        """
        Получение данных из таблицы
        
        Args:
            range_name: Диапазон ячеек (например, "A:Z" для всех данных)
        
        Returns:
            Список строк с данными или None при ошибке
        """
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheets_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            logger.info(f"📊 Получено {len(values)} строк из таблицы")
            return values
            
        except HttpError as e:
            logger.error(f"❌ Ошибка получения данных из таблицы: {e}")
            return None
    
    def update_sheet(self, range_name: str, values: List[List]) -> bool:
        """
        Обновление данных в таблице
        
        Args:
            range_name: Диапазон ячеек (например, "A1")
            values: Данные для записи
        
        Returns:
            True при успехе, False при ошибке
        """
        try:
            body = {'values': values}
            result = self.service.spreadsheets().values().update(
                spreadsheetId=self.sheets_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            logger.info(f"✅ Обновлено {result.get('updatedCells')} ячеек")
            return True
            
        except HttpError as e:
            logger.error(f"❌ Ошибка обновления таблицы: {e}")
            return False
    
    def append_sheet(self, range_name: str, values: List[List]) -> bool:
        """
        Добавление новых строк в таблицу
        
        Args:
            range_name: Диапазон для добавления (например, "A")
            values: Данные для добавления
        
        Returns:
            True при успехе, False при ошибке
        """
        try:
            body = {'values': values}
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.sheets_id,
                range=range_name,
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            logger.info(f"✅ Добавлено {len(values)} новых строк")
            return True
            
        except HttpError as e:
            logger.error(f"❌ Ошибка добавления строк: {e}")
            return False
    
    def clear_sheet(self, range_name: str = "A:Z") -> bool:
        """
        Очистка данных в таблице
        
        Args:
            range_name: Диапазон для очистки
        
        Returns:
            True при успехе, False при ошибке
        """
        try:
            self.service.spreadsheets().values().clear(
                spreadsheetId=self.sheets_id,
                range=range_name
            ).execute()
            
            logger.info(f"✅ Таблица очищена в диапазоне {range_name}")
            return True
            
        except HttpError as e:
            logger.error(f"❌ Ошибка очистки таблицы: {e}")
            return False
    
    def format_headers(self):
        """Форматирование заголовков таблицы"""
        try:
            # Заголовки для таблицы
            headers = [
                'ID',
                'Telegram ID', 
                'Имя',
                'Фамилия',
                'Телефон',
                'Дата регистрации',
                'Запрос',
                'Тип запроса',
                'ID файла'
            ]
            
            # Обновляем заголовки
            success = self.update_sheet("A1", [headers])
            if success:
                logger.info("✅ Заголовки таблицы обновлены")
            return success
            
        except Exception as e:
            logger.error(f"❌ Ошибка форматирования заголовков: {e}")
            return False
    
    def export_users_to_sheets(self, users_data: List[Tuple]) -> bool:
        """
        Экспорт пользователей в Google Sheets
        
        Args:
            users_data: Список пользователей из базы данных
        
        Returns:
            True при успехе, False при ошибке
        """
        try:
            if not users_data:
                logger.info("ℹ️ Нет данных для экспорта")
                return True
            
            # Получаем существующие данные из таблицы
            existing_data = self.get_sheet_data("A:Z")
            
            if existing_data:
                # Пропускаем заголовки
                existing_users = existing_data[1:] if len(existing_data) > 1 else []
                logger.info(f"📊 Найдено {len(existing_users)} существующих записей в таблице")
            else:
                existing_users = []
                logger.info("📊 Таблица пуста, начинаем с нуля")
            
            # Подготавливаем данные для экспорта
            export_data = []
            for user in users_data:
                # user: (id, telegram_id, first_name, last_name, phone, registration_timestamp, request, request_type, file_id)
                row = [
                    user[0],                    # ID
                    user[1],                    # Telegram ID
                    user[2] or '',              # Имя
                    user[3] or '',              # Фамилия
                    user[4] or '',              # Телефон
                    user[5] or '',              # Дата регистрации
                    user[6] or '',              # Запрос
                    user[7] or '',              # Тип запроса
                    user[8] or ''               # ID файла
                ]
                export_data.append(row)
            
            # Если таблица пуста, добавляем заголовки и все данные
            if not existing_data:
                success = self.format_headers()
                if not success:
                    return False
                
                # Добавляем все данные
                if export_data:
                    success = self.append_sheet("A2", export_data)
                    if success:
                        logger.info(f"✅ Экспортировано {len(export_data)} пользователей")
                    return success
            else:
                # Проверяем, какие записи уже есть в таблице
                existing_telegram_ids = set()
                for row in existing_users:
                    if len(row) > 1 and row[1]:  # telegram_id во второй колонке
                        try:
                            existing_telegram_ids.add(int(row[1]))
                        except (ValueError, IndexError):
                            continue
                
                # Находим новые записи
                new_users = []
                for user in users_data:
                    if user[1] not in existing_telegram_ids:  # user[1] - telegram_id
                        row = [
                            user[0],                    # ID
                            user[1],                    # Telegram ID
                            user[2] or '',              # Имя
                            user[3] or '',              # Фамилия
                            user[4] or '',              # Телефон
                            user[5] or '',              # Дата регистрации
                            user[6] or '',              # Запрос
                            user[7] or '',              # Тип запроса
                            user[8] or ''               # ID файла
                        ]
                        new_users.append(row)
                
                if new_users:
                    # Добавляем только новые записи
                    success = self.append_sheet("A", new_users)
                    if success:
                        logger.info(f"✅ Добавлено {len(new_users)} новых пользователей")
                    return success
                else:
                    logger.info("ℹ️ Все пользователи уже есть в таблице")
                    return True
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка экспорта в Google Sheets: {e}")
            return False
    
    def get_sheet_info(self) -> dict:
        """Получение информации о таблице"""
        try:
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=self.sheets_id
            ).execute()
            
            info = {
                'title': spreadsheet.get('properties', {}).get('title', 'Неизвестно'),
                'sheets': [sheet['properties']['title'] for sheet in spreadsheet.get('sheets', [])],
                'url': f"https://docs.google.com/spreadsheets/d/{self.sheets_id}"
            }
            
            return info
            
        except HttpError as e:
            logger.error(f"❌ Ошибка получения информации о таблице: {e}")
            return {}
