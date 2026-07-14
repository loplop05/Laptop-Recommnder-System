# Laptop Recommender System

A modern, AI-powered laptop recommendation engine that combines smart filtering with weighted scoring to help users find their perfect laptop based on budget, use case, performance needs, and preferences.

## 🎯 Overview

The Laptop Recommender System uses a **hard-filter → weighted-score → reason** pipeline to deliver accurate, personalized laptop recommendations. User constraints (budget, use case, screen size, brand, performance level) are enforced as strict SQL filters — a gaming laptop request never returns an office laptop, and a stated budget is never exceeded. The system features a sleek web frontend with real-time filtering and a robust Flask backend serving recommendations from a SQLite database of 24+ laptops across 3 Jordanian retailers.

## 🏗️ Architecture

```
┌─────────────┐    ┌──────────────┐    ┌────────────────┐
│ refresh_data │───▶│  SQLite DB   │───▶│  Flask API     │
│    .py       │    │ (laptops.db) │    │  (app.py)      │
│ (scraper/ETL)│    └──────────────┘    └────────┬───────┘
└─────────────┘                                  │
                                      ┌──────────▼───────┐
                                      │  ml_pipeline.py  │
                                      │  Hard Filter →   │
                                      │  Score/Rank →    │
                                      │  Reason          │
                                      └──────────────────┘
```

### Backend (Python/Flask)
- **Framework:** Flask 3.x
- **Database:** SQLite (laptops, shops, laptop_shop_offers)
- **ML Pipeline:** Hard-filter SQL queries → weighted multi-criteria scoring → deterministic reasoning
- **Data Sources:** 3 Jordanian laptop retailers (PC Circle, City Center, GTS)
- **API Endpoints:**
  - `GET /api/laptops` — Retrieve all available laptops with shop offers
  - `POST /api/recommend` — Get personalized recommendations
  - `POST /api/refresh-prices` — Update prices from retailers

### Frontend (HTML/CSS/JS)
- **Styling:** Vanilla CSS with Plus Jakarta Sans typography
- **Design:** Clean, modern cards with shop availability sections
- **Features:** 7-step wizard, real-time budget slider, shop comparison per recommendation

---

## 📊 Data Refresh Workflow

The system **does not scrape live** on every user request. Instead:

### How It Works

1. **`laptops_cache.json`** — Curated seed data with 24 laptops (specs, use cases, performance levels). This is the source of truth for laptop specifications.
2. **`refresh_data.py`** — ETL script that:
   - Seeds the SQLite database from `laptops_cache.json` (one-time)
   - Scrapes all 3 shop websites for current prices
   - Matches scraped products to known laptops via keyword scoring
   - Updates the `laptop_shop_offers` table with latest prices
3. **`laptops.db`** — SQLite database (generated, gitignored)

### Running the Refresh

```bash
# Full refresh: seed from JSON + scrape all shops
python refresh_data.py

# Seed only (no scraping) — useful for first setup
python refresh_data.py --seed

# Scrape only (assumes DB already seeded)
python refresh_data.py --scrape
```

### Scheduling Periodic Refreshes

**Linux/macOS cron** (daily at 3 AM):
```bash
0 3 * * * cd /path/to/Laptop-Recommnder-System && python refresh_data.py
```

**Windows Task Scheduler:**
Create a task that runs `python refresh_data.py` in the project directory.

### First-Time Auto-Seed

If `laptops.db` doesn't exist when the app starts, it will auto-seed from `laptops_cache.json` on first API request.

---

## 🗄️ Database Schema

```sql
-- Canonical laptop records (deduplicated by brand + model)
CREATE TABLE laptops (
    id              TEXT PRIMARY KEY,
    brand           TEXT NOT NULL,
    model           TEXT NOT NULL,
    cpu             TEXT,
    gpu             TEXT,
    ram             INTEGER,
    storage_type    TEXT DEFAULT 'SSD',
    storage_size    INTEGER,
    screen_size     REAL,
    weight          REAL,
    os              TEXT,
    use_cases       TEXT,            -- JSON array: '["gaming","work"]'
    performance_level TEXT,          -- 'entry', 'medium', 'high'
    portability     TEXT,            -- 'low', 'medium', 'high'
    image_url       TEXT,
    last_updated    TEXT             -- ISO 8601 timestamp
);

-- Shop directory with location metadata
CREATE TABLE shops (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    name     TEXT UNIQUE NOT NULL,
    location TEXT,                   -- Physical address
    phone    TEXT,                   -- Contact phone number
    website  TEXT,                   -- Shop website URL
    map_url  TEXT                    -- Google Maps link
);

-- Many-to-many: which shops carry which laptop at what price
CREATE TABLE laptop_shop_offers (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    laptop_id    TEXT    REFERENCES laptops(id),
    shop_id      INTEGER REFERENCES shops(id),
    price_jod    REAL,               -- Price in Jordanian Dinars
    product_url  TEXT,               -- Direct product link
    last_scraped TEXT,               -- ISO 8601 timestamp
    UNIQUE(laptop_id, shop_id)
);
```

### Deduplication Strategy
- Same laptop model across multiple shops → one `laptops` row, multiple `laptop_shop_offers` rows
- Each recommendation shows all shops carrying that laptop with prices, locations, and contact info

---

## 🎯 Recommendation Pipeline

