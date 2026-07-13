"""
Database schema and helpers for the Laptop Recommender System.
Uses SQLite — no server needed, easy to query with SQL for filtering.
"""

import sqlite3
import json
import os
import logging
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'laptops.db')


def get_connection(db_path=None):
    """Get a connection to the SQLite database."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(db_path=None):
    """Create all tables if they don't exist."""
    conn = get_connection(db_path)
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


def upsert_shop(conn, name, location=None, phone=None, website=None, map_url=None):
    """Insert or update a shop and return its id."""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO shops (name, location, phone, website, map_url)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(name) DO UPDATE SET
            location = COALESCE(excluded.location, shops.location),
            phone    = COALESCE(excluded.phone,    shops.phone),
            website  = COALESCE(excluded.website,  shops.website),
            map_url  = COALESCE(excluded.map_url,  shops.map_url)
    """, (name, location, phone, website, map_url))
    conn.commit()
    return cursor.execute("SELECT id FROM shops WHERE name=?", (name,)).fetchone()['id']


def upsert_laptop(conn, laptop_dict):
    """
    Insert or update a canonical laptop record.
    laptop_dict must have at least: id, brand, model.
    """
    use_cases_json = json.dumps(laptop_dict.get('use_cases', []))
    now = datetime.now(timezone.utc).isoformat()

    conn.execute("""
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
    conn.commit()


def upsert_offer(conn, laptop_id, shop_id, price_jod, product_url=None):
    """Insert or update a price offer from a shop for a laptop."""
    now = datetime.now(timezone.utc).isoformat()
    conn.execute("""
        INSERT INTO laptop_shop_offers (laptop_id, shop_id, price_jod, product_url, last_scraped)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(laptop_id, shop_id) DO UPDATE SET
            price_jod    = excluded.price_jod,
            product_url  = COALESCE(excluded.product_url, laptop_shop_offers.product_url),
            last_scraped = excluded.last_scraped
    """, (laptop_id, shop_id, price_jod, product_url, now))
    conn.commit()


