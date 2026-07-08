# Laptop Recommender System

A modern, AI-powered laptop recommendation engine that combines machine learning with an elegant web interface to help users find their perfect laptop based on budget, use case, performance needs, and preferences.

## 🎯 Overview

The Laptop Recommender System uses a hybrid machine learning approach combining content-based filtering, collaborative filtering, and KNN classification to deliver personalized laptop recommendations. The system features a sleek React-based frontend with real-time filtering and a robust Flask backend serving recommendations from a curated database of 24 laptops.

## 🏗️ Architecture

### Backend (Python/Flask)
- **Framework:** Flask 3.0.3
- **ML Pipeline:** NumPy-based KNN classifier, content-based similarity, and collaborative filtering
- **Data Source:** Jordanian laptop retailers (PC Circle scraper)
- **API Endpoints:**
  - `GET /api/laptops` — Retrieve all available laptops
  - `POST /api/recommend` — Get personalized recommendations
  - `POST /api/refresh-prices` — Update prices from retailers

### Frontend (React/TypeScript)
- **Framework:** React 19 + Vite
- **Styling:** Tailwind CSS 4 + shadcn/ui components
- **Design:** Bold & Modern aesthetic with deep navy backgrounds and electric blue accents
- **Features:** Real-time filter updates, responsive layout, animated recommendations

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 22+
- pnpm (or npm/yarn)

### Backend Setup & Environment Bootstrap

We provide a cross-platform Python bootstrap script that handles virtual environment creation, pip upgrades, dependency installation, `.env` file copying, and local system health diagnostics.

1. **Bootstrap the environment:**
   ```bash
   cd Laptop-Recommnder-System
   python bootstrap.py
   ```
   *Note: This script works on Windows, macOS, and Linux.*

2. **Configure your environment variables:**
   Open the newly generated `.env` file in the root of the backend directory and set your `OPENAI_API_KEY`:
   ```env
   OPENAI_API_KEY=sk-proj-...
   ```
   *Note: If no API key is specified, the system will fallback to local ML hybrid recommendation model logic.*

3. **Run the Flask server:**
   ```bash
   # Activate the virtual environment
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate

   # Start the application
   python app.py
   ```
   The backend will start on `http://127.0.0.1:5000`

### Frontend Setup

1. **Install dependencies:**
   ```bash
   cd ../laptop-recommender-ui
   pnpm install
   ```

2. **Start the development server:**
   ```bash
   pnpm run dev
   ```
   The frontend will be available at `http://localhost:5173` with automatic API proxying to the backend.

## 📊 ML Models

The system trains four recommendation models on a synthetic dataset of 1,000 user profiles:

| Model | Accuracy | Approach |
|-------|----------|----------|
| **Hybrid** | 72.0% | Combines all three models with weighted voting |
| **Collaborative Filtering** | 72.5% | User-based KNN on preference vectors |
| **Content-Based** | 65.5% | Feature similarity between user preferences and laptop specs |
| **KNN Classifier** | 62.5% | 15-nearest neighbors on preference encoding |

Accuracy is measured as Precision@1 (percentage of test users where the top recommendation has a rating ≥ 4.0).

## 🎨 Design Philosophy

The interface follows a **Bold & Modern** design approach:

- **Color Palette:** Deep navy backgrounds (oklch(0.12 0.01 260)) with electric blue accents (oklch(0.65 0.2 260)) and cyan highlights
- **Typography:** Sora (display) paired with Inter (body) for premium feel
- **Layout:** Asymmetric sections with strategic whitespace and gradient dividers
- **Interactions:** Smooth 200-300ms transitions with scale feedback on buttons

## 🔧 API Reference

### GET /api/laptops
Returns the current laptop database with safe fields.

**Response:**
```json
{
  "laptops": [
    {
      "brand": "ASUS",
      "model": "TUF Gaming A15",
      "cpu": "AMD Ryzen 7 7735HS",
      "gpu": "NVIDIA GeForce RTX 4060 8GB",
      "ram": 16,
      "storage": "512GB SSD",
      "screen_size": 15.6,
      "price_jod": 780,
      "use_cases": ["gaming", "content_creation"],
      "performance_level": "high",
      "portability": "medium",
      "image_url": "https://images.unsplash.com/...",
      "purchase_url": "https://..."
    }
  ],
  "count": 24
}
```

### POST /api/recommend
Get personalized laptop recommendations based on user preferences.

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
      "laptop": { /* laptop object */ },
      "score": 4.8,
      "reason": "Excellent match for gaming with high performance"
    }
  ],
  "model_accuracies": {
    "content_based": 65.5,
    "collaborative": 72.5,
    "knn_classifier": 62.5,
    "hybrid": 72.0
  }
}
```

## 🔐 Security Features

- **Input Validation:** Strict allow-lists for all user inputs (budget, use case, performance, etc.)
- **Rate Limiting:** 30 requests per 60 seconds per IP
- **Security Headers:** CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy
- **Payload Size Limits:** 4KB max request size
- **HTTPS Ready:** Designed for reverse proxy deployment with HTTPS

## 📁 Project Structure

```
Laptop-Recommnder-System/
├── app.py                 # Flask application with API routes
├── ml_pipeline.py         # ML models and recommendation logic
├── data_fetcher.py        # Web scraper and data loading
├── laptops_cache.json     # Curated laptop database
└── requirements.txt       # Python dependencies

laptop-recommender-ui/
├── client/
│   ├── src/
│   │   ├── pages/Home.tsx      # Main recommendation interface
│   │   ├── App.tsx             # Router and theme setup
│   │   └── index.css           # Global styles and design tokens
│   ├── index.html              # HTML entry point
│   └── public/                 # Static assets
├── vite.config.ts          # Vite configuration with API proxy
└── package.json            # Node dependencies
```

## 🛠️ Development

### Running Tests
```bash
cd Laptop-Recommnder-System
python3 test_backend.py
```

### Building for Production
```bash
cd laptop-recommender-ui
pnpm run build
```

The build output will be in `dist/public/` ready for deployment.

## 🌐 Deployment

### Backend Deployment
1. Set `debug=False` in `app.py`
2. Deploy behind a reverse proxy (nginx/caddy) with HTTPS
3. Set environment variables for production secrets

### Frontend Deployment
The frontend is a static React SPA that can be deployed to any static hosting service (Vercel, Netlify, GitHub Pages, etc.). The API proxy in development should be replaced with the actual backend URL in production.

## 📈 Future Enhancements

1. **User Accounts:** Add authentication to save preferences and recommendation history
2. **Advanced Filtering:** Add more granular filters (GPU type, RAM speed, display refresh rate)
3. **Comparison Tool:** Allow users to compare multiple laptops side-by-side
4. **Real-time Price Updates:** Implement automated price scraping from multiple retailers
5. **Community Reviews:** Add user reviews and ratings
6. **Mobile App:** Native iOS/Android applications

## 📝 License

This project is open source and available under the MIT License.

## 👥 Contributors

- Backend ML Pipeline: Python/NumPy implementation
- Frontend UI: React 19 with Tailwind CSS
- Design: Bold & Modern aesthetic with premium typography

## 📞 Support

For issues, questions, or suggestions, please open an issue on GitHub or contact the development team.

---

**Built with ❤️ for laptop enthusiasts and decision-makers**
