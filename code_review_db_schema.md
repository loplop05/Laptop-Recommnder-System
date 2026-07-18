# Code Review: `db_schema.py`

## Overview

The `db_schema.py` file defines the SQLite database schema and provides helper functions for interacting with the database, including connection management, table initialization, and CRUD operations for laptops, shops, and offers. It also contains the `filter_laptops` function, which applies hard filters based on user preferences.

## Key Findings and Recommendations

### 1. Single Responsibility Principle (SRP) Violations

**Current State:** The `db_schema.py` file has multiple responsibilities:

*   **Schema Definition and Initialization:** `init_db` creates tables and indexes.
*   **Connection Management:** `get_connection` handles SQLite connection setup.
*   **CRUD Operations:** `upsert_shop`, `upsert_laptop`, `upsert_offer` manage data insertion and updates.
*   **Complex Query Logic:** `get_laptops_with_best_price` and `filter_laptops` contain significant query construction and data processing logic.
*   **Data Seeding:** `seed_from_json` handles migrating data from a JSON file into the database, including shop metadata and offer parsing.

**Impact:** This concentration of responsibilities makes the file large and less modular. Changes to the database structure, data access patterns, or seeding logic all impact this single file.

**Recommendation:**

*   **Separate Data Access Layer (DAL):** Create a `LaptopRepository` or `ShopRepository` class that encapsulates the CRUD operations and complex query logic (e.g., `get_laptops_with_best_price`, `filter_laptops`). This would abstract the database interactions from the rest of the application.
*   **Dedicated Seeding Module:** Move `seed_from_json` into a separate module (e.g., `db_seeder.py`) as it's a one-time or infrequent operation, distinct from the ongoing data access logic.
*   **Database Configuration:** Centralize `DB_PATH` and potentially other database-related configurations in a dedicated configuration file or object.

### 2. Open/Closed Principle (OCP) Violations

**Current State:** The `filter_laptops` function directly implements the filtering logic with hardcoded `perf_order` and `screen_ranges`. Adding new filter criteria or modifying existing ones requires direct modification of this function.

**Impact:** Extending the filtering capabilities is not straightforward and can introduce regressions.

**Recommendation:**

*   **Strategy Pattern for Filters:** Introduce a `Filter` interface or abstract class. Each specific filter (e.g., `BudgetFilter`, `UseCaseFilter`) could be a separate class. The `filter_laptops` function would then accept a list of `Filter` objects and apply them dynamically. This would make the filtering logic extensible without modifying the core `filter_laptops` function.
*   **Externalize Constants:** As noted in `ml_pipeline.py` review, `perf_order` and `screen_ranges` are duplicated. Centralizing these constants (e.g., in a `config.py`) would improve OCP by allowing changes to these values without modifying the `db_schema.py` logic.

### 3. Dependency Inversion Principle (DIP) Violations

**Current State:** The `filter_laptops` function directly depends on concrete implementations of `sqlite3` and constructs SQL queries directly. The `seed_from_json` function directly depends on `json` and `os` for file operations and `sqlite3` for database interactions.

**Impact:** The module is tightly coupled to SQLite, making it difficult to switch to a different database system (e.g., PostgreSQL, MySQL) without significant refactoring. Testing database interactions in isolation is also harder.

**Recommendation:**

*   **Abstract Database Access:** Define an abstract `IDatabaseConnection` or `IRepository` interface. The `db_schema.py` functions would then implement this interface. This allows higher-level modules (like `ml_pipeline.py`) to depend on the abstraction rather than the concrete SQLite implementation.
*   **Inject Dependencies:** Pass the database connection object (`conn`) to functions like `upsert_shop`, `upsert_laptop`, `upsert_offer`, and `filter_laptops` rather than having them call `get_connection` internally. This makes dependencies explicit and facilitates testing.

### 4. Code Smells and Readability

**Current State:**

*   **SQL Query Strings:** Long SQL query strings are embedded directly within the Python code, making them less readable and harder to manage, especially with conditional `WHERE` clauses.
*   **Duplication of Constants:** `perf_order` and `screen_ranges` are duplicated in `ml_pipeline.py` and `db_schema.py`.
*   **Magic Strings:** Use of literal strings for column names and table names throughout the SQL queries.
*   **Mixed Concerns in `seed_from_json`:** This function handles file reading, shop metadata definition, laptop data transformation, and database upserts, making it quite complex.

**Impact:** Reduced maintainability, increased risk of SQL injection (though less critical with SQLite and parameterized queries, still a good practice to abstract), and difficulty in understanding the data flow.

**Recommendation:**

*   **SQL Query Builders/ORMs:** For more complex queries, consider using a lightweight SQL query builder or an ORM (Object-Relational Mapper) if the project scope expands. For this project, carefully structured multi-line f-strings with clear parameterization can improve readability.
*   **Centralize Constants:** Move `perf_order` and `screen_ranges` to a shared `config.py` module.
*   **Enum for Column Names:** Define enums or constants for table and column names to prevent typos and improve refactoring safety.
*   **Refactor `seed_from_json`:** Break down `seed_from_json` into smaller, more focused functions: one for reading JSON, one for processing shop metadata, one for transforming laptop data, and one for performing the actual upserts.

### 5. Error Handling and Robustness

**Current State:** Error handling is minimal. For instance, `seed_from_json` assumes the JSON file exists and is well-formed. Database operations generally rely on `sqlite3`'s default error handling.

**Impact:** Unexpected file formats or database issues could lead to unhandled exceptions.

**Recommendation:**

*   **Specific Exception Handling:** Add `try-except` blocks for file operations and database interactions to catch specific exceptions (e.g., `FileNotFoundError`, `json.JSONDecodeError`, `sqlite3.Error`) and provide more informative error messages.
*   **Validation:** Implement input validation for data being inserted into the database to ensure data integrity.

## Conclusion

The `db_schema.py` module effectively manages the database for the Laptop Recommender System. However, it can be significantly improved by applying SRP, OCP, and DIP. By separating concerns into dedicated classes/modules, abstracting database interactions, and centralizing constants, the codebase will become more robust, maintainable, and easier to extend in the future.
