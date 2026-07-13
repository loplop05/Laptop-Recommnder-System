"""
refresh_data.py — ETL script for the Laptop Recommender System.

Usage:
    python refresh_data.py          # Full refresh: seed from JSON + scrape all shops
    python refresh_data.py --seed   # Only seed from JSON (no scraping)
    python refresh_data.py --scrape # Only scrape (assumes DB already seeded)

Can be scheduled via cron / Task Scheduler for periodic updates.
Example cron (daily at 3 AM):
    0 3 * * * cd /path/to/Laptop-Recommnder-System && python refresh_data.py
"""

import argparse
import logging
import os
import sys
import re
import json
from datetime import datetime, timezone

import requests
# pyrefly: ignore [missing-import]
from bs4 import BeautifulSoup

from db_schema import (
    init_db, get_connection, upsert_shop, upsert_laptop,
    upsert_offer, seed_from_json, get_laptops_with_best_price, DB_PATH
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/120.0.0.0 Safari/537.36'
}

# ─── Shop configurations with metadata ──────────────────────────────────────
SHOPS = [
    {
        "name": "PC Circle",
        "location": "Mecca Street, Amman, Jordan",
        "phone": "+962-6-585-5558",
        "website": "https://pccircle.com",
        "map_url": "https://maps.google.com/?q=PC+Circle+Amman+Jordan",
        "scrape": {
            "url": "https://pccircle.com/product-category/laptops/page/{page}/",
            "product": "li.product",
            "title": ".woocommerce-loop-product__title",
            "price": ".price",
            "link": "a",
            "img": "img",
            "pages": 3,
        },
    },
    {
        "name": "City Center",
        "location": "King Abdullah II Street, Amman, Jordan",
        "phone": "+962-6-500-1234",
        "website": "https://citycenter.jo",
        "map_url": "https://maps.google.com/?q=City+Center+Electronics+Amman+Jordan",
        "scrape": {
            "url": "https://citycenter.jo/index.php?route=product/search&search=laptop&page={page}",
            "product": ".product-layout",
            "title": "h4 a",
            "price": ".price",
            "link": "h4 a",
            "img": ".image img",
            "pages": 3,
        },
    },
    {
        "name": "GTS",
        "location": "Wasfi Al-Tal Street, Amman, Jordan",
        "phone": "+962-6-553-9876",
        "website": "https://gts.jo",
        "map_url": "https://maps.google.com/?q=GTS+Jordan+Amman",
        "scrape": {
            "url": "https://gts.jo/en/laptops-tablets/laptops/laptop-notebooks?page={page}",
            "product": ".product-layout",
            "title": "h4 a",
            "price": ".price",
            "link": "h4 a",
            "img": ".image img",
            "pages": 3,
        },
    },
]


def clean_price(price_str):
    """Extract numeric price from string (e.g., 'JD 780.00' or '650 JOD' -> 780)."""
    if not price_str:
        return None
    price_str = price_str.replace(',', '')
    matches = re.findall(r'\d+(?:\.\d+)?', price_str)
    if matches:
        try:
            val = float(matches[0])
            return int(val) if val.is_integer() else val
        except ValueError:
            return None
    return None


def match_scraped_to_db(title, conn):
    """
    Try to match a scraped product title to an existing laptop in the DB.
    Returns the laptop id if matched, else None.
    Uses keyword scoring similar to the original data_fetcher.match_laptop().
    """
    title_lower = title.lower()
    laptops = conn.execute("SELECT id, brand, model, cpu, gpu, ram FROM laptops").fetchall()

    best_match_id = None
    best_score = 0

    for lap in laptops:
        brand = lap['brand'].lower()
        model = lap['model'].lower()

        # Brand must appear in title
        if brand not in title_lower:
            continue

        score = 0

        # Model keyword matches
        for word in model.split():
            if len(word) > 2 and word in title_lower:
                score += 2

        # CPU keyword matches
        cpu_lower = (lap['cpu'] or '').lower()
        cpu_keywords = ['i5', 'i7', 'i9', 'ryzen 5', 'ryzen 7', 'ryzen 9',
                        'm1', 'm2', 'm3', 'ultra 7', 'ultra 9']
        for kw in cpu_keywords:
            if kw in cpu_lower and kw in title_lower:
                score += 3

        # GPU keyword matches
        gpu_lower = (lap['gpu'] or '').lower()
        gpu_models = ['4060', '4070', '4080', '4050', '3050', '3060', '3070']
        for gm in gpu_models:
            if gm in gpu_lower and gm in title_lower:
                score += 4
                break

        if 'iris' in gpu_lower and ('iris' in title_lower or 'intel graphics' in title_lower):
            score += 2

        # RAM match
        ram = lap['ram']
        if ram:
            if f"{ram}gb" in title_lower.replace(' ', '') or f"{ram} gb" in title_lower:
                score += 3

        # Threshold
        if score > best_score and score >= 5:
            best_score = score
            best_match_id = lap['id']

    return best_match_id