### 1. Hard Filtering (SQL WHERE — never violated)
| Constraint | Rule |
|-----------|------|
| **Budget** | `best_price <= budget` — never exceeded |
| **Use case** | Laptop's `use_cases` array must contain the requested use case |
| **Screen size** | Laptop must fall in the requested range (13-14", 15-16", 17+") |
| **Brand** | Exact match when specified (ignored when "Any") |
| **Performance** | Laptop performance level must meet or exceed requested level |

### 2. Weighted Scoring (0–100 scale)
| Factor | Weight | Description |
|--------|--------|-------------|
| Budget efficiency | 30% | Best when price uses 70–95% of budget |
| Performance match | 20% | Exact match = 100%, exceeds = 85% |
| Use case depth | 15% | Specialist laptops score higher |
| Portability | 15% | Exact match preferred |
| Screen size | 10% | In-range = 100% |
| Brand | 10% | Match bonus when specified |

### 3. Reasoning Generation
For each top-3 recommendation, a specific human-readable reason is generated from actual matched attributes:

> "It's 150 JOD under your budget, the RTX 4060 8GB handles gaming workloads with ease, 16GB RAM ensures smooth multitasking while gaming, and 512GB SSD provides good storage capacity."

No LLM dependency — deterministic, fast, and accurate.

---

## 📊 Accuracy Evaluation

### Methodology
- **50 labeled test cases** covering gaming, work, content creation, and general use with various budget/brand/screen constraints
- **Hard Constraint Satisfaction Rate**: Does the top recommendation satisfy ALL stated hard constraints?
- **Match Score**: Average weighted scoring of top-1 recommendations

### Results

```
======================================================================
  Hard Constraint Satisfaction: 46/50 (92.0%)
  Average Match Score (top-1):  94.2%
  Empty results (unexpected):   1
  Total violations found:       3

  ✅ PASS — Accuracy 92.0% meets the ≥85% target

  Violation Breakdown:
    Budget violations:      0
    Use case mismatches:    0
    Brand mismatches:       1
    Performance below req:  2
======================================================================
```

### Key Findings
- **Zero budget violations** — the hard filter guarantees no laptop ever exceeds the user's stated budget
- **Zero use-case mismatches** — a gaming request never returns a work-only laptop
- **3 edge-case violations**:
  - 1 brand mismatch (Dell content creation at 1800 JOD — only Dell laptop matching is 1850 JOD, so the relaxed filter picks ASUS instead)
  - 2 performance below requested (limited inventory at lower budgets)
  - 1 empty result (250 JOD budget with general+entry — the cheapest laptop in DB is 280 JOD)

### Running the Evaluation

```bash
python evaluate.py           # Summary only
python evaluate.py --verbose # Per-case results
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+

### Setup

1. **Bootstrap the environment:**
   ```bash
   cd Laptop-Recommnder-System
   python bootstrap.py
   ```

2. **Configure environment variables:**
   ```env
   # .env (optional — no API key needed for recommendations)
   OPENAI_API_KEY=sk-proj-...   # Only if you want the legacy LLM path
   ```

3. **Seed the database:**
   ```bash
   python refresh_data.py --seed
   ```

4. **Run the Flask server:**
   ```bash
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate

   python app.py
   ```
   The app will be available at `http://127.0.0.1:5000`

---

## 🔧 API Reference

### GET /api/laptops
Returns all laptops with shop offers.

### POST /api/recommend
Get personalized recommendations.

**Request:**
```json
{
  "budget": 800,
  "use_case": "gaming",
  "performance": "high",
  "screen_size": "15-16",
  "portability": "medium",
  "brand": "Any"
}
```

**Response:**
```json
{
  "recommendations": [
    {
      "brand": "ASUS",
      "model": "TUF Gaming A15",
      "price_jod": 780,
      "reasoning": "It's 20 JOD under your budget, the RTX 4060 8GB handles gaming workloads with ease...",
      "match_score": 89,
      "shop_offers": [
        {
          "shop_name": "City Center",
          "price_jod": 780,
          "product_url": "https://...",
          "shop_location": "King Abdullah II Street, Amman, Jordan",
          "shop_phone": "+962-6-500-1234",
          "shop_map_url": "https://maps.google.com/?q=..."
        }
      ]
    }
  ],
  "winning_model": "hard_filter_weighted_score",
  "winning_model_label": "Smart Filter + Weighted Scoring",
  "filter_stats": {
    "total_in_db": 24,
    "after_filter": 3
  }
}
```

### POST /api/refresh-prices
Trigger a scrape of all shops into the SQLite DB.

---

## 🔐 Security Features

- **Input Validation:** Strict allow-lists for all user inputs
- **Rate Limiting:** 30 requests per 60 seconds per IP
- **Security Headers:** CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy
- **Payload Size Limits:** 4KB max request size
- **HTTPS Ready:** Designed for reverse proxy deployment

---

## 📁 Project Structure

```
Laptop-Recommnder-System/
├── app.py                 # Flask application with API routes
├── ml_pipeline.py         # Hard-filter → weighted-score → reasoning pipeline
├── db_schema.py           # SQLite schema, helpers, and seeding
├── refresh_data.py        # ETL script: scrape → normalize → insert into DB
├── evaluate.py            # Accuracy evaluation (50 test cases)
├── data_fetcher.py        # Legacy scraper functions (still used by refresh_data)
├── laptops_cache.json     # Seed data (24 curated laptops)
├── laptops.db             # SQLite database (generated, gitignored)
├── requirements.txt       # Python dependencies
├── static/
│   ├── index.html         # Frontend SPA
│   ├── css/style.css      # Styles including shop offer cards
│   └── js/main.js         # Frontend logic with shop availability display
└── tests/                 # Test files
```

---

## 📝 License

This project is open source and available under the MIT License.

---

**Built with ❤️ for laptop enthusiasts and decision-makers in Jordan**
