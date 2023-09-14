# -*- coding: utf-8 -*-

import asyncio
from typing import Optional
import dp as dp
import openai
import logging
import config
import markups as nav
from aiogram import Bot, Dispatcher, types, executor
from config import OPENAI_API_KEY, TELEGRAM_BOT_TOKEN
from io import BytesIO
import aiohttp
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher.handler import SkipHandler
from html import escape
import hashlib
import time
from aiohttp import web
from aiogram.types import ContentTypes
import pytesseract
from PIL import Image, ImageEnhance
from aiogram.types import InputFile
import os
from pydub import AudioSegment
import speech_recognition as sr
import json
from yookassa import Configuration, Payment
from yookassa import Refund
import uuid
import sqlite3
import datetime
from db import Database
import glob
import schedule
from aiogram import types
from io import BytesIO
import aiohttp
from aiogram.dispatcher import Dispatcher
from translate import Translator
import sys






translator = Translator(from_lang='ru', to_lang='en')

db_file = "database.db"  # Путь к файлу SQLite базы данных
db = Database('database.db')

Configuration.account_id = config.SHOP_ID
Configuration.secret_key = config.SHOP_API_TOKEN

# Set up the OpenAI API key
openai.api_key = OPENAI_API_KEY
DEEP_AI_API_KEY = config.DEEP_AI_API_KEY
logging.basicConfig(level=logging.INFO)

# Set up the Telegram bot
bot = Bot(token=TELEGRAM_BOT_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)
CHANNEL_ID = ""
NOTSUB_MESSAGE = "Для доступа к функционалу бота подпишитесь на канал!"
db = Database('database.db')


def check_sub_channel(chat_member):
    print(chat_member['status'])
    if chat_member['status'] != 'left':
        return True
    else:
        return False


async def check_and_update_requests(user_id, text_request=True):
    user_data = db.get_user(user_id)
    text_requests_str = str(user_data['text_requests'])
    image_requests_str = str(user_data['image_requests'])

    text_requests = int(text_requests_str.split('/')[0]) if '/' in text_requests_str else 0
    image_requests = int(image_requests_str.split('/')[0]) if '/' in image_requests_str else 0

    if text_request:
        if user_data['subscription_type'] == 'standard' and text_requests >= 700:
            return False
        if user_data['subscription_type'] == 'premium' and text_requests >= 4000:
            return False
        text_requests += 1
    else:
        if user_data['subscription_type'] == 'standard' and image_requests >= 5:
            return False
        if user_data['subscription_type'] == 'premium' and image_requests >= 100:
            return False
        image_requests += 1

    db.update_requests(user_id, f"{text_requests}/{get_text_requests_limit(user_data)}",
                       f"{image_requests}/{get_image_requests_limit(user_data)}")
    return True


def get_text_requests_limit(user_data):
    subscription_type = user_data['subscription_type']
    if subscription_type == 'premium':
        return 4000
    else:
        return 700


def get_image_requests_limit(user_data):
    subscription_type = user_data['subscription_type']
    if subscription_type == 'premium':
        return 100
    else:
        return 5


@dp.message_handler(commands=['profile'])
async def profile_command(message: types.Message):
    user_id = message.from_user.id
    user_data = db.get_user(user_id)

    if user_data:
        nickname = user_data['nickname']
        subscription_type = user_data['subscription_type']
        text_requests = user_data['text_requests']
        image_requests = user_data['image_requests']

        profile_text = f"👤 Профиль пользователя:\n\n" \
                       f"🆔 ID: {user_id}\n" \
                       f"👤 Никнейм: {nickname}\n" \
                       f"📌 Тип подписки: {subscription_type}\n" \
                       f"📝 Текстовые запросы: {text_requests}\n" \
                       f"🖼️ Запросы на картинки: {image_requests}"

        await bot.send_message(chat_id=user_id, text=profile_text)
    else:
        await bot.send_message(chat_id=user_id, text="⚠️ Ваш профиль не найден.")



