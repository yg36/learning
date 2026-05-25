import sqlite3

DB_NAME = "database.db"


def connect_db():
    conn = sqlite3.connect(DB_NAME)
    return conn


def create_table():
    conn = connect_db()

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            role TEXT,
            message TEXT
        )
        """
        )

    conn.commit()
    conn.close()



def save_message(user_id, role, message):
    conn = connect_db()

    conn.execute(
        "INSERT INTO chats (user_id, role, message) VALUES (?, ?, ?)",
        (user_id, role, message)
    )

    conn.commit()
    conn.close()



def get_chat_history(user_id, limit=10):
    conn = connect_db()

    cursor = conn.execute(
        """
        SELECT role, message
        FROM chats
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (user_id, limit)
    )

    rows = cursor.fetchall()

    conn.close()

    rows.reverse()

    return rows