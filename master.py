import logging
import yaml
#import urllib.parse as urlparse
#import os
import secrets
import asyncio

import aiogram.utils.markdown as md
from aiogram.dispatcher.filters import Text
from aiogram.types import ParseMode

from aiogram.utils import executor
from aiogram import Bot, Dispatcher, types

from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State,StatesGroup

# Errors
from aiogram.utils.exceptions import BotBlocked, ChatNotFound, UserDeactivated, \
    MessageToDeleteNotFound, MessageCantBeDeleted


from database import UserDatabase, ScoreLogsDatabase
import keys as kb

url = urlparse.urlparse(os.environ['DATABASE_URL'])


user_db = UserDatabase(url)
score_db = ScoreLogsDatabase(url)

with open("config.yml", "r") as stream:
    try:
        token = yaml.safe_load(stream)['TOKEN']
    except yaml.YAMLError as exception:
        logging.error(exception)

bot = Bot(token=token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# States
class SetScore(StatesGroup):
    token = State()
    score = State()

class DelScore(StatesGroup):
    token = State()
    score = State()

class MakeMessage(StatesGroup):
    message = State()
    isSendable = State()

class AdminDeleteForm(StatesGroup):
    token = State()

class AdminForm(StatesGroup):
    token = State()

class BalanceForm(StatesGroup):
    token = State()

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):

    messageText = f"{md.bold('Привет, рад видеть тебя 👋')}\n\n" \
                  f"Гори Ясно \- это ежегодное мероприятие СтудАктива Бизнес\-информатики, посвящённое Масленице 🥞\n" \
                  f"Каждый год мы готовим увлекательную программу, собираемся вместе, угощаем гостей блинами, запиваем напитками разного уровня крепости и танцуем до утра\n\n" \
                  f"{md.bold('Ты готов начать игру? 🧐')}"

    await message.answer(messageText, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb.start_game_btn)

@dp.message_handler(Text(equals='Обновить меню 📖', ignore_case=True))
@dp.message_handler(commands=['menu'])
async def menu_update(message: types.Message):
    if user_db.isAdmin(message.from_user.id):
        await message.answer(md.bold("Твое меню обновлено 🥴"), parse_mode=ParseMode.MARKDOWN_V2,
                             reply_markup=kb.admin_menu)
    else:
        await message.answer(md.bold("Твое меню обновлено 🥴"), parse_mode=ParseMode.MARKDOWN_V2,
                             reply_markup=kb.player_menu)

async def generate_key():
    return secrets.token_hex(3)

@dp.callback_query_handler(text=['start_game'])
async def cmd_start_game(query: types.CallbackQuery):
    username = query.from_user.username if query.from_user.username is not None else 'None'
    token = await generate_key()


    if user_db.user_exists(query.from_user.id):
        user_db.update_user(user_bot_id=query.from_user.id, username=username)
        token = user_db.get_token(user_bot_id=query.from_user.id)[0]
    else:
        while not user_db.valid_token(token):
            token = await generate_key()

        user_db.add_user(user_bot_id=query.from_user.id, token=token, username=username)

    messageText = f"{md.italic('Поздравляю тебя, ты в игре 🤪!')}\n\n" \
                  f"{md.italic('Твой игровой токен 📇:')} {md.bold(token)}"

    try:
        await bot.send_message(query.from_user.id, messageText, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb.player_menu)
    except (BotBlocked, ChatNotFound, UserDeactivated) as exception:
        logging.error(exception)


@dp.message_handler(lambda message: user_db.user_exists(message.from_user.id), Text(equals='Узнать токен 📇', ignore_case=True))
@dp.message_handler(lambda message: user_db.user_exists(message.from_user.id), commands=['token'])
async def get_token(message: types.Message):
    token = user_db.get_token(user_bot_id=message.from_user.id)[0]

    try:
        await message.answer(f"{md.italic('Твой токен 📇:')} {md.bold(token)} ", parse_mode=ParseMode.MARKDOWN_V2)
    except (BotBlocked, ChatNotFound, UserDeactivated) as exception:
        logging.error(exception)


@dp.message_handler(lambda message: user_db.user_exists(message.from_user.id), Text(equals='Баланс 💰', ignore_case=True))
@dp.message_handler(lambda message: user_db.user_exists(message.from_user.id), commands=['getscore'])
async def get_score(message: types.Message):
    score = user_db.get_score_by_user_bot_id(user_bot_id=message.from_user.id)

    try:
        await message.answer(f"{md.italic('Твой баланс 💰:')} {md.bold(score)} очков", parse_mode=ParseMode.MARKDOWN_V2)
    except (BotBlocked, ChatNotFound, UserDeactivated) as exception:
        logging.error(exception)

