#!/bin/bash

# Скрипт установки Naumova Telegram Bot как systemd службы
# Запускать с правами root: sudo ./install_service.sh

set -e

echo "🤖 Установка Naumova Telegram Bot как systemd службы..."

# Проверяем, что скрипт запущен от root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Этот скрипт должен быть запущен с правами root (sudo)"
    exit 1
fi

# Пути
BOT_DIR="/opt/telegram_bots/NaumovaDO_biznesscouch"
SERVICE_FILE="naumova-bot.service"
SERVICE_NAME="naumova-bot"

# Создаем пользователя для бота
echo "👤 Создание пользователя telegram..."
if ! id "telegram" &>/dev/null; then
    useradd -r -s /bin/false -d /opt/telegram_bots telegram
    echo "✅ Пользователь telegram создан"
else
    echo "ℹ️  Пользователь telegram уже существует"
fi

# Создаем директорию для ботов
echo "📁 Создание директории для ботов..."
mkdir -p /opt/telegram_bots
chown telegram:telegram /opt/telegram_bots

# Копируем файлы бота
echo "📋 Копирование файлов бота..."
if [ -d "$BOT_DIR" ]; then
    echo "ℹ️  Директория $BOT_DIR уже существует. Обновляем файлы..."
    cp -r . "$BOT_DIR/"
else
    cp -r . "$BOT_DIR"
fi

# Устанавливаем права доступа
echo "🔐 Настройка прав доступа..."
chown -R telegram:telegram "$BOT_DIR"
chmod -R 755 "$BOT_DIR"

# Создаем виртуальное окружение
echo "🐍 Создание виртуального окружения Python..."
cd "$BOT_DIR"
if [ ! -d "venv" ]; then
    sudo -u telegram python3.12 -m venv venv
    echo "✅ Виртуальное окружение создано"
else
    echo "ℹ️  Виртуальное окружение уже существует"
fi

# Устанавливаем зависимости
echo "📦 Установка зависимостей..."
sudo -u telegram "$BOT_DIR/venv/bin/pip" install -r requirements.txt

# Запускаем миграцию базы данных
echo "🗄️  Миграция базы данных..."
sudo -u telegram "$BOT_DIR/venv/bin/python" migrate_db.py

# Копируем service файл
echo "⚙️  Установка systemd службы..."
cp "$SERVICE_FILE" /etc/systemd/system/
systemctl daemon-reload

# Включаем автозапуск службы
echo "🚀 Включение автозапуска службы..."
systemctl enable "$SERVICE_NAME"

echo ""
echo "✅ Установка завершена!"
echo ""
echo "📋 Команды для управления службой:"
echo "   Запуск:     sudo systemctl start $SERVICE_NAME"
echo "   Остановка:  sudo systemctl stop $SERVICE_NAME"
echo "   Перезапуск: sudo systemctl restart $SERVICE_NAME"
echo "   Статус:     sudo systemctl status $SERVICE_NAME"
echo "   Логи:       sudo journalctl -u $SERVICE_NAME -f"
echo ""
echo "⚠️  Не забудьте настроить файл .env с токеном бота!"
echo "   Файл должен находиться в: $BOT_DIR/.env"
echo ""
echo "🚀 Для запуска бота выполните: sudo systemctl start $SERVICE_NAME" 