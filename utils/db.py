import sqlite3
import os
import sys


def get_exe_dir():
    return (
        os.path.dirname(sys.executable)
        if getattr(sys, "frozen", False)
        else os.path.abspath(".")
    )


data_path = os.path.join(get_exe_dir(), "data")
ipv6_address_path = os.path.join(data_path, "ipv6_address.db")


def init_ipv6_table():
    os.makedirs(data_path, exist_ok=True)

    # Kết nối database SQLite
    conn = sqlite3.connect(ipv6_address_path)
    cursor = conn.cursor()
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS ipv6_address (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ipv6 TEXT NOT NULL,
        group_name VARCHAR(200) NOT NULL,
        port VARCHAR(200) NOT NULL,
        interface_name TEXT NOT NULL
    )
    """
    )
    conn.commit()
    conn.close()