""" Rating """
@dp.message_handler(lambda message: user_db.user_exists(message.from_user.id), Text(equals='Рейтинг 🏆', ignore_case=True))
@dp.message_handler(lambda message: user_db.user_exists(message.from_user.id), commands=['rating'])
async def get_rating(message: types.Message):
    allPlayers = sorted(user_db.get_all_players(), key=lambda i: i[2], reverse=True)

    messageText = f"{md.bold('🏆 Рейтинг Гори Ясно 2023:')}\n\n"

    for _ in range(0,10):
        try:
            messageText += f"{md.italic(str(_+1)+')')} {md.bold(allPlayers[_][1])} \- {md.italic(allPlayers[_][2])} 💰\n"
        except IndexError as exception:
            logging.error(exception)
            break

    try:
        playerPlace = [index for (index, user_bot_id) in enumerate(allPlayers) if user_bot_id[0] == message.from_user.id][0] + 1
    except IndexError as exception:
        logging.error(exception)
        playerPlace = -1

    messageText += f"\n{md.italic('Вы на')} {md.bold(playerPlace)} {md.italic('месте')} 🥇"

    await message.answer(messageText, parse_mode=ParseMode.MARKDOWN_V2)

""" Set Balance"""
@dp.message_handler(lambda message: user_db.isAdmin(message.from_user.id) is True, Text(equals='Пополнить баланс 📈', ignore_case=True))
@dp.message_handler(lambda message: user_db.isAdmin(message.from_user.id) is True, commands=['addscore'])
async def add_score(message: types.Message):
    await SetScore.token.set()
    await message.answer(md.bold("Введи токен игрока 📇:"), parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb.cancel_process_score)

