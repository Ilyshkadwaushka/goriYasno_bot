from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton


start_game_btn = InlineKeyboardMarkup(row_width=1).add(
    InlineKeyboardButton('Готов ✅', callback_data='start_game')
)


player_menu = ReplyKeyboardMarkup(
    resize_keyboard=True, one_time_keyboard=False, row_width=2
).add(KeyboardButton("Баланс 💰"), KeyboardButton("Рейтинг 🏆"), KeyboardButton("Узнать токен 📇"), KeyboardButton("Обновить меню 📖"))

admin_menu = ReplyKeyboardMarkup(
    resize_keyboard=True, one_time_keyboard=False, row_width=2
).add(KeyboardButton("Пополнить баланс 📈"), KeyboardButton("Уменьшить баланс 📉"), KeyboardButton("Узнать чужой баланс 🔍"),
      KeyboardButton("Дать админку ⚖️"), KeyboardButton("Баланс 💰"), KeyboardButton("Рейтинг 🏆"),
      KeyboardButton("Узнать токен 📇"), KeyboardButton("Обновить меню 📖"))

cancel_process_score = ReplyKeyboardMarkup(
    resize_keyboard=True, one_time_keyboard=True, row_width=1
).add(KeyboardButton(text='Отмена ❌'))

score = InlineKeyboardMarkup(row_width=5).add(
    InlineKeyboardButton(text='10', callback_data='score_10'),
    InlineKeyboardButton(text='15', callback_data='score_15'),
    InlineKeyboardButton(text='20', callback_data='score_20'),
    InlineKeyboardButton(text='25', callback_data='score_25'),
    InlineKeyboardButton(text='30', callback_data='score_30')
)

isSendableBtns = InlineKeyboardMarkup(row_width=2).add(
    InlineKeyboardButton('Да', callback_data='send_btn'),
    InlineKeyboardButton('Нет', callback_data='not_send_btn')
)