@dp.message_handler(commands=['set_premium'])
async def set_premium_command(message: types.Message):
    user_id = message.from_user.id

    # Получение текущего времени
    current_time = datetime.datetime.now()

    # Добавление 30 дней к текущему времени
    time_sub = current_time + datetime.timedelta(days=30)

    # Проверяем, существует ли пользователь в базе данных
    if db.user_exists(user_id):
        # Обновляем статус подписки на "premium"
        db.update_subscription_type(user_id, "premium")

        # Обновляем лимиты для пользователя
        db.update_requests_limit(user_id, text_requests_limit=2000, image_requests_limit=50)

        # Обновляем время подписки на месяц
        subscription_expiry = datetime.datetime.now() + datetime.timedelta(days=30)
        db.update_subscription_time_sub(user_id, subscription_expiry)

        await message.reply("Статус 'premium' успешно установлен.")
    else:
        await message.reply("Пользователь не найден в базе данных.")


@dp.callback_query_handler(lambda call: call.data == 'pay_subscription')
async def process_callback_button1(call: types.CallbackQuery):
    await bot.answer_callback_query(call.id)
    await send_invoice(call.message.chat.id)


async def send_invoice(chat_id):
    title = "Премиум подписка на 1 месяц"
    description = "Получите доступ к расширенным возможностям бота: 2000 запросов  и 50 изображений в месяц."
    payload = "subscription_payload"
    provider_token = ""
    start_parameter = "subscription"
    currency = "RUB"
    price = 300 * 100  # Умножьте на 100, чтобы конвертировать в копейки
    prices = [types.LabeledPrice(label=title, amount=price)]

    await bot.send_invoice(
        chat_id=chat_id,
        title=title,
        description=description,
        payload=payload,
        provider_token=provider_token,
        start_parameter=start_parameter,
        currency=currency,
        prices=prices,
    )


@dp.message_handler(commands=['premium'])
async def premium_command(message: types.Message):
    text = "Бот позволяет ежемесячно бесплатно отправлять до 700 запросов к Open AI для генерации  и создавать 5 изображений . Такой лимит обеспечивает скорость и качество работы.\n\nНужно больше? Подключите премиум-подписку на месяц за 300 руб.\n\nПремиум-подписка включает:\n✅ до 4000 запросов ;\n✅ до 100 запросов на создание картинок в месяц;\n✅ нет паузы между запросами;\n✅ поддержание высокой скорости работы, даже в период повышенной нагрузки;\n✅ более 1000 встроенных текстовых шаблонов (скоро)"
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    button1 = types.InlineKeyboardButton(text="Канал подписки", url="https://t.me/openaichn")
    button2 = types.InlineKeyboardButton(text="Оплатить подписку", callback_data="pay_subscription")
    button3 = types.InlineKeyboardButton(text="Связаться с поддержкой", url="https://t.me/nikitinno")
    keyboard.add(button1, button2, button3)
    await bot.send_message(chat_id=message.chat.id, text=text, reply_markup=keyboard)


@dp.pre_checkout_query_handler(lambda query: True)
async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@dp.message_handler(content_types=ContentTypes.SUCCESSFUL_PAYMENT)
async def process_successful_payment(message: types.Message):
    user_id = message.from_user.id
    # Обновите статус подписки пользователя в вашей базе данных
    db.set_subscription(user_id)  # Используйте экземпляр базы данных для вызова функции set_subscription()
    await bot.send_message(chat_id=message.chat.id, text="Спасибо за оплату! Ваша подписка активирована.")


@dp.message_handler(content_types=['voice'])
async def handle_voice(message: types.Message):
    voice_file = await bot.download_file_by_id(message.voice.file_id)
    ogg_file_path = f"voice_{message.voice.file_id}.ogg"
    wav_file_path = f"voice_{message.voice.file_id}.wav"

    with open(ogg_file_path, 'wb') as f:
        f.write(voice_file.read())

    convert_ogg_to_wav(ogg_file_path, wav_file_path)

    recognized_text = transcribe_audio(wav_file_path)

    if await check_and_update_requests(message.from_user.id):
        # Получить ответ от GPT-3.5-turbo API
        gpt_response = await ai(recognized_text, message.from_user.id)
        await message.reply(gpt_response)
    else:
        await message.reply("Превышен лимит запросов.")

    # Удалить файлы после использования
    os.remove(ogg_file_path)
    os.remove(wav_file_path)


