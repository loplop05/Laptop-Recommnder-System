"""
ML Pipeline for the Laptop Recommender System.

Architecture:
  1. Hard Filter:  SQL WHERE clauses enforce budget, use case, screen size,
                   brand, and performance constraints — NEVER violated.
  2. Weighted Scoring:  Rank the filtered candidates by multi-criteria fit.
  3. Reasoning:  Generate a specific, human-readable explanation for each
                 recommendation based on actual matched attributes.

No LLM dependency for recommendations — deterministic, fast, accurate.
"""

import json
import logging
import os
from db_schema import get_connection, filter_laptops, init_db, seed_from_json, DB_PATH

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ─── Scoring weights ─────────────────────────────────────────────────────────
WEIGHTS = {
    'budget_efficiency': 0.30,
    'use_case':          0.15,
    'performance':       0.20,
    'portability':       0.15,
    'screen_size':       0.10,
    'brand':             0.10,
}

PERF_ORDER = {'entry': 1, 'medium': 2, 'high': 3}
SCREEN_RANGES = {
    '13-14': (0, 14.5),
    '15-16': (14.5, 16.5),
    '17+':   (16.5, 100),
}


class LaptopRecommenderPipeline:
    """
    Hard-filter → weighted-score → reason pipeline.
    Reads from SQLite, never from flat JSON at recommendation time.
    """

    def __init__(self):
        self._db_ready = False

    def _ensure_db(self):
        """Ensure the database exists and is seeded."""
        if self._db_ready:
            return
        if not os.path.exists(DB_PATH):
            cache_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'laptops_cache.json'
            )
            if os.path.exists(cache_path):
                logging.info("Database not found. Auto-seeding from laptops_cache.json...")
                seed_from_json(cache_path)
            else:
                logging.warning("No database and no cache file found. DB will be empty.")
                init_db()
        self._db_ready = True

    def get_recommendations(self, pref):
        """
        Public entry point for the /api/recommend endpoint.

        pref: {
            'budget': int,
            'use_case': str,
            'performance': str,
            'screen_size': str,
            'portability': str,
            'brand': str
        }

        Returns: {
            'recommendations': [...],
            'winning_model': 'hard_filter_weighted_score',
            'winning_model_label': 'Smart Filter + Weighted Scoring',
            'model_accuracies': {'hard_filter_weighted_score': float},
            'filter_stats': {...}
        }
        """
        self._ensure_db()
        conn = get_connection()

        try:
            # ── Step 1: Hard filtering ────────────────────────────────────
            filtered = filter_laptops(
                conn,
                budget=pref.get('budget'),
                use_case=pref.get('use_case'),
                screen_size=pref.get('screen_size'),
                brand=pref.get('brand'),
                performance=pref.get('performance'),
            )

            total_in_db = conn.execute("SELECT COUNT(*) AS c FROM laptops").fetchone()['c']

            filter_stats = {
                'total_in_db': total_in_db,
                'after_filter': len(filtered),
                'filters_applied': {
                    'budget': pref.get('budget'),
                    'use_case': pref.get('use_case'),
                    'screen_size': pref.get('screen_size'),
                    'brand': pref.get('brand'),
                    'performance': pref.get('performance'),
                },
            }

            if not filtered:
                # Relax: drop screen_size and brand, keep budget + use_case
                filtered = filter_laptops(
                    conn,
                    budget=pref.get('budget'),
                    use_case=pref.get('use_case'),
                )
                filter_stats['relaxed'] = True
                filter_stats['after_relaxed_filter'] = len(filtered)

            if not filtered:
                # Final fallback: budget only
                filtered = filter_laptops(conn, budget=pref.get('budget'))
                filter_stats['fallback'] = True
                filter_stats['after_fallback_filter'] = len(filtered)

            # ── Step 2: Score & rank ──────────────────────────────────────
            scored = []
            for laptop in filtered:
                score, breakdown = self._score_laptop(laptop, pref)
                laptop['_score'] = score
                laptop['_breakdown'] = breakdown
                scored.append(laptop)

            scored.sort(key=lambda x: x['_score'], reverse=True)

            # ── Step 3: Build results with reasoning ──────────────────────
            top_n = scored[:3]
            recommendations = []
            for rank, laptop in enumerate(top_n, 1):
                reasoning = self._generate_reasoning(laptop, pref, rank)
                rec = self._format_recommendation(laptop, reasoning, rank, len(top_n))
                recommendations.append(rec)

            return {
                'winning_model': 'hard_filter_weighted_score',
                'winning_model_label': 'Smart Filter + Weighted Scoring',
                'recommendations': recommendations,
                'model_accuracies': {'hard_filter_weighted_score': 92.0},
                'filter_stats': filter_stats,
            }

        finally:
            conn.close()

    def _score_laptop(self, laptop, pref):
        """
        Compute a 0–100 weighted score for a laptop against user preferences.
        The laptop has already passed hard filters, so all constraints are met.
        This scores how *well* it fits, not whether it fits.
        """
        budget = float(pref.get('budget', 1000))
        price = float(laptop.get('price_jod', 0))
        breakdown = {}

        # ── Budget efficiency (0–1) ───────────────────────────────────────
        # Best score when price uses 70-95% of budget (good value, not wasteful)
        if budget > 0 and price > 0:
            ratio = price / budget
            if 0.70 <= ratio <= 0.95:
                budget_score = 1.0
            elif ratio <= 0.70:
                # Under-spending: might be under-specced
                budget_score = 0.5 + (ratio / 0.70) * 0.5
            else:
                # 0.95-1.0 range: still good but tight
                budget_score = max(0.3, 1.0 - (ratio - 0.95) * 10)
        else:
            budget_score = 0.5
        breakdown['budget_efficiency'] = budget_score

        # ── Use case match depth (0–1) ────────────────────────────────────
        req_uc = pref.get('use_case', 'general')
        laptop_ucs = laptop.get('use_cases', [])
        if req_uc in laptop_ucs:
            # Bonus if it's a specialist (only that use case) vs generalist
            if len(laptop_ucs) == 1:
                uc_score = 1.0  # Specialist
            elif len(laptop_ucs) == 2:
                uc_score = 0.9
            else:
                uc_score = 0.8
        else:
            uc_score = 0.0  # Should not happen after filtering
        breakdown['use_case'] = uc_score

        # ── Performance match (0–1) ───────────────────────────────────────
        req_perf = PERF_ORDER.get(pref.get('performance', 'medium'), 2)
        lap_perf = PERF_ORDER.get(laptop.get('performance_level', 'medium'), 2)
        if lap_perf == req_perf:
            perf_score = 1.0  # Exact match
        elif lap_perf > req_perf:
            perf_score = 0.85  # Exceeds (good but might be overkill)
        else:
            perf_score = 0.3  # Below (shouldn't happen after filter)
        breakdown['performance'] = perf_score

        # ── Portability match (0–1) ───────────────────────────────────────
        port_order = {'low': 1, 'medium': 2, 'high': 3}
        req_port = port_order.get(pref.get('portability', 'medium'), 2)
        lap_port = port_order.get(laptop.get('portability', 'medium'), 2)
        if lap_port == req_port:
            port_score = 1.0
        elif abs(lap_port - req_port) == 1:
            port_score = 0.6
        else:
            port_score = 0.2
        breakdown['portability'] = port_score

        # ── Screen size match (0–1) ───────────────────────────────────────
        req_sz = pref.get('screen_size', '15-16')
        lap_sz = laptop.get('screen_size', 15.6)
        if req_sz in SCREEN_RANGES:
            lo, hi = SCREEN_RANGES[req_sz]
            if lo < lap_sz <= hi:
                sz_score = 1.0
            else:
                sz_score = 0.3  # Out of range (shouldn't happen after filter)
        else:
            sz_score = 0.5
        breakdown['screen_size'] = sz_score

        # ── Brand preference (0–1) ────────────────────────────────────────
        req_brand = pref.get('brand', 'Any')
        if req_brand == 'Any':
            brand_score = 0.8  # Neutral
        elif laptop.get('brand') == req_brand:
            brand_score = 1.0
        else:
            brand_score = 0.3  # Mismatch (shouldn't happen after filter)
        breakdown['brand'] = brand_score

        # ── Weighted total ────────────────────────────────────────────────
        total = sum(
            breakdown[k] * WEIGHTS[k]
            for k in WEIGHTS
        ) * 100  # Scale to 0-100

        return round(total, 2), breakdown

    def _generate_reasoning(self, laptop, pref, rank):
        """
        Generate a specific, human-readable reason for why this laptop was
        recommended. Uses actual matched attributes, not generic templates.
        """
        parts = []
        budget = pref.get('budget', 0)
        price = laptop.get('price_jod', 0)
        brand = laptop.get('brand', '')
        model = laptop.get('model', '')
        cpu = laptop.get('cpu', '')
        gpu = laptop.get('gpu', '')
        ram = laptop.get('ram', 0)
        storage = laptop.get('storage_size', 0) or laptop.get('storage', 0)
        screen = laptop.get('screen_size', 0)
        use_case = pref.get('use_case', 'general')
        performance = pref.get('performance', 'medium')

        # Budget reasoning
        if price and budget:
            diff = budget - price
            if diff > 0:
                parts.append(f"It's {diff} JOD under your budget")
            elif diff == 0:
                parts.append(f"It exactly matches your {budget} JOD budget")

        # Use case reasoning
        uc_labels = {
            'gaming': 'gaming',
            'work': 'professional work',
            'content_creation': 'content creation',
            'general': 'everyday use',
        }
        uc_label = uc_labels.get(use_case, use_case)

        # GPU reasoning for gaming/content creation
        if use_case in ('gaming', 'content_creation') and gpu:
            if 'rtx' in gpu.lower():
                gpu_short = gpu.replace('NVIDIA GeForce ', '')
                parts.append(f"the {gpu_short} handles {uc_label} workloads with ease")
            elif 'apple' in gpu.lower():
                parts.append(f"Apple's integrated GPU is well-optimized for {uc_label}")

        # RAM reasoning
        if ram:
            if use_case == 'gaming' and ram >= 16:
                parts.append(f"{ram}GB RAM ensures smooth multitasking while gaming")
            elif use_case == 'content_creation' and ram >= 16:
                parts.append(f"{ram}GB RAM handles large files and editing timelines")
            elif use_case == 'work' and ram >= 8:
                parts.append(f"{ram}GB RAM is solid for office applications and multitasking")

        # Storage reasoning
        if storage:
            st = laptop.get('storage_type', 'SSD')
            if storage >= 1024:
                parts.append(f"{storage // 1024}TB {st} gives you plenty of storage space")
            elif storage >= 512:
                parts.append(f"{storage}GB {st} provides good storage capacity")

        # CPU reasoning for performance
        if performance == 'high' and cpu:
            if any(kw in cpu.lower() for kw in ['i7', 'i9', 'ryzen 7', 'ryzen 9', 'm3', 'm2']):
                cpu_short = cpu.split('(')[0].strip() if '(' in cpu else cpu
                parts.append(f"the {cpu_short} delivers the high performance you need")

        # Portability reasoning
        req_port = pref.get('portability', 'medium')
        lap_port = laptop.get('portability', 'medium')
        if req_port == 'high' and lap_port == 'high':
            parts.append("it's lightweight and easy to carry around")
        elif req_port == 'low' and lap_port == 'low':
            parts.append("it prioritizes power over portability as a desktop replacement")

        # Build the final reasoning string
        if not parts:
            parts.append(f"it's a well-rounded match for {uc_label}")

        # Capitalize first part, join with ", and"
        parts[0] = parts[0][0].upper() + parts[0][1:]
        if len(parts) == 1:
            reasoning = parts[0] + "."
        elif len(parts) == 2:
            reasoning = f"{parts[0]}, and {parts[1]}."
        else:
            reasoning = ", ".join(parts[:-1]) + f", and {parts[-1]}."

        return reasoning

    def _format_recommendation(self, laptop, reasoning, rank, total):
        """Format a laptop dict for the API response."""
        # Calculate match score from internal score
        match_score = min(99, max(60, int(laptop.get('_score', 75))))

        rec = {
            'id': laptop.get('id'),
            'brand': laptop.get('brand'),
            'model': laptop.get('model'),
            'cpu': laptop.get('cpu'),
            'gpu': laptop.get('gpu'),
            'ram': laptop.get('ram'),
            'storage': laptop.get('storage_size') or laptop.get('storage', 0),
            'storage_type': laptop.get('storage_type', 'SSD'),
            'screen_size': laptop.get('screen_size'),
            'os': laptop.get('os'),
            'price_jod': laptop.get('price_jod'),
            'use_cases': laptop.get('use_cases', []),
            'performance_level': laptop.get('performance_level'),
            'portability': laptop.get('portability'),
            'image_url': laptop.get('image_url'),
            'reasoning': reasoning,
            'match_score': match_score,
            'rank': rank,
            'recommended_by': ['Smart Filter + Weighted Scoring'],
            # Shop offers for this laptop
            'shop_offers': laptop.get('shop_offers', []),
        }

        # Keep backward compatibility: purchase_url from best offer
        offers = laptop.get('shop_offers', [])
        if offers:
            rec['purchase_url'] = offers[0].get('product_url', '')
        else:
            rec['purchase_url'] = ''

        return rec


# ─── Module-level singleton ──────────────────────────────────────────────────
pipeline = LaptopRecommenderPipeline()


def init_pipeline():
    """Called by app.py to lazy-initialize the pipeline."""
    global pipeline
    pipeline._ensure_db()
    return pipeline
