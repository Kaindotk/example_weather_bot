from config import weather_token
import requests
from aiogram import Bot, Dispatcher, executor, types
from config import bot_token
import logging
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.storage import BaseStorage, FSMContext
from aiogram.types.callback_query import CallbackQuery
from database import *
import pprint
import asyncio
import aioschedule as schedule
import time

pp = pprint.PrettyPrinter(indent=4)

bot = Bot(bot_token)
dp = Dispatcher(bot, storage=MemoryStorage())


logging.basicConfig(level=logging.INFO)

delete_inline = types.InlineKeyboardMarkup()
item_delete = types.InlineKeyboardButton(
    "✖️", callback_data="delete")
delete = delete_inline.add(item_delete)


class Form(StatesGroup):
    F1 = State()
    CITY = State()


@dp.message_handler(commands="start")
async def start(message: types.Message):

    kb = types.InlineKeyboardMarkup(row_width=2)

    kb_weather = types.InlineKeyboardButton(
        "Посмотреть погоду ☁️", callback_data="view_weather")
    kb_about = types.InlineKeyboardButton(
        "О боте ❓", callback_data="about")
    kb_settings = types.InlineKeyboardButton(
        "Настройки ⚙", callback_data="settings")

    kb = kb.add(kb_weather, kb_about, kb_settings)

    user_id = message.chat.id
    print(user_id)

    write_user(user_id)

    await message.answer("Привет! Я Винди, бот - который показывает погоду, а в будущем будет рассказывать о паропланеризме. Выбери что тебе нужно:", reply_markup=kb)


@dp.callback_query_handler(text="about")
async def about(call: CallbackQuery):
    kb = types.InlineKeyboardMarkup()

    kb_back = types.InlineKeyboardButton("⬅ Выход", callback_data="back")

    kb.add(kb_back)

    await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Привет! Как я уже говорил, я Винди. Умный бот, с кучей(пока нет)функций.\nМой автор идеи: Никита Захаров\nТот, кто меня собрал и поддерживает мою жизнеспобоность: @blzme ", reply_markup=kb)


@dp.callback_query_handler(text="view_weather", state=None)
async def get_city(call: CallbackQuery):

    kb = types.InlineKeyboardMarkup()

    kb_back = types.InlineKeyboardButton(
        "❌ Остановить", callback_data="stop_state")

    kb.add(kb_back)

    await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Напиши свой город: ", reply_markup=kb)

    await Form.F1.set()


