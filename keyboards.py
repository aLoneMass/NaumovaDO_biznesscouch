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
            InlineKeyboardButton("👥 Показать всех пользователей", callback_data="show_all_users"),
            InlineKeyboardButton("📅 Показать сегодняшние регистрации", callback_data="show_today")
        ]
    ]
    return InlineKeyboardMarkup(keyboard) 