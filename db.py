import sqlite3


class Database:
    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    user_id INTEGER UNIQUE,
    nickname TEXT,
    text_requests INTEGER DEFAULT 0,
    image_requests INTEGER DEFAULT 0,
    time_sub TIMESTAMP,
    subscription_type TEXT DEFAULT 'standard'
)""")
        self.connection.commit()

    def add_user(self, user_id, nickname):
        with self.connection:
            print(f"Добавление пользователя с ID {user_id} в базу данных.")
            result = self.cursor.execute("INSERT INTO 'users'('user_id', 'nickname') VALUES (?, ?)",
                                         (user_id, nickname))
            self.connection.commit()
            print(f"Результат добавления пользователя с ID {user_id}: {result}")

    def user_exists(self, user_id):
        with self.connection:
            print(f"Проверка существования пользователя с ID {user_id} в базе данных.")
            result = self.cursor.execute('SELECT * FROM "users" WHERE "user_id" = ?', (user_id,)).fetchall()
            print(f"Результат проверки существования пользователя с ID {user_id}: {result}")
            return bool(len(result))

    def set_nickname(self, user_id, nickname):
        with self.connection:
            return self.cursor.execute("UPDATE 'users' SET 'nickname' = ? WHERE 'user_id' = ?", (nickname, user_id))

    def get_signup(self, user_id):
        with self.connection:
            result = self.cursor.execute("SELECT 'signup' FROM 'users' WHERE 'user_id' = ?", (user_id,)).fetchall()
            for row in result:
                signup = str(row[0])
            return signup

    def set_signup(self, user_id, signup):
        with self.connection:
            return self.cursor.execute("UPDATE 'users' SET 'signup' = ? WHERE 'user_id' = ?", (signup, user_id))

    def get_time_sub(self, user_id):
        with self.connection:
            result = self.cursor.execute("SELECT 'time_sub' FROM 'users' WHERE 'user_id' = ?", (user_id,)).fetchall()
            for row in result:
                time_sub = str(row[0])
            return time_sub

    def get_user(self, user_id):
        self.cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        user_data = self.cursor.fetchone()
        if user_data:
            user_dict = {
                "id": user_data[0],
                "user_id": user_data[1],
                "nickname": user_data[2],
                "registration_date": user_data[3],
                "last_command": user_data[4],
                "text_requests": user_data[5],
                "image_requests": user_data[6],
                "subscription_type": user_data[7],
            }
            return user_dict
        else:
            return None

    def set_subscription(self, user_id):
        with self.connection:
            try:
                self.cursor.execute(
                    "UPDATE users SET subscription_type = 'premium', time_sub = CURRENT_TIMESTAMP WHERE user_id = ?",
                    (user_id,))
                self.connection.commit()
                return True
            except Exception as e:
                print(f"Ошибка при обновлении подписки: {e}")
                return False

    def update_requests(self, user_id, text_requests, image_requests):
        with self.connection:
            cursor = self.connection.cursor()
            cursor.execute("UPDATE users SET text_requests = ?, image_requests = ? WHERE user_id = ?",
                           (text_requests, image_requests, user_id))

    def update_subscription_type(self, user_id, subscription_type):
        with self.connection:
            cursor = self.connection.cursor()
            cursor.execute("UPDATE users SET subscription_type = ? WHERE user_id = ?", (subscription_type, user_id))

    def set_time_sub(self, user_id, time_sub):
        with self.connection:
            cursor = self.connection.cursor()
            cursor.execute("UPDATE users SET time_sub = ? WHERE user_id = ?", (time_sub, user_id))

    def update_requests_limit(self, user_id, text_requests_limit, image_requests_limit):
        with self.connection:
            cursor = self.connection.cursor()
            cursor.execute("UPDATE users SET text_requests_limit = ?, image_requests_limit = ? WHERE user_id = ?",
                           (text_requests_limit, image_requests_limit, user_id))

    def update_subscription_time_sub(self, user_id, time_sub):
        with self.connection:
            cursor = self.connection.cursor()
            cursor.execute("UPDATE users SET time_sub = ? WHERE user_id = ?", (time_sub, user_id))

