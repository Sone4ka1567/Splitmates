HELLO = {
    "en": "Hello, ",
    "ru": "Привет, "
}
START_TEXT = {
    "en": "I'll help you and your friends keep track of the total expenses!",
    "ru": "Я помогу тебе и твои друзьям следить за общими расходами!"
}
HELP_TEXT = {
    "en": "To start using me, just add me to a chat!\n" \
        "Now I will describe each command in detail:\n\n" \
        "/start - Enter this command to start interacting with me.\n" \
        "/lang - Enter this command to change the language.\n" \
        "/register phone preferred_bank - Register in the chat and specify your phone number for transfers and your preferred bank.\n" \
        "/ping @username - The bot will send a private message to this person indicating their debt to you. For this, the person must have sent the command /start in a private chat with the bot.\n" \
        "/expense amount currency description - Add an expense. The bot will then offer to select participants from the list of registered users and you must click the \"Split equally\" button. To specify different proportions, select people one by one.\n" \
        "/debts - Show a list of all debts in the chat. By clicking on \"Convert to one currency\" the bot will convert all debts to one currency, at the rate on the date of entry.\n" \
        "/debts_to_me - Show a list of all debts owed to you personally.\n" \
        "/my_debts - Show a list of all your debts.\n" \
        "/pay_debt @username - Pay off your debt to username. The bot will first write how much you owe them and will offer to pay. Respond to the bot's message with the paid amount and currency.",

    "ru": "Для того, чтобы начать мной пользоваться - просто добавь меня в чат!\n" \
        "Сейчас я подробно опишу каждую команду:\n\n" \
        "/start - Введите эту команду чтоб начать общение со мной.\n" \
        "/lang - Введите эту команду чтоб поменять язык.\n" \
        "/register phone preffered_bank - Так вы зарегистрируетесь в чате и укажете свой номер телефона для переводов и желаемый банк.\n" \
        "/ping @username - Бот отправит этому человеку личное сообщение с указанием его долга вам. Для этого человек должен в личных сообщениях с ботом отправить команду /start\n" \
        "/expense amount currency description - Добавить трату. В ответ бот предложит выбрать участников из списка зарегистрированных и надо нажать кнопку \"Разделить поровну\".\n Чтоб указать разнве пропорции - выбирайте людей по одному.\n" \
        "/debts - Показать список всех долгов в чате. По кнопке \"Привести к одной валюте\" бот сконвертирует все долги к одной валюте, по курсу на момент даты добавления.\n" \
        "/debts_to_me - Показать список всех долгов лично вам.\n" \
        "/my_debts - Показать список всех ваших долгов.\n" \
        "/pay_debt @username - Погасить ваш долг username. Сначала бот напишет, сколько вы ему должны и предложит оплатить. Ответьте на сообщение бота оплаченной суммой и валютой."
}
REGISTER_TEXT_WRONG_FORMAT = {
    "en": "Please send the command in the format /register phone preferred_bank",
    "ru": "Пожалуйста, отправьте команду в формате /register phone preffered_bank"
}
REGISTER_TEXT = {
    "en": "You have been successfully registered.",
    "ru": "Вы успешно зарегистрированы."
}
PING_NO_DEBT = {
    "en": "You don't owe anything to {}, I don't know why you were pinged :)",
    "ru": "Ты ничего не должен {}, не знаю зачем тебя пинганули:)"
}
PING_START = {
    "en": "You owe {}:\n",
    "ru": "Ты должен {}:\n"
}
SUCCESSFULL_MESSAGE = {
    "en": "Message sent successfully!",
    "ru": "Сообщение успешно отправлено!"
}
CANNOT_SEND_MESSAGE = {
    "en": "Failed to send a message to user @{}",
    "ru": "Не удалось отправить сообщение пользователю @{}"
}
USER_NOT_FOUND = {
    "en": "User not found.",
    "ru": "Пользователь не найден."
}
PING_WRONG_FORMAT = {
    "en": "Please specify the user in the message, for example: /ping @username",
    "ru": "Пожалуйста, укажите пользователя в сообщении, например: /ping @username"
}
EXPENSE_WRONG_FORMAT = {
    "en": "Use the command in the format: /expense amount currency description",
    "ru": "Используйте команду в формате: /expense amount currency description"
}
WRONG_CURRENCY = {
    "en": "Sorry, currently only the following currencies are available: {}",
    "ru": "Извините, пока что доступны только валюты: {}"
}
EQUAL_SPLIT = {
    "en": "Split equally",
    "ru": "Разделить поровну"
}
CHOOSE_USERS_FOR_SPLIT = {
    "en": "Select users for splitting the expenses:",
    "ru": "Выберите пользователей для распределения затрат:"
}
PLEASE_CHOOSE_USERS = {
    "en": "Please select the users.",
    "ru": "Пожалуйста, выберите пользователей."
}
DEBTS_UPDATED = {
    "en": "Debts have been updated and evenly distributed.",
    "ru": "Долги обновлены и поровну разделены."
}
NO_ACTIVE_DEBTS = {
    "en": "There are no active debts in this chat.",
    "ru": "В этом чате нет активных долгов."
}
DEBTS_IN_CHAT = {
    "en": "Debts in chat:\n",
    "ru": "Долги в чате:\n"
}
USER_OWES_USER = {
    "en": "User {} owes user {}",
    "ru": "Пользователь {} должен пользователю {}"
}
CONVERT_TO_CURRENCY = {
    "en": "Convert to same currency",
    "ru": "Привести к одной валюте"
}
NOBODY_OWES = {
    "en": "Nobody owes you:(",
    "ru": "Тебе никто не должен:("
}
WHO_OWES = {
    "en": "Owe {}:\n",
    "ru": "Должны {}:\n"
}
USER_OWES_YOU = {
    "en": "User {} owes",
    "ru": "Пользователь {} должен"
}
YOU_OWE_NOONE = {
    "en": "You do not owe anyone:)",
    "ru": "Ты никому не должен:)"
}
YOU_OWE = {
    "en": "{} owe:\n",
    "ru": "{} должен:\n"
}
YOU_OWE_USER = {
    "en": "To user {creditor} you owe",
    "ru": "Пользователю {} ты должен"
}
CURRENCY_TO_CAST = {
    "en": "Select a currency to convert all debts:",
    "ru": "Выберите валюту для приведения всех долгов:"
}
NO_DEBTS_SELECTED = {
    "en": "No debts to convert.",
    "ru": "Долгов для приведения нет."
}
CURRENCY_CONVERTION_ERROR = {
    "en": "Currency convertion error.",
    "ru": "Ошибка конвертации валют."
}
DEBTS_CONVERTED_TO = {
    "en": "Debts converted to currency {}:\n",
    "ru": "Долги, приведенные к валюте {}:\n"
}
PAY_DEBT_WRONG_FORMAT = {
    "en": "Please specify the user in the message, for example: /pay_debt @username",
    "ru": "Пожалуйста, укажите пользователя в сообщении, например: /pay_debt @username"
}
NO_DEBTS_TO_USER = {
    "en": "There are no debts to this user.",
    "ru": "Долгов этому пользователю нет."
}
ALL_DEBTS_TO_USER = {
    "en": "All debts to user @{}:\n",
    "ru": "Все долги пользователю @{}:\n"
}
PHONE_BANK = {
    "en": "Phone: {}, Bank: {}\n",
    "ru": "Телефон: {}, Банк: {}\n"
}
PAY = {
    "en": "Pay",
    "ru": "Оплатить"
}
PAYMENT_FORMAT = {
    "en": "Enter the payment amount and currency in the format: amount currency",
    "ru": "Введите сумму и валюту платежа в формате: amount currency"
}
CONVERSION_ERROR = {
    "en": "Debt conversion error.",
    "ru": "Ошибка конвертации долга."
}
ALL_DEBTS_PAID =  {
    "en": "All debts successfully paid.",
    "ru": "Все долги успешно оплачены."
}
NOT_ALL_PAID = {
    "en": "Payment was successful, but the remaining balance of {} {} has not been exhausted.",
    "ru": "Оплата прошла успешно, но остаток {} {} не исчерпан."
}
LANGUAGE_CHOOSE = {
    "en": "Please select your language:",
    "ru": "Пожалуйста, выберите язык:"
}
LANGUAGE_SET_TO = {
    "en": "Language has been set to {}.",
    "ru": "Язык поменяли на {}."
}
LANGUAGE_UPDATED = {
    "en": "Language updated!",
    "ru": "Язык обновлен!"
}