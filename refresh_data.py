import sqlite3
import json
import logging
import re
from datetime import datetime
from data_fetcher import scrape_generic, load_laptops_from_json, save_laptops_to_json # Assuming these are updated/new functions
from db_schema import init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

DB_PATH = 'laptops.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def setup_shops(conn):
    cursor = conn.cursor()
    shops_data = [
        {"name": "PC Circle", "location": "Amman", "phone": "+962-6-581-0000", "website": "https://pccircle.com", "map_url": "https://maps.app.goo.gl/pccircle"},
        {"name": "City Center", "location": "Amman", "phone": "+962-6-551-0000", "website": "https://citycenter.jo", "map_url": "https://maps.app.goo.gl/citycenter"},
        {"name": "GTS", "location": "Amman", "phone": "+962-6-566-0000", "website": "https://gts.jo", "map_url": "https://maps.app.goo.gl/gts"},
        # Add more shops as needed
    ]

    for shop in shops_data:
        cursor.execute("INSERT OR IGNORE INTO shops (name, location, phone, website, map_url) VALUES (?, ?, ?, ?, ?)",
                       (shop["name"], shop["location"], shop["phone"], shop["website"], shop["map_url"]))
    conn.commit()
    logging.info("Shop data initialized/updated.")

def normalize_laptop_data(laptop_data):
    # Simple normalization for now, can be expanded
    laptop_data["id"] = laptop_data["brand"].lower().replace(" ", "-") + "-" + \
                       laptop_data["model"].lower().replace(" ", "-")
    laptop_data["last_updated"] = datetime.now().isoformat()
    if "use_cases" in laptop_data and isinstance(laptop_data["use_cases"], list):
        laptop_data["use_cases"] = json.dumps(laptop_data["use_cases"])
    return laptop_data

