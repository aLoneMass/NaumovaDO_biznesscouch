#!/bin/bash

# Скрипт настройки переменных окружения для Naumova Telegram Bot
# Использование: ./setup_env.sh

set -e

BOT_DIR="/opt/telegram_bots/NaumovaDO_biznesscouch"
ENV_FILE="$BOT_DIR/.env"

echo "⚙️  Настройка переменных окружения для Naumova Telegram Bot"
echo ""

# Проверяем, установлен ли бот
if [ ! -d "$BOT_DIR" ]; then
    echo "❌ Бот не установлен. Сначала выполните: ./deploy.sh install"
    exit 1
fi

# Проверяем, существует ли уже .env файл
if [ -f "$ENV_FILE" ]; then
    echo "ℹ️  Файл .env уже существует."
    read -p "Хотите перезаписать его? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Настройка отменена."
        exit 1
    fi
fi

echo ""
echo "📝 Введите данные для настройки бота:"
echo ""

# Запрашиваем токен бота
read -p "🤖 Токен бота от @BotFather: " BOT_TOKEN
if [ -z "$BOT_TOKEN" ]; then
    echo "❌ Токен бота обязателен!"
    exit 1
fi

# Запрашиваем ID администраторов
read -p "👥 ID администраторов (через запятую): " ADMINS
if [ -z "$ADMINS" ]; then
    echo "❌ ID администраторов обязательны!"
    exit 1
fi

# Запрашиваем ID для резервных копий
read -p "💾 ID для получения резервных копий: " BACKUPTO
if [ -z "$BACKUPTO" ]; then
    echo "❌ ID для резервных копий обязателен!"
    exit 1
fi

# Создаем .env файл
echo "📄 Создание файла .env..."
cat > "$ENV_FILE" << EOF
# Токен бота от @BotFather
BOT_TOKEN=$BOT_TOKEN

# ID администраторов (через запятую)
ADMINS=$ADMINS

# ID для отправки резервных копий
BACKUPTO=$BACKUPTO
EOF

# Устанавливаем правильные права доступа
chown telegram:telegram "$ENV_FILE"
chmod 600 "$ENV_FILE"

echo ""
echo "✅ Файл .env создан успешно!"
echo "📁 Расположение: $ENV_FILE"
echo ""
echo "📋 Настройки:"
echo "   Токен бота: ${BOT_TOKEN:0:10}..."
echo "   Администраторы: $ADMINS"
echo "   Резервные копии: $BACKUPTO"
echo ""
echo "🚀 Теперь можно запустить бота:"
echo "   ./deploy.sh restart" 