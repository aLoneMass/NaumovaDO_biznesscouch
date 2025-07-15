#!/bin/bash

# Скрипт быстрого развертывания Naumova Telegram Bot
# Использование: ./deploy.sh [install|update|restart|logs|status]

set -e

SERVICE_NAME="naumova-bot"
BOT_DIR="/opt/telegram_bots/NaumovaDO_biznesscouch"

case "$1" in
    "install")
        echo "🚀 Установка Naumova Telegram Bot..."
        sudo ./install_service.sh
        ;;
    "update")
        echo "📦 Обновление Naumova Telegram Bot..."
        if [ ! -d "$BOT_DIR" ]; then
            echo "❌ Бот не установлен. Сначала выполните: ./deploy.sh install"
            exit 1
        fi
        
        # Останавливаем службу
        sudo systemctl stop "$SERVICE_NAME" 2>/dev/null || true
        
        # Копируем новые файлы
        sudo cp -r . "$BOT_DIR/"
        sudo chown -R telegram:telegram "$BOT_DIR"
        
        # Обновляем зависимости
        sudo -u telegram "$BOT_DIR/venv/bin/pip" install -r requirements.txt
        
        # Запускаем миграцию
        sudo -u telegram "$BOT_DIR/venv/bin/python" migrate_db.py
        
        # Перезапускаем службу
        sudo systemctl restart "$SERVICE_NAME"
        echo "✅ Обновление завершено!"
        ;;
    "restart")
        echo "🔄 Перезапуск службы..."
        sudo systemctl restart "$SERVICE_NAME"
        echo "✅ Служба перезапущена!"
        ;;
    "stop")
        echo "🛑 Остановка службы..."
        sudo systemctl stop "$SERVICE_NAME"
        echo "✅ Служба остановлена!"
        ;;
    "start")
        echo "🚀 Запуск службы..."
        sudo systemctl start "$SERVICE_NAME"
        echo "✅ Служба запущена!"
        ;;
    "status")
        echo "📊 Статус службы:"
        sudo systemctl status "$SERVICE_NAME" --no-pager
        ;;
    "logs")
        echo "📋 Логи службы (Ctrl+C для выхода):"
        sudo journalctl -u "$SERVICE_NAME" -f
        ;;
    "logs-all")
        echo "📋 Все логи службы:"
        sudo journalctl -u "$SERVICE_NAME" --no-pager
        ;;
    "uninstall")
        echo "🗑️  Удаление Naumova Telegram Bot..."
        sudo ./uninstall_service.sh
        ;;
    *)
        echo "🤖 Naumova Telegram Bot - Скрипт управления"
        echo ""
        echo "Использование: ./deploy.sh [команда]"
        echo ""
        echo "Команды:"
        echo "  install    - Установить бота как службу"
        echo "  update     - Обновить файлы бота"
        echo "  restart    - Перезапустить службу"
        echo "  start      - Запустить службу"
        echo "  stop       - Остановить службу"
        echo "  status     - Показать статус службы"
        echo "  logs       - Показать логи в реальном времени"
        echo "  logs-all   - Показать все логи"
        echo "  uninstall  - Удалить бота и службу"
        echo ""
        echo "Примеры:"
        echo "  ./deploy.sh install    # Первая установка"
        echo "  ./deploy.sh update     # Обновление после изменений"
        echo "  ./deploy.sh logs       # Просмотр логов"
        ;;
esac 