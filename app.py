import os
import logging
from functools import wraps
from flask import Flask, jsonify, request
from dotenv import load_dotenv

from config import (
    RATE_LIMIT, RATE_WINDOW, BUDGET_MIN, BUDGET_MAX,
    ALLOWED_USE_CASES, ALLOWED_PERFORMANCE, ALLOWED_SCREEN_SIZES,
    ALLOWED_PORTABILITIES, ALLOWED_BRANDS, DB_PATH, CACHE_PATH
)
from db_schema import DatabaseManager, LaptopRepository, seed_from_json

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ─── Application factory ──────────────────────────────────────────────────────
app = Flask(__name__, static_url_path='/static', static_folder='static')

# ─── Security headers middleware ──────────────────────────────────────────────
@app.after_request
def set_security_headers(response):
    """Attach strict security headers to every response."""
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' https://fonts.googleapis.com 'unsafe-inline'; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' https://images.unsplash.com https://pccircle.com https://citycenter.jo https://gts.jo https://os-jo.com data:; "
        "connect-src 'self'; "
        "object-src 'none'; "
        "frame-ancestors 'none';"
    )
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
    if request.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store'
    return response

# ─── Rate limiting (simple in-memory per-IP) ─────────────────────────────────
from collections import defaultdict
import time

_rate_store = defaultdict(lambda: {'count': 0, 'reset_at': 0})

def rate_limited(f):
    """Decorator: simple per-IP sliding-window rate limiter."""
    @wraps(f)
    def decorated(*args, **kwargs):
        ip = request.remote_addr or '0.0.0.0'
        now = time.time()
        entry = _rate_store[ip]
        if now > entry['reset_at']:
            entry['count'] = 0
            entry['reset_at'] = now + RATE_WINDOW
        entry['count'] += 1
        if entry['count'] > RATE_LIMIT:
            logging.warning(f"Rate limit exceeded for IP: {ip}")
            return jsonify({'error': 'Too many requests. Please try again later.'}), 429
        return f(*args, **kwargs)
    return decorated

# ─── Lazy-load ML pipeline ────────────────────────────────────────────────────
_pipeline = None

def get_pipeline():
    global _pipeline
    if _pipeline is None:
        from ml_pipeline import init_pipeline
        _pipeline = init_pipeline()
    return _pipeline

# ─── Request Validation ──────────────────────────────────────────────────────
class PreferenceValidator:
    @staticmethod
    def validate(data):
        """Validate recommendation preferences."""
        if not data or not isinstance(data, dict):
            return None, "Invalid request body"

        try:
            budget = int(data.get('budget'))
            if not (BUDGET_MIN <= budget <= BUDGET_MAX):
                raise ValueError
        except (TypeError, ValueError):
            return None, f"Budget must be between {BUDGET_MIN} and {BUDGET_MAX} JOD"

        # Normalize brand casing (e.g. 'Asus' -> 'ASUS', 'apple' -> 'Apple')
        raw_brand = str(data.get('brand', 'Any')).strip()
        brand_map = {b.lower(): b for b in ALLOWED_BRANDS}
        brand = brand_map.get(raw_brand.lower(), raw_brand)

        validations = [
            ('use_case', ALLOWED_USE_CASES),
            ('performance', ALLOWED_PERFORMANCE),
            ('screen_size', ALLOWED_SCREEN_SIZES),
            ('portability', ALLOWED_PORTABILITIES),
        ]

        for field, allowed in validations:
            val = data.get(field)
            if val not in allowed:
                return None, f"Invalid {field} value"

        if brand not in ALLOWED_BRANDS:
            return None, "Invalid brand value"

        return {
            'budget': budget,
            'use_case': data.get('use_case'),
            'performance': data.get('performance'),
            'screen_size': data.get('screen_size'),
            'portability': data.get('portability'),
            'brand': brand,
        }, None

# ─── Routes ──────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    """Serve the landing page."""
    if not os.path.exists(os.path.join(app.static_folder, 'index.html')):
        return "Frontend files not found.", 404
    return app.send_static_file('index.html')

@app.route('/quiz')
def quiz():
    """Serve the quiz wizard page."""
    if not os.path.exists(os.path.join(app.static_folder, 'quiz.html')):
        return "Quiz file not found.", 404
    return app.send_static_file('quiz.html')

@app.route('/results')
def results():
    """Serve the recommendations results page."""
    if not os.path.exists(os.path.join(app.static_folder, 'results.html')):
        return "Results file not found.", 404
    return app.send_static_file('results.html')

@app.route('/api/laptops', methods=['GET'])
@rate_limited
def get_laptops():
    """Return the current laptop database."""
    if not os.path.exists(DB_PATH) and os.path.exists(CACHE_PATH):
        seed_from_json(CACHE_PATH)
    
    conn = DatabaseManager.get_connection()
    try:
        repo = LaptopRepository(conn)
        laptops = repo.get_all_with_best_price()
        
        safe_fields = ['brand', 'model', 'cpu', 'gpu', 'ram', 'storage_size',
                       'screen_size', 'price_jod', 'use_cases',
                       'performance_level', 'portability', 'image_url',
                       'shop_offers']
        result = [{k: lap[k] for k in safe_fields if k in lap} for lap in laptops]
        return jsonify({'laptops': result, 'count': len(result)})
    finally:
        conn.close()

@app.route('/api/recommend', methods=['POST'])
@rate_limited
def recommend():
    """Accept user preferences and return laptop recommendations."""
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 400
    if request.content_length and request.content_length > 4096:
        return jsonify({'error': 'Request too large'}), 413

    data = request.get_json(silent=True)
    pref, error = PreferenceValidator.validate(data)
    if error:
        return jsonify({'error': error}), 400

    try:
        pipeline = get_pipeline()
        result = pipeline.get_recommendations(pref)
        return jsonify(result)
    except Exception as e:
        logging.error(f"Recommendation engine error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/refresh-prices', methods=['POST'])
@rate_limited
def refresh_prices():
    """Trigger a scrape of JOD prices."""
    try:
        from refresh_data import scrape_all_shops
        count = scrape_all_shops()
        return jsonify({'message': f'Prices refreshed. {count} offer(s) updated.', 'updated': count})
    except Exception as e:
        logging.error(f"Price refresh error: {e}")
        return jsonify({'message': 'Could not refresh prices. Using cached data.', 'updated': 0}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = '0.0.0.0' if os.environ.get('PORT') else '127.0.0.1'
    app.run(host=host, port=port, debug=False)
