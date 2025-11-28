import asyncio
import logging
import aiohttp

import json


from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup


logging.basicConfig(level=logging.INFO)


API_TOKEN = ''
WEBHOOK_URL = ''



bot = Bot(token=API_TOKEN)
dp = Dispatcher()




class Survey(StatesGroup):
    debt_amount = State()
    other_property = State()
    collateral_property = State()
    credit_delays = State()




def get_debt_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="До 500"), KeyboardButton(text="От 500")],
            [KeyboardButton(text="Больше 1.000")]
        ],
        resize_keyboard=True
    )


def get_yes_no_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Да"), KeyboardButton(text="Нет")]
        ],
        resize_keyboard=True
    )


# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Это бот опросник!\n\n"
        "1. Общая сумма долга:",
        reply_markup=get_debt_keyboard()
    )
    await state.set_state(Survey.debt_amount)


# Обработка суммы долга
@dp.message(Survey.debt_amount)
async def process_debt(message: types.Message, state: FSMContext):
    if message.text not in ["До 500", "От 500", "Больше 1.000"]:
        await message.answer("Пожалуйста, выберите вариант из кнопок:")
        return

    await state.update_data(debt_amount=message.text)
    await message.answer(
        "2. Имеется ли иное имущество, кроме единственного жилья?",
        reply_markup=get_yes_no_keyboard()
    )
    await state.set_state(Survey.other_property)


# Обработка имущества
@dp.message(Survey.other_property)
async def process_property(message: types.Message, state: FSMContext):
    if message.text not in ["Да", "Нет"]:
        await message.answer("Пожалуйста, выберите Да или Нет:")
        return

    await state.update_data(other_property=message.text)
    await message.answer(
        "3. На вас оформлено залоговое имущество?",
        reply_markup=get_yes_no_keyboard()
    )
    await state.set_state(Survey.collateral_property)


# Обработка залогового имущества
@dp.message(Survey.collateral_property)
async def process_collateral(message: types.Message, state: FSMContext):
    if message.text not in ["Да", "Нет"]:
        await message.answer("Пожалуйста, выберите Да или Нет:")
        return

    await state.update_data(collateral_property=message.text)
    await message.answer(
        "4. Имеются просрочки по кредитам?",
        reply_markup=get_yes_no_keyboard()
    )
    await state.set_state(Survey.credit_delays)




@dp.message(Survey.credit_delays)
async def process_delays(message: types.Message, state: FSMContext):
    if message.text not in ["Да", "Нет"]:
        await message.answer("Пожалуйста, выберите Да или Нет:")
        return




    user_data = await state.get_data()
    user_data['credit_delays'] = message.text
    user_data['user_id'] = message.from_user.id
    user_data['username'] = message.from_user.username



    # Отправляем данные на вебхук
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    WEBHOOK_URL,
                    json=user_data,
                    headers={'Content-Type': 'application/json'}
            ) as response:
                if response.status == 200:
                    await message.answer(
                        "Спасибо! Опрос завершен. Данные отправлены.",
                        reply_markup=types.ReplyKeyboardRemove()
                    )
                else:
                    await message.answer(
                        "Ошибка отправки данных. Попробуйте позже.",
                        reply_markup=types.ReplyKeyboardRemove()
                    )
    except Exception as e:
        await message.answer(
            "Ошибка соединения. Попробуйте позже.",
            reply_markup=types.ReplyKeyboardRemove()
        )

    await state.clear()





async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
