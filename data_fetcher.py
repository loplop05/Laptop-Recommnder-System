import re
import json
import logging
import requests
import os
from datetime import datetime

from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def clean_price(price_str):
    """
    Extract numeric price from string (e.g., 'JD 780.00' or '650 JOD' -> 780).
    """
    if not price_str:
        return None
    # Remove commas
    price_str = price_str.replace(",", "")
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

def scrape_generic(url_template, product_selector, title_selector, price_selector, link_selector, img_selector, shop_id, pages=2):
    """
    Generic scraper for WooCommerce/OpenCart based Jordanian shops.
    Returns a list of dictionaries with scraped laptop data.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    scraped_laptops_data = []
    
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
                
                if not price or price < 300: # Increase minimum price to filter out accessories
                    continue
                
                # Basic check to ensure it's a laptop
                if not any(kw in title.lower() for kw in ["laptop", "notebook", "zenbook", "vivobook", "thinkpad", "ideapad", "predator", "helios", "nitro", "legion", "macbook", "proart", "rog", "tuf", "victus", "gaming"]):
                    continue
                    
                link_elem = product.select_one(link_selector)
                link = link_elem['href'] if link_elem and link_elem.has_attr('href') else url
                
                img_elem = product.select_one(img_selector)
                img = None
                if img_elem:
                    img = img_elem.get('src') or img_elem.get('data-src') or img_elem.get('srcset')
                    if img and ',' in img: # Handle srcset
                        img = img.split(',')[0].split(' ')[0]
                
                # For now, just return the raw scraped data. Matching and deduplication will happen in ETL.
                scraped_laptops_data.append({
                    "title": title,
                    "price_jod": price,
                    "purchase_url": link,
                    "image_url": img,
                    "shop_id": shop_id,
                    "last_scraped": datetime.now().isoformat()
                })
                    
        except Exception as e:
            logging.error(f"Error scraping {url}: {e}")
            
    return scraped_laptops_data

# These functions are no longer needed as data will be loaded from SQLite
def load_laptops_from_json():
    return []

def save_laptops_to_json(laptops):
    return False

# The main execution block for testing scraping is removed as it will be handled by refresh_data.py
# if __name__ == '__main__':
#     logging.info("Running multi-shop scrape test...")
#     success, count = scrape_all_shops()
#     logging.info(f"Scrape completed. Success: {success}, Total Updated: {count} laptops.")
