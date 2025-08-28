#!/usr/bin/env python3
"""
Telegram bot for NaumovaDO business coach
"""
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardRemove, BotCommand, BotCommandScopeChat
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes, ConversationHandler
)

from database import Database
from keyboards import get_contact_keyboard, get_request_actions_keyboard
from backup_service import BackupService
from google_sheets_service import GoogleSheetsService

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

# Путь к базе данных
DB_PATH = "/opt/telegram_bots/NaumovaDO_biznesscouch/naumovado.db"

# Инициализация сервиса резервных копий
backup_service = None
if BOT_TOKEN and BACKUPTO:
    backup_service = BackupService(BOT_TOKEN, BACKUPTO, DB_PATH)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик команды /start"""
    user = update.effective_user
    
    # Проверяем, является ли пользователь администратором
    if user.id in ADMINS:
        await update.message.reply_text(
            "👋 Добро пожаловать в панель администратора!\n\n"
            "Используйте команды из меню бота (кнопка 'Меню' рядом со строкой ввода):\n"
            "• /show_users - показать всех пользователей\n"
            "• /show_today - показать сегодняшние регистрации\n"
            "• /export_sheets - выгрузить базу в Excel\n\n"
            "Или нажмите /help для получения справки."
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
    request_type = None
    file_id = None
    
    if update.message.text:
        request_content = f"Текст: {update.message.text}"
        request_type = "text"
    elif update.message.photo:
        request_content = f"Фото: {update.message.caption or 'Без описания'}"
        request_type = "photo"
        file_id = update.message.photo[-1].file_id  # Берем последнее (самое качественное) фото
    elif update.message.voice:
        request_content = f"Голосовое сообщение: {update.message.caption or 'Без описания'}"
        request_type = "voice"
        file_id = update.message.voice.file_id
    elif update.message.video_note:
        request_content = f"Видеокружок: {update.message.caption or 'Без описания'}"
        request_type = "video_note"
        file_id = update.message.video_note.file_id
    else:
        request_content = "Неизвестный тип контента"
        request_type = "unknown"
    
    # Сохраняем запрос в базу данных
    success = db.update_user_request(user.id, request_content, request_type, file_id)
    
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
    


async def show_users_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда для показа всех пользователей"""
    user = update.effective_user
    
    if user.id not in ADMINS:
        await update.message.reply_text("❌ У вас нет доступа к этой команде.")
        return
    
    users = db.get_all_users()
    if users:
        message = "👥 Все пользователи:\n\n"
        for user_data in users:
            message += f"ID: {user_data[1]}\n"
            message += f"Имя: {user_data[2]} {user_data[3] or ''}\n"
            message += f"Телефон: {user_data[4]}\n"
            message += f"Регистрация: {user_data[5]}\n"
            message += f"Запрос: {user_data[6] or 'Не указан'}\n"
            
            # Добавляем информацию о типе контента
            if user_data[7]:  # request_type
                message += f"Тип контента: {user_data[7]}\n"
            
            message += "─" * 30 + "\n"
        
        # Разбиваем на части, если сообщение слишком длинное
        if len(message) > 4096:
            for i in range(0, len(message), 4096):
                await update.message.reply_text(message[i:i+4096])
        else:
            await update.message.reply_text(message)
        
        # Отправляем медиафайлы отдельно
        await send_media_files(context.bot, update.message.chat_id, users)
    else:
        await update.message.reply_text("📭 Пользователей пока нет.")

