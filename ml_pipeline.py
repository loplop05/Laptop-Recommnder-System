import sqlite3
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DB_PATH = 'laptops.db'

class LaptopRecommenderPipeline:
    def __init__(self):
        self.brands_list = ["Apple", "ASUS", "Lenovo", "HP", "Dell", "Acer", "MSI", "Razer"]
        self.use_cases_list = ["gaming", "work", "content_creation", "general"]
        self.screen_sizes_list = ["13-14", "15-16", "17+"]
        self.performance_map = {"entry": 1, "medium": 2, "high": 3}
        self.portability_map = {"low": 1, "medium": 2, "high": 3}

    def get_db_connection(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def _hard_filter_laptops(self, pref, cursor):
        query = """
            SELECT
                l.id, l.brand, l.model, l.cpu, l.gpu, l.ram, l.storage_type, l.storage_size, l.screen_size, l.weight, l.os, l.use_cases, l.performance_level, l.portability, l.image_url,
                GROUP_CONCAT(s.name || '|' || lso.price_jod || '|' || lso.product_url || '|' || s.location || '|' || s.phone || '|' || s.website || '|' || s.map_url) AS offers
            FROM laptops l
            JOIN laptop_shop_offers lso ON l.id = lso.laptop_id
            JOIN shops s ON lso.shop_id = s.id
            WHERE 1=1
        """
        params = []

        # 1. Budget (strict)
        budget = pref.get("budget")
        if budget:
            query += " AND lso.price_jod <= ?"
            params.append(budget)

        # 2. Use Case (Soft filter: prioritize, don't strictly exclude)
        # 3. Screen Size (Soft filter: prioritize)
        # 4. Brand (Soft filter: prioritize)
        # 5. Performance Level (Soft filter: prioritize)
        # For now, keep only budget as a hard filter to ensure results are always returned
        # and rely on weighted scoring for the rest.

        query += " GROUP BY l.id"
        cursor.execute(query, params)
        return cursor.fetchall()

    def _calculate_score(self, pref, laptop):
        score = 0.0

        # 1. Budget efficiency (30%)
        budget = pref.get("budget")
        if budget:
            # Assuming laptop['offers'] contains a list of dicts, take the lowest price
            offers = [o.split('|') for o in laptop['offers'].split(',')] if laptop['offers'] else []
            prices = [float(o[1]) for o in offers]
            price = min(prices) if prices else budget + 1 # If no offers, make it expensive

            if price <= budget:
                # Closer to budget is better, but not over
                score += (price / budget) * 0.30 # Lower ratio is better, so invert
            else:
                score -= 1.0 # Heavy penalty for being over budget

        # 2. Use-case match depth (15%)
        req_use_case = pref.get("use_case")
        laptop_use_cases = json.loads(laptop["use_cases"]) if laptop["use_cases"] else []
        if req_use_case in laptop_use_cases:
            score += 0.15

        # 3. Performance match (20%)
        req_perf_val = self.performance_map.get(pref.get("performance"), 1)
        lap_perf_val = self.performance_map.get(laptop["performance_level"], 1)
        if lap_perf_val >= req_perf_val:
            score += 0.20 * (lap_perf_val / 3.0) # Higher performance gets more score

        # 4. Portability match (15%)
        req_port_val = self.portability_map.get(pref.get("portability"), 1)
        lap_port_val = self.portability_map.get(laptop["portability"], 1)
        if lap_port_val >= req_port_val:
            score += 0.15 * (lap_port_val / 3.0)

        # 5. Screen size exact match bonus (10%)
        req_screen_size = pref.get("screen_size")
        lap_screen_size = laptop["screen_size"]
        if req_screen_size == "13-14" and 13.0 <= lap_screen_size <= 14.9:
            score += 0.10
        elif req_screen_size == "15-16" and 15.0 <= lap_screen_size <= 16.9:
            score += 0.10
        elif req_screen_size == "17+" and lap_screen_size >= 17.0:
            score += 0.10

        # 6. Brand preference bonus (10%)
        brand_pref = pref.get("brand")
        if brand_pref != "Any" and brand_pref == laptop["brand"]:
            score += 0.10

        return score

    def _generate_reasoning(self, pref, laptop):
        reasons = []

        # Budget
        offers = [o.split('|') for o in laptop['offers'].split(',')] if laptop['offers'] else []
        prices = [float(o[1]) for o in offers]
        min_price = min(prices) if prices else "N/A"
        budget = pref.get("budget")
        if budget and min_price != "N/A" and min_price <= budget:
            reasons.append(f"It fits your budget of {budget} JOD, with prices starting from {min_price} JOD.")
        elif budget and min_price != "N/A" and min_price > budget:
            reasons.append(f"While slightly above your budget of {budget} JOD, its features justify the price of {min_price} JOD.")

        # Use Case
        req_use_case = pref.get("use_case")
        laptop_use_cases = json.loads(laptop["use_cases"]) if laptop["use_cases"] else []
        if req_use_case in laptop_use_cases:
            reasons.append(f"It's ideal for your primary use case: {req_use_case.replace('_', ' ').title()}.")

        # Performance
        req_perf = pref.get("performance")
        lap_perf = laptop["performance_level"]
        if self.performance_map.get(lap_perf, 1) >= self.performance_map.get(req_perf, 1):
            reasons.append(f"Its {lap_perf.title()} performance level meets your requirements.")

        # Screen Size
        req_screen = pref.get("screen_size")
        lap_screen = laptop["screen_size"]
        reasons.append(f"With a {lap_screen}\" screen, it aligns with your {req_screen} preference.")

        # Portability
        req_port = pref.get("portability")
        lap_port = laptop["portability"]
        if self.portability_map.get(lap_port, 1) >= self.portability_map.get(req_port, 1):
            reasons.append(f"Its {lap_port.title()} portability is suitable for your needs.")

        # Brand
        brand_pref = pref.get("brand")
        if brand_pref != "Any" and brand_pref == laptop["brand"]:
            reasons.append(f"It's a {laptop['brand']} laptop, matching your brand preference.")

        return " ".join(reasons) if reasons else "A great match based on your preferences."

    def get_recommendations(self, pref):
        conn = self.get_db_connection()
        cursor = conn.cursor()

        filtered_laptops_rows = self._hard_filter_laptops(pref, cursor)
        
        laptops_with_scores = []
        for row in filtered_laptops_rows:
            laptop = dict(row)
            score = self._calculate_score(pref, laptop)
            laptops_with_scores.append({"laptop": laptop, "score": score})

        # Sort by score (descending)
        laptops_with_scores.sort(key=lambda x: x["score"], reverse=True)

        recommendations = []
        for item in laptops_with_scores[:5]: # Top 5 recommendations
            laptop_data = item["laptop"]
            laptop_data["reasoning"] = self._generate_reasoning(pref, laptop_data)
            
            # Parse offers string back into a structured list
            offers_str = laptop_data.pop('offers') # Remove raw offers string
            parsed_offers = []
            if offers_str:
                for offer_item in offers_str.split(','):
                    parts = offer_item.split('|')
                    if len(parts) == 7:
                        parsed_offers.append({
                            "shop_name": parts[0],
                            "price_jod": float(parts[1]),
                            "product_url": parts[2],
                            "shop_location": parts[3],
                            "shop_phone": parts[4],
                            "shop_website": parts[5],
                            "shop_map_url": parts[6]
                        })
            laptop_data["offers"] = parsed_offers

            recommendations.append(laptop_data)

        conn.close()
        return {"recommendations": recommendations}

def init_pipeline():
    return LaptopRecommenderPipeline()
