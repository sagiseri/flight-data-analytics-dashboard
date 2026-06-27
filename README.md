# ✈️ Flight Data Analytics Dashboard

## 👨‍💻 Authors
- Sagi Seri (ID: 209389972)  
- Yishai Heller (ID: 323114314)

---

## 📊 Project Overview
This project analyzes flight data using SQL, Python, and interactive dashboards.

It includes:
- Data processing using DuckDB and SQLite
- Advanced SQL queries on flight datasets
- Creation of summary tables for faster analysis
- Interactive dashboard built with Streamlit
- Visualizations using Matplotlib, Seaborn, and Plotly

---

## 📁 Project Structure

### 1. `queries.py`
Uses DuckDB and SQLite to:
- Load flight data from CSV
- Run complex SQL queries (delays, cancellations, performance)
- Generate summary tables
- Export results to SQLite database

---

### 2. `dashboard.py`
Interactive Streamlit dashboard that:
- Connects to `small_tables.db`
- Displays multiple analytical views (delays, cancellations, performance)
- Supports navigation between sections
- Shows up to 500 rows per table
- Includes visualizations (bar charts, pie charts, scatter plots, line charts)

---

### 3. `small_tables.db`
SQLite database containing processed and aggregated tables for fast analysis.

---

### 4. `sample_500_rows.csv`
Sample dataset (500 rows) from the original flight dataset.

---

### 5. `requirements.txt`
Contains required Python libraries:
- Streamlit  
- Pandas  
- NumPy  
- SQLite (built-in)  
- Matplotlib  
- Seaborn  
- Plotly  

---

### 6. `תרגיל מסכם`
Final assignment document including:
- Queries explanations
- Screenshots of the dashboard
- Full documentation of the project requirements

---

### 7. SQLite Tables Description
The database includes multiple analytical tables:

- **airline_delays_small** – airline delay performance analysis  
- **diverted_flights_small** – diverted flights statistics  
- **cancellations_rollup_small** – cancellation analysis by region  
- **flight_analysis_small** – flight timing and delay trends  
- **aircraft_performance_small** – aircraft performance metrics  
- **state_delays_small** – delays by destination state  

These tables help identify trends and operational insights in aviation data.

---

## ▶️ How to Run

```bash
pip install -r requirements.txt