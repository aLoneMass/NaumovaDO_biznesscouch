#!/bin/bash

# Скрипт для развертывания и управления Telegram ботом Наумовой

BOT_DIR="/home/telegram/naumova-bot"
SERVICE_NAME="naumova-bot"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ОШИБКА: $1${NC}"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ПРЕДУПРЕЖДЕНИЕ: $1${NC}"
}

# Проверка прав администратора
check_sudo() {
    if [[ $EUID -ne 0 ]]; then
        error "Этот скрипт должен выполняться с правами администратора (sudo)"
        exit 1
    fi
}

# Установка службы
install() {
    log "Установка Telegram бота Наумовой..."
    
    # Создание пользователя telegram
    if ! id "telegram" &>/dev/null; then
        log "Создание пользователя telegram..."
        useradd -r -s /bin/bash -d /home/telegram telegram
    fi
    
    # Создание директории
    mkdir -p $BOT_DIR
    chown telegram:telegram $BOT_DIR
    
    # Копирование файлов
    log "Копирование файлов..."
    cp -r . $BOT_DIR/
    chown -R telegram:telegram $BOT_DIR
    
    # Установка зависимостей
    log "Установка зависимостей Python..."
    sudo -u telegram bash -c "cd $BOT_DIR && pip3 install -r requirements.txt"
    
    # Создание файла службы systemd
    cat > /etc/systemd/system/$SERVICE_NAME.service << EOF
[Unit]
Description=Telegram Bot Naumova
After=network.target

[Service]
Type=simple
User=telegram
WorkingDirectory=$BOT_DIR
Environment=PATH=$BOT_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=/usr/bin/python3 $BOT_DIR/bot.py
Restart=always
RestartSec=10

# Логирование
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$SERVICE_NAME

# Ограничения
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=$BOT_DIR

[Install]
WantedBy=multi-user.target
EOF

    # Настройка journald для ограничения размера логов
    mkdir -p /etc/systemd/journald.conf.d
    cat > /etc/systemd/journald.conf.d/naumova-bot.conf << EOF
# Ограничение логов для бота Наумовой
[Journal]
SystemMaxUse=10M
SystemKeepFree=100M
SystemMaxFileSize=1M
Compress=yes
MaxRetentionSec=7day
EOF

    # Перезагрузка systemd и включение службы
    systemctl daemon-reload
    systemctl enable $SERVICE_NAME
    
    log "Установка завершена!"
    log "Для запуска бота выполните: sudo ./deploy.sh start"
    log "Для настройки переменных окружения: sudo ./deploy.sh setup-env"
}

# Удаление службы
uninstall() {
    log "Удаление Telegram бота Наумовой..."
    
    # Остановка и отключение службы
    systemctl stop $SERVICE_NAME 2>/dev/null || true
    systemctl disable $SERVICE_NAME 2>/dev/null || true
    
    # Удаление файла службы
    rm -f /etc/systemd/system/$SERVICE_NAME.service
    systemctl daemon-reload
    
    # Удаление конфигурации journald
    rm -f /etc/systemd/journald.conf.d/naumova-bot.conf
    
    # Удаление директории (с подтверждением)
    if [ -d "$BOT_DIR" ]; then
        read -p "Удалить директорию $BOT_DIR? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf $BOT_DIR
            log "Директория удалена"
        fi
    fi
    
    log "Удаление завершено!"
}

# Настройка переменных окружения
setup_env() {
    log "Настройка переменных окружения..."
    
    if [ ! -f "$BOT_DIR/.env" ]; then
        cp $BOT_DIR/.env.example $BOT_DIR/.env
        chown telegram:telegram $BOT_DIR/.env
        chmod 600 $BOT_DIR/.env
        log "Файл .env создан из .env.example"
        log "Отредактируйте файл $BOT_DIR/.env и укажите необходимые переменные"
    else
        log "Файл .env уже существует"
    fi
    
    log "Для редактирования выполните: sudo nano $BOT_DIR/.env"
}

