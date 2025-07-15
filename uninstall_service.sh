#!/bin/bash

# Скрипт удаления Naumova Telegram Bot systemd службы
# Запускать с правами root: sudo ./uninstall_service.sh

set -e

echo "🗑️  Удаление Naumova Telegram Bot systemd службы..."

# Проверяем, что скрипт запущен от root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Этот скрипт должен быть запущен с правами root (sudo)"
    exit 1
fi

# Пути
BOT_DIR="/opt/telegram_bots/NaumovaDO_biznesscouch"
SERVICE_NAME="naumova-bot"

# Останавливаем и отключаем службу
echo "🛑 Остановка службы..."
systemctl stop "$SERVICE_NAME" 2>/dev/null || true
systemctl disable "$SERVICE_NAME" 2>/dev/null || true

# Удаляем service файл
echo "🗂️  Удаление файлов службы..."
rm -f /etc/systemd/system/"$SERVICE_NAME".service
systemctl daemon-reload

# Удаляем файлы бота
echo "📁 Удаление файлов бота..."
if [ -d "$BOT_DIR" ]; then
    rm -rf "$BOT_DIR"
    echo "✅ Файлы бота удалены"
else
    echo "ℹ️  Директория бота не найдена"
fi

# Проверяем, есть ли другие боты в директории
if [ -d "/opt/telegram_bots" ] && [ -z "$(ls -A /opt/telegram_bots)" ]; then
    echo "📁 Удаление пустой директории /opt/telegram_bots..."
    rmdir /opt/telegram_bots
fi

# Удаляем пользователя telegram (если нет других ботов)
if [ ! -d "/opt/telegram_bots" ]; then
    echo "👤 Удаление пользователя telegram..."
    userdel telegram 2>/dev/null || true
    echo "✅ Пользователь telegram удален"
else
    echo "ℹ️  Пользователь telegram оставлен (есть другие боты)"
fi

echo ""
echo "✅ Удаление завершено!"
echo ""
echo "📋 Что было удалено:"
echo "   - systemd служба $SERVICE_NAME"
echo "   - Файлы бота в $BOT_DIR"
echo "   - Пользователь telegram (если не было других ботов)" 