# CAS Portfolio Analytics & Benchmarking Engine

An end-to-end data engineering and visualization pipeline. This project extracts transaction data from raw Consolidated Account Statement (CAS) PDFs, warehouses it in a custom PostgreSQL database, calculates complex performance metrics (like XIRR) via Python, and visualizes the exact alpha against shadow benchmarks in Power BI.

## 🛠 Tech Stack
* **Backend & Processing:** Python
* **Data Warehouse:** PostgreSQL
* **Visualization & Analytics:** Power BI (DAX)
* **Version Control:** Git / GitHub

## 🚀 Key Features Built
* **CAS PDF Parsing Engine:** Python scripts designed to extract unstructured financial data and transactions from raw CAS files and normalize them for a relational database.
* **Programmatic XIRR Calculation:** Advanced Python logic to pre-calculate annualized returns (XIRR) based on exact transaction cash flow dates, stored directly in the database.
* **Relational Database Architecture:** Custom PostgreSQL schema (including tables like `shadow_benchmark_values` and `benchmark_metrics`) to handle long-format time-series data for multiple AMCs and portfolios.
* **Shadow Benchmarking:** Directly compares actual portfolio current value against hypothetical investments in the Nifty 50 and Nifty 500 indexes on the exact same transaction dates.

* *(Note: The raw PDF statements and Power BI file containing embedded financial data are kept local for privacy and security).*