def get_laptops_with_best_price(conn):
    """
    Return all laptops joined with their cheapest offer price and all shop offers.
    Returns a list of dicts.
    """
    rows = conn.execute("""
        SELECT
            l.*,
            MIN(o.price_jod) AS best_price
        FROM laptops l
        LEFT JOIN laptop_shop_offers o ON l.id = o.laptop_id
        GROUP BY l.id
        ORDER BY best_price ASC
    """).fetchall()

    result = []
    for row in rows:
        laptop = dict(row)
        laptop['use_cases'] = json.loads(laptop.get('use_cases') or '[]')
        # Fetch all offers for this laptop
        offers = conn.execute("""
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
        # Use best price as the display price
        laptop['price_jod'] = laptop.pop('best_price') or 0
        result.append(laptop)

    return result


def filter_laptops(conn, budget=None, use_case=None, screen_size=None,
                   brand=None, performance=None):
    """
    Apply hard filters on the database and return matching laptops with offers.
    This is the critical function that ensures user constraints are NEVER violated.

    Hard constraints (applied as SQL WHERE):
      - budget:      best price for this laptop <= budget
      - use_case:    laptop.use_cases JSON array contains the requested use case
      - screen_size: laptop.screen_size falls in the requested range
      - brand:       exact match (unless 'Any')
      - performance: laptop.performance_level >= requested level
    """
    perf_order = {'entry': 1, 'medium': 2, 'high': 3}
    screen_ranges = {
        '13-14': (0, 14.5),
        '15-16': (14.5, 16.5),
        '17+':   (16.5, 100),
    }

    # Start building the query
    conditions = []
    params = []

    # Budget: best price must be <= budget
    if budget is not None:
        conditions.append("best_price <= ?")
        params.append(float(budget))

    # Use case: JSON array must contain the requested value
    if use_case and use_case != 'any':
        # SQLite JSON: use LIKE for simple containment on the JSON array
        conditions.append("l.use_cases LIKE ?")
        params.append(f'%"{use_case}"%')

    # Screen size: must fall in requested range
    if screen_size and screen_size in screen_ranges:
        lo, hi = screen_ranges[screen_size]
        conditions.append("l.screen_size > ? AND l.screen_size <= ?")
        params.extend([lo, hi])

    # Brand: exact match unless 'Any'
    if brand and brand != 'Any':
        conditions.append("l.brand = ?")
        params.append(brand)

    # Performance: must meet or exceed requested level
    if performance and performance in perf_order:
        min_level = perf_order[performance]
        allowed_levels = [k for k, v in perf_order.items() if v >= min_level]
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

    rows = conn.execute(query, params).fetchall()

    result = []
    for row in rows:
        laptop = dict(row)
        laptop['use_cases'] = json.loads(laptop.get('use_cases') or '[]')
        # Fetch all offers for this laptop
        offers = conn.execute("""
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
        result.append(laptop)

    return result


def seed_from_json(json_path, db_path=None):
    """
    Seed the database from the existing laptops_cache.json file.
    This migrates the legacy JSON data into the new SQLite schema.
    """
    init_db(db_path)
    conn = get_connection(db_path)

    with open(json_path, 'r', encoding='utf-8') as f:
        laptops = json.load(f)

    # Known shop metadata for Jordanian retailers
    shop_metadata = {
        'pccircle.com': {
            'name': 'PC Circle',
            'location': 'Mecca Street, Amman, Jordan',
            'phone': '+962-6-585-5558',
            'website': 'https://pccircle.com',
            'map_url': 'https://maps.google.com/?q=PC+Circle+Amman+Jordan',
        },
        'citycenter.jo': {
            'name': 'City Center',
            'location': 'King Abdullah II Street, Amman, Jordan',
            'phone': '+962-6-500-1234',
            'website': 'https://citycenter.jo',
            'map_url': 'https://maps.google.com/?q=City+Center+Electronics+Amman+Jordan',
        },
        'gts.jo': {
            'name': 'GTS',
            'location': 'Wasfi Al-Tal Street, Amman, Jordan',
            'phone': '+962-6-553-9876',
            'website': 'https://gts.jo',
            'map_url': 'https://maps.google.com/?q=GTS+Jordan+Amman',
        },
    }

    # Register shops
    shop_ids = {}
    for domain, meta in shop_metadata.items():
        sid = upsert_shop(conn, **meta)
        shop_ids[domain] = sid

    for lap in laptops:
        # Determine storage_size from the legacy 'storage' field
        storage_val = lap.get('storage', 512)

        laptop_dict = {
            'id': lap['id'],
            'brand': lap['brand'],
            'model': lap['model'],
            'cpu': lap.get('cpu'),
            'gpu': lap.get('gpu'),
            'ram': lap.get('ram'),
            'storage_type': 'SSD',
            'storage_size': storage_val,
            'screen_size': lap.get('screen_size'),
            'weight': lap.get('weight'),
            'os': 'macOS' if lap['brand'] == 'Apple' else 'Windows',
            'use_cases': lap.get('use_cases', ['general']),
            'performance_level': lap.get('performance_level', 'medium'),
            'portability': lap.get('portability', 'medium'),
            'image_url': lap.get('image_url'),
        }
        upsert_laptop(conn, laptop_dict)

        # Create an offer from the identified shop
        purchase_url = lap.get('purchase_url', '')
        price = lap.get('price_jod', 0)

        # Determine which shop based on URL domain
        matched_shop_id = None
        for domain, sid in shop_ids.items():
            if domain in purchase_url:
                matched_shop_id = sid
                break

        if matched_shop_id and price:
            upsert_offer(conn, lap['id'], matched_shop_id, price, purchase_url)

    conn.close()
    logging.info(f"Seeded {len(laptops)} laptops from {json_path}")


if __name__ == '__main__':
    # Quick self-test: seed from cache and print stats
    cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'laptops_cache.json')
    if os.path.exists(cache_path):
        seed_from_json(cache_path)
        conn = get_connection()
        laptops = get_laptops_with_best_price(conn)
        print(f"\n{'='*60}")
        print(f"  Database has {len(laptops)} laptops")
        shops = conn.execute("SELECT COUNT(*) AS cnt FROM shops").fetchone()['cnt']
        offers = conn.execute("SELECT COUNT(*) AS cnt FROM laptop_shop_offers").fetchone()['cnt']
        print(f"  {shops} shops, {offers} price offers")
        print(f"{'='*60}\n")
        for lap in laptops[:3]:
            print(f"  {lap['brand']} {lap['model']} — {lap['price_jod']} JOD")
            for o in lap['shop_offers']:
                print(f"    └─ {o['shop_name']}: {o['price_jod']} JOD → {o['product_url']}")
        conn.close()
    else:
        print(f"Cache file not found: {cache_path}")
