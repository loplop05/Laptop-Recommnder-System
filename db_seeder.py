import json
import logging
from db_schema import DatabaseManager, LaptopRepository, ShopRepository

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DatabaseSeeder:
    """Handles migrating legacy JSON data into the SQLite database."""

    def __init__(self, db_path=None):
        self.db_path = db_path
        # Known shop metadata for Jordanian retailers
        self.shop_metadata = {
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

    def seed(self, json_path):
        """Perform the seeding process."""
        DatabaseManager.init_db(self.db_path)
        conn = DatabaseManager.get_connection(self.db_path)
        
        try:
            laptop_repo = LaptopRepository(conn)
            shop_repo = ShopRepository(conn)

            with open(json_path, 'r', encoding='utf-8') as f:
                laptops = json.load(f)

            # Register shops
            shop_ids = {}
            for domain, meta in self.shop_metadata.items():
                sid = shop_repo.upsert_shop(**meta)
                shop_ids[domain] = sid

            for lap in laptops:
                laptop_dict = self._transform_laptop_data(lap)
                laptop_repo.upsert_laptop(laptop_dict)

                # Create an offer from the identified shop
                purchase_url = lap.get('purchase_url', '')
                price = lap.get('price_jod', 0)

                matched_shop_id = self._match_shop(purchase_url, shop_ids)
                if matched_shop_id and price:
                    shop_repo.upsert_offer(lap['id'], matched_shop_id, price, purchase_url)

            logging.info(f"Seeded {len(laptops)} laptops from {json_path}")
        finally:
            conn.close()

    def _transform_laptop_data(self, lap):
        """Map legacy JSON fields to new database schema."""
        return {
            'id': lap['id'],
            'brand': lap['brand'],
            'model': lap['model'],
            'cpu': lap.get('cpu'),
            'gpu': lap.get('gpu'),
            'ram': lap.get('ram'),
            'storage_type': 'SSD',
            'storage_size': lap.get('storage', 512),
            'screen_size': lap.get('screen_size'),
            'weight': lap.get('weight'),
            'os': 'macOS' if lap['brand'] == 'Apple' else 'Windows',
            'use_cases': lap.get('use_cases', ['general']),
            'performance_level': lap.get('performance_level', 'medium'),
            'portability': lap.get('portability', 'medium'),
            'image_url': lap.get('image_url'),
        }

    def _match_shop(self, purchase_url, shop_ids):
        """Determine shop ID based on the purchase URL domain."""
        for domain, sid in shop_ids.items():
            if domain in purchase_url:
                return sid
        return None
