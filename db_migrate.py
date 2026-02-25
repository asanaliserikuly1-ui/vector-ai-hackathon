import sqlite3
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "vector_ai.db")

def cols(cur, table):
    cur.execute(f"PRAGMA table_info({table});")
    return {row[1] for row in cur.fetchall()}

def add_col(cur, table, name, sql_type, default_sql="''"):
    if name in cols(cur, table):
        print(f"OK: {table}.{name} exists")
        return
    cur.execute(f"ALTER TABLE {table} ADD COLUMN {name} {sql_type} DEFAULT {default_sql};")
    print(f"ADDED: {table}.{name}")

def main():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    # market_fit_snapshot new columns (если их ещё нет)
    add_col(cur, "market_fit_snapshot", "missing_json", "TEXT", "'[]'")
    add_col(cur, "market_fit_snapshot", "have_json", "TEXT", "'[]'")
    add_col(cur, "market_fit_snapshot", "top_market_json", "TEXT", "'[]'")
    add_col(cur, "market_fit_snapshot", "note", "VARCHAR(120)", "''")

    # если осталась старая колонка market_missing_json — можно оставить (не мешает),
    # или позже сделаем перенос данных.

    con.commit()
    con.close()
    print("DONE")

if __name__ == "__main__":
    main()