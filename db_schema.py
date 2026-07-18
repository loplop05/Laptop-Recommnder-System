"""
Database schema and helpers for the Laptop Recommender System.
Uses SQLite — no server needed, easy to query with SQL for filtering.
"""

import sqlite3
import json
import logging
from datetime import datetime, timezone
from config import DB_PATH, PERF_ORDER, SCREEN_RANGES

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class DatabaseManager:
    """Handles database connections and schema initialization."""

    @staticmethod
    def get_connection(db_path=None):
        """Get a connection to the SQLite database."""
        path = db_path or DB_PATH
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    @staticmethod
    def init_db(db_path=None):
        """Create all tables if they don't exist."""
        conn = DatabaseManager.get_connection(db_path)
        cursor = conn.cursor()

        cursor.executescript("""
            -- Canonical laptop records (deduplicated by brand+model)
            CREATE TABLE IF NOT EXISTS laptops (
                id              TEXT PRIMARY KEY,
                brand           TEXT NOT NULL,
                model           TEXT NOT NULL,
                cpu             TEXT,
                gpu             TEXT,
                ram             INTEGER,
                storage_type    TEXT DEFAULT 'SSD',
                storage_size    INTEGER,
                screen_size     REAL,
                weight          REAL,
                os              TEXT,
                use_cases       TEXT,            -- JSON array e.g. '["gaming","work"]'
                performance_level TEXT,
                portability     TEXT,
                image_url       TEXT,
                last_updated    TEXT,
                UNIQUE(brand, model)
            );

            -- Shop directory
            CREATE TABLE IF NOT EXISTS shops (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                name     TEXT UNIQUE NOT NULL,
                location TEXT,
                phone    TEXT,
                website  TEXT,
                map_url  TEXT
            );

            -- Many-to-many: which shops carry which laptop at what price
            CREATE TABLE IF NOT EXISTS laptop_shop_offers (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                laptop_id    TEXT    NOT NULL REFERENCES laptops(id),
                shop_id      INTEGER NOT NULL REFERENCES shops(id),
                price_jod    REAL,
                product_url  TEXT,
                last_scraped TEXT,
                UNIQUE(laptop_id, shop_id)
            );

            -- Index for fast filtering
            CREATE INDEX IF NOT EXISTS idx_laptops_brand ON laptops(brand);
            CREATE INDEX IF NOT EXISTS idx_laptops_perf  ON laptops(performance_level);
            CREATE INDEX IF NOT EXISTS idx_offers_price  ON laptop_shop_offers(price_jod);
            CREATE INDEX IF NOT EXISTS idx_offers_laptop ON laptop_shop_offers(laptop_id);
        """)

        conn.commit()
        conn.close()
        logging.info(f"Database initialized at {db_path or DB_PATH}")


