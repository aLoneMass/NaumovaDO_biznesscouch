#!/bin/bash

# Скрипт настройки ограничения размера логов для Naumova Telegram Bot
# Запускать с правами root: sudo ./setup_logging.sh

set -e

echo "📋 Настройка ограничения размера логов для Naumova Telegram Bot"
echo ""

# Проверяем, что скрипт запущен от root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Этот скрипт должен быть запущен с правами root (sudo)"
    exit 1
fi

# Создаем директорию для конфигурации journald
echo "📁 Создание директории для конфигурации journald..."
mkdir -p /etc/systemd/journald.conf.d

# Копируем конфигурацию
echo "⚙️  Копирование конфигурации логов..."
cp journald.conf /etc/systemd/journald.conf.d/naumova-bot.conf

# Перезапускаем journald
echo "🔄 Перезапуск journald..."
systemctl restart systemd-journald

# Проверяем статус
echo "📊 Проверка статуса journald..."
systemctl status systemd-journald --no-pager

echo ""
echo "✅ Настройка логов завершена!"
echo ""
echo "📋 Настройки:"
echo "   Максимальный размер логов: 10 МБ"
echo "   Время хранения: 7 дней"
echo "   Сжатие: включено"
echo ""
echo "📋 Команды для управления логами:"
echo "   Просмотр размера логов:"
echo "     sudo journalctl --disk-usage"
echo ""
echo "   Очистка старых логов:"
echo "     sudo journalctl --vacuum-size=10M"
echo "     sudo journalctl --vacuum-time=7d"
echo ""
echo "   Просмотр логов бота:"
echo "     sudo ./deploy.sh logs"
echo ""
echo "   Просмотр размера логов бота:"
echo "     sudo journalctl -u naumova-bot --disk-usage" 