def transcribe_audio(file_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(file_path) as source:
        audio = recognizer.record(source)

    try:
        text = recognizer.recognize_google(audio, language='ru-RU')
        return text
    except sr.UnknownValueError:
        return "Не удалось распознать аудио"
    except sr.RequestError as e:
        return f"Ошибка сервиса распознавания речи: {e}"


@dp.message_handler(content_types=['voice'])
async def handle_voice(message: types.Message):
    voice_file = await bot.download_file_by_id(message.voice.file_id)
    file_path = f"voice_{message.voice.file_id}.ogg"

    with open(file_path, 'wb') as f:
        f.write(voice_file.read())

    # Здесь вам нужно будет преобразовать файл OGG в поддерживаемый формат, например, WAV.

    recognized_text = transcribe_audio(file_path)
    await message.reply(recognized_text)


from pydub import AudioSegment


def convert_ogg_to_wav(ogg_file_path, wav_file_path):
    audio = AudioSegment.from_ogg(ogg_file_path)
    audio.export(wav_file_path, format="wav")


# Функция для удаления старых файлов голосовых сообщений
def remove_old_voice_files():
    voice_files = glob.glob('voice_*.ogg')  # Замените путь на путь к папке с голосовыми файлами
    threshold = datetime.datetime.now() - datetime.timedelta(days=2)  # Установите временной порог

    for file in voice_files:
        created_time = datetime.datetime.fromtimestamp(os.path.getctime(file))
        if created_time < threshold:
            os.remove(file)


# Функция для удаления старых файлов аудио
def remove_old_audio_files():
    audio_files = glob.glob('voice_*.wav')  # Замените путь на путь к папке с аудио файлами
    threshold = datetime.datetime.now() - datetime.timedelta(days=2)  # Установите временной порог

    for file in audio_files:
        created_time = datetime.datetime.fromtimestamp(os.path.getctime(file))
        if created_time < threshold:
            os.remove(file)


# Установите расписание выполнения функций проверки и удаления старых файлов
schedule.every(2).days.at("03:00").do(remove_old_voice_files)  # Удаление файлов голосовых сообщений раз в 2 дня
schedule.every(2).days.at("03:00").do(remove_old_audio_files)  # Удаление аудио файлов раз в 2 дня


def preprocess_image(image):
    # Изменить размер изображения
    image = image.resize((image.width * 2, image.height * 2), Image.BICUBIC)

    # Увеличить контраст
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2)

    # Повысить яркость
    enhancer = ImageEnhance.Brightness(image)
    image = enhancer.enhance(1.2)

    return image


def recognize_text(image_data):
    with Image.open(BytesIO(image_data)) as image:
        image = preprocess_image(image)
        recognized_text = pytesseract.image_to_string(image, lang='rus')
    return recognized_text


@dp.message_handler(content_types=types.ContentType.PHOTO)
async def handle_photos(message: types.Message):
    image_file_id = message.photo[-1].file_id
    image_file = await bot.download_file_by_id(image_file_id)

    user_data = db.get_user(message.from_user.id)
    text_requests_str = user_data["text_requests"]
    text_requests = int(text_requests_str.split('/')[0]) + 1 if '/' in text_requests_str else 0

    db.update_requests(message.from_user.id, f"{text_requests}/{get_text_requests_limit(user_data)}", user_data["image_requests"])

    recognized_text = recognize_text(image_file.read())
    await bot.send_message(message.chat.id, recognized_text)

@dp.message_handler(commands=['channel'])
async def group(message: types.Message):
    # Создаем ссылку на группу и отправляем ее пользователю
    group_link = ""
    group_image = ""  # Замените ссылку на реальную картинку

    # Создаем кнопку для перехода на группу
    button = InlineKeyboardButton(text="Перейти на канал", url=group_link)
    keyboard = InlineKeyboardMarkup().add(button)

    # Отправляем сообщение с картинкой и кнопкой на группу
    await bot.send_photo(chat_id=message.chat.id, photo=group_image,
                         caption="Нажмите кнопку ниже, чтобы перейти на канал", reply_markup=keyboard)




