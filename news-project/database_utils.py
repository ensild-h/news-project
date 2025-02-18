import sqlite3

def initialize_database():
    connection = sqlite3.connect("news_analysis.db")
    cursor = connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_text TEXT,
            summary TEXT,
            keywords TEXT,
            sentiment TEXT,
            category TEXT,
            timestamp TEXT
        )
    ''')
    connection.commit()
    connection.close()
