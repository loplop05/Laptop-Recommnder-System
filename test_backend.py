import logging
from ml_pipeline import LaptopRecommenderPipeline
from data_fetcher import scrape_pc_circle, load_laptops

logging.basicConfig(level=logging.INFO)

def test_pipeline():
    print("--- Testing ML Pipeline ---")
    pipeline = LaptopRecommenderPipeline()
    pipeline.train_and_evaluate_models()
    print(f"Model Accuracies: {pipeline.model_accuracies}")
    
    # Test a single recommendation
    pref = {
        "budget": 800,
        "use_case": "gaming",
        "performance": "high",
        "screen_size": "15-16",
        "portability": "medium",
        "brand": "Any"
    }
    recommendations = pipeline.get_recommendations(pref)
    print(f"Recommendations for gaming (800 JOD): {len(recommendations.get('recommendations', []))} laptops found.")
    if recommendations.get('recommendations'):
        top = recommendations['recommendations'][0]
        print(f"Top Pick: {top['brand']} {top['model']} - {top['price_jod']} JOD")

def test_scraper():
    print("\n--- Testing Scraper ---")
    # Note: This might fail if the site is down or blocking, but we check the logic
    success, count = scrape_pc_circle()
    print(f"Scraper Success: {success}, Updated: {count}")

if __name__ == "__main__":
    try:
        test_pipeline()
    except Exception as e:
        print(f"Pipeline Test Failed: {e}")
        
    try:
        test_scraper()
    except Exception as e:
        print(f"Scraper Test Failed: {e}")