# Define the help command handler
@dp.message_handler(commands=['help'])
async def help(message: types.Message):
    help_text = "🤖 Привет! Я бот OpenAI на базе модели 3.5 Turbo. Чем я могу помочь?\n\n" \
                "🌟 Вот некоторые из команд, которые я могу выполнить:\n" \
                "/start - Начать диалог со мной\n" \
                "/help - Получить справку\n" \
                "/weather - Узнать прогноз погоды\n" \
                "/news - Получить последние новости\n" \
                "/define - Определить значения слова\n" \
                "/joke - Рассказать случайную шутку\n" \
                "/fact - Показать случайный факт\n" \
                "/quote - Вывести случайную цитату\n" \
                "/music - Найти песню по названию\n" \
                "/movie - Получить информацию о фильме\n\n" \
                "/generate_image - Генерация изображений\n\n"\
                "✨ Это только некоторые из команд, которые я могу выполнить. Если у вас есть другие запросы, " \
                "просто сообщите мне, и я постараюсь помочь вам."

    await bot.send_message(chat_id=message.chat.id, text=help_text)


@dp.message_handler(commands=['clear'])
async def clear_context(message: types.Message):
    # Clear the previous context
    openai.api_key = None

    # Image URL for the clear context message
    image_url = "https://drive.google.com/uc?id=1vheuk9n7xWkiAjo_vSrzTgL89CMvArIE"

    # Send a message with the image
    await bot.send_photo(chat_id=message.chat.id, photo=image_url, caption="Ваш контекст общения удален.")








@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    if message.chat.type == 'private':
        user_id = message.from_user.id
        nickname = message.from_user.username or message.from_user.first_name or message.from_user.last_name
        # Проверяем, существует ли пользователь в базе данных
        if db.user_exists(user_id):
            print(f"Пользователь с ID {user_id} уже существует в базе данных.")
        else:
            # Добавляем пользователя в базу данных
            db.add_user(user_id, nickname)
            print(f"Пользователь с ID {user_id} успешно добавлен в базу данных.")

        if check_sub_channel(await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=message.from_user.id)):
            welcome_message = f"""😎 Добро пожаловать, {nickname}!

🤖 Я - искусственный интеллект, который умеет:

✅ Писать и редактировать тексты
✅ Переводить с любого языка на любой
✅ Писать и редактировать код
✅ Отвечать на вопросы
✅ Создавать изображения по текстовому запросу
✅ Распознавать текст со скриншотов .
✅ Запоминать контекст общения  (последние 50 сообщений он будет хранить в переписке и отвечать основываясь на предыдущем диалоге).

♨️ Я уже умею распознавать ваши голосовые сообщения и отвечает на них в текстовом виде. 

‼️ Попробуйте отправить мне голосовое сообщение сейчас

💬 Бота можно добавить в групповые чаты и общаться с ним вместе с друзьями! Чтобы бот понял, что в группе вы обращаетесь к нему, напишите символ собаку @, во всплывающем окне выберите бота и пишите свой запрос.  Попробуй прямо сейчас у нас в чате https://t.me/openaichnl

😍 Вы можете общаться с ботом, как с живым собеседником, задавая вопросы на любом языке. Обратите внимание, что иногда бот придумывает факты, а также обладает ограниченными знаниями о событиях после 2021 года.

✉️ Чтобы получить текстовый ответ, просто напишите в чат ваш вопрос.

🌅 Чтобы сгенерировать изображение, начните свой запрос с /generate_image, а затем введите текст. Например: /generate_image зеленое дерево на фоне заката.Запросы для генерации изображений автоматически переводяться на анг.язык для лучшего распознавания.

🚀 Помните, что ботом вместе с вами пользуются ещё много людей, он может отвечать с задержкой. Чтобы ускорить ответы, вы можете подписаться на /premium.     v.1.10"""

            await bot.send_message(chat_id=message.chat.id, text=welcome_message, reply_markup=nav.profileKeyboard)
        else:
            await bot.send_message(message.from_user.id, NOTSUB_MESSAGE, reply_markup=nav.checkSubMenu)