async def show_today_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда для показа сегодняшних регистраций"""
    user = update.effective_user
    
    if user.id not in ADMINS:
        await update.message.reply_text("❌ У вас нет доступа к этой команде.")
        return
    
    users = db.get_today_registrations()
    if users:
        message = f"📅 Регистрации за {datetime.now().strftime('%d.%m.%Y')}:\n\n"
        for user_data in users:
            message += f"ID: {user_data[1]}\n"
            message += f"Имя: {user_data[2]} {user_data[3] or ''}\n"
            message += f"Телефон: {user_data[4]}\n"
            message += f"Время: {user_data[5]}\n"
            message += f"Запрос: {user_data[6] or 'Не указан'}\n"
            
            # Добавляем информацию о типе контента
            if user_data[7]:  # request_type
                message += f"Тип контента: {user_data[7]}\n"
            
            message += "─" * 30 + "\n"
        
        if len(message) > 4096:
            for i in range(0, len(message), 4096):
                await update.message.reply_text(message[i:i+4096])
        else:
            await update.message.reply_text(message)
        
        # Отправляем медиафайлы отдельно
        await send_media_files(context.bot, update.message.chat_id, users)
    else:
        await update.message.reply_text("📭 Сегодня новых регистраций нет.")

async def send_media_files(bot, chat_id, users):
    """Отправка медиафайлов администратору"""
    for user_data in users:
        if user_data[8]:  # file_id
            try:
                caption = f"📎 Медиафайл от пользователя {user_data[2]} {user_data[3] or ''} (ID: {user_data[1]})"
                
                if user_data[7] == "photo":
                    await bot.send_photo(chat_id=chat_id, photo=user_data[8], caption=caption)
                elif user_data[7] == "voice":
                    await bot.send_voice(chat_id=chat_id, voice=user_data[8], caption=caption)
                elif user_data[7] == "video_note":
                    await bot.send_video_note(chat_id=chat_id, video_note=user_data[8])
                    await bot.send_message(chat_id=chat_id, text=caption)
                
                # Небольшая задержка между отправками
                import asyncio
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Ошибка при отправке медиафайла для пользователя {user_data[1]}: {e}")

async def export_to_sheets_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда экспорта данных в Google Sheets"""
    user = update.effective_user
    
    if user.id not in ADMINS:
        await update.message.reply_text("❌ У вас нет прав для выполнения этой команды.")
        return
    
    await update.message.reply_text("🔄 Начинаю экспорт данных в Google Sheets...")
    
    try:
        # Инициализируем сервис Google Sheets
        sheets_service = GoogleSheetsService()
        
        # Получаем информацию о таблице
        sheet_info = sheets_service.get_sheet_info()
        if sheet_info:
            await update.message.reply_text(
                f"📊 Таблица: {sheet_info.get('title', 'Неизвестно')}\n"
                f"🔗 Ссылка: {sheet_info.get('url', 'Недоступна')}"
            )
        
        # Получаем всех пользователей из базы
        users = db.get_all_users()
        await update.message.reply_text(f"👥 Найдено {len(users)} пользователей в базе данных")
        
        if not users:
            await update.message.reply_text("ℹ️ Нет пользователей для экспорта")
            return
        
        # Экспортируем данные
        success = sheets_service.export_users_to_sheets(users)
        
        if success:
            await update.message.reply_text("✅ Экспорт завершен успешно!")
        else:
            await update.message.reply_text("❌ Ошибка при экспорте данных")
            
    except Exception as e:
        error_msg = f"❌ Ошибка экспорта: {str(e)}"
        logger.error(error_msg)
        await update.message.reply_text(error_msg)

async def handle_admin_show_users(query, context):
    """Обработчик кнопки 'Все пользователи' для администраторов"""
    users = db.get_all_users()
    if users:
        message = "👥 Все пользователи:\n\n"
        for user_data in users:
            message += f"ID: {user_data[1]}\n"
            message += f"Имя: {user_data[2]} {user_data[3] or ''}\n"
            message += f"Телефон: {user_data[4]}\n"
            message += f"Регистрация: {user_data[5]}\n"
            message += f"Запрос: {user_data[6] or 'Не указан'}\n"
            
            if user_data[7]:  # request_type
                message += f"Тип контента: {user_data[7]}\n"
            
            message += "─" * 30 + "\n"
        
        # Разбиваем на части, если сообщение слишком длинное
        if len(message) > 4096:
            for i in range(0, len(message), 4096):
                await query.edit_message_text(message[i:i+4096])
        else:
            await query.edit_message_text(message)
        
        # Отправляем медиафайлы отдельно
        await send_media_files(context.bot, query.message.chat_id, users)
    else:
        await query.edit_message_text("📭 Пользователей пока нет.")

async def handle_admin_show_today(query, context):
    """Обработчик кнопки 'Сегодняшние' для администраторов"""
    users = db.get_today_registrations()
    if users:
        message = f"📅 Регистрации за {datetime.now().strftime('%d.%m.%Y')}:\n\n"
        for user_data in users:
            message += f"ID: {user_data[1]}\n"
            message += f"Имя: {user_data[2]} {user_data[3] or ''}\n"
            message += f"Телефон: {user_data[4]}\n"
            message += f"Время: {user_data[5]}\n"
            message += f"Запрос: {user_data[6] or 'Не указан'}\n"
            
            if user_data[7]:  # request_type
                message += f"Тип контента: {user_data[7]}\n"
            
            message += "─" * 30 + "\n"
        
        if len(message) > 4096:
            for i in range(0, len(message), 4096):
                await query.edit_message_text(message[i:i+4096])
        else:
            await query.edit_message_text(message)
        
        # Отправляем медиафайлы отдельно
        await send_media_files(context.bot, query.message.chat_id, users)
    else:
        await query.edit_message_text("📭 Сегодня новых регистраций нет.")

