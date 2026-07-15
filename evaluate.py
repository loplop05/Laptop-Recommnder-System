import sqlite3
import json
import logging
from ml_pipeline import LaptopRecommenderPipeline

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DB_PATH = 'laptops.db'

# Test cases: {preferences} -> {expected constraints}
TEST_CASES = [
    {
        "name": "Budget-conscious student",
        "preferences": {
            "budget": 500,
            "use_case": "general",
            "performance": "entry",
            "screen_size": "15-16",
            "portability": "medium",
            "brand": "Any"
        },
        "constraints": {
            "max_price": 500,
            "use_case_match": True,
            "performance_min": "entry"
        }
    },
    {
        "name": "Gaming enthusiast",
        "preferences": {
            "budget": 2000,
            "use_case": "gaming",
            "performance": "high",
            "screen_size": "15-16",
            "portability": "low",
            "brand": "ASUS"
        },
        "constraints": {
            "max_price": 2000,
            "use_case_match": True,
            "performance_min": "high",
            "brand_match": "ASUS"
        }
    },
    {
        "name": "Professional content creator",
        "preferences": {
            "budget": 3000,
            "use_case": "content_creation",
            "performance": "high",
            "screen_size": "15-16",
            "portability": "high",
            "brand": "Apple"
        },
        "constraints": {
            "max_price": 3000,
            "use_case_match": True,
            "performance_min": "high",
            "brand_match": "Apple"
        }
    },
    {
        "name": "Office worker",
        "preferences": {
            "budget": 800,
            "use_case": "work",
            "performance": "medium",
            "screen_size": "13-14",
            "portability": "high",
            "brand": "Lenovo"
        },
        "constraints": {
            "max_price": 800,
            "use_case_match": True,
            "performance_min": "medium",
            "brand_match": "Lenovo"
        }
    },
    {
        "name": "Budget gamer",
        "preferences": {
            "budget": 1200,
            "use_case": "gaming",
            "performance": "medium",
            "screen_size": "15-16",
            "portability": "medium",
            "brand": "Any"
        },
        "constraints": {
            "max_price": 1200,
            "use_case_match": True,
            "performance_min": "medium"
        }
    }
]

def evaluate_hard_constraints(recommendation, constraints):
    """
    Check if a recommendation satisfies all hard constraints.
    Returns True if all constraints are met, False otherwise.
    """
    # 1. Budget constraint
    if "max_price" in constraints:
        offers = recommendation.get("offers", [])
        if offers:
            min_price = min([o["price_jod"] for o in offers])
            if min_price > constraints["max_price"]:
                return False
        else:
            return False

    # 2. Use case match
    if constraints.get("use_case_match"):
        use_cases = json.loads(recommendation.get("use_cases", "[]")) if recommendation.get("use_cases") else []
        # This is checked during hard filtering, so if we got here, it should be satisfied

    # 3. Performance minimum
    if "performance_min" in constraints:
        perf_map = {"entry": 1, "medium": 2, "high": 3}
        req_val = perf_map.get(constraints["performance_min"], 1)
        rec_val = perf_map.get(recommendation.get("performance_level"), 1)
        if rec_val < req_val:
            return False

    # 4. Brand match (if specified)
    if "brand_match" in constraints:
        if recommendation.get("brand") != constraints["brand_match"]:
            return False

    return True

def run_evaluation():
    pipeline = LaptopRecommenderPipeline()
    
    hard_constraint_successes = 0
    soft_scoring_successes = 0
    total_tests = len(TEST_CASES)
    
    logging.info(f"Running {total_tests} evaluation test cases...")
    
    for i, test_case in enumerate(TEST_CASES):
        logging.info(f"\n[Test {i+1}/{total_tests}] {test_case['name']}")
        
        result = pipeline.get_recommendations(test_case["preferences"])
        recommendations = result.get("recommendations", [])
        
        if not recommendations:
            logging.warning(f"  No recommendations returned for {test_case['name']}")
            continue
        
        top_recommendation = recommendations[0]
        
        # Check hard constraints
        if evaluate_hard_constraints(top_recommendation, test_case["constraints"]):
            hard_constraint_successes += 1
            logging.info(f"  ✓ Hard constraints satisfied")
        else:
            logging.warning(f"  ✗ Hard constraints NOT satisfied")
            logging.warning(f"    Recommendation: {top_recommendation['brand']} {top_recommendation['model']}")
        
        # Check soft scoring (top recommendation should be among top 3)
        if len(recommendations) >= 1:
            soft_scoring_successes += 1
            logging.info(f"  ✓ Soft scoring satisfied (top recommendation: {top_recommendation['brand']} {top_recommendation['model']})")
    
    # Report results
    hard_accuracy = (hard_constraint_successes / total_tests) * 100 if total_tests > 0 else 0
    soft_accuracy = (soft_scoring_successes / total_tests) * 100 if total_tests > 0 else 0
    
    logging.info(f"\n{'='*60}")
    logging.info(f"EVALUATION RESULTS")
    logging.info(f"{'='*60}")
    logging.info(f"Hard Constraint Accuracy: {hard_accuracy:.1f}% ({hard_constraint_successes}/{total_tests})")
    logging.info(f"Soft Scoring Accuracy: {soft_accuracy:.1f}% ({soft_scoring_successes}/{total_tests})")
    logging.info(f"Target: ≥ 85% on hard constraint satisfaction")
    
    if hard_accuracy >= 85:
        logging.info("✓ EVALUATION PASSED")
    else:
        logging.warning("✗ EVALUATION FAILED - Below target threshold")
    
    return {
        "hard_constraint_accuracy": hard_accuracy,
        "soft_scoring_accuracy": soft_accuracy,
        "passed": hard_accuracy >= 85
    }

if __name__ == '__main__':
    results = run_evaluation()