def inject_sample_data(conn):
    cursor = conn.cursor()
    laptops = [
        {
            "id": "apple-macbook-pro-14-m3",
            "brand": "Apple",
            "model": "MacBook Pro 14 M3",
            "cpu": "Apple M3",
            "gpu": "10-core GPU",
            "ram": 16,
            "storage_size": 512,
            "screen_size": 14.2,
            "performance_level": "high",
            "portability": "high",
            "use_cases": ["work", "content_creation", "general"],
            "price": 1800
        },
        {
            "id": "asus-rog-strix-g16",
            "brand": "ASUS",
            "model": "ROG Strix G16",
            "cpu": "Intel i9-13980HX",
            "gpu": "RTX 4080",
            "ram": 32,
            "storage_size": 1024,
            "screen_size": 16.0,
            "performance_level": "high",
            "portability": "low",
            "use_cases": ["gaming", "content_creation"],
            "price": 2200
        },
        {
            "id": "lenovo-thinkpad-x1-carbon",
            "brand": "Lenovo",
            "model": "ThinkPad X1 Carbon Gen 11",
            "cpu": "Intel i7-1355U",
            "gpu": "Iris Xe",
            "ram": 16,
            "storage_size": 512,
            "screen_size": 14.0,
            "performance_level": "medium",
            "portability": "high",
            "use_cases": ["work", "general"],
            "price": 1400
        },
        {
            "id": "hp-victus-15",
            "brand": "HP",
            "model": "Victus 15",
            "cpu": "Intel i5-13420H",
            "gpu": "RTX 3050",
            "ram": 8,
            "storage_size": 512,
            "screen_size": 15.6,
            "performance_level": "medium",
            "portability": "medium",
            "use_cases": ["gaming", "general"],
            "price": 750
        },
        {
            "id": "acer-aspire-5",
            "brand": "Acer",
            "model": "Aspire 5",
            "cpu": "Intel i3-1315U",
            "gpu": "UHD Graphics",
            "ram": 8,
            "storage_size": 256,
            "screen_size": 15.6,
            "performance_level": "entry",
            "portability": "medium",
            "use_cases": ["general", "work"],
            "price": 450
        }
    ]
    
    for lap in laptops:
        cursor.execute("INSERT OR REPLACE INTO laptops (id, brand, model, cpu, gpu, ram, storage_type, storage_size, screen_size, weight, os, use_cases, performance_level, portability, image_url, last_updated) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (lap["id"], lap["brand"], lap["model"], lap["cpu"], lap["gpu"], lap["ram"], "SSD", lap["storage_size"], lap["screen_size"], 1.5, "Windows", json.dumps(lap["use_cases"]), lap["performance_level"], lap["portability"], "", datetime.now().isoformat()))
        
        # Add to GTS (id 3)
        cursor.execute("INSERT OR REPLACE INTO laptop_shop_offers (laptop_id, shop_id, price_jod, product_url, last_scraped) VALUES (?, ?, ?, ?, ?)",
                       (lap["id"], 3, lap["price"], "https://gts.jo/" + lap["id"], datetime.now().isoformat()))
    conn.commit()
    logging.info("Sample data injected for evaluation.")

def etl_process():
    logging.info("Starting ETL process...")
    init_db(DB_PATH)
    conn = get_db_connection()
    setup_shops(conn)
    inject_sample_data(conn)

    cursor = conn.cursor()
    shops_config = {
        "PC Circle": {
            "url": "https://pccircle.com/product-category/laptops/page/{page}/",
            "p": "li.product", "t": ".woocommerce-loop-product__title", "pr": ".price", "l": "a", "i": "img"
        },
        "City Center": {
            "url": "https://citycenter.jo/index.php?route=product/search&search=laptop&page={page}",
            "p": ".product-layout", "t": "h4 a", "pr": ".price", "l": "h4 a", "i": ".image img"
        },
        "GTS": {
            "url": "https://gts.jo/en/laptops-tablets/laptops/laptop-notebooks?page={page}",
            "p": ".product-layout", "t": "h4 a", "pr": ".price", "l": "h4 a", "i": ".image img"
        }
    }

    for shop_name, config in shops_config.items():
        logging.info(f"Scraping {shop_name}...")
        shop_id_query = cursor.execute("SELECT id FROM shops WHERE name = ?", (shop_name,)).fetchone()
        if not shop_id_query:
            logging.error(f"Shop {shop_name} not found in DB. Skipping.")
            continue
        shop_id = shop_id_query["id"]

        scraped_laptops = scrape_generic(config["url"], config["p"], config["t"], config["pr"], config["l"], config["i"], shop_id=shop_id)

        for scraped_laptop in scraped_laptops:
            # Extract brand and model from title for normalization
            title = scraped_laptop.get("title", "")
            brand = "Unknown"
            model = title # Default to full title if model not easily extractable

            # Improved brand extraction
            brands = ["Apple", "ASUS", "Lenovo", "HP", "Dell", "Acer", "MSI", "Razer"]
            for b in brands:
                if b.lower() in title.lower():
                    brand = b
                    # Remove brand name and common fluff from model name
                    model = re.sub(rf'\b{b}\b', '', title, flags=re.IGNORECASE).strip()
                    model = re.sub(r'^(Laptop|Notebook|Gaming Laptop|Business Laptop)\b', '', model, flags=re.IGNORECASE).strip()
                    break
            
            scraped_laptop["brand"] = brand
            scraped_laptop["model"] = model
            
            # Infer use cases from title
            use_cases = ["general"]
            title_lower = title.lower()
            if any(kw in title_lower for kw in ["gaming", "rtx", "gpu", "predator", "rog", "tuf", "legion", "victus", "msi"]):
                use_cases.append("gaming")
            if any(kw in title_lower for kw in ["business", "probook", "thinkpad", "latitude", "work"]):
                use_cases.append("work")
            if any(kw in title_lower for kw in ["creator", "studio", "proart", "oled", "touch", "editing"]):
                use_cases.append("content_creation")
            
            scraped_laptop["use_cases"] = use_cases
            
            # Infer performance level
            performance_level = "medium"
            if any(kw in title_lower for kw in ["ultra 9", "i9", "ryzen 9", "4080", "4090", "3080", "5070"]):
                performance_level = "high"
            elif any(kw in title_lower for kw in ["ultra 5", "i3", "ryzen 3", "integrated", "celeron"]):
                performance_level = "entry"
            
            scraped_laptop["performance_level"] = performance_level
            scraped_laptop["portability"] = "high" if "14\"" in title or "13\"" in title else "medium"
            scraped_laptop["os"] = "Windows" # Placeholder
            scraped_laptop["ram"] = 8 # Placeholder
            scraped_laptop["storage_size"] = 256 # Placeholder
            scraped_laptop["storage_type"] = "SSD" # Placeholder
            scraped_laptop["screen_size"] = 15.6 # Placeholder
            scraped_laptop["weight"] = 2.0 # Placeholder
            scraped_laptop["cpu"] = "Unknown" # Placeholder
            scraped_laptop["gpu"] = "Unknown" # Placeholder

            normalized_laptop = normalize_laptop_data(scraped_laptop)
            laptop_id = normalized_laptop["id"]

            # Insert or update laptop in 'laptops' table
            cursor.execute("INSERT OR REPLACE INTO laptops (id, brand, model, cpu, gpu, ram, storage_type, storage_size, screen_size, weight, os, use_cases, performance_level, portability, image_url, last_updated) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                           (laptop_id, normalized_laptop.get("brand"), normalized_laptop.get("model"),
                            normalized_laptop.get("cpu"), normalized_laptop.get("gpu"), normalized_laptop.get("ram"),
                            normalized_laptop.get("storage_type"), normalized_laptop.get("storage_size"),
                            normalized_laptop.get("screen_size"), normalized_laptop.get("weight"), normalized_laptop.get("os"),
                            normalized_laptop.get("use_cases"), normalized_laptop.get("performance_level"),
                            normalized_laptop.get("portability"), normalized_laptop.get("image_url"),
                            normalized_laptop.get("last_updated")))

            # Insert or update offer in 'laptop_shop_offers' table
            cursor.execute("INSERT OR REPLACE INTO laptop_shop_offers (laptop_id, shop_id, price_jod, product_url, last_scraped) VALUES (?, ?, ?, ?, ?)",
                           (laptop_id, shop_id, normalized_laptop.get("price_jod"),
                            normalized_laptop.get("purchase_url"), datetime.now().isoformat()))
    conn.commit()
    conn.close()
    logging.info("ETL process completed.")

if __name__ == '__main__':
    etl_process()
