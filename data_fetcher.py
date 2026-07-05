from _typeshed import importlib
import os
import re
import json
import logging
import requests

# pyrefly: ignore [missing-import]
from bs4 import  BeautifulSoup   


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CACHE_FILE = 'laptops_cache.json'
ACTIVE_FILE = 'laptops_active.json'

def load_laptops():
    """
    Load laptops from active file, or fallback to the pristine cache.
    """
    target = ACTIVE_FILE if os.path.exists(ACTIVE_FILE) else CACHE_FILE
    try:
        with open(target, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading laptops from {target}: {e}")
        # Final fallback to pristine cache if active is corrupted
        if target == ACTIVE_FILE:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

def save_laptops(laptops):
    """
    Save the laptop database to active file.
    """
    try:
        with open(ACTIVE_FILE, 'w', encoding='utf-8') as f:
            json.dump(laptops, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logging.error(f"Error saving laptops to {ACTIVE_FILE}: {e}")
        return False

def clean_price(price_str):
    """
    Extract numeric price from string (e.g., 'JD 780.00' or '650 JOD' -> 780).
    """
    if not price_str:
        return None
    # Remove commas
    price_str = price_str.replace(',', '')
    # Find all decimal/integer numbers
    matches = re.findall(r'\d+(?:\.\d+)?', price_str)
    if matches:
        # Return the float/int of the first match
        try:
            val = float(matches[0])
            return int(val) if val.is_integer() else val
        except ValueError:
            return None
    return None

def match_laptop(scraped_title, scraped_price, scraped_link, scraped_img, laptops):
    """
    Matches a scraped product title and price with our curated laptops database.
    Uses keyword tokens to determine the best fit.
    """
    title_lower = scraped_title.lower()
    best_match = None
    best_score = 0
    
    for laptop in laptops:
        brand = laptop['brand'].lower()
        model = laptop['model'].lower()
        
        # Brand must match
        if brand not in title_lower:
            continue
            
        score = 0
        
        # Check model keyword matches
        model_words = model.split()
        for word in model_words:
            if len(word) > 2 and word in title_lower:
                score += 2
                
        # Check CPU specs (e.g., i5, i7, i9, r7, r9, m2, m3)
        cpu_lower = laptop['cpu'].lower()
        cpu_keywords = ['i5', 'i7', 'i9', 'ryzen 5', 'ryzen 7', 'ryzen 9', 'm1', 'm2', 'm3', 'ultra 7', 'ultra 9']
        for kw in cpu_keywords:
            if kw in cpu_lower and kw in title_lower:
                score += 3
        
        # Check GPU keywords
        gpu_lower = laptop['gpu'].lower()
        if 'rtx 4060' in gpu_lower and '4060' in title_lower:
            score += 4
        elif 'rtx 4070' in gpu_lower and '4070' in title_lower:
            score += 4
        elif 'rtx 4080' in gpu_lower and '4080' in title_lower:
            score += 4
        elif 'rtx 3050' in gpu_lower and '3050' in title_lower:
            score += 4
        elif 'iris' in gpu_lower and ('iris' in title_lower or 'intel graphics' in title_lower or 'integrated' in title_lower):
            score += 2
            
        # Check RAM size
        ram_str = f"{laptop['ram']}gb"
        ram_alt = f"{laptop['ram']} gb"
        if ram_str in title_lower or ram_alt in title_lower:
            score += 3
            
        # Threshold for a good match
        if score > best_score and score >= 5:
            best_score = score
            best_match = laptop

    return best_match

def scrape_generic(url_template, product_selector, title_selector, price_selector, link_selector, img_selector, pages=2):
    """
    Generic scraper for WooCommerce/OpenCart based Jordanian shops.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    laptops = load_laptops()
    if not laptops:
        return False, 0
        
    updated_count = 0
    matched_ids = set()
    
    for page in range(1, pages + 1):
        url = url_template.format(page=page)
        logging.info(f"Scraping: {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                logging.warning(f"Failed to fetch {url}, status code: {response.status_code}")
                continue
                
            soup = BeautifulSoup(response.text, 'html.parser')
            products = soup.select(product_selector)
            
            if not products:
                logging.warning(f"No products found on {url}")
                continue
                
            for product in products:
                title_elem = product.select_one(title_selector)
                price_elem = product.select_one(price_selector)
                if not title_elem or not price_elem:
                    continue
                    
                title = title_elem.text.strip()
                price = clean_price(price_elem.text.strip())
                
                if not price or price < 100:
                    continue
                    
                link_elem = product.select_one(link_selector)
                link = link_elem['href'] if link_elem and link_elem.has_attr('href') else url
                
                img_elem = product.select_one(img_selector)
                img = None
                if img_elem:
                    img = img_elem.get('src') or img_elem.get('data-src') or img_elem.get('srcset')
                    if img and ',' in img: # Handle srcset
                        img = img.split(',')[0].split(' ')[0]
                
                matched = match_laptop(title, price, link, img, laptops)
                if matched and matched['id'] not in matched_ids:
                    matched['price_jod'] = price
                    if link and 'product-category' not in link and 'search' not in link:
                        matched['purchase_url'] = link
                    if img and (not matched.get('image_url') or 'unsplash' not in matched['image_url']):
                        matched['image_url'] = img
                        
                    matched_ids.add(matched['id'])
                    updated_count += 1
                    logging.info(f"Updated {matched['brand']} {matched['model']} from {url.split('/')[2]}: {price} JOD")
                    
        except Exception as e:
            logging.error(f"Error scraping {url}: {e}")
            
    if updated_count > 0:
        save_laptops(laptops)
        return True, updated_count
    return False, 0

def scrape_all_shops():
    """
    Run scrapers for all supported shops.
    """
    shops = [
        {
            "name": "PC Circle",
            "url": "https://pccircle.com/product-category/laptops/page/{page}/",
            "p": "li.product", "t": ".woocommerce-loop-product__title", "pr": ".price", "l": "a", "i": "img"
        },
        {
            "name": "City Center",
            "url": "https://citycenter.jo/index.php?route=product/search&search=laptop&page={page}",
            "p": ".product-layout", "t": "h4 a", "pr": ".price", "l": "h4 a", "i": ".image img"
        },
        {
            "name": "OS-JO",
            "url": "https://os-jo.com/index.php?route=product/search&search=laptop&page={page}",
            "p": ".product-layout", "t": "h4 a", "pr": ".price", "l": "h4 a", "i": ".image img"
        },
        {
            "name": "GTS",
            "url": "https://gts.jo/en/laptops-tablets/laptops/laptop-notebooks?page={page}",
            "p": ".product-layout", "t": "h4 a", "pr": ".price", "l": "h4 a", "i": ".image img"
        }
    ]
    
    
    total_updated = 0
    for shop in shops:
        success, count = scrape_generic(shop["url"], shop["p"], shop["t"], shop["pr"], shop["l"], shop["i"])
        if success:
            total_updated += count
            logging.info(f"Shop {shop['name']} update successful: {count} laptops.")
            
    return total_updated > 0, total_updated

if __name__ == '__main__':
    logging.info("Running multi-shop scrape test...")
    success, count = scrape_all_shops()
    logging.info(f"Scrape completed. Success: {success}, Total Updated: {count} laptops.")
