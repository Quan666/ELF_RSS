import os
import sqlite3

from pathlib import Path

os.chdir("./data")

db_paths = list(Path("./").glob("*.db"))
conn = sqlite3.connect("cache.db")
cursor = conn.cursor()
cursor.execute(
    """
        CREATE TABLE IF NOT EXISTS main (
            "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            "link" TEXT,
            "title" TEXT,
            "image_hash" TEXT,
            "datetime" TEXT DEFAULT (DATETIME('Now', 'LocalTime'))
        );
        """
)
cursor.close()
conn.commit()
conn.close()


def delete_db_file(file_path):
    if Path(file_path):
        os.remove(file_path)


for i in [str(i) for i in db_paths]:
    conn = sqlite3.connect("cache.db")
    db_name = i.replace(".db", "")
    table_name = db_name + ".main"
    conn.execute(f"ATTACH DATABASE '{i}' AS {db_name}")
    cursor = conn.cursor()
    cursor.execute(
        f"""
    INSERT INTO main (link, title, image_hash, datetime)
    SELECT link, title, image_hash, datetime
    FROM {table_name};
    """
    )
    cursor.close()
    conn.commit()
    conn.close()
    delete_db_file(i)