@dp.message_handler()
async def start(message: types.Message):
    if message.chat.type == 'private':
        user_id = message.from_user.id
        nickname = message.from_user.username or message.from_user.first_name or message.from_user.last_name
        # Проверяем, существует ли пользователь в базе данных
        if db.user_exists(user_id):
            print(f"Пользователь с ID {user_id} уже существует в базе данных.")
        else:
            # Добавляем пользователя в базу данных
            db.add_user(user_id, nickname)
            print(f"Пользователь с ID {user_id} успешно добавлен в базу данных.")

        if message.text == "СТАРТ":
            await bot.send_message(message.from_user.id, f"""😎 Добро пожаловать, {nickname}!

🤖 Я - искусственный интеллект, который умеет:

✅ Писать и редактировать тексты
✅ Переводить с любого языка на любой
✅ Писать и редактировать код
✅ Отвечать на вопросы
✅ Создавать изображения по текстовому запросу
✅ Распознавать текст со скриншотов .
✅ Запоминать контекст общения  (последние 50 сообщений он будет хранить в переписке и отвечать основываясь на предыдущем диалоге).

♨️ Я уже умею распознавать ваши голосовые сообщения и отвечает на них в текстовом виде. 

‼️ Попробуйте отправить мне голосовое сообщение сейчас

💬 Бота можно добавить в групповые чаты и общаться с ним вместе с друзьями! Чтобы бот понял, что в группе вы обращаетесь к нему, напишите символ собаку @, во всплывающем окне выберите бота и пишите свой запрос.  Попробуй прямо сейчас у нас в чате https://t.me/openaichnl

😍 Вы можете общаться с ботом, как с живым собеседником, задавая вопросы на любом языке. Обратите внимание, что иногда бот придумывает факты, а также обладает ограниченными знаниями о событиях после 2021 года.

✉️ Чтобы получить текстовый ответ, просто напишите в чат ваш вопрос.

🌅 Чтобы сгенерировать изображение, начните свой запрос с /generate_image, а затем введите текст. Например: /generate_image зеленое дерево на фоне заката. Запросы для генерации изображений автоматически переводятся на английский язык для лучшего распознавания.

🚀 Помните, что ботом вместе с вами пользуются ещё много людей, он может отвечать с задержкой. Чтобы ускорить ответы и получить гораздо больше возможностей, вы можете подписаться на /premium.     v.1.10""")
        elif message.text.startswith('/generate_image'):
            prompt = message.text[len('/generate_image'):].strip()
            if not prompt:
                await message.reply("Пожалуйста, введите описание изображения после команды. Например: /generate_image зеленое дерево на фоне заката. Не забывайте ваше сообщение для удобства распознавания нейронной сети , переводиться на анлийский автоматически.")
            else:
                if not await check_and_update_requests(message.from_user.id, text_request=False):
                    await bot.send_message(chat_id=message.chat.id,
                                           text="Вы превысили лимит запросов на генерацию изображений,преобретите премиум подписку для расширения возможностей")
                else:
                    translated_prompt = translator.translate(prompt)
                    print(f"Translated prompt: {translated_prompt}")
                    image_data = await generate_image(translated_prompt)
                    if image_data:
                        await bot.send_photo(chat_id=message.chat.id, photo=image_data)
                    else:
                        await message.reply("Извините, не удалось сгенерировать изображение.")
        elif check_sub_channel(await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=message.from_user.id)):
            if not await check_and_update_requests(message.from_user.id, text_request=True):
                await bot.send_message(chat_id=message.chat.id,
                                       text="Вы превысили лимит текстовых запросов,преобретите премиум подписку для расширения возможностей")
            else:
                # Use the ai function to generate a response
                ai_message = await ai(message.text, message.chat.id)

                # Send the AI's message to the user
                if ai_message:
                    await bot.send_message(chat_id=message.chat.id, text=ai_message)
        else:
            await bot.send_message(message.from_user.id, NOTSUB_MESSAGE, reply_markup=nav.checkSubMenu)


@dp.message_handler(commands=['generate_image'])
async def generate_image_command(message: types.Message):
    if check_sub_channel(await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=message.from_user.id)):
        # Пользователь является подписчиком, выполняем команду `\generate_image`
        prompt = message.get_args()
        if not prompt:
            await message.reply("Пожалуйста, введите описание изображения после команды. Например: /generate_image зеленое дерево на фоне заката.")
            return

        negative_prompt = "deformed, distorted, disfigured:1.3), poorly drawn, bad anatomy, wrong anatomy, extra limb, missing limb, floating limbs, (mutated hands and fingers:1.4), disconnected limbs, mutation, mutated, ugly, disgusting, blurry, amputation"
        image_data = await generate_image(grid_size="1", width="", height="", negative_prompt=negative_prompt)

        if image_data:
            await bot.send_photo(chat_id=message.chat.id, photo=image_data)
        else:
            await message.reply("Извините, не удалось сгенерировать изображение. ")
    else:
        # Пользователь не является подписчиком, отправляем сообщение о недоступности команды
        await bot.send_message(message.chat.id, "Для использования данной команды необходимо подписаться на канал.")


