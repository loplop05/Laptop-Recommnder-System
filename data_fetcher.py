import os
import re
import json
import logging
import requests
from bs4 import BeautifulSoup

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

def scrape_pc_circle():
    """
    Scrape laptop listings from PC Circle and update active pricing.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    laptops = load_laptops()
    if not laptops:
        logging.error("No laptops available to update.")
        return False, 0
        
    updated_count = 0
    matched_ids = set()
    
    # Scrape first 2 pages of laptop listings
    for page in range(1, 3):
        url = f"https://pccircle.com/product-category/laptops/page/{page}/"
        logging.info(f"Scraping page {page}: {url}")
        
        try:
            # Short timeout to avoid blocking if the site is slow
            response = requests.get(url, headers=headers, timeout=12)
            if response.status_code != 200:
                logging.warning(f"Failed to fetch {url}, status code: {response.status_code}")
                break
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find product cards (typically 'li.product' or 'div.product-grid-item' in WooCommerce)
            products = soup.select('li.product') or soup.select('.product-grid-item') or soup.select('.product')
            
            if not products:
                logging.warning(f"No products found on page {page} with standard selectors.")
                break
                
            for product in products:
                # Title
                title_elem = product.select_one('.woocommerce-loop-product__title') or product.select_one('.product-title') or product.select_one('h2') or product.select_one('h3')
                if not title_elem:
                    continue
                title = title_elem.text.strip()
                
                # Price
                price_elem = product.select_one('.price') or product.select_one('.woocommerce-Price-amount')
                if not price_elem:
                    continue
                price_text = price_elem.text.strip()
                price = clean_price(price_text)
                
                if not price or price < 100:  # Ignore weirdly low prices or missing prices
                    continue
                    
                # Link
                link_elem = product.select_one('a')
                link = link_elem['href'] if link_elem and link_elem.has_attr('href') else url
                
                # Image
                img_elem = product.select_one('img')
                img = img_elem['src'] if img_elem and img_elem.has_attr('src') else None
                if img and 'placeholder' in img and img_elem.has_attr('data-src'):
                    img = img_elem['data-src']
                
                # Try to match with database
                matched = match_laptop(title, price, link, img, laptops)
                if matched and matched['id'] not in matched_ids:
                    # Update price
                    old_price = matched['price_jod']
                    matched['price_jod'] = price
                    matched['purchase_url'] = link
                    # Update image only if it's a valid link and we don't have a high-res unsplash one
                    if img and not matched['image_url'].startswith('https://images.unsplash.com'):
                        matched['image_url'] = img
                        
                    matched_ids.add(matched['id'])
                    updated_count += 1
                    logging.info(f"Updated {matched['brand']} {matched['model']}: {old_price} JOD -> {price} JOD")
                    
        except Exception as e:
            logging.error(f"Error scraping PC Circle page {page}: {e}")
            break
            
    if updated_count > 0:
        save_laptops(laptops)
        return True, updated_count
    return False, 0

if __name__ == '__main__':
    logging.info("Running standalone scrape test...")
    success, count = scrape_pc_circle()
    logging.info(f"Scrape completed. Success: {success}, Updated: {count} laptops.")
