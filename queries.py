import duckdb

def connect_to_db(db_path):
    """
        Connects to a DuckDB database.

        Parameters:
            db_path (str): The path to the DuckDB database file.

        Returns:
            conn: A connection object to the DuckDB database.
        """
    return duckdb.connect(db_path)


def drop_table_if_exists(conn, table_name):
    """
       Drops a table in the DuckDB database if it exists.

       Parameters:
           conn: A connection object to the DuckDB database.
           table_name (str): The name of the table to drop.
       """

    conn.execute(f"DROP TABLE IF EXISTS {table_name};")


def create_table_from_csv(conn, csv_path, table_name):
    """
        Creates a table in DuckDB from a CSV file.

        Parameters:
            conn: A connection object to the DuckDB database.
            csv_path (str): The path to the CSV file.
            table_name (str): The name of the table to create.
        """
    conn.execute(f"""
        CREATE TABLE {table_name} AS
        SELECT * FROM read_csv_auto('{csv_path}');
    """)


def run_query_and_save(conn, query, result_table_name):
    """
       Executes a SQL query and saves the results into a new table in DuckDB.

       Parameters:
           conn: A connection object to the DuckDB database.
           query (str): The SQL query to execute.
           result_table_name (str): The name of the table to store the results.

       Returns:
           columns (list): A list of column names from the result set.
           result (list): A list of rows from the result set.
       """
    conn.execute(f"DROP TABLE IF EXISTS {result_table_name};")

    # מריץ את השאילתה ושומר את התוצאות בטבלה חדשה
    conn.execute(f"CREATE TABLE {result_table_name} AS {query}")

    result = conn.execute(f"SELECT * FROM {result_table_name}").fetchall()
    columns = [desc[0] for desc in conn.description]
    return columns, result


def create_small_table(conn, large_table_name, small_table_name, sample_size=500):
    """
        Creates a smaller table by sampling rows from a larger table.

        Parameters:
            conn: A connection object to the DuckDB database.
            large_table_name (str): The name of the larger table to sample from.
            small_table_name (str): The name of the smaller table to create.
            sample_size (int): The number of rows to sample (default is 500).
        """
    # מוחק את הטבלה הקטנה אם היא כבר קיימת
    conn.execute(f"DROP TABLE IF EXISTS {small_table_name};")


    conn.execute(f"""
        CREATE TABLE {small_table_name} AS
        SELECT * FROM {large_table_name}
        LIMIT {sample_size};
    """)


def transfer_to_sqlite(conn, duckdb_table_name, sqlite_db_path, sqlite_table_name):
    """
    Transfers a table from DuckDB to SQLite.

    Parameters:
        conn: A connection object to the DuckDB database.
        duckdb_table_name (str): The name of the table in DuckDB.
        sqlite_db_path (str): The path to the SQLite database file.
        sqlite_table_name (str): The name of the table in SQLite.
    """

    conn.execute(f"ATTACH '{sqlite_db_path}' AS sqlite_db (TYPE SQLITE);")


    conn.execute(f"DROP TABLE IF EXISTS sqlite_db.{sqlite_table_name};")


    conn.execute(f"CREATE TABLE sqlite_db.{sqlite_table_name} AS SELECT * FROM {duckdb_table_name};")


    conn.execute("DETACH sqlite_db;")


def print_results(columns, result):
    """
        Prints the results of a query in a readable format.

        Parameters:
            columns (list): A list of column names.
            result (list): A list of rows from the result set.
        """
    print(" | ".join(columns))
    for row in result:
        print(row)