class LaptopRepository:
    """Data Access Layer for Laptop-related operations."""

    def __init__(self, conn):
        self.conn = conn

    def upsert_laptop(self, laptop_dict):
        """Insert or update a canonical laptop record."""
        use_cases_json = json.dumps(laptop_dict.get('use_cases', []))
        now = datetime.now(timezone.utc).isoformat()

        self.conn.execute("""
            INSERT INTO laptops (id, brand, model, cpu, gpu, ram, storage_type, storage_size,
                                 screen_size, weight, os, use_cases, performance_level,
                                 portability, image_url, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                cpu              = COALESCE(excluded.cpu,              laptops.cpu),
                gpu              = COALESCE(excluded.gpu,              laptops.gpu),
                ram              = COALESCE(excluded.ram,              laptops.ram),
                storage_type     = COALESCE(excluded.storage_type,     laptops.storage_type),
                storage_size     = COALESCE(excluded.storage_size,     laptops.storage_size),
                screen_size      = COALESCE(excluded.screen_size,      laptops.screen_size),
                weight           = COALESCE(excluded.weight,           laptops.weight),
                os               = COALESCE(excluded.os,               laptops.os),
                use_cases        = excluded.use_cases,
                performance_level= COALESCE(excluded.performance_level,laptops.performance_level),
                portability      = COALESCE(excluded.portability,      laptops.portability),
                image_url        = COALESCE(excluded.image_url,        laptops.image_url),
                last_updated     = excluded.last_updated
        """, (
            laptop_dict['id'],
            laptop_dict['brand'],
            laptop_dict['model'],
            laptop_dict.get('cpu'),
            laptop_dict.get('gpu'),
            laptop_dict.get('ram'),
            laptop_dict.get('storage_type', 'SSD'),
            laptop_dict.get('storage') or laptop_dict.get('storage_size'),
            laptop_dict.get('screen_size'),
            laptop_dict.get('weight'),
            laptop_dict.get('os'),
            use_cases_json,
            laptop_dict.get('performance_level'),
            laptop_dict.get('portability'),
            laptop_dict.get('image_url'),
            now,
        ))
        self.conn.commit()

    def get_all_with_best_price(self):
        """Return all laptops joined with their cheapest offer price."""
        rows = self.conn.execute("""
            SELECT
                l.*,
                MIN(o.price_jod) AS best_price
            FROM laptops l
            LEFT JOIN laptop_shop_offers o ON l.id = o.laptop_id
            GROUP BY l.id
            ORDER BY best_price ASC
        """).fetchall()

        return [self._process_laptop_row(row) for row in rows]

    def filter_laptops(self, budget=None, use_case=None, screen_size=None,
                        brand=None, performance=None):
        """Apply hard filters on the database."""
        conditions = []
        params = []

        if budget is not None:
            conditions.append("best_price <= ?")
            params.append(float(budget))

        if use_case and use_case != 'any':
            conditions.append("l.use_cases LIKE ?")
            params.append(f'%"{use_case}"%')

        if screen_size and screen_size in SCREEN_RANGES:
            lo, hi = SCREEN_RANGES[screen_size]
            conditions.append("l.screen_size > ? AND l.screen_size <= ?")
            params.extend([lo, hi])

        if brand and brand != 'Any':
            conditions.append("l.brand = ?")
            params.append(brand)

        if performance and performance in PERF_ORDER:
            min_level = PERF_ORDER[performance]
            allowed_levels = [k for k, v in PERF_ORDER.items() if v >= min_level]
            placeholders = ','.join(['?'] * len(allowed_levels))
            conditions.append(f"l.performance_level IN ({placeholders})")
            params.extend(allowed_levels)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        query = f"""
            SELECT l.*, MIN(o.price_jod) AS best_price
            FROM laptops l
            LEFT JOIN laptop_shop_offers o ON l.id = o.laptop_id
            GROUP BY l.id
            HAVING {where_clause}
            ORDER BY best_price ASC
        """

        rows = self.conn.execute(query, params).fetchall()
        return [self._process_laptop_row(row) for row in rows]

    def _process_laptop_row(self, row):
        """Convert a database row into a dictionary and fetch offers."""
        laptop = dict(row)
        laptop['use_cases'] = json.loads(laptop.get('use_cases') or '[]')
        
        offers = self.conn.execute("""
            SELECT o.price_jod, o.product_url, o.last_scraped,
                   s.name AS shop_name, s.location AS shop_location,
                   s.phone AS shop_phone, s.website AS shop_website,
                   s.map_url AS shop_map_url
            FROM laptop_shop_offers o
            JOIN shops s ON o.shop_id = s.id
            WHERE o.laptop_id = ?
            ORDER BY o.price_jod ASC
        """, (laptop['id'],)).fetchall()
        
        laptop['shop_offers'] = [dict(o) for o in offers]
        laptop['price_jod'] = laptop.pop('best_price') or 0
        return laptop


class ShopRepository:
    """Data Access Layer for Shop-related operations."""

    def __init__(self, conn):
        self.conn = conn

    def upsert_shop(self, name, location=None, phone=None, website=None, map_url=None):
        """Insert or update a shop and return its id."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO shops (name, location, phone, website, map_url)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                location = COALESCE(excluded.location, shops.location),
                phone    = COALESCE(excluded.phone,    shops.phone),
                website  = COALESCE(excluded.website,  shops.website),
                map_url  = COALESCE(excluded.map_url,  shops.map_url)
        """, (name, location, phone, website, map_url))
        self.conn.commit()
        return cursor.execute("SELECT id FROM shops WHERE name=?", (name,)).fetchone()['id']

    def upsert_offer(self, laptop_id, shop_id, price_jod, product_url=None):
        """Insert or update a price offer from a shop for a laptop."""
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute("""
            INSERT INTO laptop_shop_offers (laptop_id, shop_id, price_jod, product_url, last_scraped)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(laptop_id, shop_id) DO UPDATE SET
                price_jod    = excluded.price_jod,
                product_url  = COALESCE(excluded.product_url, laptop_shop_offers.product_url),
                last_scraped = excluded.last_scraped
        """, (laptop_id, shop_id, price_jod, product_url, now))
        self.conn.commit()


# Backward compatibility helpers (delegating to new classes)
def get_connection(db_path=None):
    return DatabaseManager.get_connection(db_path)

def init_db(db_path=None):
    DatabaseManager.init_db(db_path)

def filter_laptops(conn, **kwargs):
    repo = LaptopRepository(conn)
    return repo.filter_laptops(**kwargs)

def get_laptops_with_best_price(conn):
    repo = LaptopRepository(conn)
    return repo.get_all_with_best_price()

def upsert_shop(conn, **kwargs):
    repo = ShopRepository(conn)
    return repo.upsert_shop(**kwargs)

def upsert_laptop(conn, laptop_dict):
    repo = LaptopRepository(conn)
    repo.upsert_laptop(laptop_dict)

def upsert_offer(conn, **kwargs):
    repo = ShopRepository(conn)
    repo.upsert_offer(**kwargs)

def seed_from_json(json_path, db_path=None):
    """Seed the database from JSON. Moved logic to separate module if needed, but keeping here for now with refactored internals."""
    from db_seeder import DatabaseSeeder
    seeder = DatabaseSeeder(db_path)
    seeder.seed(json_path)