# State '*' to handle all states
#@dp.message_handler(state='*', commands='Отмена')
@dp.message_handler(Text(equals='Отмена ❌', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    """
    Allow to cancel any action
    """
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info('Cancelling state %r', current_state)
    # Cancel state and inform user about it
    await state.finish()
    # And remove keyboard (just in case)
    await message.answer(md.bold("Процесс остановлен ❌"), parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb.admin_menu)

@dp.message_handler(state=SetScore.token)
async def process_token(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['token'] = message.text.lower()

        try:
            if not user_db.valid_token(data['token']):
                await message.answer(md.bold("Введи количество баллов:"), parse_mode=ParseMode.MARKDOWN_V2,
                                     reply_markup=kb.cancel_process_score)
                await SetScore.score.set()
            else:
                await SetScore.token.set()
                await message.answer(f"{md.italic('Данного игрока не существует')}\n{md.bold('🔄 Введи токен повторно:')}",
                                    parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb.cancel_process_score)
        except (BotBlocked, ChatNotFound, UserDeactivated) as exception:
            logging.error(exception)


@dp.message_handler(lambda message: not message.text.isdigit() or not (0 <= int(message.text) <= 1000), state=SetScore.score)
async def failed_process_set_score(message: types.Message,):
    try:
        await message.delete()
    except (MessageCantBeDeleted, MessageToDeleteNotFound) as exception:
        logging.error(exception)
    """
    If age is not a digit
    """
    messageText = f"{md.italic('Пожалуйста, укажите число, не превышающее 1000!')}\n{md.bold('💰 Введи количество баллов:')}"

    await message.answer(messageText, parse_mode=ParseMode.MARKDOWN_V2)

@dp.message_handler(state=SetScore.score)
async def process_score(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['score'] = int(message.text)

        finalScore = data['score'] + user_db.get_score_by_token(data['token'])
        user_bot_id_to = user_db.get_user_bot_id(data['token'])

        user_db.set_score(token=data['token'], score=finalScore)
        score_db.create_log(message.from_user.id, user_bot_id_to, data['score'])

        try:
            await bot.send_message(user_bot_id_to, f"{md.italic('Тебе начислено')} {md.bold(data['score'])} {md.italic('баллов.')}\n\n"
                                                   f"{md.italic('Твой баланс:')} {md.bold(finalScore)} {md.italic('баллов 💰')}",
                                   parse_mode=ParseMode.MARKDOWN_V2)

            await message.answer(md.bold("Баланс пополнен ✅"), parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb.admin_menu)
        except (BotBlocked, ChatNotFound, UserDeactivated) as exception:
            logging.error(exception)

    await state.finish()


""" Create Message """
@dp.message_handler(lambda message: message.from_user.id in [331603730, 754913814, 970546274], commands=['message'])
async def create_message(message: types.Message):
    await MakeMessage.message.set()
    await message.answer(md.bold("Введи сообщение для рассылки:"), parse_mode=ParseMode.MARKDOWN_V2,
                         reply_markup=kb.cancel_process_score)

@dp.message_handler(state=MakeMessage.message)
async def process_create_message(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['message'] = f"{md.text(message.text)}\n\n" \
                          f"{md.italic('До скорых встреч,')}\n{md.italic('Ваш СтудАктив БИ ❤️')}"

        await MakeMessage.isSendable.set()
        await message.answer(f"{md.italic('Итоговое сообщение: ')}\n\n{md.text(data['message'])}\n\n{md.italic('Отправляем?')}",
                             parse_mode=ParseMode.MARKDOWN, reply_markup=kb.isSendableBtns)




@dp.callback_query_handler(state=MakeMessage.isSendable, text=['send_btn', 'not_send_btn'])
async def process_send_message(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['isSendable'] = query.data

        if data['isSendable'] == 'send_btn':
            users = user_db.get_all_players()

            for _ in users:
                try:
                    await bot.send_message(_[0], data['message'], parse_mode=ParseMode.MARKDOWN)
                    await asyncio.sleep(1)
                except (BotBlocked, ChatNotFound, UserDeactivated) as exception:
                    logging.error(exception)
                    pass

            await state.finish()
            await bot.send_message(query.from_user.id, md.bold('Сообщение отправлено всем пользователям ✅'),
                                 parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb.admin_menu)
        else:
            await state.finish()
            await bot.send_message(query.from_user.id, md.bold("Процесс отменен ❌"), parse_mode=ParseMode.MARKDOWN_V2,
                                 reply_markup=kb.admin_menu)


""" Delete admin """
@dp.message_handler(lambda message: message.from_user.id in [331603730, 754913814, 970546274], commands=['delete'])
async def delete_admin(message: types.Message):
    await AdminDeleteForm.token.set()
    await message.answer(md.bold("Введи токен игрока 📇:"), parse_mode=ParseMode.MARKDOWN_V2,
                         reply_markup=kb.cancel_process_score)

@dp.message_handler(state=AdminDeleteForm.token)
async def process_delete_admin(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['token'] = message.text.lower()

        try:
            if not user_db.valid_token(data['token']):
                user_db.deladmin(data['token'])
                await message.answer(md.bold('Настройки пользователя обновлены ✅'),
                                     parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb.admin_menu)

                await bot.send_message(user_db.get_user_bot_id(data['token']), f"{md.bold('У вас отняли админку 🤔')}",
                                       parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb.admin_menu)

                await state.finish()
            else:
                await AdminDeleteForm.token.set()
                await message.answer(
                    f"{md.italic('Данного игрока не существует')}\n{md.bold('🔄 Введи токен повторно:')}",
                    parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb.cancel_process_score)
        except (BotBlocked, ChatNotFound, UserDeactivated) as exception:
            logging.error(exception)


""" Check Player Balance"""
@dp.message_handler(lambda message: user_db.isAdmin(message.from_user.id) is True, Text(equals='Узнать чужой баланс 🔍', ignore_case=True))
@dp.message_handler(lambda message: user_db.isAdmin(message.from_user.id) is True, commands=['getscore'])
async def check_balance(message: types.Message):
    await BalanceForm.token.set()
    await message.answer(md.bold("Введи токен игрока 📇:"), parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb.cancel_process_score)

@dp.message_handler(state=BalanceForm.token)
async def process_token(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['token'] = message.text.lower()

        try:
            if not user_db.valid_token(data['token']):

                messageText = f"{md.italic('Баланс игрока')} {md.quote_html(data['token'])}: " \
                              f"{md.bold(user_db.get_score_by_token(data['token']))} 💰"
                await message.answer(messageText, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb.admin_menu)

                await state.finish()
            else:
                await BalanceForm.token.set()
                await message.answer(
                    f"{md.italic('Данного игрока не существует')}\n{md.bold('🔄 Введи токен повторно:')}",
                    parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb.cancel_process_score)
        except (BotBlocked, ChatNotFound, UserDeactivated) as exception:
            logging.error(exception)

""" Make admin process """
@dp.message_handler(lambda message: user_db.isAdmin(message.from_user.id) is True, Text(equals='Дать админку ⚖️', ignore_case=True))
@dp.message_handler(lambda message: user_db.isAdmin(message.from_user.id) is True , commands=['makeadmin'])
async def process_makeadmin(message: types.Message):
    await AdminForm.token.set()
    await message.answer(md.bold("Введи токен игрока 📇:"), parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb.cancel_process_score)

@dp.message_handler(state=AdminForm.token)
async def process_token(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['token'] = message.text.lower()

        try:
            if not user_db.valid_token(data['token']):
                user_db.makeadmin(data['token'], message.from_user.id)
                await message.answer(md.bold('Настройки пользователя обновлены ✅'),
                                     parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb.admin_menu)

                await bot.send_message(user_db.get_user_bot_id(data['token']), f"{md.bold('Вас сделали админом 😎')}",
                                       parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb.admin_menu)

                await state.finish()
            else:
                await AdminForm.token.set()
                await message.answer(
                    f"{md.italic('Данного игрока не существует')}\n{md.bold('🔄 Введи токен повторно:')}",
                    parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb.cancel_process_score)
        except (BotBlocked, ChatNotFound, UserDeactivated) as exception:
            logging.error(exception)



""" Delete balance """
@dp.message_handler(lambda message: user_db.isAdmin(message.from_user.id) is True, Text(equals='Уменьшить баланс 📉', ignore_case=True))
@dp.message_handler(lambda message: user_db.isAdmin(message.from_user.id) is True, commands=['delscore'])
async def del_score(message: types.Message):
    await DelScore.token.set()
    await message.answer(md.bold("Введи токен игрока 📇:"), parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb.cancel_process_score)

@dp.message_handler(state=DelScore.token)
async def process_del_token(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['token'] = message.text.lower()

        try:
            if not user_db.valid_token(data['token']):
                await message.answer(md.bold("Введи количество баллов:"), parse_mode=ParseMode.MARKDOWN_V2,
                                     reply_markup=kb.cancel_process_score)
                await DelScore.score.set()
            else:
                await DelScore.token.set()
                await message.answer(f"{md.italic('Данного игрока не существует')}\n{md.bold('🔄 Введи токен повторно:')}",
                    parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb.cancel_process_score)
        except (BotBlocked, ChatNotFound, UserDeactivated) as exception:
            logging.error(exception)


@dp.message_handler(lambda message: not message.text.isdigit() or not (0 <= int(message.text) <= 1000), state=DelScore.score)
async def failed_process_del_score(message: types.Message,):
    try:
        await message.delete()
    except (MessageCantBeDeleted, MessageToDeleteNotFound) as exception:
        logging.error(exception)
    """
    If age is not a digit
    """
    messageText = f"{md.italic('Пожалуйста, укажите число, не превышающее 1000!')}\n{md.bold('💰 Введи количество баллов:')}"

    await message.answer(messageText, parse_mode=ParseMode.MARKDOWN_V2)

@dp.message_handler(state=DelScore.score)
async def process_del_score(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['score'] = int(message.text)

        availableTokens = user_db.get_score_by_token(data['token'])

        if availableTokens - data['score'] < 0:
            await DelScore.score.set()

            messageText = f"{md.italic('Данное количество токенов снять невозможно!')}\n" \
                          f"{md.italic('💰 Введи доступное количество для снятия: ')} {md.bold(availableTokens)} {md.italic('баллов.')}"
            await message.answer(messageText, parse_mode=ParseMode.MARKDOWN_V2)
        else:
            score = availableTokens-data['score']
            user_bot_id_to = user_db.get_user_bot_id(data['token'])

            user_db.set_score(token=data['token'], score=score)
            score_db.create_log(message.from_user.id, user_bot_id_to, -data['score'])

            try:
                await bot.send_message(user_bot_id_to,
                                       f"{md.italic('С тебя снято')} {md.bold(data['score'])} {md.italic('баллов.')}\n\n"
                                       f"{md.italic('Твой баланс:')} {md.bold(score)} {md.italic('баллов 💰')}",
                                       parse_mode=ParseMode.MARKDOWN_V2)

                await message.answer(md.bold("Баланс уменьшен ✅"), parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb.admin_menu)
            except (BotBlocked, ChatNotFound, UserDeactivated) as exception:
                logging.error(exception)

            await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)