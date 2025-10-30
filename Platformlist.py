import asyncio
from datetime import datetime
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

BOT_TOKEN = ""

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_states = {}
user_trips = {}
user_drivers = {}
user_vehicles = {}
user_selections = {}  # Для хранения выбранных водителей и транспорта


def get_main_menu_keyboard():
    k = [
        [InlineKeyboardButton(text='  Создать рейс', callback_data='create_trip')],
        [InlineKeyboardButton(text='  Мои водители', callback_data='my_drivers')],
        [InlineKeyboardButton(text='  Мой транспорт', callback_data='my_transport')],
        [InlineKeyboardButton(text='  Мои рейсы', callback_data='my_trips')],
        [InlineKeyboardButton(text='  Платформа', callback_data='platform')],
        [InlineKeyboardButton(text='  Поддержка', callback_data='support')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=k)


def get_back_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back"))
    return builder.as_markup()


def get_trip_type_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔄 Регулярный", callback_data="regular_trip"))
    builder.row(InlineKeyboardButton(text="🎯 Заказной", callback_data="custom_trip"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back"))
    return builder.as_markup()


def get_drivers_management_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="➕ Добавить водителя", callback_data="add_driver"))
    builder.row(InlineKeyboardButton(text="🗑️ Удалить водителя", callback_data="delete_driver"))
    builder.row(InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu"))
    return builder.as_markup()


def get_vehicles_management_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="➕ Добавить транспорт", callback_data="add_vehicle"))
    builder.row(InlineKeyboardButton(text="🗑️ Удалить транспорт", callback_data="delete_vehicle"))
    builder.row(InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu"))
    return builder.as_markup()


def get_drivers_selection_keyboard(user_id):
    """Клавиатура для выбора нескольких водителей с отметкой галочкой"""
    user_drivers_list = user_drivers.get(user_id, [])
    selected_drivers = user_selections.get(user_id, {}).get('selected_drivers', [])

    builder = InlineKeyboardBuilder()

    for i, driver in enumerate(user_drivers_list):
        if i in selected_drivers:
            builder.row(InlineKeyboardButton(text=f"✅ {driver['name']}", callback_data=f"toggle_driver_{i}"))
        else:
            builder.row(InlineKeyboardButton(text=f"❌ {driver['name']}", callback_data=f"toggle_driver_{i}"))

    if selected_drivers:
        builder.row(InlineKeyboardButton(text="🚀 Продолжить с выбранными водителями", callback_data="confirm_drivers"))

    builder.row(InlineKeyboardButton(text="➕ Добавить водителя", callback_data="add_driver_in_trip"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back"))

    return builder.as_markup()


def get_vehicles_selection_keyboard(user_id):
    """Клавиатура для выбора транспорта"""
    user_vehicles_list = user_vehicles.get(user_id, [])
    builder = InlineKeyboardBuilder()

    for i, vehicle in enumerate(user_vehicles_list):
        builder.row(
            InlineKeyboardButton(text=f"{vehicle['model']} ({vehicle['number']})", callback_data=f"select_vehicle_{i}"))

    builder.row(InlineKeyboardButton(text="➕ Добавить транспорт", callback_data="add_vehicle_in_trip"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back"))

    return builder.as_markup()


def validate_datetime_format(datetime_text: str) -> bool:
    try:
        parts = datetime_text.split()
        if len(parts) != 2:
            return False

        date_part, time_part = parts
        date_parts = date_part.split('.')
        if len(date_parts) != 3:
            return False

        day, month, year = date_parts
        if not (day.isdigit() and month.isdigit() and year.isdigit()):
            return False

        day_int = int(day)
        month_int = int(month)
        year_int = int(year)
        current_year = datetime.now().year

        if not (1 <= month_int <= 12):
            return False
        if not (year_int >= current_year):
            return False

        if month_int in [1, 3, 5, 7, 8, 10, 12]:
            if not (1 <= day_int <= 31):
                return False
        elif month_int in [4, 6, 9, 11]:
            if not (1 <= day_int <= 30):
                return False
        else:
            if (year_int % 4 == 0 and year_int % 100 != 0) or (year_int % 400 == 0):
                if not (1 <= day_int <= 29):
                    return False
            else:
                if not (1 <= day_int <= 28):
                    return False

        time_parts = time_part.split(':')
        if len(time_parts) != 2:
            return False

        hour, minute = time_parts
        if not (hour.isdigit() and minute.isdigit()):
            return False

        hour_int = int(hour)
        minute_int = int(minute)
        if not (0 <= hour_int <= 23 and 0 <= minute_int <= 59):
            return False

        return True
    except:
        return False


def validate_birth_date(date_text: str) -> bool:
    try:
        date_parts = date_text.split('.')
        if len(date_parts) != 3:
            return False

        day, month, year = date_parts
        if not (day.isdigit() and month.isdigit() and year.isdigit()):
            return False

        day_int = int(day)
        month_int = int(month)
        year_int = int(year)

        if not (1 <= month_int <= 12):
            return False
        if not (1900 <= year_int <= datetime.now().year - 18):
            return False

        if month_int in [1, 3, 5, 7, 8, 10, 12]:
            if not (1 <= day_int <= 31):
                return False
        elif month_int in [4, 6, 9, 11]:
            if not (1 <= day_int <= 30):
                return False
        else:
            if (year_int % 4 == 0 and year_int % 100 != 0) or (year_int % 400 == 0):
                if not (1 <= day_int <= 29):
                    return False
            else:
                if not (1 <= day_int <= 28):
                    return False

        return True
    except:
        return False


def validate_passport(passport_text: str) -> bool:
    return len(passport_text) == 10 and passport_text.isdigit()


def validate_vehicle_number(number_text: str) -> bool:
    if len(number_text) < 3:
        return False
    return any(c.isalpha() for c in number_text) or any(c.isdigit() for c in number_text)


def validate_route(route_text: str) -> bool:
    parts = route_text.split('-')
    return len(parts) >= 2 and all(part.strip() for part in parts)


def get_user_state(user_id):
    user_state = user_states.get(user_id)
    if isinstance(user_state, dict):
        return user_state.get("state")
    return None


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    user_states[user_id] = {"state": "waiting_company_name"}

    try:
        await message.answer_photo(
            photo=FSInputFile("Pictures/Hello.jpg"),
            caption="👨‍💻 Я - твой бот помощник\n\n Чат-бот технологической компании 'Моя платформа'.\n\n📌 Загрузите список пассажиров прямо здесь.\n\nНо для начала, давайте зарегистрируемся!",
            parse_mode="HTML"
        )
    except:
        await message.answer(
            "👨‍💻 Я - твой бот помощник\n\n Чат-бот технологической компании 'Моя платформа'.\n\n📌 Загрузите список пассажиров прямо здесь.\n\nНо для начала, давайте зарегистрируемся!",
            parse_mode="HTML"
        )

    await message.answer(
        "🏢 Введите название компании перевозчика\n\nНапример: ИП Иванов",
        parse_mode="HTML"
    )


@dp.message(lambda message: get_user_state(message.from_user.id) == "waiting_company_name")
async def handle_company_name(message: types.Message):
    user_id = message.from_user.id
    user_states[user_id] = {"state": "waiting_phone"}

    await message.answer(
        f"📞 Теперь введите телефон для обратной связи:",
        parse_mode="HTML"
    )


@dp.message(lambda message: get_user_state(message.from_user.id) == "waiting_phone")
async def handle_phone(message: types.Message):
    user_id = message.from_user.id
    user_states[user_id] = {}

    await message.answer(
        f"✅ Регистрация завершена!\n\nТеперь вы можете создавать рейсы и управлять своими водителями и транспортом.✨✨✨",
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )


@dp.callback_query(lambda c: c.data == "back_to_menu")
async def handle_back_to_menu(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_states[user_id] = {}

    await callback.message.answer(
        "📋 Главное меню:",
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )


@dp.callback_query(lambda c: c.data == "back")
async def handle_back(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_state = user_states.get(user_id, {})
    current_state = user_state.get("state")
    previous_state = user_state.get("previous_state")

    # Если нет предыдущего состояния, возвращаем в главное меню
    if not previous_state:
        await handle_back_to_menu(callback)
        return

    # Возврат на предыдущий шаг в процессе создания рейса
    if current_state == "waiting_trip_type":
        await handle_back_to_menu(callback)
    elif current_state == "waiting_route":
        await handle_create_trip(callback)
    elif current_state == "waiting_departure_datetime":
        user_state.update({
            "state": "waiting_route",
            "previous_state": "waiting_trip_type"
        })
        trip_type = user_state.get('trip_type', '')
        await callback.message.edit_text(
            f"✅ Выбран тип рейса: {trip_type.upper() if trip_type else ''}\n\n📍 Введите маршрут в формате:\nГород-Город-Город\n\nНапример: Москва-Смоленск-Москва",
            parse_mode="HTML",
            reply_markup=get_back_keyboard()
        )
    elif current_state == "waiting_arrival_datetime":
        user_state.update({
            "state": "waiting_departure_datetime",
            "previous_state": "waiting_route"
        })
        route = user_state.get('route', '')
        await callback.message.edit_text(
            f"📍 Маршрут: {route}\n\n📅 Введите дату и время отправления:\nНапример: 05.01.2025 14:00",
            parse_mode="HTML",
            reply_markup=get_back_keyboard()
        )
    elif current_state == "waiting_driver_selection":
        user_state.update({
            "state": "waiting_arrival_datetime",
            "previous_state": "waiting_departure_datetime"
        })
        departure_datetime = user_state.get('departure_datetime', '')
        await callback.message.edit_text(
            f"📅 Дата и время отправления: {departure_datetime}\n\n🕒 Введите дату и время прибытия:\nНапример: 05.01.2025 18:00",
            parse_mode="HTML",
            reply_markup=get_back_keyboard()
        )
    elif current_state == "waiting_vehicle_selection":
        # Возврат к выбору водителя
        user_drivers_list = user_drivers.get(user_id, [])
        if user_drivers_list:
            keyboard = get_drivers_selection_keyboard(user_id)
            await callback.message.edit_text(
                "👨‍💼 Выберите водителей (можно несколько):",
                parse_mode="HTML",
                reply_markup=keyboard
            )
        else:
            user_state.update({
                "state": "waiting_new_driver_name",
                "previous_state": "waiting_driver_selection"
            })
            await callback.message.edit_text(
                "👨‍💼 У вас пока нет водителей. Давайте добавим первого!",
                parse_mode="HTML"
            )
            await callback.message.answer("👤 Введите ФИО водителя:\n\nНапример: Небываев Олег Васильевич")
    elif current_state == "waiting_passenger_count":
        # Возврат к выбору транспорта
        user_vehicles_list = user_vehicles.get(user_id, [])
        if user_vehicles_list:
            keyboard = get_vehicles_selection_keyboard(user_id)
            await callback.message.edit_text(
                "🚌 Выберите транспорт:",
                parse_mode="HTML",
                reply_markup=keyboard
            )
        else:
            user_state.update({
                "state": "waiting_new_vehicle_model",
                "previous_state": "waiting_vehicle_selection"
            })
            await callback.message.edit_text(
                "🚌 У вас пока нет транспорта. Давайте добавим первый!",
                parse_mode="HTML"
            )
            await callback.message.answer("🚗 Введите название транспорта:\n\nНапример: Спринтер")
    elif current_state in ["waiting_new_driver_name", "waiting_new_driver_birth_date", "waiting_new_driver_passport"]:
        # Возврат к выбору водителя при создании нового
        user_drivers_list = user_drivers.get(user_id, [])
        if user_drivers_list:
            keyboard = get_drivers_selection_keyboard(user_id)
            await callback.message.edit_text(
                "👨‍💼 Выберите водителей (можно несколько):",
                parse_mode="HTML",
                reply_markup=keyboard
            )
        else:
            user_state.update({
                "state": "waiting_new_driver_name",
                "previous_state": "waiting_driver_selection"
            })
            await callback.message.edit_text(
                "👨‍💼 У вас пока нет водителей. Давайте добавим первого!",
                parse_mode="HTML"
            )
            await callback.message.answer("👤 Введите ФИО водителя:\n\nНапример: Небываев Олег Васильевич")
    elif current_state in ["waiting_new_vehicle_model", "waiting_new_vehicle_number"]:
        # Возврат к выбору транспорта при создании нового
        user_vehicles_list = user_vehicles.get(user_id, [])
        if user_vehicles_list:
            keyboard = get_vehicles_selection_keyboard(user_id)
            await callback.message.edit_text(
                "🚌 Выберите транспорт:",
                parse_mode="HTML",
                reply_markup=keyboard
            )
        else:
            user_state.update({
                "state": "waiting_new_vehicle_model",
                "previous_state": "waiting_vehicle_selection"
            })
            await callback.message.edit_text(
                "🚌 У вас пока нет транспорта. Давайте добавим первый!",
                parse_mode="HTML"
            )
            await callback.message.answer("🚗 Введите название транспорта:\n\nНапример: Спринтер")
    else:
        await callback.message.answer(
            "📋 Главное меню:",
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard()
        )


@dp.callback_query(lambda c: c.data == "create_trip")
async def handle_create_trip(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_states[user_id] = {
        "state": "waiting_trip_type",
        "previous_state": "menu"
    }

    await callback.message.edit_text(
        "🗺️ Создание нового рейса\n\nВыберите тип рейса:",
        parse_mode="HTML",
        reply_markup=get_trip_type_keyboard()
    )


@dp.callback_query(lambda c: c.data in ["regular_trip", "custom_trip"])
async def handle_trip_type_selection(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    trip_type = "регулярный" if callback.data == "regular_trip" else "заказной"
    user_states[user_id] = {
        "state": "waiting_route",
        "previous_state": "waiting_trip_type",
        "trip_type": trip_type
    }

    await callback.message.edit_text(
        f"✅ Выбран тип рейса: {trip_type.upper()}\n\n📍 Введите маршрут в формате:\nГород-Город-Город\n\nНапример: Москва-Смоленск-Москва",
        parse_mode="HTML",
        reply_markup=get_back_keyboard()
    )


@dp.message(lambda message: get_user_state(message.from_user.id) == "waiting_route")
async def handle_route(message: types.Message):
    user_id = message.from_user.id
    user_state = user_states.get(user_id, {})
    route_text = message.text.strip()

    if not validate_route(route_text):
        await message.answer(
            "❌ Неверный формат маршрута!\n\n📍 Пожалуйста, введите маршрут в формате:\nГород-Город-Город\n\nНапример: Москва-Смоленск-Москва",
            reply_markup=get_back_keyboard()
        )
        return

    user_state.update({
        "route": route_text,
        "state": "waiting_departure_datetime",
        "previous_state": "waiting_route"
    })

    await message.answer(
        f"📍 Маршрут: {route_text}\n\n📅 Введите дату и время отправления:\nНапример: 05.01.2025 14:00",
        parse_mode="HTML",
        reply_markup=get_back_keyboard()
    )


@dp.message(lambda message: get_user_state(message.from_user.id) == "waiting_departure_datetime")
async def handle_departure_datetime(message: types.Message):
    user_id = message.from_user.id
    user_state = user_states.get(user_id, {})
    datetime_text = message.text.strip()

    if not validate_datetime_format(datetime_text):
        await message.answer(
            "❌ Неверный формат!\n\nПожалуйста, введите дату и время в формате:\nДД.ММ.ГГГГ ЧЧ:ММ\n\nНапример: 05.01.2025 14:00\n\nПопробуйте еще раз:",
            parse_mode="HTML",
            reply_markup=get_back_keyboard()
        )
        return

    user_state.update({
        "departure_datetime": datetime_text,
        "state": "waiting_arrival_datetime",
        "previous_state": "waiting_departure_datetime"
    })

    await message.answer(
        f"📅 Дата и время отправления: {datetime_text}\n\n🕒 Введите дату и время прибытия:\nНапример: 05.01.2025 18:00",
        parse_mode="HTML",
        reply_markup=get_back_keyboard()
    )


@dp.message(lambda message: get_user_state(message.from_user.id) == "waiting_arrival_datetime")
async def handle_arrival_datetime(message: types.Message):
    user_id = message.from_user.id
    user_state = user_states.get(user_id, {})
    datetime_text = message.text.strip()

    if not validate_datetime_format(datetime_text):
        await message.answer(
            "❌ Неверный формат!\n\nПожалуйста, введите дату и время в формате:\nДД.ММ.ГГГГ ЧЧ:ММ\n\nНапример: 05.01.2025 18:00\n\nПопробуйте еще раз:",
            parse_mode="HTML",
            reply_markup=get_back_keyboard()
        )
        return

    user_state.update({
        "arrival_datetime": datetime_text,
        "state": "waiting_driver_selection",
        "previous_state": "waiting_arrival_datetime"
    })

    user_drivers_list = user_drivers.get(user_id, [])
    if user_drivers_list:
        # Показываем инлайн клавиатуру для выбора водителей
        keyboard = get_drivers_selection_keyboard(user_id)
        await message.answer(
            "👨‍💼 Выберите водителей (можно несколько):",
            parse_mode="HTML",
            reply_markup=keyboard
        )
    else:
        user_state.update({
            "state": "waiting_new_driver_name",
            "previous_state": "waiting_driver_selection"
        })
        await message.answer("👨‍💼 У вас пока нет водителей. Давайте добавим первого!", reply_markup=get_back_keyboard())
        await message.answer("👤 Введите ФИО водителя:\n\nНапример: Небываев Олег Васильевич")


# Обработчики выбора водителей через инлайн кнопки
@dp.callback_query(lambda c: c.data.startswith("toggle_driver_"))
async def handle_toggle_driver(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    driver_index = int(callback.data.split("_")[2])

    # Инициализируем структуру для хранения выбранных водителей
    if user_id not in user_selections:
        user_selections[user_id] = {}
    if 'selected_drivers' not in user_selections[user_id]:
        user_selections[user_id]['selected_drivers'] = []

    selected_drivers = user_selections[user_id]['selected_drivers']

    # Добавляем или удаляем водителя из выбранных
    if driver_index in selected_drivers:
        selected_drivers.remove(driver_index)
    else:
        selected_drivers.append(driver_index)

    # Обновляем клавиатуру с новым состоянием выбора
    user_drivers_list = user_drivers.get(user_id, [])
    if user_drivers_list:
        keyboard = get_drivers_selection_keyboard(user_id)
        await callback.message.edit_text(
            "👨‍💼 Выберите водителей (можно несколько):",
            parse_mode="HTML",
            reply_markup=keyboard
        )
    else:
        await callback.answer("❌ Список водителей пуст")


@dp.callback_query(lambda c: c.data == "confirm_drivers")
async def handle_confirm_drivers(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_state = user_states.get(user_id, {})
    selected_drivers = user_selections.get(user_id, {}).get('selected_drivers', [])

    if not selected_drivers:
        await callback.answer("❌ Сначала выберите хотя бы одного водителя")
        return

    user_drivers_list = user_drivers.get(user_id, [])
    selected_drivers_objects = []

    for driver_index in selected_drivers:
        if 0 <= driver_index < len(user_drivers_list):
            selected_drivers_objects.append(user_drivers_list[driver_index])

    if selected_drivers_objects:
        user_state.update({
            "drivers": selected_drivers_objects,
            "state": "waiting_vehicle_selection",
            "previous_state": "waiting_driver_selection"
        })

        # Показываем инлайн клавиатуру для выбора транспорта
        user_vehicles_list = user_vehicles.get(user_id, [])
        if user_vehicles_list:
            keyboard = get_vehicles_selection_keyboard(user_id)
            await callback.message.edit_text(
                "🚌 Выберите транспорт:",
                parse_mode="HTML",
                reply_markup=keyboard
            )
        else:
            user_state.update({
                "state": "waiting_new_vehicle_model",
                "previous_state": "waiting_vehicle_selection"
            })
            await callback.message.edit_text(
                "🚌 У вас пока нет транспорта. Давайте добавим первый!",
                parse_mode="HTML"
            )
            await callback.message.answer("🚗 Введите название транспорта:\n\nНапример: Спринтер")
    else:
        await callback.answer("❌ Ошибка выбора водителей")


@dp.callback_query(lambda c: c.data == "add_driver_in_trip")
async def handle_add_driver_in_trip(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_states[user_id] = {
        "state": "waiting_new_driver_name",
        "previous_state": "waiting_driver_selection"
    }
    await callback.message.edit_text(
        "👤 Введите ФИО водителя:\n\nНапример: Небываев Артем Павлович",
        reply_markup=get_back_keyboard()
    )


# Обработчики выбора транспорта через инлайн кнопки
@dp.callback_query(lambda c: c.data.startswith("select_vehicle_"))
async def handle_select_vehicle(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_state = user_states.get(user_id, {})
    vehicle_index = int(callback.data.split("_")[2])

    user_vehicles_list = user_vehicles.get(user_id, [])
    if 0 <= vehicle_index < len(user_vehicles_list):
        vehicle_selected = user_vehicles_list[vehicle_index]
        user_state.update({
            "vehicle": vehicle_selected,
            "state": "waiting_passenger_count",
            "previous_state": "waiting_vehicle_selection"
        })

        await callback.message.edit_text(
            "👥 Введите количество пассажиров:",
            parse_mode="HTML",
            reply_markup=get_back_keyboard()
        )
    else:
        await callback.answer("❌ Ошибка выбора транспорта")


@dp.callback_query(lambda c: c.data == "add_vehicle_in_trip")
async def handle_add_vehicle_in_trip(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_states[user_id] = {
        "state": "waiting_new_vehicle_model",
        "previous_state": "waiting_vehicle_selection"
    }
    await callback.message.edit_text(
        "🚗 Введите название транспорта:\n\nНапример: Спринтер",
        reply_markup=get_back_keyboard()
    )


@dp.message(lambda message: get_user_state(message.from_user.id) == "waiting_new_driver_name")
async def handle_new_driver_name(message: types.Message):
    user_id = message.from_user.id
    user_state = user_states.get(user_id, {})
    user_state.update({
        "new_driver_name": message.text,
        "state": "waiting_new_driver_birth_date",
        "previous_state": "waiting_new_driver_name"
    })
    await message.answer("📅 Введите дату рождения водителя:\n\nНапример: 01.01.1999", reply_markup=get_back_keyboard())


@dp.message(lambda message: get_user_state(message.from_user.id) == "waiting_new_driver_birth_date")
async def handle_new_driver_birth_date(message: types.Message):
    user_id = message.from_user.id
    user_state = user_states.get(user_id, {})

    if not validate_birth_date(message.text):
        await message.answer(
            "❌ Неверный формат даты!\n\nПожалуйста, введите дату в формате ДД.ММ.ГГГГ\n\nНапример: 01.01.1999",
            reply_markup=get_back_keyboard()
        )
        return

    user_state.update({
        "new_driver_birth_date": message.text,
        "state": "waiting_new_driver_passport",
        "previous_state": "waiting_new_driver_birth_date"
    })
    await message.answer("📄 Введите номер паспорта водителя (10 цифр):\n\nНапример: 1234567891",
                         reply_markup=get_back_keyboard())


@dp.message(lambda message: get_user_state(message.from_user.id) == "waiting_new_driver_passport")
async def handle_new_driver_passport(message: types.Message):
    user_id = message.from_user.id
    user_state = user_states.get(user_id, {})

    if not validate_passport(message.text):
        await message.answer(
            "❌ Неверный формат паспорта!\n\nПожалуйста, введите 10 цифр\n\nНапример: 1234567891",
            reply_markup=get_back_keyboard()
        )
        return

    new_driver = {
        "name": user_state["new_driver_name"],
        "birth_date": user_state["new_driver_birth_date"],
        "passport": message.text
    }

    if user_id not in user_drivers:
        user_drivers[user_id] = []
    user_drivers[user_id].append(new_driver)

    # После добавления водителя возвращаемся к выбору водителей
    user_state.update({
        "state": "waiting_driver_selection",
        "previous_state": "waiting_new_driver_passport"
    })

    # Показываем обновленный список водителей с инлайн кнопками
    user_drivers_list = user_drivers.get(user_id, [])
    if user_drivers_list:
        keyboard = get_drivers_selection_keyboard(user_id)
        await message.answer(
            "✅ Водитель добавлен!\n\n👨‍💼 Выберите водителей (можно несколько):",
            parse_mode="HTML",
            reply_markup=keyboard
        )
    else:
        await message.answer("❌ Ошибка при добавлении водителя")


@dp.message(lambda message: get_user_state(message.from_user.id) == "waiting_new_vehicle_model")
async def handle_new_vehicle_model(message: types.Message):
    user_id = message.from_user.id
    user_state = user_states.get(user_id, {})
    user_state.update({
        "new_vehicle_model": message.text,
        "state": "waiting_new_vehicle_number",
        "previous_state": "waiting_new_vehicle_model"
    })
    await message.answer("🔢 Введите госномер транспорта:\n\nНапример: а777аа31", reply_markup=get_back_keyboard())


@dp.message(lambda message: get_user_state(message.from_user.id) == "waiting_new_vehicle_number")
async def handle_new_vehicle_number(message: types.Message):
    user_id = message.from_user.id
    user_state = user_states.get(user_id, {})

    if not validate_vehicle_number(message.text):
        await message.answer(
            "❌ Неверный формат номера!\n\nПожалуйста, введите корректный номер транспорта\n\nНапример: а777аа31",
            reply_markup=get_back_keyboard()
        )
        return

    new_vehicle = {
        "model": user_state["new_vehicle_model"],
        "number": message.text.upper()
    }

    if user_id not in user_vehicles:
        user_vehicles[user_id] = []
    user_vehicles[user_id].append(new_vehicle)

    user_state.update({
        "state": "waiting_vehicle_selection",
        "previous_state": "waiting_new_vehicle_number"
    })

    # Показываем обновленный список транспорта с инлайн кнопками
    user_vehicles_list = user_vehicles.get(user_id, [])
    if user_vehicles_list:
        keyboard = get_vehicles_selection_keyboard(user_id)
        await message.answer(
            "✅ Транспорт добавлен!\n\n🚌 Выберите транспорт:",
            parse_mode="HTML",
            reply_markup=keyboard
        )
    else:
        await message.answer("❌ Ошибка при добавлении транспорта")


@dp.message(lambda message: get_user_state(message.from_user.id) == "waiting_passenger_count")
async def handle_passenger_count(message: types.Message):
    user_id = message.from_user.id
    user_state = user_states.get(user_id, {})

    # Проверяем наличие всех необходимых данных
    required_fields = ['trip_type', 'route', 'departure_datetime', 'arrival_datetime', 'drivers', 'vehicle']
    missing_fields = []

    for field in required_fields:
        if field not in user_state:
            missing_fields.append(field)

    if missing_fields:
        error_message = "❌ Произошла ошибка: недостаточно данных для создания рейса.\n\nОтсутствуют данные: " + ", ".join(
            missing_fields)
        await message.answer(
            error_message,
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard()
        )
        # Сбрасываем состояние
        user_states[user_id] = {}
        return

    if not message.text.isdigit():
        await message.answer("❌ Пожалуйста, введите число пассажиров.\nНапример: 15", reply_markup=get_back_keyboard())
        return

    user_state["passenger_count"] = message.text

    trip_id = len(user_trips.get(user_id, [])) + 1
    trip_data = {
        "id": trip_id,
        "trip_type": user_state['trip_type'],
        "route": user_state['route'],
        "departure_datetime": user_state['departure_datetime'],
        "arrival_datetime": user_state['arrival_datetime'],
        "drivers": user_state['drivers'],
        "vehicle": user_state['vehicle'],
        "passenger_count": user_state['passenger_count'],
        "status": "активный"
    }

    if user_id not in user_trips:
        user_trips[user_id] = []
    user_trips[user_id].append(trip_data)

    # Очищаем выбор пользователя
    if user_id in user_selections:
        user_selections[user_id] = {}

    user_states[user_id] = {}

    # Формируем список водителей для отображения
    drivers_text = ", ".join([driver['name'] for driver in user_state['drivers']])

    trip_info = f"""
✅ Рейс успешно создан!

📋 Информация о рейсе:
├ Тип рейса: {user_state['trip_type'].upper()}
├ Маршрут: {user_state['route']}
├ Отправление: {user_state['departure_datetime']}
├ Прибытие: {user_state['arrival_datetime']}
├ Водители: {drivers_text}
├ Транспорт: {user_state['vehicle']['model']} ({user_state['vehicle']['number']})
└ Количество пассажиров: {user_state['passenger_count']}

📌 Рейс добавлен в ваш список рейсов.
"""

    await message.answer(
        trip_info,
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )


@dp.callback_query(lambda c: c.data == "my_drivers")
async def handle_my_drivers(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_drivers_list = user_drivers.get(user_id, [])

    if not user_drivers_list:
        await callback.message.edit_text(
            "👨‍💼 Мои водители\n\n🚫 У вас пока нет добавленных водителей.",
            parse_mode="HTML",
            reply_markup=get_drivers_management_keyboard()
        )
        return

    drivers_text = "👨‍💼 Мои водители\n\n"
    for i, driver in enumerate(user_drivers_list, 1):
        drivers_text += f"""
{i}. {driver['name']}
   📅 Дата рождения: {driver['birth_date']}
   📄 Паспорт: {driver['passport']}
────────────────────
"""

    await callback.message.edit_text(
        drivers_text,
        parse_mode="HTML",
        reply_markup=get_drivers_management_keyboard()
    )


@dp.callback_query(lambda c: c.data == "my_transport")
async def handle_my_transport(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_vehicles_list = user_vehicles.get(user_id, [])

    if not user_vehicles_list:
        await callback.message.edit_text(
            "🚌 Мой транспорт\n\n🚫 У вас пока нет добавленного транспорта.",
            parse_mode="HTML",
            reply_markup=get_vehicles_management_keyboard()
        )
        return

    vehicles_text = "🚌 Мой транспорт\n\n"
    for i, vehicle in enumerate(user_vehicles_list, 1):
        vehicles_text += f"""
{i}. {vehicle['model']}
   🔢 Номер: {vehicle['number']}
────────────────────
"""

    await callback.message.edit_text(
        vehicles_text,
        parse_mode="HTML",
        reply_markup=get_vehicles_management_keyboard()
    )


@dp.callback_query(lambda c: c.data == "add_driver")
async def handle_add_driver_from_menu(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_states[user_id] = {
        "state": "waiting_new_driver_name",
        "previous_state": "menu"
    }
    await callback.message.edit_text(
        "👤 Введите ФИО водителя:\n\nНапример: Небываев Артем Павлович",
        reply_markup=get_back_keyboard()
    )


@dp.callback_query(lambda c: c.data == "add_vehicle")
async def handle_add_vehicle_from_menu(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_states[user_id] = {
        "state": "waiting_new_vehicle_model",
        "previous_state": "menu"
    }
    await callback.message.edit_text(
        "🚗 Введите название транспорта:\n\nНапример: Спринтер",
        reply_markup=get_back_keyboard()
    )


@dp.callback_query(lambda c: c.data == "delete_driver")
async def handle_delete_driver(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_drivers_list = user_drivers.get(user_id, [])

    if not user_drivers_list:
        await callback.answer("🚫 У вас нет водителей для удаления.")
        return

    builder = InlineKeyboardBuilder()
    for i, driver in enumerate(user_drivers_list, 1):
        builder.row(InlineKeyboardButton(text=f"{i}. {driver['name']}", callback_data=f"delete_driver_{i - 1}"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="my_drivers"))

    await callback.message.edit_text(
        "🗑️ Выберите водителя для удаления:",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )


@dp.callback_query(lambda c: c.data.startswith("delete_driver_"))
async def handle_driver_deletion(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    driver_index = int(callback.data.split("_")[2])

    user_drivers_list = user_drivers.get(user_id, [])

    if 0 <= driver_index < len(user_drivers_list):
        driver_name = user_drivers_list[driver_index]['name']
        del user_drivers_list[driver_index]
        await callback.message.edit_text(
            f"✅ Водитель {driver_name} удален из вашего списка.",
            parse_mode="HTML",
            reply_markup=get_drivers_management_keyboard()
        )
    else:
        await callback.answer("❌ Водитель не найден.")


@dp.callback_query(lambda c: c.data == "delete_vehicle")
async def handle_delete_vehicle(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_vehicles_list = user_vehicles.get(user_id, [])

    if not user_vehicles_list:
        await callback.answer("🚫 У вас нет транспорта для удаления.")
        return

    builder = InlineKeyboardBuilder()
    for i, vehicle in enumerate(user_vehicles_list, 1):
        builder.row(InlineKeyboardButton(text=f"{i}. {vehicle['model']} ({vehicle['number']})",
                                         callback_data=f"delete_vehicle_{i - 1}"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="my_transport"))

    await callback.message.edit_text(
        "🗑️ Выберите транспорт для удаления:",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )


@dp.callback_query(lambda c: c.data.startswith("delete_vehicle_"))
async def handle_vehicle_deletion(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    vehicle_index = int(callback.data.split("_")[2])

    user_vehicles_list = user_vehicles.get(user_id, [])

    if 0 <= vehicle_index < len(user_vehicles_list):
        vehicle_model = user_vehicles_list[vehicle_index]['model']
        del user_vehicles_list[vehicle_index]
        await callback.message.edit_text(
            f"✅ Транспорт {vehicle_model} удален из вашего списка.",
            parse_mode="HTML",
            reply_markup=get_vehicles_management_keyboard()
        )
    else:
        await callback.answer("❌ Транспорт не найден.")


user_trip_pages = {}


@dp.callback_query(lambda c: c.data == "my_trips")
async def handle_my_trips(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_trips_list = user_trips.get(user_id, [])

    if not user_trips_list:
        await callback.message.edit_text(
            "📋 Мои рейсы\n\n🚫 У вас пока нет созданных рейсов.\n🗺️ Создайте первый рейс через меню 'Создать рейс'",
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard()
        )
        return

    user_trip_pages[user_id] = 0
    await show_trip_page(callback, user_id, 0)


async def show_trip_page(callback: types.CallbackQuery, user_id: int, page: int):
    user_trips_list = user_trips.get(user_id, [])
    trips_per_page = 3
    start_index = page * trips_per_page
    end_index = start_index + trips_per_page

    current_trips = user_trips_list[start_index:end_index]

    if not current_trips:
        await callback.answer("❌ Нет рейсов для отображения на этой странице.")
        return

    trips_text = "📋 Мои рейсы\n\n"
    trips_text += "Выберите рейс для просмотра подробной информации\n\n"

    for i, trip in enumerate(current_trips, 1):
        # Формируем список водителей для отображения
        drivers_text = ", ".join([driver['name'] for driver in trip['drivers']])
        trips_text += f"🔹 {trip['route']}\n"
        trips_text += f"   📅 {trip['departure_datetime']}\n"
        trips_text += f"   👤 {drivers_text}\n"
        trips_text += f"   🚗 {trip['vehicle']['model']}\n"
        trips_text += "────────────────────\n"

    builder = InlineKeyboardBuilder()

    for i in range(len(current_trips)):
        builder.row(InlineKeyboardButton(text=f"Рейс {start_index + i + 1}", callback_data=f"trip_{start_index + i}"))

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data="prev_trips"))
    if end_index < len(user_trips_list):
        nav_buttons.append(InlineKeyboardButton(text="Следующие ➡️", callback_data="next_trips"))

    if nav_buttons:
        builder.row(*nav_buttons)

    builder.row(InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu"))

    await callback.message.edit_text(
        trips_text,
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )


@dp.callback_query(lambda c: c.data.startswith("trip_"))
async def handle_trip_selection(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    try:
        trip_number = int(callback.data.split("_")[1])
        user_trips_list = user_trips.get(user_id, [])

        if 0 <= trip_number < len(user_trips_list):
            trip = user_trips_list[trip_number]

            # Формируем список водителей для отображения
            drivers_text = "\n".join([f"   👤 {driver['name']}" for driver in trip['drivers']])

            trip_info = f"""
🔹 Рейс #{trip['id']}
├ Тип: {trip['trip_type'].upper()}
├ Маршрут: {trip['route']}
├ Отправление: {trip['departure_datetime']}
├ Прибытие: {trip['arrival_datetime']}
{drivers_text}
├ Транспорт: {trip['vehicle']['model']} ({trip['vehicle']['number']})
├ Пассажиры: {trip['passenger_count']}
└ Статус: {trip['status']}
"""
            builder = InlineKeyboardBuilder()
            builder.row(InlineKeyboardButton(text="🔙 Назад к рейсам", callback_data="my_trips"))
            builder.row(InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu"))

            await callback.message.edit_text(
                trip_info,
                parse_mode="HTML",
                reply_markup=builder.as_markup()
            )
        else:
            await callback.answer("❌ Рейс не найден.")
    except (ValueError, IndexError):
        await callback.answer("❌ Неверный формат номера рейса.")


@dp.callback_query(lambda c: c.data in ["next_trips", "prev_trips"])
async def handle_trips_navigation(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    current_page = user_trip_pages.get(user_id, 0)

    if callback.data == "next_trips":
        new_page = current_page + 1
    else:
        new_page = max(0, current_page - 1)

    user_trip_pages[user_id] = new_page
    await show_trip_page(callback, user_id, new_page)


@dp.callback_query(lambda c: c.data == "platform")
async def handle_platform(callback: types.CallbackQuery):
    try:
        await callback.message.answer_photo(
            photo=FSInputFile("Pictures/Platform.jpg"),
            caption="""🖥️ Платформа

Если остались вопросы ознакомьтесь с нашей платформой 📱
https://moyaplatforma.ru/""",
            parse_mode="HTML",
            reply_markup=get_back_keyboard()
        )
    except:
        await callback.message.answer(
            """🖥️ Платформа

Если остались вопросы ознакомьтесь с нашей платформой 📱
https://moyaplatforma.ru/""",
            parse_mode="HTML",
            reply_markup=get_back_keyboard()
        )


@dp.callback_query(lambda c: c.data == "support")
async def handle_support(callback: types.CallbackQuery):
    try:
        await callback.message.answer_photo(
            photo=FSInputFile("Pictures/Help.jpg"),
            caption="""📢 Поддержка

Если вам нужна срочная помощь, позвоните сюда:
+79155762192""",
            parse_mode="HTML",
            reply_markup=get_back_keyboard()
        )
    except:
        await callback.message.answer(
            """📢 Поддержка

Если вам нужна срочная помощь, позвоните сюда:
+79155762192""",
            parse_mode="HTML",
            reply_markup=get_back_keyboard()
        )


@dp.message()
async def handle_unknown_message(message: types.Message):
    current_state = get_user_state(message.from_user.id)

    if current_state is None:
        await message.answer(
            "❌ Пожалуйста, используйте кнопки меню для навигации:",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await message.answer(
            "❌ Непонятный запрос. Пожалуйста, следуйте инструкциям выше.",
            reply_markup=get_back_keyboard()
        )


async def main():
    print("Bot started!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
