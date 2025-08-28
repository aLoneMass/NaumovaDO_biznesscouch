from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

def get_contact_keyboard():
    """Клавиатура для запроса контакта"""
    keyboard = [
        [KeyboardButton("📱 Поделиться контактом", request_contact=True)]
    ]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

def get_request_actions_keyboard():
    """Инлайн клавиатура для действий с запросом"""
    keyboard = [
        [
            InlineKeyboardButton("🔄 Поменять запрос", callback_data="change_request"),
            InlineKeyboardButton("✅ Завершить", callback_data="finish")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_keyboard():
    """Клавиатура для администраторов"""
    keyboard = [
        [
            InlineKeyboardButton("👥 Все пользователи", callback_data="admin_show_users"),
            InlineKeyboardButton("📅 Сегодняшние", callback_data="admin_show_today")
        ],
        [
            InlineKeyboardButton("📊 Выгрузить в Excel", callback_data="admin_export_sheets"),
            InlineKeyboardButton("❓ Помощь", callback_data="admin_help")
        ]
    ]
    return InlineKeyboardMarkup(keyboard) 