import os

from aiogram import Bot, types
from aiogram.contrib.fsm_storage.files import JSONStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor, markdown as md
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from tech import Database, texts, get_exchange_rate, CURRENCY_EXCHANGE_OPTIONS


LANG_OPTIONS = {
    'ru': 'Русский',
    'en': 'English'
}

BOT_API_TOKEN = os.environ.get('BOT_API_TOKEN')

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
    db.register_chat(message.chat.id)

    lang = db.get_chat_lang(message.chat.id)

    await reset_state(message, state)

    hello_phrase = texts.HELLO[lang] + message.from_user.first_name + "\\!"
    await message.answer(
        md.text(
            hello_phrase,
            md.escape_md(texts.START_TEXT[lang]),
            sep="\n"
        ),
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.update_data(keyboard_deleted=False)


@dp.message_handler(commands=["help"], state="*")
async def help_command(message: types.Message, state: FSMContext) -> None:
    await reset_state(message, state)
    lang = db.get_chat_lang(message.chat.id)
    await message.answer(
        md.escape_md(texts.HELP_TEXT[lang]),
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.update_data(keyboard_deleted=False)


@dp.message_handler(commands=["register"], state="*")
async def register_command(message: types.Message, state: FSMContext) -> None:
    await reset_state(message, state)

    lang = db.get_chat_lang(message.chat.id)

    args = message.get_args().split()
    if len(args) < 2:
        await state.update_data(keyboard_deleted=False)
        await message.reply(md.escape_md(texts.REGISTER_TEXT_WRONG_FORMAT[lang]))
        return

    db.register_user(message, args[0], args[1])

    await message.reply(
        md.text(
            md.escape_md(texts.REGISTER_TEXT[lang]),
            sep="\n"
        ),
        reply_markup=types.ReplyKeyboardRemove()
    )

    await state.update_data(keyboard_deleted=False)


@dp.message_handler(commands=["lang"], state="*")
async def lang_command(message: types.Message, state: FSMContext) -> None:
    await reset_state(message, state)
    lang = db.get_chat_lang(message.chat.id)
    markup = InlineKeyboardMarkup(row_width=2)
    for value, human_name in LANG_OPTIONS.items():
        lang_button = InlineKeyboardButton(human_name, callback_data=f'set_lang:{value}')
        markup.add(lang_button)

    await message.reply(md.escape_md(texts.LANGUAGE_CHOOSE[lang]), reply_markup=markup)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('set_lang:'))
async def set_language(callback_query: types.CallbackQuery):
    lang = callback_query.data.split(':')[1]

    db.update_chat_lang(callback_query.message.chat.id, lang)
    lang = db.get_chat_lang(callback_query.message.chat.id)

    await callback_query.message.edit_text(md.escape_md(texts.LANGUAGE_SET_TO[lang].format(LANG_OPTIONS[lang])))
    await callback_query.answer(md.escape_md(texts.LANGUAGE_UPDATED[lang]))


@dp.message_handler(commands=["ping"], state="*")
async def ping_command(message: types.Message, state: FSMContext) -> None:
    await reset_state(message, state)

    lang = db.get_chat_lang(message.chat.id)

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

                if len(debts) == 0:
                    text = md.escape_md(texts.PING_NO_DEBT[lang].format(message.from_user.full_name))
                else:
                    text = md.escape_md(texts.PING_START[lang].format(message.from_user.full_name))

                for debt in debts:
                    text += md.escape_md(f"{debt[3]} {debt[4]}\n")

                await bot.send_message(user_id, text)
                await message.reply(md.escape_md(texts.SUCCESSFULL_MESSAGE[lang]))
            except Exception:
                await message.reply(md.escape_md(texts.CANNOT_SEND_MESSAGE[lang].format(username)))
        else:
            await message.reply(md.escape_md(texts.USER_NOT_FOUND[lang]))
    else:
        await message.reply(md.escape_md(texts.PING_WRONG_FORMAT[lang]))

    await state.update_data(keyboard_deleted=False)


@dp.message_handler(commands=["expense"], state="*")
async def expense_command(message: types.Message, state: FSMContext) -> None:
    await reset_state(message, state)
    lang = db.get_chat_lang(message.chat.id)

    args = message.get_args().split(maxsplit=2)
    if len(args) < 3:
        await message.reply(md.escape_md(texts.EXPENSE_WRONG_FORMAT[lang]))
        return

    amount, currency, description = args

    if currency not in CURRENCY_EXCHANGE_OPTIONS:
        await message.reply(md.escape_md(texts.WRONG_CURRENCY[lang].format(', '.join(CURRENCY_EXCHANGE_OPTIONS))))
        return

    await state.update_data(amount=float(amount), lang=lang, currency=currency, description=description, chat_id=message.chat.id, selected_users=[])

    users = db.get_users_in_chat(message.chat.id)
    keyboard = InlineKeyboardMarkup(row_width=2)
    for user in users:
        button = InlineKeyboardButton(user[1], callback_data=f"user_{user[0]}")
        keyboard.add(button)

    equal_button = InlineKeyboardButton(texts.EQUAL_SPLIT[lang], callback_data="equal")
    keyboard.add(equal_button)

    await ExpenseState.choosing_users.set()
    await message.reply(md.escape_md(texts.CHOOSE_USERS_FOR_SPLIT[lang]), reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data.startswith("user_"), state=ExpenseState.choosing_users)
async def add_user_to_list(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = int(callback_query.data.split("_")[1])
    data = await state.get_data()
    selected_users = data.get("selected_users", [])

    lang = data.get("lang", "ru")

    users = db.get_users_in_chat(data['chat_id'])
    keyboard = InlineKeyboardMarkup(row_width=2)

    if user_id not in selected_users:
        selected_users.append(user_id)
    else:
        selected_users.remove(user_id)

    await state.update_data(selected_users=selected_users)

    for user in users:
        status = "✓ " if user[0] in selected_users else ""
        username_button = f"{status}{user[1]}"
        button = InlineKeyboardButton(username_button, callback_data=f"user_{user[0]}")
        keyboard.add(button)

    equal_button = InlineKeyboardButton(texts.EQUAL_SPLIT[lang], callback_data="equal")
    keyboard.add(equal_button)

    await callback_query.message.edit_reply_markup(keyboard)
    await callback_query.answer()


@dp.callback_query_handler(text_contains="equal", state=ExpenseState.choosing_users)
async def process_equal_division(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    data = await state.get_data()
    users = data.get("selected_users", [])
    lang = data.get("lang", "ru")

    if not users:
        await callback_query.message.reply(md.escape_md(texts.PLEASE_CHOOSE_USERS[lang]))
        return

    amount_per_user = data['amount'] / len(users)
    for user_id in users:
        await db.update_or_add_debt(
            creditor_id=callback_query.from_user.id, debtor_id=user_id, amount=amount_per_user,
            currency=data['currency'], description=data['description'], chat_id=data['chat_id']
        )

    await callback_query.message.reply(md.escape_md(texts.DEBTS_UPDATED[lang]))
    await state.finish()


@dp.message_handler(commands=["debts"], state="*")
async def debts_command(message: types.Message, state: FSMContext):
    await reset_state(message, state)
    lang = db.get_chat_lang(message.chat.id)

    debts = db.get_debts_from_chat(message.chat.id)
    # (debt_id, debtor_id, creditor_id, amount, currency) с сортированными ID

    if not debts:
        await message.reply(md.escape_md(texts.NO_ACTIVE_DEBTS[lang]))
        return
    
    await state.update_data(debts_to_convert=debts)

    response = md.escape_md(texts.DEBTS_IN_CHAT[lang])
    for debt in debts:
        username_1, username_2 = db.get_username_by_user_id(debt[1]), db.get_username_by_user_id(debt[2]), 
        response += md.escape_md(texts.USER_OWES_USER[lang].format(username_1, username_2) + f" {debt[3]} {debt[4]}\n")

    keyboard = InlineKeyboardMarkup()

    convert_button = InlineKeyboardButton(texts.CONVERT_TO_CURRENCY[lang], callback_data="choose_currency")
    keyboard.add(convert_button)

    await message.reply(response, reply_markup=keyboard)


@dp.message_handler(commands=["debts_to_me"], state="*")
async def debts_to_me_command(message: types.Message, state: FSMContext) -> None:
    await reset_state(message, state)
    lang = db.get_chat_lang(message.chat.id)

    debts = db.get_debts_by_creditor_id(message.chat.id, message.from_user.id)
    # (debt_id, debtor_id, creditor_id, amount, currency) с сортированными ID

    if not debts:
        await message.reply(md.escape_md(texts.NOBODY_OWES[lang]))
        return
    
    await state.update_data(debts_to_convert=debts)

    creditor_name = db.get_username_by_user_id(message.from_user.id)

    response =  md.escape_md(texts.WHO_OWES[lang].format(creditor_name))
    for debt in debts:
        debtor = db.get_username_by_user_id(debt[1])
        response += md.escape_md(texts.USER_OWES_YOU[lang].format(debtor) + f" {debt[3]} {debt[4]}\n")

    keyboard = InlineKeyboardMarkup()
    convert_button = InlineKeyboardButton(texts.CONVERT_TO_CURRENCY[lang], callback_data="choose_currency")
    keyboard.add(convert_button)

    await message.reply(response, reply_markup=keyboard)


@dp.message_handler(commands=["my_debts"], state="*")
async def my_debts_command(message: types.Message, state: FSMContext) -> None:
    await reset_state(message, state)
    lang = db.get_chat_lang(message.chat.id)

    debts = db.get_debts_by_debtor_id(message.chat.id, message.from_user.id)
    # (debt_id, debtor_id, creditor_id, amount, currency, date) с сортированными ID
    if not debts:
        await message.reply(md.escape_md(texts.YOU_OWE_NOONE[lang]))
        return

    await state.update_data(debts_to_convert=debts)

    debtor_name = db.get_username_by_user_id(message.from_user.id)

    response = md.escape_md(texts.YOU_OWE[lang].format(debtor_name))
    for debt in debts:
        creditor = db.get_username_by_user_id(debt[2])
        response += md.escape_md(texts.YOU_OWE_USER[lang].format(creditor) + f" {debt[3]} {debt[4]}\n")

    keyboard = InlineKeyboardMarkup()

    convert_button = InlineKeyboardButton(texts.CONVERT_TO_CURRENCY[lang], callback_data="choose_currency")
    keyboard.add(convert_button)

    await message.reply(response, reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data == "choose_currency", state="*")
async def choose_currency(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    data = await state.get_data()
    lang = data.get("lang", "ru")
    keyboard = InlineKeyboardMarkup()
    for currency in CURRENCY_EXCHANGE_OPTIONS:
        currency_button = InlineKeyboardButton(currency, callback_data=f"convert_to_{currency}")
        keyboard.add(currency_button)

    await callback_query.message.reply(md.escape_md(texts.CURRENCY_TO_CAST[lang]), reply_markup=keyboard)


@dp.callback_query_handler(text_contains="convert_to_", state="*")
async def convert_currency(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    selected_currency = callback_query.data.split("_")[2]

    data = await state.get_data()
    debts_to_convert = data.get("debts_to_convert", [])
    lang = data.get("lang", "ru")

    if not debts_to_convert:
        await callback_query.message.reply(md.escape_md(texts.NO_DEBTS_SELECTED[lang]))
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
                await callback_query.message.reply(md.escape_md(texts.CURRENCY_CONVERTION_ERROR[lang]))
                continue

        if key not in consolidated_debts:
            consolidated_debts[key] = [0, selected_currency]

        if debtor_id < creditor_id:
            consolidated_debts[key][0] += amount
        else:
            consolidated_debts[key][0] -= amount

    response = md.escape_md(texts.DEBTS_CONVERTED_TO[lang].format(selected_currency))
    for (debtor_id, creditor_id), (amount, currency) in consolidated_debts.items():
        username1 = db.get_username_by_user_id(debtor_id)
        username2 = db.get_username_by_user_id(creditor_id)
        if amount >= 0:
            response += md.escape_md(texts.USER_OWES_USER[lang].format(username1, username2) + f" {abs(amount)} {currency}\n")
        else:
            response += md.escape_md(texts.USER_OWES_USER[lang].format(username2, username1) + f" {abs(amount)} {currency}\n")

    await callback_query.message.reply(response)
    await state.finish()


@dp.message_handler(commands=["pay_debt"], state="*")
async def pay_debt_command(message: types.Message, state: FSMContext) -> None:
    await reset_state(message, state)
    lang = db.get_chat_lang(message.chat.id)

    username = None
    if message.entities:
        for entity in message.entities:
            if entity.type == "mention":
                start = entity.offset + 1  # '+1' чтобы пропустить символ '@'
                length = entity.length - 1
                username = message.text[start:start+length]
                break

    if not username:
        await message.reply(md.escape_md(texts.PAY_DEBT_WRONG_FORMAT[lang]))
        await state.update_data(keyboard_deleted=False)
        return
    
    creditor_id = db.get_user_id_by_username(username)
    if not creditor_id:
        await message.reply(md.escape_md(texts.USER_NOT_FOUND[lang]))
        return
    
    debtor_id = message.from_user.id
    debts = db.get_debts_for_pair(message.chat.id, creditor_id, debtor_id)
    if not debts:
        await message.reply(md.escape_md(texts.NO_DEBTS_TO_USER[lang]))
        return
    
    phone_number, preferred_bank = db.get_user_contact_info(message.chat.id, creditor_id)

    response = md.escape_md(texts.ALL_DEBTS_TO_USER[lang].format(username))
    for debt in debts:
        response +=  md.escape_md(f"{debt[3]} {debt[4]}\n") # amount and currency

    response += md.escape_md(texts.PHONE_BANK[lang].format(phone_number, preferred_bank))

    await state.set_data({
        'debts': debts,
        'creditor_id': creditor_id,
        'debtor_id': debtor_id,
        'lang': lang
    })

    keyboard = InlineKeyboardMarkup(row_width=2)
    convert_button = InlineKeyboardButton(texts.CONVERT_TO_CURRENCY[lang], callback_data="convert_for_payment")
    pay_button = InlineKeyboardButton(texts.PAY[lang], callback_data="initiate_payment")
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
    data = await state.get_data()
    lang = data.get("lang", "ru")
    keyboard = InlineKeyboardMarkup()
    for currency in CURRENCY_EXCHANGE_OPTIONS:
        currency_button = InlineKeyboardButton(currency, callback_data=f"currency_for_payment_{currency}")
        keyboard.add(currency_button)

    await callback_query.message.reply(md.escape_md(texts.CURRENCY_TO_CAST[lang]), reply_markup=keyboard)


@dp.callback_query_handler(text_contains="currency_for_payment_", state="*")
async def convert_debts_for_payment(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    selected_currency = callback_query.data.split("_")[3]

    data = await state.get_data()
    debts = data.get('debts')
    lang = data.get("lang", "ru")

    converted_values = await consolidate_and_convert_debts(debts, selected_currency)
    await state.update_data({'debts': converted_values})

    keyboard = InlineKeyboardMarkup()
    pay_button = InlineKeyboardButton(texts.PAY[lang], callback_data="initiate_payment")
    keyboard.add(pay_button)

    response = md.escape_md(texts.DEBTS_CONVERTED_TO[lang].format(selected_currency))
    for (amount, currency) in converted_values.values():
        response += md.escape_md(f"{amount} {currency}\n")

    await callback_query.message.reply(response, reply_markup=keyboard)
    await callback_query.answer()


@dp.callback_query_handler(text_contains="initiate_payment", state="*")
async def initiate_payment_process(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()

    data = await state.get_data()
    lang = data.get("lang", "ru")

    await state.set_state(DebtPaymentStates.awaiting_payment)
    await callback_query.message.reply(texts.PAYMENT_FORMAT[lang])


async def process_payment_logic(message, amount_paid, currency_paid, state):
    data = await state.get_data()
    debtor_id = data['debtor_id']
    creditor_id = data['creditor_id']
    lang = data.get("lang", "ru")

    # Реализация функции ищет все долги в валюте платежа
    specific_debts = db.get_debts_by_currency(message.chat.id, debtor_id, creditor_id, currency_paid)
    # debt_id, amount
    
    remaining_amount = amount_paid

    for debt in specific_debts:
        if remaining_amount <= db.epsilon:
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
            if remaining_amount <= db.epsilon:
                break
            try:
                converted_amount = await get_exchange_rate(debt[2], currency_paid, debt[1], debt[3])
            except Exception:
                await message.reply(md.escape_md(texts.CONVERSION_ERROR[lang]))
                continue

            if remaining_amount >= converted_amount:
                remaining_amount -= converted_amount
                db.delete_debt(debt[0])
            else:
                converted_remaining_debt = await get_exchange_rate(currency_paid, debt[2], remaining_amount, debt[3])
                db.update_debt(debt[0], debt[1] - converted_remaining_debt)
                remaining_amount = 0
    
    if remaining_amount > db.epsilon:
        await message.reply(md.escape_md(texts.NOT_ALL_PAID[lang].format(remaining_amount, currency_paid)))
    else:
        await message.reply(md.escape_md(texts.ALL_DEBTS_PAID[lang]))


@dp.message_handler(state=DebtPaymentStates.awaiting_payment)
async def handle_payment_entry(message: types.Message, state: FSMContext):
    lang = db.get_chat_lang(message.chat.id)
    try:
        amount_paid, currency_paid = message.text.split()
        amount_paid = float(amount_paid)
    except ValueError:
        await message.reply(md.escape_md(texts.PAYMENT_FORMAT[lang]))
        return

    await process_payment_logic(message, amount_paid, currency_paid, state)
    await state.finish()


def main():
    db.start()
    executor.start_polling(dp)
    db.finish()


if __name__ == "__main__":
    main()
