import pprint
import sqlite3

db = sqlite3.connect("server.db")
cursor = db.cursor()


def write_user(user_id):
    cursor.execute(f"SELECT * FROM users WHERE chat_id = {user_id}")
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO users VALUES (?, ?, ?)",
                       (user_id, False, "-"))
        print("Записан")
        db.commit()
    else:
        pass


def set_sub(user_id, city):
    cursor.execute(f"SELECT allowed FROM users WHERE chat_id = {user_id}")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            f"UPDATE users SET allowed = True WHERE chat_id = {user_id}")
        cursor.execute(
            f"UPDATE users SET city = (?) WHERE chat_id = (?)", (city, user_id))
        db.commit()
    else:
        pass


def decline_sub(user_id):
    cursor.execute(f"SELECT allowed FROM users WHERE chat_id = {user_id}")
    if cursor.fetchone()[0] == 1:
        cursor.execute(
            f"UPDATE users SET allowed = False, city = '-' WHERE chat_id = {user_id}")
        db.commit()
    else:
        pass
