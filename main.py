import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import os


BOT_TOKEN = "8842910786:AAHcY3m1aN23ZGJA6-jiYWn1z_3MZrIyXPk"
ADMIN_ID = 7165162714  

logging.basicConfig(level=logging.INFO)


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Состояния FSM
class AdminStates(StatesGroup):
    waiting_for_account = State()
    waiting_for_photo = State()
    waiting_for_video = State()
    waiting_for_file = State()

# Словарь для хранения временных данных
temp_data = {
    "user_chat_id": None,
    "app_key": None
}

# Словарь приложений
APPS = {
    "messenger": {"name": "Мессенджер Мак", "button": "📱 Установка Мессенджер Мак"},
    "avito": {"name": "Авито", "button": "🏪 Установка Авито"},
    "alfabank": {"name": "Альфа Банк", "button": "🏦 Установка Альфа Банк"},
}

# Главное меню
def get_main_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=APPS["messenger"]["button"], callback_data="app_messenger")],
        [InlineKeyboardButton(text=APPS["avito"]["button"], callback_data="app_avito")],
        [InlineKeyboardButton(text=APPS["alfabank"]["button"], callback_data="app_alfabank")],
        [InlineKeyboardButton(text="📱 Полный список приложений", callback_data="full_list")]
    ])
    return keyboard

# Меню для администратора
def get_admin_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Отправить аккаунт", callback_data="admin_send_account")],
        [InlineKeyboardButton(text="🖼️ Отправить фото", callback_data="admin_send_photo")],
        [InlineKeyboardButton(text="🎥 Отправить видео", callback_data="admin_send_video")],
        [InlineKeyboardButton(text="📎 Отправить файл", callback_data="admin_send_file")],
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")]
    ])
    return keyboard

# Клавиатура для возврата
def get_back_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")]
    ])
    return keyboard

@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        "👋 Привет! Я бот по помощи установки отечественных приложений на ваш iPhone.\n\n"
        "Выберите тип приложения:",
        reply_markup=get_main_menu()
    )

@dp.callback_query(lambda c: c.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery):
    # Если админ, показываем админ-меню
    if callback.from_user.id == ADMIN_ID:
        await callback.message.edit_text(
            "👨‍💼 Панель администратора\n\n"
            "Выберите действие:",
            reply_markup=get_admin_menu()
        )
    else:
        await callback.message.edit_text(
            "👋 Привет! Я бот по помощи установки отечественных приложений на ваш iPhone.\n\n"
            "Выберите тип приложения:",
            reply_markup=get_main_menu()
        )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "full_list")
async def full_list(callback: types.CallbackQuery):
    text = "📱 Полный список доступных приложений:\n\n"
    for key, app in APPS.items():
        text += f"• {app['name']}\n"
    text += "\nВыберите приложение из меню выше для установки."
    
    await callback.message.edit_text(
        text,
        reply_markup=get_back_menu()
    )
    await callback.answer()

# Обработчики для администратора
@dp.callback_query(lambda c: c.data == "admin_send_account" and c.from_user.id == ADMIN_ID)
async def admin_send_account(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "✏️ Введите логин и пароль для пользователя в формате:\n"
        "`логин:пароль`\n\n"
        "Или отправьте одним сообщением через пробел: `логин пароль`",
        parse_mode="Markdown"
    )
    await state.set_state(AdminStates.waiting_for_account)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "admin_send_photo" and c.from_user.id == ADMIN_ID)
async def admin_send_photo(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "🖼️ Отправьте фото, которое хотите передать пользователю.\n\n"
        "💡 Подсказка: можно отправить фото с подписью"
    )
    await state.set_state(AdminStates.waiting_for_photo)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "admin_send_video" and c.from_user.id == ADMIN_ID)
async def admin_send_video(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "🎥 Отправьте видео, которое хотите передать пользователю.\n\n"
        "💡 Подсказка: можно отправить видео с подписью"
    )
    await state.set_state(AdminStates.waiting_for_video)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "admin_send_file" and c.from_user.id == ADMIN_ID)
async def admin_send_file(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "📎 Отправьте файл, который хотите передать пользователю.\n\n"
        "Поддерживаются любые типы файлов"
    )
    await state.set_state(AdminStates.waiting_for_file)
    await callback.answer()

# Обработчик выбора приложения пользователем
@dp.callback_query(lambda c: c.data.startswith("app_"))
async def select_app(callback: types.CallbackQuery):
    app_key = callback.data.split("_")[1]
    app_name = APPS.get(app_key, {}).get("name", "неизвестное приложение")
    
    # Сохраняем данные пользователя
    temp_data["user_chat_id"] = callback.message.chat.id
    temp_data["app_key"] = app_key
    
    await callback.message.edit_text(
        f"⏳ Пожалуйста, ожидайте генерации аккаунта для установки приложения «{app_name}»...\n\n"
        f"Уведомление отправлено администратору. Ожидайте ответа.",
        reply_markup=get_back_menu()
    )
    
    # Уведомление администратору
    user = callback.from_user
    user_info = f"@{user.username}" if user.username else f"{user.full_name} (ID: {user.id})"
    
    admin_text = (
        f"🔔 **Новый запрос на установку приложения!**\n\n"
        f"👤 Пользователь: {user_info}\n"
        f"📱 Приложение: {app_name}\n"
        f"🆔 Chat ID: {callback.message.chat.id}\n\n"
        f"Используйте панель администратора для отправки аккаунта или файлов."
    )
    
    # Отправляем уведомление админу с меню
    await bot.send_message(
        chat_id=ADMIN_ID,
        text=admin_text,
        parse_mode="Markdown",
        reply_markup=get_admin_menu()
    )
    
    await callback.answer()

