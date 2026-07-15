import sqlite3

def init_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Canonical laptop records (deduplicated)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS laptops (
            id TEXT PRIMARY KEY,
            brand TEXT NOT NULL,
            model TEXT NOT NULL,
            cpu TEXT,
            gpu TEXT,
            ram INTEGER,
            storage_type TEXT DEFAULT 'SSD',
            storage_size INTEGER,
            screen_size REAL,
            weight REAL,
            os TEXT,
            use_cases TEXT,           -- JSON array
            performance_level TEXT,
            portability TEXT,
            image_url TEXT,
            last_updated TEXT
        );
    ''')

    # Shop info
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            location TEXT,
            phone TEXT,
            website TEXT,
            map_url TEXT
        );
    ''')

    # Many-to-many: which shops carry which laptop at what price
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS laptop_shop_offers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            laptop_id TEXT REFERENCES laptops(id),
            shop_id INTEGER REFERENCES shops(id),
            price_jod REAL,
            product_url TEXT,
            last_scraped TEXT,
            UNIQUE(laptop_id, shop_id)
        );
    ''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db('laptops.db')
    print("Database schema initialized in laptops.db")
