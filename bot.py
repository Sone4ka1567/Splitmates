import datetime

from aiogram import Bot, types
from aiogram.contrib.fsm_storage.files import JSONStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import Dispatcher, FSMContext, filters
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor, markdown as md
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from tech import Database, texts, get_exchange_rate, CURRENCY_EXCHANGE_OPTIONS


bot = Bot(token=BOT_API_TOKEN, parse_mode="MarkdownV2")
storage = JSONStorage('./storage.json')

dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

db = Database()


class ExpenseState(StatesGroup):
    choosing_users = State()

class DebtPaymentStates(StatesGroup):
    awaiting_payment = State()


async def reset_state(message: types.Message, state: FSMContext) -> None:
    user_data = await state.get_data()

    if "keyboard_deleted" in user_data and user_data["keyboard_deleted"] and \
            "message_id" in user_data and user_data["message_id"] is not None:
        await bot.edit_message_reply_markup(message.chat.id, user_data["message_id"], reply_markup=None)
        await state.update_data(keyboard_deleted=True)

    await state.finish()


@dp.message_handler(commands=["start"], state="*")
async def start_command(message: types.Message, state: FSMContext) -> None:
    db.register_chat(message)

    await reset_state(message, state)
    await message.answer(
        md.text(
            "Привет, {name}\\!".format(name=message.from_user.first_name),
            md.escape_md(texts.START_TEXT),
            sep="\n"
        ),
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.update_data(keyboard_deleted=False)


@dp.message_handler(commands=["help"], state="*")
async def help_command(message: types.Message, state: FSMContext) -> None:
    await reset_state(message, state)
    await message.answer(
        md.escape_md(texts.HELP_TEXT),
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.update_data(keyboard_deleted=False)


@dp.message_handler(commands=["register"], state="*")
async def register_command(message: types.Message, state: FSMContext) -> None:
    await reset_state(message, state)

    args = message.get_args().split()
    if len(args) < 2:
        await state.update_data(keyboard_deleted=False)
        await message.reply(md.escape_md("Пожалуйста, отправьте команду в формате /register phone preffered_bank"))
        return

    db.register_user(message, args[0], args[1])

    await message.reply(
        md.text(
            md.escape_md(texts.REGISTER_TEXT),
            sep="\n"
        ),
        reply_markup=types.ReplyKeyboardRemove()
    )

    await state.update_data(keyboard_deleted=False)


@dp.message_handler(commands=["lang"], state="*")
async def lang_command(message: types.Message, state: FSMContext) -> None:
    pass


@dp.message_handler(commands=["ping"], state="*")
async def ping_command(message: types.Message, state: FSMContext) -> None:
    await reset_state(message, state)
    username = None
    if message.entities:
        for entity in message.entities:
            if entity.type == "mention":
                start = entity.offset + 1  # '+1' чтобы пропустить символ '@'
                length = entity.length - 1
                username = message.text[start:start+length]
                break

    if username:
        user_id = db.get_user_id_by_username(username)

        if user_id:
            try:
                debts = db.get_debts_for_pair(message.chat.id, message.from_user.id, user_id)

                text = md.escape_md(f"Ты должен {message.from_user.full_name}:\n")
                for debt in debts:
                    text += md.escape_md(f"{debt[3]} {debt[4]}\n")

                await bot.send_message(user_id, text)
                await message.reply(md.escape_md("Сообщение успешно отправлено!"))
            except Exception as e:
                await message.reply(md.escape_md(f"Не удалось отправить сообщение пользователю @{username}: {e}"))
        else:
            await message.reply(md.escape_md("Пользователь не найден."))
    else:
        await message.reply(md.escape_md("Пожалуйста, укажите пользователя в сообщении, например: /ping @username"))

    await state.update_data(keyboard_deleted=False)


@dp.message_handler(commands=["expense"], state="*")
async def expense_command(message: types.Message, state: FSMContext) -> None:
    args = message.get_args().split(maxsplit=2)
    if len(args) < 3:
        await message.reply(md.escape_md("Используйте команду в формате: /expense amount currency description"))
        return

    amount, currency, description = args
    await state.update_data(amount=float(amount), currency=currency, description=description, chat_id=message.chat.id, selected_users=[])

    users = db.get_users_in_chat(message.chat.id)
    keyboard = InlineKeyboardMarkup(row_width=2)
    for user in users:
        button = InlineKeyboardButton(user[1], callback_data=f"user_{user[0]}")
        keyboard.add(button)

    equal_button = InlineKeyboardButton("Разделить поровну", callback_data="equal")
    keyboard.add(equal_button)

    await ExpenseState.choosing_users.set()
    await message.reply(md.escape_md("Выберите пользователей для распределения затрат:"), reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data.startswith("user_"), state=ExpenseState.choosing_users)
async def add_user_to_list(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = int(callback_query.data.split("_")[1])
    data = await state.get_data()
    selected_users = data.get("selected_users", [])

    users = db.get_users_in_chat(data['chat_id'])
    keyboard = InlineKeyboardMarkup(row_width=2)

    # Обновляем список выбранных пользователей
    if user_id not in selected_users:
        selected_users.append(user_id)
    else:
        selected_users.remove(user_id)

    await state.update_data(selected_users=selected_users)

    # Обновляем текст кнопок
    for user in users:
        status = "✓ " if user[0] in selected_users else ""
        username_button = f"{status}{user[1]}"
        button = InlineKeyboardButton(username_button, callback_data=f"user_{user[0]}")
        keyboard.add(button)

    equal_button = InlineKeyboardButton("Разделить поровну", callback_data="equal")
    keyboard.add(equal_button)

    await callback_query.message.edit_reply_markup(keyboard)
    await callback_query.answer()


@dp.callback_query_handler(text_contains="equal", state=ExpenseState.choosing_users)
async def process_equal_division(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    data = await state.get_data()
    users = data.get("selected_users", [])
    if not users:
        await callback_query.message.reply(md.escape_md("Пожалуйста, выберите пользователей."))
        return

    amount_per_user = data['amount'] / len(users)
    for user_id in users:
        db.update_or_add_debt(
            creditor_id=callback_query.from_user.id, debtor_id=user_id, amount=amount_per_user,
            currency=data['currency'], description=data['description'], chat_id=data['chat_id']
        )
    
    await callback_query.message.reply(md.escape_md("Долги обновлены и поровну разделены."))
    await state.finish()


@dp.message_handler(commands=["debts"], state="*")
async def debts_command(message: types.Message, state: FSMContext):
    debts = db.get_debts_from_chat(message.chat.id)
    # (debt_id, debtor_id, creditor_id, amount, currency) с сортированными ID

    if not debts:
        await message.reply(md.escape_md("В этом чате нет активных долгов."))
        return
    
    await state.update_data(debts_to_convert=debts)

    response = md.escape_md("Долги в чате:\n")
    for debt in debts:
        username_1, username_2 = db.get_username_by_user_id(debt[1]), db.get_username_by_user_id(debt[2]), 
        response += md.escape_md(f"Пользователь {username_1} должен пользователю {username_2} {debt[3]} {debt[4]}\n")

    keyboard = InlineKeyboardMarkup()

    convert_button = InlineKeyboardButton("Привести к одной валюте", callback_data="choose_currency")
    keyboard.add(convert_button)

    await message.reply(response, reply_markup=keyboard)


@dp.message_handler(commands=["debts_to_me"], state="*")
async def debts_to_me_command(message: types.Message, state: FSMContext) -> None:
    debts = db.get_debts_by_creditor_id(message.chat.id, message.from_user.id)
    # (debt_id, debtor_id, creditor_id, amount, currency) с сортированными ID

    if not debts:
        await message.reply(md.escape_md("Тебе никто не должен лох педальный."))
        return
    
    await state.update_data(debts_to_convert=debts)

    creditor_name = db.get_username_by_user_id(message.from_user.id)

    response =  md.escape_md(f"Должны {creditor_name}:\n")
    for debt in debts:
        debtor = db.get_username_by_user_id(debt[1])
        response += md.escape_md(f"Пользователь {debtor} должен {debt[3]} {debt[4]}\n")

    keyboard = InlineKeyboardMarkup()
    convert_button = InlineKeyboardButton("Привести к одной валюте", callback_data="choose_currency")
    keyboard.add(convert_button)

    await message.reply(response, reply_markup=keyboard)


@dp.message_handler(commands=["my_debts"], state="*")
async def my_debts_command(message: types.Message, state: FSMContext) -> None:
    debts = db.get_debts_by_debtor_id(message.chat.id, message.from_user.id)
    # (debt_id, debtor_id, creditor_id, amount, currency, date) с сортированными ID
    if not debts:
        await message.reply(md.escape_md("Ты красава никому не должен."))
        return

    await state.update_data(debts_to_convert=debts)

    debtor_name = db.get_username_by_user_id(message.from_user.id)

    response = md.escape_md(f"{debtor_name} должен:\n")
    for debt in debts:
        creditor = db.get_username_by_user_id(debt[2])
        response += md.escape_md(f"Пользователю {creditor} должен {debt[3]} {debt[4]}\n")

    keyboard = InlineKeyboardMarkup()
    # Эта кнопка запускает процесс выбора валюты
    convert_button = InlineKeyboardButton("Привести к одной валюте", callback_data="choose_currency")
    keyboard.add(convert_button)

    await message.reply(response, reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data == "choose_currency", state="*")
async def choose_currency(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    keyboard = InlineKeyboardMarkup()
    for currency in CURRENCY_EXCHANGE_OPTIONS:
        currency_button = InlineKeyboardButton(currency, callback_data=f"convert_to_{currency}")
        keyboard.add(currency_button)

    await callback_query.message.reply(md.escape_md("Выберите валюту для приведения всех долгов:"), reply_markup=keyboard)


@dp.callback_query_handler(text_contains="convert_to_", state="*")
async def convert_currency(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    selected_currency = callback_query.data.split("_")[2]

    data = await state.get_data()
    debts_to_convert = data.get("debts_to_convert", [])

    if not debts_to_convert:
        await callback_query.message.reply(md.escape_md("Долгов для приведения нет."))
        return

    consolidated_debts = {}

    for debt in debts_to_convert:
        debtor_id, creditor_id = debt[1], debt[2]
        amount, currency, date = debt[3], debt[4], debt[5]

        key = tuple(sorted([debtor_id, creditor_id]))

        if currency in CURRENCY_EXCHANGE_OPTIONS and currency != selected_currency:
            try:
                amount = await get_exchange_rate(currency, selected_currency, amount, date)
                currency = selected_currency
            except Exception as e:
                await callback_query.message.reply(md.escape_md(f"Ошибка конвертации валют: {str(e)}"))
                continue

        if key not in consolidated_debts:
            consolidated_debts[key] = [0, selected_currency]

        if debtor_id < creditor_id:
            consolidated_debts[key][0] += amount
        else:
            consolidated_debts[key][0] -= amount

    response = md.escape_md(f"Долги, приведенные к валюте {selected_currency}:\n")
    for (debtor_id, creditor_id), (amount, currency) in consolidated_debts.items():
        username1 = db.get_username_by_user_id(debtor_id)
        username2 = db.get_username_by_user_id(creditor_id)
        if amount >= 0:
            response += md.escape_md(f"Пользователь {username1} должен пользователю {username2} {abs(amount)} {currency}\n")
        else:
            response += md.escape_md(f"Пользователь {username2} должен пользователю {username1} {abs(amount)} {currency}\n")

    await callback_query.message.reply(response)
    await state.finish()


@dp.message_handler(commands=["pay_debt"], state="*")
async def pay_debt_command(message: types.Message, state: FSMContext) -> None:
    await reset_state(message, state)
    username = None
    if message.entities:
        for entity in message.entities:
            if entity.type == "mention":
                start = entity.offset + 1  # '+1' чтобы пропустить символ '@'
                length = entity.length - 1
                username = message.text[start:start+length]
                break

    if not username:
        await message.reply(md.escape_md("Пожалуйста, укажите пользователя в сообщении, например: /pay_debt @username"))
        await state.update_data(keyboard_deleted=False)
        return
    
    creditor_id = db.get_user_id_by_username(username)
    if not creditor_id:
        await message.reply(md.escape_md("Пользователь не найден."))
        return
    
    debtor_id = message.from_user.id
    debts = db.get_debts_for_pair(message.chat.id, creditor_id, debtor_id)
    if not debts:
        await message.reply(md.escape_md("Долгов этому пользователю нет."))
        return
    
    phone_number, preferred_bank = db.get_user_contact_info(message.chat.id, creditor_id)

    response = md.escape_md(f"Все долги пользователю @{username}:\n")
    for debt in debts:
        response +=  md.escape_md(f"{debt[3]} {debt[4]}\n") # amount and currency

    response += md.escape_md(f"Телефон: {phone_number}, Банк: {preferred_bank}\n")

    await state.set_data({
        'debts': debts,
        'creditor_id': creditor_id,
        'debtor_id': debtor_id
    })

    keyboard = InlineKeyboardMarkup(row_width=2)
    convert_button = InlineKeyboardButton("Привести к одной валюте", callback_data="convert_for_payment")
    pay_button = InlineKeyboardButton("Оплатить", callback_data="initiate_payment")
    keyboard.add(convert_button, pay_button)

    await message.reply(response, reply_markup=keyboard)


async def consolidate_and_convert_debts(debts, target_currency):
    converted_debts = {}
    for debt in debts:
        debtor_id, creditor_id, amount, currency, date = debt[1], debt[2], debt[3], debt[4], debt[5]
        if currency == target_currency:
            converted_amount = amount
        else:
            converted_amount = await get_exchange_rate(currency, target_currency, amount, date)

        # Создаем ключ из ID дебитора и кредитора для агрегации
        key = (debtor_id, creditor_id)
        if key in converted_debts:
            # Суммируем суммы, если ключ уже есть
            converted_debts[key] = (converted_debts[key][0] + converted_amount, target_currency)
        else:
            # Добавляем новый ключ с суммой и валютой
            converted_debts[key] = (converted_amount, target_currency)
    return converted_debts


@dp.callback_query_handler(text_contains="convert_for_payment", state="*")
async def convert_for_payment(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    keyboard = InlineKeyboardMarkup()
    for currency in CURRENCY_EXCHANGE_OPTIONS:
        currency_button = InlineKeyboardButton(currency, callback_data=f"currency_for_payment_{currency}")
        keyboard.add(currency_button)

    await callback_query.message.reply(md.escape_md("Выберите валюту для приведения всех долгов:"), reply_markup=keyboard)


@dp.callback_query_handler(text_contains="currency_for_payment_", state="*")
async def convert_debts_for_payment(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    selected_currency = callback_query.data.split("_")[3]

    data = await state.get_data()
    debts = data.get('debts')

    converted_values = await consolidate_and_convert_debts(debts, selected_currency)
    await state.update_data({'debts': converted_values})

    keyboard = InlineKeyboardMarkup()
    pay_button = InlineKeyboardButton("Оплатить", callback_data="initiate_payment")
    keyboard.add(pay_button)

    response = md.escape_md("Долги приведены к одной валюте:\n")
    for (amount, currency) in converted_values.values():
        response += md.escape_md(f"{amount} {currency}\n")

    await callback_query.message.reply(response, reply_markup=keyboard)
    await callback_query.answer()


@dp.callback_query_handler(text_contains="initiate_payment", state="*")
async def initiate_payment_process(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    # Исправленный способ установки состояния:
    await state.set_state(DebtPaymentStates.awaiting_payment)
    await callback_query.message.reply("Введите сумму и валюту платежа в формате: 100 USD")


async def process_payment_logic(message, amount_paid, currency_paid, state):
    data = await state.get_data()
    debtor_id = data['debtor_id']
    creditor_id = data['creditor_id']

    # Реализация функции ищет все долги в валюте платежа
    specific_debts = db.get_debts_by_currency(message.chat.id, debtor_id, creditor_id, currency_paid)
    # debt_id, amount
    
    remaining_amount = amount_paid

    for debt in specific_debts:
        if remaining_amount <= 0:
            break
        if remaining_amount >= debt[1]:
            remaining_amount -= debt[1]
            db.delete_debt(debt[0])
        else:
            db.update_debt(debt[0], debt[1] - remaining_amount)
            remaining_amount = 0

    if remaining_amount > 0:
        other_debts = db.get_other_currency_debts(message.chat.id, debtor_id, creditor_id, currency_paid)
        # debt_id, amount, currency, date

        for debt in other_debts:
            if remaining_amount <= 0:
                break
            try:
                converted_amount = await get_exchange_rate(debt[2], currency_paid, debt[1], debt[3])
            except Exception as e:
                await message.reply(md.escape_md(f"Ошибка конвертации для долга {debt[0]}: {str(e)}"))
                continue

            if remaining_amount >= converted_amount:
                remaining_amount -= converted_amount
                db.delete_debt(debt[0])
            else:
                converted_remaining_debt = await get_exchange_rate(currency_paid, debt[2], remaining_amount, debt[3])
                db.update_debt(debt[0], debt[1] - converted_remaining_debt)
                remaining_amount = 0
    
    if remaining_amount > 0:
        await message.reply(md.escape_md(f"Оплата прошла успешно, но остаток {remaining_amount} {currency_paid} не исчерпан."))
    else:
        await message.reply(md.escape_md("Все долги успешно оплачены."))


@dp.message_handler(state=DebtPaymentStates.awaiting_payment)
async def handle_payment_entry(message: types.Message, state: FSMContext):
    try:
        amount_paid, currency_paid = message.text.split()
        amount_paid = float(amount_paid)
    except ValueError:
        await message.reply(md.escape_md("Неверный формат. Пожалуйста, введите сумму и валюту в формате: amount currency"))
        return

    # Логика обновления долгов, регистрация платежа и обновление остатков
    await process_payment_logic(message, amount_paid, currency_paid, state)
    await state.finish()


def main():
    db.start()
    executor.start_polling(dp)
    db.finish()


if __name__ == "__main__":
    main()