# Обработка ввода логина и пароля от админа
@dp.message(AdminStates.waiting_for_account)
async def handle_account_input(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет прав для этого действия.")
        await state.clear()
        return
    
    text = message.text.strip()
    
    # Проверяем формат
    if ":" in text:
        login, password = text.split(":", 1)
    elif " " in text:
        parts = text.split()
        if len(parts) >= 2:
            login, password = parts[0], " ".join(parts[1:])
        else:
            await message.answer("❌ Неверный формат! Используйте: `логин:пароль`")
            return
    else:
        await message.answer("❌ Неверный формат! Используйте: `логин:пароль`")
        return
    
    login = login.strip()
    password = password.strip()
    
    if not login or not password:
        await message.answer("❌ Логин и пароль не могут быть пустыми!")
        return
    
    user_id = temp_data.get("user_chat_id")
    if not user_id:
        await message.answer("❌ Нет активного запроса от пользователя!")
        await state.clear()
        return
    
    try:
        # Отправляем аккаунт пользователю
        await bot.send_message(
            chat_id=user_id,
            text=f"✅ Ваш аккаунт для установки приложения:\n\n"
                 f"🔑 Логин: `{login}`\n"
                 f"🔒 Пароль: `{password}`\n\n"
                 f"Используйте эти данные для входа в приложение.",
            parse_mode="Markdown"
        )
        
        await message.answer(f"✅ Аккаунт успешно отправлен пользователю (Chat ID: {user_id})")
        temp_data["user_chat_id"] = None
        
    except Exception as e:
        await message.answer(f"❌ Ошибка при отправке: {str(e)}")
    
    await state.clear()

# Обработка отправки фото от админа
@dp.message(AdminStates.waiting_for_photo)
async def handle_photo(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет прав для этого действия.")
        await state.clear()
        return
    
    if not message.photo:
        await message.answer("❌ Пожалуйста, отправьте фото.")
        return
    
    user_id = temp_data.get("user_chat_id")
    if not user_id:
        await message.answer("❌ Нет активного запроса от пользователя!")
        await state.clear()
        return
    
    try:
        # Отправляем фото пользователю
        photo = message.photo[-1]  # Берем фото в максимальном качестве
        caption = message.caption or "📸 Фото от администратора"
        
        await bot.send_photo(
            chat_id=user_id,
            photo=photo.file_id,
            caption=caption
        )
        
        await message.answer(f"✅ Фото успешно отправлено пользователю (Chat ID: {user_id})")
        
    except Exception as e:
        await message.answer(f"❌ Ошибка при отправке: {str(e)}")
    
    await state.clear()

# Обработка отправки видео от админа
@dp.message(AdminStates.waiting_for_video)
async def handle_video(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет прав для этого действия.")
        await state.clear()
        return
    
    if not message.video:
        await message.answer("❌ Пожалуйста, отправьте видео.")
        return
    
    user_id = temp_data.get("user_chat_id")
    if not user_id:
        await message.answer("❌ Нет активного запроса от пользователя!")
        await state.clear()
        return
    
    try:
        # Отправляем видео пользователю
        caption = message.caption or "🎥 Видео от администратора"
        
        await bot.send_video(
            chat_id=user_id,
            video=message.video.file_id,
            caption=caption
        )
        
        await message.answer(f"✅ Видео успешно отправлено пользователю (Chat ID: {user_id})")
        
    except Exception as e:
        await message.answer(f"❌ Ошибка при отправке: {str(e)}")
    
    await state.clear()

# Обработка отправки файла от админа
@dp.message(AdminStates.waiting_for_file)
async def handle_file(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет прав для этого действия.")
        await state.clear()
        return
    
    if not message.document:
        await message.answer("❌ Пожалуйста, отправьте файл.")
        return
    
    user_id = temp_data.get("user_chat_id")
    if not user_id:
        await message.answer("❌ Нет активного запроса от пользователя!")
        await state.clear()
        return
    
    try:
        # Отправляем файл пользователю
        caption = message.caption or "📎 Файл от администратора"
        
        await bot.send_document(
            chat_id=user_id,
            document=message.document.file_id,
            caption=caption
        )
        
        await message.answer(f"✅ Файл успешно отправлен пользователю (Chat ID: {user_id})")
        
    except Exception as e:
        await message.answer(f"❌ Ошибка при отправке: {str(e)}")
    
    await state.clear()

# Обработчик для сообщений от обычных пользователей
@dp.message()
async def handle_user_messages(message: types.Message):
    # Если сообщение от админа, но не в состоянии - показываем меню
    if message.from_user.id == ADMIN_ID:
        await message.answer(
            "👨‍💼 Панель администратора\n\n"
            "Используйте кнопки для управления:",
            reply_markup=get_admin_menu()
        )
        return
    
    # Для обычных пользователей
    await message.answer(
        "Используйте кнопки для выбора приложения.",
        reply_markup=get_main_menu()
    )

# Запуск бота
async def main():
    print("🤖 Бот запущен!")
    print(f"👨‍💼 ID администратора: {ADMIN_ID}")
    print("📱 Бот готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())