@dp.message_handler(state=Form.F1)
async def give_weather(message: types.Message, state: FSMContext):
    city = message.text

    kb = types.InlineKeyboardMarkup()

    kb_back = types.InlineKeyboardButton("⬅ Выход", callback_data="back")

    kb.add(kb_back)

    try:
        r = requests.get(
            f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={weather_token}&units=metric&lang=ru")
        data = r.json()
        city = data["name"]
        desc_weather = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        pressure = data["main"]["pressure"]
        visibility = data["visibility"]//1000
        wind_deg = data["wind"]["deg"]
        if wind_deg > 22:
            compass = "Северо-восток"
        if wind_deg >= 90:
            compass = "Восток"
        if wind_deg > 112:
            compass = "Юго-восток"
        if wind_deg >= 180:
            compass = "Юг"
        if wind_deg > 202:
            compass = "Юго-запад"
        if wind_deg >= 270:
            compass = "Запад"
        if wind_deg >= 292:
            compass = "Северо-запад"
        if wind_deg > 337:
            compass = "Север"
        elif wind_deg == 0:
            compass = "Север"
        wind_speed = data["wind"]["speed"]
        if wind_speed > 8 or desc_weather == "rain" or desc_weather == "snow" or desc_weather == "shower rain" or desc_weather == "thunderstorm" or desc_weather == "mist":
            wind_alert = "сейчас запрещено летать."
        elif wind_speed > 6:
            wind_alert = "сейчас не стоит летать."
        elif wind_speed <= 6:
            wind_alert = "cейчас отличная скорость ветра, чтоб полетать."
        elif wind_speed == 0:
            wind_alert = "cейчас нет ветра"
        await message.answer(f"Сейчас в городе {city} - {desc_weather}\nТемпература: {temp}°C\nОщущается как: {feels_like}°C\nВлажность: {humidity}%\nДавление: {pressure} hPa\nВидимость: {visibility} км\nСкорость ветра: {wind_speed} м\с\nРекомендация: {wind_alert}\nНаправление ветра: {wind_deg}° {compass}", reply_markup=kb)
    except Exception as ex:
        print(ex)
        await message.answer("Проверьте название города и напишиет /start")

    await state.finish()


@dp.callback_query_handler(text="settings")
async def settings(call: CallbackQuery):
    kb = types.InlineKeyboardMarkup(row_width=1)

    user_id = call.message.chat.id
    cursor.execute(f"SELECT allowed FROM users WHERE chat_id = {user_id}")
    check_sub = cursor.fetchone()[0]

    if check_sub == 0:
        kb_check_sub = types.InlineKeyboardButton(
            "Подписаться на рассылку", callback_data="subscribe")
    else:
        kb_check_sub = types.InlineKeyboardButton(
            "Отменить подписку", callback_data="decline_sub")

    kb_back = types.InlineKeyboardButton("⬅ Выход", callback_data="back")

    kb.add(kb_back, kb_check_sub)

    await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Настройки Винди:", reply_markup=kb)


@dp.callback_query_handler(text="subscribe", state=None)
async def subscribe(call: CallbackQuery):

    kb = types.InlineKeyboardMarkup()

    kb_back = types.InlineKeyboardButton(
        "❌ Остановить", callback_data="stop_state")

    kb.add(kb_back)

    await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Отлично, теперь напишите мне город, о котором вы будете получать рассылку", reply_markup=kb)

    await Form.CITY.set()


@dp.message_handler(state=Form.CITY)
async def set_city(message: types.Message, state: FSMContext):
    city = message.text
    user_id = message.chat.id

    kb = types.InlineKeyboardMarkup()

    kb_back = types.InlineKeyboardButton("⬅ Выход", callback_data="back")

    kb.add(kb_back)

    try:
        r = requests.get(
            f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={weather_token}&units=metric&lang=ru")
        await message.answer("Отлично, город записан! Ждите ближайшей рассылки", reply_markup=kb)
        set_sub(user_id, city)
        await state.finish()
    except Exception as ex:
        print(ex)
        await message.answer("Проверь город и попробуй ещё раз", reply_markup=kb)
        await state.finish()


async def write_sub_weather():

    cursor.execute("SELECT chat_id, city FROM users WHERE allowed = True")
    users = cursor.fetchall()
    for user in users:
        chat_id = user[0]
        city = user[1]

        r = requests.get(
            f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={weather_token}&units=metric&lang=ru")
        data = r.json()
        city = data["name"]
        desc_weather = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        pressure = data["main"]["pressure"]
        visibility = data["visibility"]//1000
        wind_deg = data["wind"]["deg"]
        if wind_deg > 22:
            compass = "Северо-восток"
        if wind_deg >= 90:
            compass = "Восток"
        if wind_deg > 112:
            compass = "Юго-восток"
        if wind_deg >= 180:
            compass = "Юг"
        if wind_deg > 202:
            compass = "Юго-запад"
        if wind_deg >= 270:
            compass = "Запад"
        if wind_deg >= 292:
            compass = "Северо-запад"
        if wind_deg > 337:
            compass = "Север"
        elif wind_deg == 0:
            compass = "Север"
        wind_speed = data["wind"]["speed"]
        if wind_speed > 8 or desc_weather == "rain" or desc_weather == "snow" or desc_weather == "shower rain" or desc_weather == "thunderstorm":
            wind_alert = "сейчас запрещено летать."
        elif wind_speed > 6:
            wind_alert = "сейчас не стоит летать."
        elif wind_speed <= 6:
            wind_alert = "cейчас отличная скорость ветра, чтоб полетать."
        elif wind_speed == 0:
            wind_alert = "cейчас нет ветра"
        text_to_user = (f"Сейчас в городе {city} - {desc_weather}\nТемпература: {temp}°C\nОщущается как: {feels_like}°C\nВлажность: {humidity}%\nДавление: {pressure} hPa\nВидимость: {visibility} км\nСкорость ветра: {wind_speed} м\с\nРекомендация: {wind_alert}\nНаправление ветра: {wind_deg}° {compass}")

        await bot.send_message(chat_id, text_to_user, reply_markup=delete)


async def start_write():
    schedule.every(1).hours.do(write_sub_weather)

    while True:
        await schedule.run_pending()
        await asyncio.sleep(1)


@dp.callback_query_handler(text="decline_sub")
async def subscribe(call: CallbackQuery):

    kb = types.InlineKeyboardMarkup(row_width=1)

    kb_subscribe = types.InlineKeyboardButton(
        "Подписаться на рассылку", callback_data="subscribe")
    kb_back = types.InlineKeyboardButton("⬅ Выход", callback_data="back")

    kb.add(kb_back, kb_subscribe)

    user_id = call.message.chat.id
    decline_sub(user_id)

    await bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=kb)


@dp.callback_query_handler(text="back")
async def back_to_main(call: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(row_width=2)

    kb_weather = types.InlineKeyboardButton(
        "Посмотреть погоду ☁️", callback_data="view_weather")
    kb_about = types.InlineKeyboardButton(
        "О боте ❓", callback_data="about")
    kb_settings = types.InlineKeyboardButton(
        "Настройки ⚙", callback_data="settings")

    kb = kb.add(kb_weather, kb_about, kb_settings)

    await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Привет! Я бот, который показывает погоду. Выбери что тебе нужно:", reply_markup=kb)


@dp.callback_query_handler(text="stop_state", state=Form.F1)
async def stop_state(call: types.CallbackQuery, state: FSMContext):

    kb = types.InlineKeyboardMarkup(row_width=2)

    kb_weather = types.InlineKeyboardButton(
        "Посмотреть погоду ☁️", callback_data="view_weather")
    kb_about = types.InlineKeyboardButton(
        "О боте ❓", callback_data="about")
    kb_settings = types.InlineKeyboardButton(
        "Настройки ⚙", callback_data="settings")

    kb = kb.add(kb_weather, kb_about, kb_settings)

    await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Привет! Я бот, который показывает погоду. Выбери что тебе нужно:", reply_markup=kb)
    await state.finish()


@dp.callback_query_handler(text="delete")
async def delete_message(call: types.CallbackQuery):
    await call.message.delete()


async def shutdown(dispatcher: Dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(start_write())
    executor.start_polling(dp, skip_updates=True)
