import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes, ConversationHandler
)

from database import Database
from keyboards import get_contact_keyboard, get_request_actions_keyboard, get_admin_keyboard
from backup_service import BackupService

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния разговора
WAITING_CONTACT, WAITING_REQUEST = range(2)

# Инициализация базы данных
db = Database()

# Получение переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMINS = [int(admin_id.strip()) for admin_id in os.getenv('ADMINS', '').split(',') if admin_id.strip()]
BACKUPTO = os.getenv('BACKUPTO')

# Инициализация сервиса резервных копий
backup_service = None
if BOT_TOKEN and BACKUPTO:
    backup_service = BackupService(BOT_TOKEN, BACKUPTO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик команды /start"""
    user = update.effective_user
    
    # Проверяем, является ли пользователь администратором
    if user.id in ADMINS:
        await update.message.reply_text(
            "👋 Добро пожаловать в панель администратора!",
            reply_markup=get_admin_keyboard()
        )
        return ConversationHandler.END
    
    # Приветствие обычного пользователя
    await update.message.reply_text(
        f"👋 Здравствуйте, {user.first_name}!\n\n"
        "Для продолжения работы с ботом необходимо предоставить ваш контакт.",
        reply_markup=get_contact_keyboard()
    )
    
    return WAITING_CONTACT

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик получения контакта"""
    user = update.effective_user
    contact = update.message.contact
    
    # Сохраняем пользователя в базу данных
    success = db.add_user(
        telegram_id=user.id,
        first_name=contact.first_name or user.first_name,
        last_name=contact.last_name or user.last_name,
        phone=contact.phone_number
    )
    
    if success:
        await update.message.reply_text(
            "✅ Контакт успешно получен!\n\n"
            "Теперь, пожалуйста, введите ваш запрос в свободной форме.\n"
            "Это может быть текст, фото, голосовое сообщение или видеокружок.",
            reply_markup=ReplyKeyboardRemove()
        )
        return WAITING_REQUEST
    else:
        await update.message.reply_text(
            "❌ Произошла ошибка при сохранении контакта. Попробуйте еще раз.",
            reply_markup=get_contact_keyboard()
        )
        return WAITING_CONTACT

async def handle_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик получения запроса пользователя"""
    user = update.effective_user
    
    # Определяем тип контента и формируем описание
    if update.message.text:
        request_content = f"Текст: {update.message.text}"
    elif update.message.photo:
        request_content = f"Фото: {update.message.caption or 'Без описания'}"
    elif update.message.voice:
        request_content = f"Голосовое сообщение: {update.message.caption or 'Без описания'}"
    elif update.message.video_note:
        request_content = f"Видеокружок: {update.message.caption or 'Без описания'}"
    else:
        request_content = "Неизвестный тип контента"
    
    # Сохраняем запрос в базу данных
    success = db.update_user_request(user.id, request_content)
    
    if success:
        await update.message.reply_text(
            "🙏 Спасибо! Ваш запрос принят и будет обработан в ближайшее время.",
            reply_markup=get_request_actions_keyboard()
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            "❌ Произошла ошибка при сохранении запроса. Попробуйте еще раз."
        )
        return WAITING_REQUEST

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик callback запросов"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    if query.data == "change_request":
        await query.edit_message_text(
            "Пожалуйста, введите новый запрос в свободной форме.\n"
            "Это может быть текст, фото, голосовое сообщение или видеокружок."
        )
        context.user_data['waiting_for_new_request'] = True
        return WAITING_REQUEST
    
    elif query.data == "finish":
        await query.edit_message_text("✅ Спасибо за обращение! До свидания!")
        return ConversationHandler.END
    
    # Обработка админских команд
    elif user.id in ADMINS:
        if query.data == "show_all_users":
            users = db.get_all_users()
            if users:
                message = "👥 Все пользователи:\n\n"
                for user_data in users:
                    message += f"ID: {user_data[1]}\n"
                    message += f"Имя: {user_data[2]} {user_data[3] or ''}\n"
                    message += f"Телефон: {user_data[4]}\n"
                    message += f"Регистрация: {user_data[5]}\n"
                    message += f"Запрос: {user_data[6] or 'Не указан'}\n"
                    message += "─" * 30 + "\n"
                
                # Разбиваем на части, если сообщение слишком длинное
                if len(message) > 4096:
                    for i in range(0, len(message), 4096):
                        await query.message.reply_text(message[i:i+4096])
                else:
                    await query.message.reply_text(message)
            else:
                await query.message.reply_text("📭 Пользователей пока нет.")
        
        elif query.data == "show_today":
            users = db.get_today_registrations()
            if users:
                message = f"📅 Регистрации за {datetime.now().strftime('%d.%m.%Y')}:\n\n"
                for user_data in users:
                    message += f"ID: {user_data[1]}\n"
                    message += f"Имя: {user_data[2]} {user_data[3] or ''}\n"
                    message += f"Телефон: {user_data[4]}\n"
                    message += f"Время: {user_data[5]}\n"
                    message += f"Запрос: {user_data[6] or 'Не указан'}\n"
                    message += "─" * 30 + "\n"
                
                if len(message) > 4096:
                    for i in range(0, len(message), 4096):
                        await query.message.reply_text(message[i:i+4096])
                else:
                    await query.message.reply_text(message)
            else:
                await query.message.reply_text("📭 Сегодня новых регистраций нет.")

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /admin для администраторов"""
    user = update.effective_user
    
    if user.id in ADMINS:
        await update.message.reply_text(
            "👋 Панель администратора",
            reply_markup=get_admin_keyboard()
        )
    else:
        await update.message.reply_text("❌ У вас нет доступа к панели администратора.")

def main() -> None:
    """Основная функция запуска бота"""
    if not BOT_TOKEN:
        logger.error("Не указан токен бота в переменной BOT_TOKEN")
        return
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Создаем обработчик разговора для обычных пользователей
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAITING_CONTACT: [
                MessageHandler(filters.CONTACT, handle_contact),
                MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: u.message.reply_text(
                    "Пожалуйста, поделитесь контактом, используя кнопку ниже.",
                    reply_markup=get_contact_keyboard()
                ))
            ],
            WAITING_REQUEST: [
                MessageHandler(
                    filters.TEXT | filters.PHOTO | filters.VOICE | filters.VIDEO_NOTE,
                    handle_request
                )
            ]
        },
        fallbacks=[CommandHandler("start", start)]
    )
    
    # Добавляем обработчики
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(CommandHandler("admin", admin_command))
    
    # Запускаем сервис резервных копий
    if backup_service:
        backup_service.start_scheduler()
    
    # Запускаем бота
    print("🤖 Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main() 