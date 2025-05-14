import sqlite3 as sq

db = sq.connect("app/database.db")
cur = db.cursor()
MAX_DAILY_READINGS = 3

async def db_start():
    cur.execute("CREATE TABLE IF NOT EXISTS accounts("
                "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                "tg_id INTEGER, "
                "tg_username TEXT,"
                "request_count INTEGER DEFAULT 0)")
    db.commit()


async def get_user_id(user_id, username):
    cur.execute("SELECT * FROM accounts WHERE tg_id = ?", (user_id,))
    if cur.fetchone() is None:
        cur.execute("INSERT INTO accounts (tg_id, tg_username) VALUES (?, ?)", (user_id, username))
        db.commit()


async def get_update_count(user_id):
    result = cur.execute("SELECT request_count FROM accounts WHERE tg_id = ?", (user_id,)).fetchone()

    if result is None:
        return False

    request_count = result[0]

    if request_count >= MAX_DAILY_READINGS:
        return False
    else:
        cur.execute("UPDATE accounts SET request_count = request_count + 1 WHERE tg_id = ?", (user_id,))
        db.commit()
        return True