def scrape_shop(shop_config, conn):
    """
    Scrape a single shop and update offers in the database.
    Returns the number of updated/created offers.
    """
    shop_id = upsert_shop(
        conn,
        name=shop_config['name'],
        location=shop_config.get('location'),
        phone=shop_config.get('phone'),
        website=shop_config.get('website'),
        map_url=shop_config.get('map_url'),
    )

    scrape_cfg = shop_config['scrape']
    updated = 0

    for page in range(1, scrape_cfg['pages'] + 1):
        url = scrape_cfg['url'].format(page=page)
        logging.info(f"Scraping: {url}")

        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            if response.status_code != 200:
                logging.warning(f"Failed to fetch {url}, status {response.status_code}")
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            products = soup.select(scrape_cfg['product'])

            if not products:
                logging.warning(f"No products found on {url}")
                continue

            for product in products:
                title_elem = product.select_one(scrape_cfg['title'])
                price_elem = product.select_one(scrape_cfg['price'])
                if not title_elem or not price_elem:
                    continue

                title = title_elem.text.strip()
                price = clean_price(price_elem.text.strip())

                if not price or price < 100:
                    continue

                link_elem = product.select_one(scrape_cfg['link'])
                link = link_elem['href'] if link_elem and link_elem.has_attr('href') else url

                img_elem = product.select_one(scrape_cfg['img'])
                img = None
                if img_elem:
                    img = img_elem.get('src') or img_elem.get('data-src') or img_elem.get('srcset')
                    if img and ',' in img:
                        img = img.split(',')[0].split(' ')[0]

                # Try to match to existing laptop
                laptop_id = match_scraped_to_db(title, conn)
                if laptop_id:
                    upsert_offer(conn, laptop_id, shop_id, price, link)

                    # Update image if we got a real product image
                    if img and 'unsplash' not in (img or ''):
                        conn.execute(
                            "UPDATE laptops SET image_url = ? WHERE id = ?",
                            (img, laptop_id)
                        )
                        conn.commit()

                    updated += 1
                    logging.info(f"  Matched: {title[:60]}... → {laptop_id} @ {price} JOD")

        except Exception as e:
            logging.error(f"Error scraping {url}: {e}")

    return updated


def scrape_all_shops(conn=None):
    """Run scrapers for all configured shops."""
    own_conn = conn is None
    if own_conn:
        conn = get_connection()

    total = 0
    for shop in SHOPS:
        try:
            count = scrape_shop(shop, conn)
            total += count
            logging.info(f"Shop '{shop['name']}': {count} offers updated")
        except Exception as e:
            logging.error(f"Failed to scrape {shop['name']}: {e}")

    if own_conn:
        conn.close()

    logging.info(f"Total offers updated: {total}")
    return total


def print_summary():
    """Print a summary of the database state."""
    conn = get_connection()
    laptops_count = conn.execute("SELECT COUNT(*) AS cnt FROM laptops").fetchone()['cnt']
    shops_count = conn.execute("SELECT COUNT(*) AS cnt FROM shops").fetchone()['cnt']
    offers_count = conn.execute("SELECT COUNT(*) AS cnt FROM laptop_shop_offers").fetchone()['cnt']

    print(f"\n{'='*60}")
    print(f"  Database Summary ({DB_PATH})")
    print(f"{'='*60}")
    print(f"  Laptops:     {laptops_count}")
    print(f"  Shops:       {shops_count}")
    print(f"  Offers:      {offers_count}")
    print(f"  Last run:    {datetime.now(timezone.utc).isoformat()}")
    print(f"{'='*60}\n")

    # Show some examples
    laptops = get_laptops_with_best_price(conn)
    for lap in laptops[:5]:
        offers_str = ', '.join(
            f"{o['shop_name']}={o['price_jod']}JOD" for o in lap['shop_offers']
        )
        print(f"  {lap['brand']} {lap['model']}: {lap['price_jod']} JOD [{offers_str}]")

    conn.close()


def main():
    parser = argparse.ArgumentParser(
        description='Refresh the laptop database from shop websites.'
    )
    parser.add_argument('--seed', action='store_true',
                        help='Only seed from laptops_cache.json (no scraping)')
    parser.add_argument('--scrape', action='store_true',
                        help='Only scrape (assumes DB is already seeded)')
    parser.add_argument('--db', type=str, default=None,
                        help='Path to SQLite database file')
    args = parser.parse_args()

    if args.db:
        import db_schema
        db_schema.DB_PATH = args.db

    do_seed = not args.scrape  # seed unless --scrape only
    do_scrape = not args.seed  # scrape unless --seed only

    if do_seed:
        cache_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'laptops_cache.json'
        )
        if os.path.exists(cache_path):
            logging.info("Seeding database from laptops_cache.json...")
            seed_from_json(cache_path, args.db)
        else:
            logging.error(f"Cache file not found: {cache_path}")
            sys.exit(1)

    if do_scrape:
        logging.info("Scraping all shops...")
        total = scrape_all_shops()
        logging.info(f"Scraping complete. {total} offers updated.")

    print_summary()


if __name__ == '__main__':
    main()
