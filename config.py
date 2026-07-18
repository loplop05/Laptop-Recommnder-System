import os

# Database Configuration
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'laptops.db')
CACHE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'laptops_cache.json')

# Rate Limiting
RATE_LIMIT = 30
RATE_WINDOW = 60

# Budget Constraints
BUDGET_MIN = 100
BUDGET_MAX = 10000

# Allowed Values (Allow-lists)
ALLOWED_USE_CASES = {"gaming", "work", "content_creation", "general"}
ALLOWED_PERFORMANCE = {"entry", "medium", "high"}
ALLOWED_SCREEN_SIZES = {"13-14", "15-16", "17+"}
ALLOWED_PORTABILITIES = {"low", "medium", "high"}
ALLOWED_BRANDS = {"Apple", "ASUS", "Lenovo", "HP", "Dell", "Acer", "MSI", "Razer", "Any"}

# Order and Ranges
PERF_ORDER = {'entry': 1, 'medium': 2, 'high': 3}
PORTABILITY_ORDER = {'low': 1, 'medium': 2, 'high': 3}
SCREEN_RANGES = {
    '13-14': (0, 14.5),
    '15-16': (14.5, 16.5),
    '17+':   (16.5, 100),
}

# Scoring Weights
SCORING_WEIGHTS = {
    'budget_efficiency': 0.30,
    'use_case':          0.15,
    'performance':       0.20,
    'portability':       0.15,
    'screen_size':       0.10,
    'brand':             0.10,
}

# Use Case Labels for Reasoning
USE_CASE_LABELS = {
    'gaming': 'gaming',
    'work': 'professional work',
    'content_creation': 'content creation',
    'general': 'everyday use',
}