async def generate_image(prompt: str, grid_size: str = "1", width: str = "768", height: str = "768",
                         negative_prompt: str = "deformed, distorted, disfigured:1.3), poorly drawn, bad anatomy, wrong anatomy, extra limb, missing limb, floating limbs, (mutated hands and fingers:1.4), disconnected limbs, mutation, mutated, ugly, disgusting, blurry, amputation") -> \
Optional[BytesIO]:
    async with aiohttp.ClientSession() as session:
        async with session.post(
                "https://api.deepai.org/api/text2img",
                data={
                    "text": prompt,
                    "grid_size": grid_size,
                    "width": width,
                    "height": height,
                    "negative_prompt": negative_prompt,
                },
                headers={"api-key": DEEP_AI_API_KEY},
        ) as response:
            if response.status == 200:
                json_response = await response.json()
                image_url = json_response["output_url"]

                async with session.get(image_url) as image_response:
                    if image_response.status == 200:
                        image_data = BytesIO(await image_response.read())
                        image_data.name = "generated_image.png"
                        return image_data
                    else:
                        print(f"Error getting image: {image_response.status}")
            else:
                print(f"Error generating image: {response.status}")

    return None


dp.register_message_handler(generate_image_command, commands=['generate_image'])









@dp.callback_query_handler(text="subchanneldone")
async def subchanneldone(call: types.CallbackQuery):
    await bot.delete_message(call.from_user.id, call.message.message_id)
    if check_sub_channel(await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=call.from_user.id)):
        await bot.send_message(call.from_user.id,
                               text="Добро пожаловать в чат с ботом GPT 3.5 Turbo! Я очень рад приветствовать вас здесь и помочь вам в любых вопросах и задачах.",
                               reply_markup=nav.profileKeyboard)
    else:
        await bot.send_message(call.from_user.id, NOTSUB_MESSAGE, reply_markup=nav.checkSubMenu)







# Глобальный словарь для хранения истории сообщений
user_message_histories = {}
# Максимальное количество хранящихся сообщений для каждого пользователя
max_messages_per_user = 50


async def ai(prompt, user_id):
    try:
        if user_id not in user_message_histories:
            user_message_histories[user_id] = [
                {"role": "system", "content": 'Тебя зовут OpenAiBot и ты лучший персональный помошник!'}]

        user_message_histories[user_id].append({"role": "user", "content": prompt})

        # Удаление старых сообщений, если количество сообщений превышает максимальное значение
        if len(user_message_histories[user_id]) > max_messages_per_user:
            user_message_histories[user_id].pop(1)
            user_message_histories[user_id].pop(1)

        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=user_message_histories[user_id]
        )

        bot_response = completion.choices[0].message.content
        bot_response = escape(bot_response)
        user_message_histories[user_id].append({"role": "assistant", "content": bot_response})

        return bot_response
    except Exception as e:
        logging.error(f"Error in ai function: {e}")
        restart_bot()

def restart_bot():
    logging.info("Restarting bot in 5 seconds...")
    time.sleep(5)
    python = sys.executable
    os.execl(python, python, *sys.argv)

@dp.message_handler(content_types=types.ContentTypes.TEXT)
async def echo(message: types.Message):
    # Get the user's message
    user_message = message.text

    # Use the ai function to generate a response
    ai_message = await ai(user_message, message.chat.id)

    # Send the AI's message to the user
    if ai_message:
        await bot.send_message(chat_id=message.chat.id, text=ai_message)


async def main():
    while True:
        try:
            await dp.start_polling()
        except Exception as e:
            logging.error(f"Error occurred: {e}")
            logging.info("Restarting bot in 5 seconds...")
            time.sleep(5)
            python = sys.executable
            os.execl(python, python, *sys.argv)

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    while True:
        try:
            asyncio.run(main())
        except Exception as e:
            logging.error(f"Error occurred: {e}")
            logging.info("Restarting bot in 5 seconds...")
            time.sleep(5)
            python = sys.executable
            os.execl(python, python, *sys.argv)
        run_schedule()