# Запуск службы
start() {
    log "Запуск службы $SERVICE_NAME..."
    systemctl start $SERVICE_NAME
    systemctl status $SERVICE_NAME --no-pager
}

# Остановка службы
stop() {
    log "Остановка службы $SERVICE_NAME..."
    systemctl stop $SERVICE_NAME
    systemctl status $SERVICE_NAME --no-pager
}

# Перезапуск службы
restart() {
    log "Перезапуск службы $SERVICE_NAME..."
    systemctl restart $SERVICE_NAME
    systemctl status $SERVICE_NAME --no-pager
}

# Статус службы
status() {
    log "Статус службы $SERVICE_NAME:"
    systemctl status $SERVICE_NAME --no-pager
}

# Просмотр логов
logs() {
    log "Логи службы (Ctrl+C для выхода):"
    journalctl -u $SERVICE_NAME -f
}

# Обновление бота
update() {
    log "Обновление бота..."
    
    # Остановка службы
    systemctl stop $SERVICE_NAME
    
    # Резервная копия
    if [ -d "$BOT_DIR" ]; then
        cp -r $BOT_DIR ${BOT_DIR}_backup_$(date +%Y%m%d_%H%M%S)
        log "Создана резервная копия"
    fi
    
    # Копирование новых файлов
    cp -r . $BOT_DIR/
    chown -R telegram:telegram $BOT_DIR
    
    # Установка зависимостей
    sudo -u telegram bash -c "cd $BOT_DIR && pip3 install -r requirements.txt"
    
    # Запуск службы
    systemctl start $SERVICE_NAME
    
    log "Обновление завершено!"
    systemctl status $SERVICE_NAME --no-pager
}

# Проверка базы данных
check_db() {
    log "Проверка базы данных..."
    sudo -u telegram bash -c "cd $BOT_DIR && python3 check_db.py"
}

# Тестирование резервного копирования
test_backup() {
    log "Тестирование резервного копирования..."
    sudo -u telegram bash -c "cd $BOT_DIR && python3 test_backup.py"
}

# Очистка логов
clean_logs() {
    log "Очистка логов..."
    journalctl --vacuum-time=1d --unit=$SERVICE_NAME
    log "Логи очищены"
}

# Показать справку
show_help() {
    echo "Использование: $0 {команда}"
    echo ""
    echo "Команды:"
    echo "  install     - Установить бота как службу"
    echo "  uninstall   - Удалить бота и службу"
    echo "  setup-env   - Настроить переменные окружения"
    echo "  start       - Запустить службу"
    echo "  stop        - Остановить службу"
    echo "  restart     - Перезапустить службу"
    echo "  status      - Показать статус службы"
    echo "  logs        - Показать логи в реальном времени"
    echo "  update      - Обновить бота"
    echo "  check-db    - Проверить состояние базы данных"
    echo "  test-backup - Протестировать резервное копирование"
    echo "  clean-logs  - Очистить старые логи"
    echo "  help        - Показать эту справку"
    echo ""
    echo "Примеры:"
    echo "  sudo $0 install    # Установка"
    echo "  sudo $0 setup-env  # Настройка переменных"
    echo "  sudo $0 start      # Запуск"
    echo "  sudo $0 logs       # Просмотр логов"
}

# Основная логика
case "$1" in
    install)
        check_sudo
        install
        ;;
    uninstall)
        check_sudo
        uninstall
        ;;
    setup-env)
        check_sudo
        setup_env
        ;;
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    logs)
        logs
        ;;
    update)
        check_sudo
        update
        ;;
    check-db)
        check_db
        ;;
    test-backup)
        test_backup
        ;;
    clean-logs)
        clean_logs
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        error "Неизвестная команда: $1"
        echo ""
        show_help
        exit 1
        ;;
esac 