async def handle_admin_export_sheets(query, context):
    """Обработчик кнопки 'Выгрузить в Excel' для администраторов"""
    await query.edit_message_text("🔄 Начинаю экспорт данных в Google Sheets...")
    
    try:
        # Инициализируем сервис Google Sheets
        sheets_service = GoogleSheetsService()
        
        # Получаем информацию о таблице
        sheet_info = sheets_service.get_sheet_info()
        if sheet_info:
            await query.edit_message_text(
                f"📊 Таблица: {sheet_info.get('title', 'Неизвестно')}\n"
                f"🔗 Ссылка: {sheet_info.get('url', 'Недоступна')}\n\n"
                "🔄 Экспортирую данные..."
            )
        
        # Получаем всех пользователей из базы
        users = db.get_all_users()
        await query.edit_message_text(f"👥 Найдено {len(users)} пользователей в базе данных\n\n🔄 Экспортирую...")
        
        if not users:
            await query.edit_message_text("ℹ️ Нет пользователей для экспорта")
            return
        
        # Экспортируем данные
        success = sheets_service.export_users_to_sheets(users)
        
        if success:
            await query.edit_message_text(
                "✅ Экспорт завершен успешно!\n\n"
                f"📊 Данные выгружены в таблицу: {sheet_info.get('title', 'Неизвестно')}\n"
                f"🔗 Ссылка: {sheet_info.get('url', 'Недоступна')}"
            )
        else:
            await query.edit_message_text("❌ Ошибка при экспорте данных")
            
    except Exception as e:
        error_msg = f"❌ Ошибка экспорта: {str(e)}"
        logger.error(error_msg)
        await query.edit_message_text(error_msg)

async def handle_admin_help(query, context):
    """Обработчик кнопки 'Помощь' для администраторов"""
    help_text = (
        "🤖 Помощь по управлению ботом:\n\n"
        "👥 Все пользователи - показать всех зарегистрированных пользователей\n"
        "📅 Сегодняшние - показать регистрации за сегодня\n"
        "📊 Выгрузить в Excel - экспортировать новых пользователей в Google Sheets\n"
        "❓ Помощь - показать эту справку\n\n"
        "💡 Используйте кнопки выше для управления ботом"
    )
    await query.edit_message_text(help_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда помощи"""
    user = update.effective_user
    
    if user.id in ADMINS:
        help_text = (
            "🤖 Помощь по командам бота:\n\n"
            "Для администраторов:\n"
            "• /start - приветствие и инструкции\n"
            "• /show_users - показать всех пользователей\n"
            "• /show_today - показать сегодняшние регистрации\n"
            "• /export_sheets - выгрузить базу в Excel\n"
            "• /help - показать эту справку\n\n"
            "💡 Все команды доступны в меню бота (кнопка 'Меню' рядом со строкой ввода)\n\n"
            "Для пользователей:\n"
            "• /start - начать работу с ботом"
        )
    else:
        help_text = (
            "🤖 Помощь по использованию бота:\n\n"
            "1. Нажмите /start для начала работы\n"
            "2. Поделитесь контактом\n"
            "3. Отправьте ваш запрос (текст, фото, голосовое или видеокружок)\n"
            "4. При необходимости измените запрос или завершите работу"
        )
    
    await update.message.reply_text(help_text)

async def setup_bot_commands(application):
    """Настройка команд бота для разных типов пользователей"""
    try:
        # Базовые команды для всех пользователей
        basic_commands = [
            BotCommand("start", "🚀 Начать работу с ботом"),
            BotCommand("help", "❓ Справка по командам")
        ]
        
        # Команды для администраторов
        admin_commands = [
            BotCommand("show_users", "👥 Показать всех пользователей"),
            BotCommand("show_today", "📅 Сегодняшние регистрации"),
            BotCommand("export_sheets", "📊 Выгрузить базу в Excel")
        ]
        
        # Устанавливаем базовые команды для всех пользователей
        await application.bot.set_my_commands(basic_commands)
        
        # Устанавливаем команды для администраторов (они будут видны только им)
        if ADMINS:
            for admin_id in ADMINS:
                try:
                    await application.bot.set_my_commands(
                        basic_commands + admin_commands,
                        scope=BotCommandScopeChat(chat_id=admin_id)
                    )
                except Exception as e:
                    logger.warning(f"Не удалось установить команды для админа {admin_id}: {e}")
        
        logger.info("✅ Команды бота настроены")
        
    except Exception as e:
        logger.error(f"❌ Ошибка настройки команд: {e}")

def main() -> None:
    """Основная функция запуска бота"""
    if not BOT_TOKEN:
        logger.error("Не указан токен бота в переменной BOT_TOKEN")
        return
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Настраиваем команды бота через post_init
    application.post_init = setup_bot_commands
    
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
    application.add_handler(CommandHandler("show_users", show_users_command))
    application.add_handler(CommandHandler("show_today", show_today_command))
    application.add_handler(CommandHandler("export_sheets", export_to_sheets_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Запускаем сервис резервных копий
    if backup_service:
        logger.info("🔄 Инициализация сервиса резервных копий...")
        backup_service.start_scheduler()
        logger.info("✅ Сервис резервных копий запущен")
    else:
        logger.warning("⚠️ Сервис резервных копий не инициализирован (отсутствует токен или BACKUPTO)")
    
    # Запускаем бота
    print("🤖 Бот запущен...")
    
    # Команды бота можно настроить вручную через BotFather или через API после запуска
    # Для автоматической настройки команд используйте BotFather: /setcommands
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main() 