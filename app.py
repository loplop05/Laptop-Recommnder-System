import os
import json
import logging
import secrets
from functools import wraps
# pyrefly: ignore [missing-import]
from flask import Flask, render_template, jsonify, request, abort

# Configure logging — do NOT log sensitive user data
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ─── Application factory ──────────────────────────────────────────────────────
app = Flask(__name__, static_url_path='/static', static_folder='static')

# TODO(security): In production, serve over HTTPS via a reverse proxy (nginx/caddy).
# TODO(security): Consider OAuth providers for any future user accounts.
# TODO(security): Implement MFA if user accounts are added in the future.

# ─── Security headers middleware ──────────────────────────────────────────────
@app.after_request
def set_security_headers(response):
    """Attach strict security headers to every response."""
    # Allow images from Unsplash CDN used in laptop database
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
    # Prevent back-button cache leaks for API routes
    if request.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store'
    return response


# ─── Rate limiting (simple in-memory per-IP) ─────────────────────────────────
from collections import defaultdict
import time

_rate_store = defaultdict(lambda: {'count': 0, 'reset_at': 0})
RATE_LIMIT = 30        # requests
RATE_WINDOW = 60       # seconds


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


# ─── Allowed values (strict allow-lists) ─────────────────────────────────────
ALLOWED_USE_CASES = {"gaming", "work", "content_creation", "general"}
ALLOWED_PERFORMANCE = {"entry", "medium", "high"}
ALLOWED_SCREEN_SIZES = {"13-14", "15-16", "17+"}
ALLOWED_PORTABILITIES = {"low", "medium", "high"}
ALLOWED_BRANDS = {"Apple", "ASUS", "Lenovo", "HP", "Dell", "Acer", "MSI", "Razer", "Any"}
BUDGET_MIN = 100
BUDGET_MAX = 10000


# ─── Lazy-load ML pipeline ────────────────────────────────────────────────────
_pipeline = None

def get_pipeline():
    global _pipeline
    if _pipeline is None:
        from ml_pipeline import init_pipeline
        logging.info("Initializing ML pipeline...")
        _pipeline = init_pipeline()
        logging.info("ML pipeline ready.")
    return _pipeline


# ─── Routes ──────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    """Serve the main SPA."""
    # Ensure index.html exists before serving
    if not os.path.exists(os.path.join(app.static_folder, 'index.html')):
        return "Frontend files not found. Please ensure 'static/index.html' exists.", 404
    return app.send_static_file('index.html')


@app.route('/api/laptops', methods=['GET'])
@rate_limited
def get_laptops():
    """Return the current laptop database (specs only, no internal ids)."""
    from data_fetcher import load_laptops
    laptops = load_laptops()
    # Return safe subset of fields
    safe_fields = ['brand', 'model', 'cpu', 'gpu', 'ram', 'storage',
                   'screen_size', 'price_jod', 'use_cases',
                   'performance_level', 'portability', 'image_url', 'purchase_url']
    result = [{k: lap[k] for k in safe_fields if k in lap} for lap in laptops]
    return jsonify({'laptops': result, 'count': len(result)})


@app.route('/api/recommend', methods=['POST'])
@rate_limited
def recommend():
    """
    Accept user preferences and return laptop recommendations.
    All inputs are strictly validated against allow-lists before use.
    """
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 400

    # Reject oversized payloads (>4 KB)
    if request.content_length and request.content_length > 4096:
        return jsonify({'error': 'Request too large'}), 413

    try:
        data = request.get_json(force=False, silent=True)
    except Exception:
        return jsonify({'error': 'Invalid JSON body'}), 400

    if not data or not isinstance(data, dict):
        return jsonify({'error': 'Invalid request body'}), 400

    # ── Strict input validation ──────────────────────────────────────────────

    # 1. Budget — must be an integer within [BUDGET_MIN, BUDGET_MAX]
    raw_budget = data.get('budget')
    try:
        budget = int(raw_budget)
        if not (BUDGET_MIN <= budget <= BUDGET_MAX):
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({'error': f'Budget must be an integer between {BUDGET_MIN} and {BUDGET_MAX} JOD'}), 400

    # 2. Use case — must be in allow-list
    use_case = data.get('use_case', '')
    if use_case not in ALLOWED_USE_CASES:
        return jsonify({'error': 'Invalid use_case value'}), 400

    # 3. Performance — must be in allow-list
    performance = data.get('performance', '')
    if performance not in ALLOWED_PERFORMANCE:
        return jsonify({'error': 'Invalid performance value'}), 400

    # 4. Screen size — must be in allow-list
    screen_size = data.get('screen_size', '')
    if screen_size not in ALLOWED_SCREEN_SIZES:
        return jsonify({'error': 'Invalid screen_size value'}), 400

    # 5. Portability — must be in allow-list
    portability = data.get('portability', '')
    if portability not in ALLOWED_PORTABILITIES:
        return jsonify({'error': 'Invalid portability value'}), 400

    # 6. Brand — must be in allow-list
    brand = data.get('brand', 'Any')
    if brand not in ALLOWED_BRANDS:
        return jsonify({'error': 'Invalid brand value'}), 400

    # ── Build validated preference dict ─────────────────────────────────────
    pref = {
        'budget': budget,
        'use_case': use_case,
        'performance': performance,
        'screen_size': screen_size,
        'portability': portability,
        'brand': brand,
    }

    # ── Run ML pipeline ──────────────────────────────────────────────────────
    try:
        pipeline = get_pipeline()
        result = pipeline.get_recommendations(pref)
    except Exception as e:
        logging.error(f"Recommendation engine error: {e}")
        return jsonify({'error': 'Recommendation engine encountered an error. Please try again.'}), 500

    return jsonify(result)


@app.route('/api/refresh-prices', methods=['POST'])
@rate_limited
def refresh_prices():
    """
    Trigger a background scrape of JOD prices from Jordanian retailers.
    Falls back silently to local cache if scraping fails.
    """
    try:
        from data_fetcher import scrape_all_shops
        success, count = scrape_all_shops()
        if success:
            return jsonify({'message': f'Prices refreshed. {count} laptop(s) updated across all shops.', 'updated': count})
        else:
            return jsonify({'message': 'Prices are up to date (no changes from online sources).', 'updated': 0})
    except Exception as e:
        logging.error(f"Price refresh error: {e}")
        return jsonify({'message': 'Could not refresh prices. Using cached data.', 'updated': 0}), 200


# ─── Entry point ─────────────────────────────────────────────────────────────
if __name__ == '__main__':
    # SECURITY: Listen on localhost only. Never use 0.0.0.0 in production.
    # Pre-warm the pipeline before accepting requests
    get_pipeline()
    app.run(host='127.0.0.1', port=5000, debug=False)
