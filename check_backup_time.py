#!/usr/bin/env python3
"""
Скрипт для проверки времени и тестирования резервного копирования
"""

import os
import schedule
import time
from datetime import datetime
from dotenv import load_dotenv
from backup_service import BackupService

# Загрузка переменных окружения
load_dotenv()

def check_time():
    """Проверка текущего времени"""
    now = datetime.now()
    print(f"🕐 Текущее время: {now.strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"📅 День недели: {now.strftime('%A')}")
    print(f"🌍 Часовой пояс: {time.tzname[0] if time.daylight == 0 else time.tzname[1]}")
    
    # Проверяем, близко ли время к 21:00
    target_hour = 21
    current_hour = now.hour
    current_minute = now.minute
    
    if current_hour == target_hour:
        print(f"✅ Сейчас время резервного копирования (21:00)!")
    elif current_hour == target_hour - 1 and current_minute >= 55:
        print(f"⏰ До резервного копирования осталось {60 - current_minute} минут")
    elif current_hour == target_hour + 1 and current_minute <= 5:
        print(f"⏰ Резервное копирование было {current_minute} минут назад")
    else:
        hours_until = (target_hour - current_hour) % 24
        print(f"⏰ До резервного копирования осталось примерно {hours_until} часов")

def test_scheduler():
    """Тестирование планировщика"""
    print("\n🧪 Тестирование планировщика...")
    
    # Получаем переменные окружения
    bot_token = os.getenv('BOT_TOKEN')
    backup_to = os.getenv('BACKUPTO')
    
    if not bot_token or not backup_to:
        print("❌ Отсутствуют переменные окружения BOT_TOKEN или BACKUPTO")
        return
    
    print(f"✅ Переменные окружения найдены")
    print(f"🤖 Токен бота: {bot_token[:10]}...")
    print(f"📱 ID для резервных копий: {backup_to}")
    
    # Создаем сервис резервных копий
    backup_service = BackupService(bot_token, backup_to)
    
    # Планируем задачу на 1 минуту вперед для тестирования
    test_time = datetime.now().replace(second=0, microsecond=0)
    test_time = test_time.replace(minute=test_time.minute + 1)
    
    print(f"⏰ Планируем тестовую отправку на {test_time.strftime('%H:%M')}")
    
    # Планируем тестовую задачу
    schedule.every().day.at(test_time.strftime("%H:%M")).do(backup_service.send_backup)
    
    # Запускаем планировщик на 2 минуты
    print("🔄 Запускаем планировщик на 2 минуты...")
    start_time = time.time()
    
    while time.time() - start_time < 120:  # 2 минуты
        schedule.run_pending()
        time.sleep(1)
    
    print("✅ Тест планировщика завершен")

def main():
    """Основная функция"""
    print("🔍 Проверка системы резервного копирования")
    print("=" * 50)
    
    # Проверяем время
    check_time()
    
    # Тестируем планировщик
    test_scheduler()
    
    print("\n✅ Проверка завершена")

if __name__ == '__main__':
    main() 