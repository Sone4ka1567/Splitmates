import datetime
import sqlite3


class Database():
    def __init__(self):
        self.connection = sqlite3.connect("database.db")
        self.cursor = self.connection.cursor()

    def start(self):
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS chats (chat_id INTEGER PRIMARY KEY, language VARCHAR(256) DEFAULT 'ru');"
        )
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS users (user_id INT, chat_id INT, username VARCHAR(256), phone_number VARCHAR(256) NOT NULL, preferred_bank VARCHAR(256)," +
            "primary key (user_id, chat_id));"
        )
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS debts (" +
            "debt_id INTEGER PRIMARY KEY," +
            "creditor_id INTEGER NOT NULL," +
            "debtor_id INTEGER NOT NULL," +
            "amount REAL NOT NULL," +
            "currency INTEGER NOT NULL," +
            "description TEXT," +
            "date DATE NOT NULL," +
            "chat_id INTEGER NOT NULL," +
            "FOREIGN KEY (creditor_id) REFERENCES users (user_id)," +
            "FOREIGN KEY (debtor_id) REFERENCES users (user_id)," +
            "FOREIGN KEY (chat_id) REFERENCES chats (chat_id));"
        )
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS transactions (" +
            "transaction_id INTEGER PRIMARY KEY," +
            "creditor_id INTEGER NOT NULL," +
            "debtor_id INTEGER NOT NULL," +
            "amount_paid REAL NOT NULL," +
            "currency INTEGER NOT NULL," +
            "date DATE NOT NULL," +
            "chat_id INTEGER NOT NULL," +
            "FOREIGN KEY (creditor_id) REFERENCES users (user_id)," +
            "FOREIGN KEY (debtor_id) REFERENCES users (user_id)," +
            "FOREIGN KEY (chat_id) REFERENCES chats (chat_id));"
        )

    def register_chat(self, message):
        self.connection.execute(
            "INSERT OR IGNORE INTO chats (chat_id) VALUES (?)",
            (message.chat.id,)
        )
        self.connection.commit()

    def register_user(self, message, phone, bank):
        self.connection.execute(
            "INSERT INTO users (user_id, chat_id, username, phone_number, preferred_bank) VALUES (?, ?, ?, ?, ?)",
            (message.from_user.id, message.chat.id, message.from_user.username, phone, bank)
        )
        self.connection.commit()

    def get_users_in_chat(self, chat_id):
        self.cursor.execute("SELECT user_id, username FROM users WHERE chat_id = ?", (chat_id,))
        return self.cursor.fetchall()

    def update_or_add_debt(self, creditor_id, debtor_id, amount, currency, description, chat_id):
        if creditor_id == debtor_id:
            return

        self.cursor.execute("""
            SELECT amount, debt_id, creditor_id FROM debts 
            WHERE ((creditor_id = ? AND debtor_id = ?) OR (creditor_id = ? AND debtor_id = ?))
            AND currency = ? AND chat_id = ?
            """, (creditor_id, debtor_id, debtor_id, creditor_id, currency, chat_id))
        result = self.cursor.fetchone()

        if result:
            current_amount, debt_id, current_creditor_id = result
            if creditor_id == current_creditor_id:
                new_amount = current_amount + amount
            else:
                new_amount = current_amount - amount
            
            if new_amount > 0:
                self.cursor.execute("UPDATE debts SET amount = ? WHERE debt_id = ?", (new_amount, debt_id))
            elif new_amount < 0:
                # Если новая сумма отрицательная, то меняем роли и делаем сумму положительной
                new_amount = -new_amount
                self.cursor.execute("UPDATE debts SET amount = ?, creditor_id = ?, debtor_id = ? WHERE debt_id = ?", (new_amount, debtor_id, creditor_id, debt_id))
            else:
                # Удаляем запись если долг точно погашен
                self.cursor.execute("DELETE FROM debts WHERE debt_id = ?", (debt_id,))
        else:
            # Добавление новой записи в случае если подходящая пара не найдена
            self.cursor.execute("INSERT INTO debts (creditor_id, debtor_id, amount, currency, description, date, chat_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (creditor_id, debtor_id, amount, currency, description, datetime.datetime.now(tz=datetime.timezone.utc), chat_id))
        self.connection.commit()

    def get_user_contact_info(self, chat_id, user_id):
        self.cursor.execute("SELECT phone_number, preferred_bank FROM users WHERE chat_id = ? and user_id = ?", (chat_id, user_id,))
        result = self.cursor.fetchone()
        return result[0], result[1] if result else None

    def get_user_id_by_username(self, username):
        self.cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    def get_username_by_user_id(self, user_id):
        self.cursor.execute("SELECT username FROM users WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    def get_debts_from_chat(self, chat_id):
        self.cursor.execute(
            "SELECT debt_id, debtor_id, creditor_id, amount, currency, date FROM debts WHERE chat_id = ?",
            (chat_id,)
        )
        return self.cursor.fetchall()
    
    def get_debts_for_pair(self, chat_id, creditor_id, debtor_id):
        self.cursor.execute(
            "SELECT debt_id, debtor_id, creditor_id, amount, currency, date FROM debts WHERE chat_id = ? and creditor_id = ? and debtor_id = ? ",
            (chat_id, creditor_id, debtor_id)
        )
        return self.cursor.fetchall()

    def get_debts_by_debtor_id(self, chat_id, debtor_id):
        self.cursor.execute(
            "SELECT debt_id, debtor_id, creditor_id, amount, currency, date FROM debts WHERE chat_id = ? and debtor_id = ?",
            (chat_id, debtor_id)
        )
        return self.cursor.fetchall()
    
    def get_debts_by_creditor_id(self, chat_id, creditor_id):
        self.cursor.execute(
            "SELECT debt_id, debtor_id, creditor_id, amount, currency, date FROM debts WHERE chat_id = ? and creditor_id = ?",
            (chat_id, creditor_id)
        )
        return self.cursor.fetchall()
    
    def register_transaction(self, debtor_id, creditor_id, amount_paid, currency_paid, chat_id):
        self.cursor.execute("INSERT INTO transactions (creditor_id, debtor_id, amount_paid, currency, date, chat_id) VALUES (?, ?, ?, ?, ?, ?)",
                (creditor_id, debtor_id, amount_paid, currency_paid, datetime.datetime.now(tz=datetime.timezone.utc), chat_id))
        self.connection.commit()

    def delete_debt(self, debt_id):
        self.cursor.execute("DELETE FROM debts WHERE debt_id = ?", (debt_id,))
        self.connection.commit()

    def update_debt(self, debt_id, new_debt_amount):
        self.cursor.execute("UPDATE debts SET amount = ? WHERE debt_id = ?", (new_debt_amount, debt_id))
        self.connection.commit()

    def get_debts_by_currency(self, chat_id, debtor_id, creditor_id, currency):
        self.cursor.execute(
            "SELECT debt_id, amount FROM debts WHERE chat_id = ? and creditor_id = ? and debtor_id = ? and currency = ?",
            (chat_id, creditor_id, debtor_id, currency)
        )
        return self.cursor.fetchall()
    
    def get_other_currency_debts(self, chat_id, debtor_id, creditor_id, currency):
        self.cursor.execute(
            "SELECT debt_id, amount, currency, date FROM debts WHERE chat_id = ? and creditor_id = ? and debtor_id = ? and currency != ?",
            (chat_id, creditor_id, debtor_id, currency)
        )
        return self.cursor.fetchall()

    def finish(self):
        self.cursor.close()
        self.connection.close()