def main():
    """
        Main function to execute the workflow:
        1. Connects to DuckDB.
        2. Creates a table from a CSV file.
        3. Runs multiple queries and saves the results.
        4. Creates smaller tables from the results.
        5. Transfers the smaller tables to SQLite.
        """

    db_path = 'db_file.duckdb'  # נתיב ל-DuckDB
    csv_path = 'Combined_Flights_2018.csv'
    sqlite_db_path = 'small_tables.db'  # נתיב ל-SQLite
    table_name = 'my_table'  # שם הטבלה ב-DuckDB


    # מתחברים ל-DuckDB
    conn = connect_to_db(db_path)

    drop_table_if_exists(conn, table_name)

    # יוצרים את הטבלה מה-CSV
    create_table_from_csv(conn, csv_path, table_name)

    # מילון של השאילתות והטבלאות לשמירת התוצאות
    queries = {
        "query_1": {
            "query": """
                WITH airline_delays AS (
                    SELECT 
                        Operating_Airline,
                        DistanceGroup,
                        COUNT(*) AS total_flights,
                        SUM(CASE WHEN DepDel15 = 1 THEN 1 ELSE 0 END) AS delayed_flights,
                        AVG(Distance) AS avg_distance
                    FROM my_table
                    GROUP BY Operating_Airline, DistanceGroup
                    HAVING COUNT(*) >= 1000
                )
                SELECT 
                    Operating_Airline,
                    DistanceGroup,
                    ROUND(100.0 * delayed_flights / total_flights, 2) AS delay_percentage,
                    avg_distance,
                    RANK() OVER (PARTITION BY DistanceGroup ORDER BY delayed_flights DESC) AS delay_rank
                FROM airline_delays
                ORDER BY DistanceGroup, delay_percentage DESC;
            """,
            "result_table": "airline_delays_results",
            "small_table": "airline_delays_small"
        },
        "query_2": {
            "query": """
                WITH base_data AS (
                    SELECT 
                        Origin AS OriginAirportCode,
                        EXTRACT(QUARTER FROM FlightDate) AS quarter,
                        Diverted
                    FROM my_table
                ),
                quarterly_stats AS (
                    SELECT 
                        OriginAirportCode,
                        quarter,
                        COUNT(*) AS total_flights,
                        SUM(CASE WHEN Diverted = 1 THEN 1 ELSE 0 END) AS diverted_flights
                    FROM base_data
                    GROUP BY 
                        CUBE (OriginAirportCode, quarter)
                    HAVING OriginAirportCode IS NOT NULL 
                        AND quarter IS NOT NULL
                ),
                flight_metrics AS (
                    SELECT 
                        OriginAirportCode,
                        quarter,
                        total_flights,
                        diverted_flights,
                        diverted_flights AS current_quarter_diverted,
                        SUM(diverted_flights) OVER (
                            PARTITION BY OriginAirportCode 
                            ORDER BY quarter
                            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                        ) AS cumulative_diverted,
                        FIRST_VALUE(diverted_flights) OVER (
                            PARTITION BY OriginAirportCode 
                            ORDER BY quarter
                        ) AS first_quarter_diverted
                    FROM quarterly_stats
                )
                SELECT 
                    OriginAirportCode,
                    quarter,
                    ROUND(100.0 * diverted_flights / NULLIF(total_flights, 0), 2) AS diversion_rate,
                    diverted_flights,
                    cumulative_diverted
                FROM flight_metrics
                ORDER BY OriginAirportCode, quarter;
            """,
            "result_table": "diverted_flights_results",
            "small_table": "diverted_flights_small"
        },
        "query_3": {
            "query": """
                WITH cancellations_rollup AS (
                    SELECT 
                        OriginStateName AS state,
                        COALESCE(CAST(EXTRACT(QUARTER FROM FlightDate) AS VARCHAR), 'All Quarters') AS quarter,
                        COUNT(*) AS total_flights,
                        SUM(CASE WHEN Cancelled = 1 THEN 1 ELSE 0 END) AS cancelled_flights
                    FROM my_table
                    GROUP BY ROLLUP (OriginStateName, EXTRACT(QUARTER FROM FlightDate))
                ),
                cancellation_rates AS (
                    SELECT 
                        state,
                        quarter,
                        ROUND(100.0 * cancelled_flights / total_flights, 5) AS cancellation_rate
                    FROM cancellations_rollup
                )
                SELECT 
                    state,
                    CASE 
                        WHEN quarter = 'All Quarters' THEN '0' 
                        ELSE quarter 
                    END AS quarter,  
                    cancellation_rate,
                    RANK() OVER (PARTITION BY quarter ORDER BY cancellation_rate DESC) AS rank
                FROM cancellation_rates
                WHERE state IS NOT NULL 
                ORDER BY quarter, rank;
            """,
            "result_table": "cancellations_rollup_results",
            "small_table": "cancellations_rollup_small"
        },
        "query_4": {
            "query": """
                WITH flight_analysis AS (
                    SELECT 
                        EXTRACT(DOW FROM FlightDate) AS day_of_week,
                        EXTRACT(HOUR FROM STRPTIME(LPAD(CRSDepTime::VARCHAR, 4, '0'), '%H%M')) AS hour_of_day,
                        COUNT(*) AS total_flights,
                        AVG(DepDelayMinutes) AS avg_departure_delay
                    FROM my_table
                    GROUP BY 
                        EXTRACT(DOW FROM FlightDate), 
                        EXTRACT(HOUR FROM STRPTIME(LPAD(CRSDepTime::VARCHAR, 4, '0'), '%H%M'))
                )
                SELECT 
                    day_of_week,
                    hour_of_day,
                    total_flights,
                    avg_departure_delay,
                    SUM(total_flights) OVER (PARTITION BY day_of_week ORDER BY hour_of_day) AS cumulative_flights
                FROM flight_analysis
                ORDER BY day_of_week, hour_of_day;
            """,
            "result_table": "flight_analysis_results",
            "small_table": "flight_analysis_small"
        },
        "query_5": {
            "query": """
                WITH aircraft_performance AS (
                    SELECT 
                        Tail_Number,
                        COUNT(*) AS total_flights,
                        AVG(ArrDelayMinutes) AS avg_arrival_delay,
                        SUM(CASE WHEN ArrDel15 = 1 THEN 1 ELSE 0 END) AS delayed_flights
                    FROM my_table
                    WHERE Tail_Number IS NOT NULL
                    GROUP BY GROUPING SETS ((Tail_Number), ())
                    HAVING COUNT(*) >= 50
                )
                SELECT 
                    Tail_Number,
                    total_flights,
                    avg_arrival_delay,
                    ROUND(100.0 * delayed_flights / total_flights, 2) AS delay_percentage,
                    RANK() OVER (ORDER BY avg_arrival_delay DESC) AS delay_rank_by_avg,
                    RANK() OVER (ORDER BY delay_percentage DESC) AS delay_rank_by_percentage,
                    (0.6 * avg_arrival_delay + 0.4 * ROUND(100.0 * delayed_flights / total_flights, 2)) AS combined_score,
                    RANK() OVER (
                        ORDER BY (0.6 * avg_arrival_delay + 0.4 * ROUND(100.0 * delayed_flights / total_flights, 2)) DESC
                    ) AS combined_rank
                FROM aircraft_performance
                ORDER BY combined_rank;
            """,
            "result_table": "aircraft_performance_results",
            "small_table": "aircraft_performance_small"
        },
        "query_6": {
            "query": """
                WITH flight_metrics AS (
                    SELECT 
                        DestStateName AS destination_state,
                        DepDel15,
                        DepDelayMinutes,
                        CASE 
                            WHEN DepDelayMinutes <= 15 THEN 'Short'
                            WHEN DepDelayMinutes <= 45 THEN 'Medium'
                            ELSE 'Long'
                        END AS delay_category
                    FROM my_table
                ),
                state_delay_cube AS (
                    SELECT 
                        COALESCE(destination_state, 'ALL STATES') AS destination_state,
                        COALESCE(delay_category, 'ALL CATEGORIES') AS delay_category,
                        COUNT(*) AS total_flights,
                        SUM(CASE WHEN DepDel15 = 1 THEN 1 ELSE 0 END) AS delayed_flights,
                        AVG(DepDelayMinutes) AS avg_departure_delay
                    FROM flight_metrics
                    GROUP BY CUBE(destination_state, delay_category)
                ),
                state_delays AS (
                    SELECT 
                        destination_state,
                        total_flights,
                        delayed_flights,
                        avg_departure_delay,
                        ROUND(100.0 * delayed_flights / NULLIF(total_flights, 0), 2) AS delay_percentage,
                        AVG(delayed_flights) OVER (
                            ORDER BY delayed_flights 
                            ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING
                        ) AS moving_avg_delayed_flights,
                        FIRST_VALUE(delayed_flights) OVER (
                            ORDER BY delayed_flights DESC
                        ) AS highest_delayed_flights
                    FROM state_delay_cube
                    WHERE destination_state != 'ALL STATES' 
                        AND delay_category = 'ALL CATEGORIES'
                )
                SELECT 
                    destination_state,
                    total_flights,
                    delayed_flights,
                    delay_percentage,
                    ROUND(avg_departure_delay, 2) AS avg_departure_delay,
                    RANK() OVER (ORDER BY delay_percentage DESC) AS delay_rank
                FROM state_delays
                ORDER BY delay_rank;
            """,
            "result_table": "state_delays_results",
            "small_table": "state_delays_small"
        }
    }

    for query_name, query_info in queries.items():
        print(f"\nRunning {query_name}...")
        columns, result = run_query_and_save(conn, query_info["query"], query_info["result_table"])
        print_results(columns, result)

        create_small_table(conn, query_info["result_table"], query_info["small_table"])
        print(f"Created small table: {query_info['small_table']}")

    for query_info in queries.values():
        small_table_name = query_info["small_table"]
        transfer_to_sqlite(conn, small_table_name, sqlite_db_path, small_table_name)
        print(f"Transferred table {small_table_name} to SQLite.")

    conn.close()


if __name__ == "__main__":
    main()