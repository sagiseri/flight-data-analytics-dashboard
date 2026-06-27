import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import numpy as np
from matplotlib import cm


def main():
    """
    Main function to run the Streamlit dashboard.
    Sets up the page configuration and navigation.
    """
    st.set_page_config(page_title="Flight Data Dashboard")

    # Load data from SQLite database
    conn = sqlite3.connect('small_tables.db')

    # Create sidebar for navigation
    pages = {
        "Questions": questions_page,
        "Story and Insights": story_page,
        "Aircraft Performance": lambda: display_table(conn, "aircraft_performance_small", "Aircraft Performance"),
        "Airline Delays": lambda: display_table(conn, "airline_delays_small", "Airline Delays"),
        "Cancellations Rollup": lambda: display_table(conn, "cancellations_rollup_small", "Cancellations Rollup"),
        "Diverted Flights": lambda: display_table(conn, "diverted_flights_small", "Diverted Flights"),
        "Flight Analysis": lambda: display_table(conn, "flight_analysis_small", "Flight Analysis"),
        "State Delays": lambda: display_table(conn, "state_delays_small", "State Delays"),
    }

    selection = st.sidebar.radio("Go to", list(pages.keys()))
    pages[selection]()
    conn.close()


def apply_table_styling(df, table_name):
    """
    Applies conditional formatting to the dataframe based on table type.

    Args:
        df (pd.DataFrame): Input dataframe
        table_name (str): Name of the table for conditional styling

    Returns:
        pd.Styler: Styled dataframe
    """
    styling_config = {
        "airline_delays_small": {
            'delay_percentage': ('lightgreen', 'pink'),
            'avg_distance': ('lightblue', 'orange')
        },
        "diverted_flights_small": {
            'diversion_rate': ('lightgreen', 'pink'),
            'cumulative_diverted': ('lightblue', 'orange')
        },
        "cancellations_rollup_small": {
            'cancellation_rate': ('lightgreen', 'pink'),
            'rank': ('lightblue', 'orange')
        },
        "flight_analysis_small": {
            'avg_departure_delay': ('lightgreen', 'pink'),
            'cumulative_flights': ('lightblue', 'orange')
        },
        "aircraft_performance_small": {
            'combined_score': ('lightgreen', 'pink'),
            'delay_rank_by_avg': ('lightblue', 'orange')
        },
        "state_delays_small": {
            'delay_percentage': ('lightgreen', 'pink'),
            'avg_departure_delay': ('lightblue', 'orange')
        }
    }

    if table_name in styling_config:
        df_styled = df.style
        for column, (max_color, min_color) in styling_config[table_name].items():
            df_styled = df_styled.highlight_max(subset=[column], color=max_color) \
                .highlight_min(subset=[column], color=min_color)
        return df_styled
    return df.style


def visualize_airline_delays(df):
    """
    Creates visualization for airline delays data.
    """
    # Filter top airlines per distance group
    top_airlines_per_group = df[df['delay_rank'] == 1]

    st.write("### Top Airlines with Highest Delay Percentage per Distance Group")
    fig, ax = plt.subplots(figsize=(10, 6))

    # Create color gradient
    colors = cm.viridis(np.linspace(0, 1, len(top_airlines_per_group)))

    # Plot bars
    bars = ax.bar(
        top_airlines_per_group['DistanceGroup'],
        top_airlines_per_group['delay_percentage'],
        color=colors,
        edgecolor='black'
    )

    # Add labels
    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height + 1,
            f"{top_airlines_per_group.iloc[i]['Operating_Airline']}\n({height:.2f}%)",
            ha='center',
            fontsize=9
        )

    ax.set_xlabel("Distance Group")
    ax.set_ylabel("Delay Percentage")
    plt.xticks(rotation=45)

    st.pyplot(fig)

    st.write("""
    1. Airline Delays by Distance Groups  
**Explanation:** This chart shows the percentage of delays for different airlines, categorized by flight distance.  
**What do we see:** Southwest Airlines experiences the highest delay rates, increasing from 21.49% on short-haul flights to 25.57% on long-haul flights.  
**Connection to the story:** The data highlights the challenge Southwest faces with long-distance flights, 
despite excelling in short-haul operations. Unlike traditional hub-based airlines, Southwest's point-to-point model may struggle with
maintaining efficiency on longer routes, contributing to higher delay rates. 
    """)


def visualize_diverted_flights(df):
    """
    Creates visualization for diverted flights data.
    """
    st.write("### Diversions by Quarter (Pie Chart)")

    # Data preparation
    df['diverted_flights'] = pd.to_numeric(df['diverted_flights'], errors='coerce').fillna(0).astype(int)
    df['quarter'] = pd.to_numeric(df['quarter'], errors='coerce').fillna(0).astype(int)

    diversions_by_quarter = df.groupby('quarter')['diverted_flights'].sum().reset_index()

    if not diversions_by_quarter.empty and diversions_by_quarter['diverted_flights'].sum() > 0:
        fig, ax = plt.subplots(figsize=(8, 8))
        wedges, texts, autotexts = ax.pie(
            diversions_by_quarter['diverted_flights'],
            labels=diversions_by_quarter['quarter'],
            autopct='%1.1f%%',
            startangle=90,
            colors=plt.cm.tab20.colors,
            textprops={'fontsize': 12}
        )

        ax.legend(wedges, diversions_by_quarter['quarter'],
                  title="Quarter", loc="center left",
                  bbox_to_anchor=(1, 0, 0.5, 1))

        ax.set_title("Diversions by Quarter", fontsize=16)
        st.pyplot(fig)
    else:
        st.write("No diversion data available to display")

    st.write("""
       2. Flight Diversions by Quarter  
**Explanation:** This chart presents the distribution of flight diversions throughout the year by quarter.  
**What do we see:** The fourth quarter (30.8%) and third quarter (30.7%) see the most diversions, while the first quarter has the fewest (16.2%).  
**Connection to the story:** Seasonal weather patterns play a crucial role in diversions. 
Winter storms in the fourth quarter, summer thunderstorms in the third, and heavy autumn rains all contribute to a high number of flight deviations.
The holiday season also increases air traffic congestion, making delays and diversions more likely. 
        """)


def visualize_cancellations(df):
    """
    Creates visualization for cancellations data.
    """
    st.write("### Cancellation Rate by State and Quarter")

    df_top = df.groupby('quarter').head(5)

    fig = px.bar(
        df_top,
        y="state",
        x="cancellation_rate",
        color="quarter",
        barmode="group",
        text="rank",
        labels={
            "state": "State",
            "cancellation_rate": "Cancellation Rate (%)",
            "quarter": "Quarter",
            "rank": "Rank"
        },
        title="Top 5 States by Cancellation Rate and Rank by Quarter",
        category_orders={"quarter": [1, 2, 3, 4]},
        orientation="h"
    )

    fig.update_layout(
        xaxis_title="Cancellation Rate (%)",
        yaxis_title="State",
        legend_title="Quarter",
        font=dict(size=12)
    )

    st.plotly_chart(fig)

    st.write("""
               6-7. Cancellation Rate by State and Quarter  
**Explanation:** This chart displays flight cancellation rates by state and quarter.  
**What do we see:** Northeastern states like Vermont and Maine have the highest cancellation rates (up to 8%), with significant variation between quarters.  
**Connection to the story:** Weather conditions are a major factor in cancellations. States in the Northeast are prone 
to severe winter storms, heavy rainfall, and fog, all of which contribute to flight disruptions. 
The data underscores how airlines and passengers in these regions must consistently adapt to unpredictable weather challenges.
                """)


def visualize_flight_analysis(df):
    """
    Creates visualization for flight analysis data.
    """
    st.write("### Scatter Plot: Average Delay vs Total Flights (Matplotlib)")

    fig, ax = plt.subplots(figsize=(10, 6))

    scatter = ax.scatter(
        df['total_flights'],
        df['avg_departure_delay'],
        c=df['day_of_week'],
        cmap='viridis',
        alpha=0.7,
        label='Data Points'
    )

    cbar = plt.colorbar(scatter)
    cbar.set_label('Day of Week')

    ax.set_xlabel("Total Flights")
    ax.set_ylabel("Average Departure Delay (minutes)")
    ax.set_title("Average Departure Delay vs Total Flights (Colored by Day of Week)")
    ax.legend()

    st.pyplot(fig)

    st.write("""
               5. Average Delay vs Total Flights  
**Explanation:** A scatter plot illustrating the relationship between total flights and average delays per airport.  
**What do we see:** Smaller airports show greater delay volatility, especially in the early morning hours. Larger airports maintain more consistent performance throughout the day.  
**Connection to the story:** The size of an airport impacts its ability to manage delays. Smaller airports, with fewer resources and less redundancy in scheduling, experience more unpredictability. Major hubs, equipped with advanced traffic management systems, handle peak-hour congestion more effectively, ensuring smoother operations throughout the day.  

                """)


def visualize_aircraft_performance(df):
    """
    Creates visualization for aircraft performance data.
    """
    st.write("### Trend of Combined Score by Tail Number (Seaborn)")

    top_5_tail_numbers = df.nlargest(5, 'combined_score')

    fig, ax = plt.subplots(figsize=(10, 6))

    sns.lineplot(
        x='Tail_Number',
        y='combined_score',
        data=top_5_tail_numbers,
        marker='o',
        ax=ax
    )

    ax.set_xlabel("Tail Number")
    ax.set_ylabel("Combined Score")
    ax.set_title("Trend of Combined Score by Tail Number (Top 5 Tail Numbers)")
    plt.xticks(rotation=45)

    st.pyplot(fig)

    st.write("""
           4. Trend of Combined Score by Tail Number  
**Explanation:** This chart tracks the performance of individual aircraft based on their tail numbers.  
**What do we see:** Aircraft N407SW has the worst combined performance score (65), indicating frequent and severe delays. Other planes show a gradual improvement in scores.  
**Connection to the story:** Each aircraft tells its own operational story. N407SW’s poor performance could be linked to its age, 
maintenance history, or the challenging routes it flies. Newer planes tend to have better reliability, 
while older ones may accumulate more delays over time due to wear and tear. This reflects how airline fleets evolve and adapt to operational demands.  
            """)



def visualize_state_delays(df):
    """
    Creates visualization for state delays data.
    """
    st.write("### State Rankings by Delay Percentage and Average Delay Time")

    df_top20 = df.nsmallest(20, 'delay_rank')

    fig = px.scatter(
        df_top20,
        x='delay_rank',
        y='delay_percentage',
        size='avg_departure_delay',
        color='avg_departure_delay',
        hover_name='destination_state',
        labels={
            'delay_rank': 'State Rank',
            'delay_percentage': 'Delay Percentage (%)',
            'avg_departure_delay': 'Average Delay Time (minutes)'
        },
        title="Top 20 States by Delay Percentage and Average Delay Time"
    )

    fig.update_layout(
        xaxis_title="State Rank",
        yaxis_title="Delay Percentage (%)",
        legend_title="Average Delay Time (minutes)",
        font=dict(size=12)
    )

    st.plotly_chart(fig)
    st.write("""
               3. State Rankings by Delay  
**Explanation:** This chart ranks states based on their flight delay percentages and average delay durations.  
**What do we see:** The top-ranking states experience delays nearing 28%, with a clear correlation between delay percentage and average delay time.  
**Connection to the story:** Geography and climate are major factors in flight delays. The Northeast, with states like Vermont, Maine, and Massachusetts, 
suffers from harsh weather conditions, dense air traffic, and limited airport capacity, leading to frequent delays. 
These factors make the region one of the most challenging for maintaining on-time performance.  

                """)




def display_table(conn, table_name, page_title):
    """
    Displays table data and corresponding visualizations.

    Args:
        conn: SQLite connection object
        table_name (str): Name of the table to display
        page_title (str): Title of the page
    """
    st.header(page_title)
    st.write(f"This page displays up to 500 rows from the {table_name} table.")

    # Fetch data
    query = f"SELECT * FROM {table_name} LIMIT 500;"
    df = pd.read_sql_query(query, conn)

    # Display styled table
    st.write(f"### Data from {table_name}")
    df_styled = apply_table_styling(df, table_name)
    st.dataframe(df_styled)

    # Call appropriate visualization function based on table name
    visualization_functions = {
        "airline_delays_small": visualize_airline_delays,
        "diverted_flights_small": visualize_diverted_flights,
        "cancellations_rollup_small": visualize_cancellations,
        "flight_analysis_small": visualize_flight_analysis,
        "aircraft_performance_small": visualize_aircraft_performance,
        "state_delays_small": visualize_state_delays
    }

    if table_name in visualization_functions:
        visualization_functions[table_name](df)


def questions_page():
    """
    Displays the Questions page content.
    """
    st.header("Questions")
    st.write("""
    1. What is the percentage of flight delays by airline and distance group? 
       And which airline is ranked with the most delays in each distance group?
    2. What is the percentage of diverted flights by airport and quarter? 
       And what are the diversion trends over time for each airport?
    3. What is the cancellation rate by country and quarter? 
       And which country has the highest cancellation rate in each quarter?
    4. How are takeoff delays distributed according to the days of the week and times of the day? 
       And what is the trend of cumulative delays throughout the day?
    5. What is the performance of airplanes according to tail number? 
       And which airplanes are ranked with the highest delays based on average delay and percentage of delays?
    6. What is the percentage of delays by destination countries? 
       And which country is ranked with the highest delay rate?
    """)

def story_page():
    """
    Displays the Story and Insights page content.
    """
    st.header("Story and Insights")
    # The content remains the same as in your original code
    st.write("""
    ###The story we want to tell: Insights from analyzing flight data from 2018

"A fascinating journey through the skies of America: the complete story of aviation in 2018"

Chapter 1: The Map That Tells It All - The Geography of Flight Delays Imagine a large map of the United States. 
Instead of the usual colors of states, our map is shaded in various tones of blue showing where the most flights are delayed. 
In some states, especially in the Northeast, nearly a third of flights do not depart on time!
Let's focus on three particularly interesting states: Vermont, Maine, and Massachusetts. 
Why are there so many problems there? It starts with the harsh weather - snowstorms in winter, heavy rains in autumn, 
and sometimes even thick fog that makes it difficult for planes to take off and land. But it's not just the weather - 
there's also the fact that these states are located in a dense area with a lot of air traffic, which creates additional challenges.

Chapter 2: The Dance of the Seasons - How the Time of Year Affects Flights. 
Let's dive into the fascinating data on delays and cancellations by season. 
When looking at the pie chart showing the annual distribution, something really interesting stands out:
In the fourth quarter (October-December): 30.8% of the deviations
In the third quarter (July-September): 30.7% of the deviations
In the second quarter (April-June): 22.3% of the deviations
In the first quarter (January-March): 16.2% of the deviations
Why is there such a difference? Let's think about it:
In winter, there are storms and snow.
In autumn, there are storms and rains.
In the summer, there are sudden thunderstorms.
In spring, the weather is more stable.
But it's not just the weather - during the holidays, more people are flying, which adds extra strain on the system.

Chapter 3: The Great Race - The data reveals a fascinating story about the differences between airlines and shows 
how each one deals with the challenge of maintaining flight punctuality and reliability. 
Here’s a close look at two of the most prominent among them:Southwest Airlines leads the table in delay percentages, 
but not in a positive way. The data shows that:
On short flights: 21.49% of the flights were delayed.
On medium-haul flights: the percentage of delays rises to about 23%.
On long flights: the percentage of delays reaches up to 25.57%.
Why does Southwest Airlines lead in delay percentages? Perhaps the reason is related to its unique business model?
United Airlines does indeed perform better than Southwest, but it is still far from perfect:
On long flights: the percentage of delays is lower, but still within the range of 16-18%.
Relative stability: United shows some stability over different distances, but still suffers from significant delay percentages.
Why does United manage to maintain better performance than Southwest? From the data, 
questions arise about why there are such differences. Why do only three companies appear for each distance group? 
It is related to the business model of each company, the type of aircraft they operate, and the way they plan their schedules.

Chapter 4: One of the fascinating findings in the analysis of airport data is how the day and time of departure affect delay times. 
Surprisingly, not only the size of the airport impacts operational stability, but also the daily and hourly dynamics.
What did we discover?
Significantly more delays in the early morning and at small airports – in the early morning hours, 
there is greater variability in delays, especially at small airports (up to 10,000 flights per year).
Shorter delays at major airports throughout most of the day – airports with high traffic (over 40,000 flights per year) 
operate more advanced management systems, which reduces delays especially during peak hours.
The cumulative load effect – as the day progresses, airports with high flight volumes manage to maintain relative stability, 
while at smaller airports, delays can accumulate and extend.

Chapter 5: Every plane is like a character in our story, with ups and downs, achievements and challenges. 
Our graph reveals the stories behind the performance of the planes, showing how each one deals with the challenges of accuracy and reliability in flights.
Here are some prominent characters from our story: N407SW: This plane is ranked first, 
but precisely because it has the highest combined score (65), it actually has the poorest performance in terms of delays. 
The high score is due to a high average delay and a high percentage of delayed flights, 
indicating that this plane faces more challenges in terms of accuracy and reliability. 
The reason for this may be related to the plane's age, the busy flight routes it operates on, or even suboptimal maintenance. 
Despite leading the ranking, it is actually an example of a plane that needs more attention to improve its performance. 
A series of other planes: the graph shows a gradual decline in the composite score as one moves up the ranking. 
Planes like N123AB and N456CD show better performance than N407SW, with lower composite scores, 
indicating a lower average of delays and a lower percentage of delayed flights. Others, like N789EF, show signs of mediocre performance,
perhaps due to their age or high flight frequency. New planes versus old ones: It can be seen that newer planes tend to perform better, 
with lower combined scores. In contrast, older planes, despite their extensive experience, show signs of wear, which affects flight accuracy and delays.
Each plane accumulates its own history: how many flight hours it has logged, which routes it has flown, and how it is maintained. 
Planes that fly on busy routes or in harsh weather conditions tend to accumulate more delays. Newer planes, 
with advanced technology and meticulous maintenance, manage to maintain high performance over time. 
In contrast, older planes, despite their extensive experience, may suffer from wear and more frequent delays.

Summary: The big picture we saw in 2018 is much more than just numbers. 
It's a story about: How does the weather affect our daily lives? How major airlines deal with challenges How airports learn to adapt to traffic. 
And how all of this affects the millions who fly every year. In the end, 
every delay and every change in the schedule affects real people - families waiting to reunite, businesspeople rushing to meetings, 
and tourists wanting to start their vacation. These data tell the story of all of us in the skies of America.

Insights that emerge from the results:

Insights from the graph ranking countries by delay percentages and average delay time:
There is a direct correlation between the percentage of delays and the average delay time - the more delays there are, the longer they tend to be.
The countries at the top of the ranking show delays in about 28% of flights with high average delay times.
A clear trend of gradual decline can be seen, indicating significant disparities between the different countries.
The colors of the dots show that the countries with the worst performance (dark blue) tend to be in the same geographical area.
Please provide the text you would like me to translate.

Insights from the quarterly deviation graph:
There is a very uneven distribution between the quarters.
The third and fourth quarters (30.7% and 30.8%) together account for more than 61% of all deviations.
The first quarter shows the lowest deviation rate (16.2%).
The data indicates a significant seasonal impact on flight deviations.

Insights from the airline graph by distance groups:
Southwest Airlines (WN) leads in delay percentages in most distance groups.
There is a trend of increasing delays as the distance increases.
United Airlines (UA) shows better performance on long-haul flights.
There are significant differences between airlines in the same distance groups.

Insights from the scatter plot of delays versus the number of flights:
There is greater variability in delays at smaller airports.
A trend of stabilization in delay times is evident as the number of flights increases.
The different colors show different patterns according to the days of the week.
Large airports tend to be more efficient in managing delays.

Insights from the cancellation rate graph by country and quarter:
Certain countries show high volatility in cancellation rates between quarters.
The northeastern states lead in cancellation rates.
There is a clear seasonal pattern in the cancellation rates.
Some countries show relative stability throughout the year while others show high volatility.
Please provide the text you would like me to translate.

Insights from the combined score trend graph by tail number:
Certain planes (such as N407SW) exhibit more frequent delays, likely due to the age of the aircraft, the types of routes they operate on, or less optimal maintenance.
Newer planes show better performance with fewer delays, while older planes experience more malfunctions that lead to delays.
The impact of maintenance and the use of advanced technology can significantly reduce delays and increase flight reliability.

Overall conclusion
Flight delays are influenced by a variety of factors – from geographical location and seasons, 
through the operational policies of airlines, to the characteristics of airports and the aircraft themselves.
 While large airports manage delays better, smaller airports still struggle with instability. 
 The future of aviation depends on optimizing air traffic management, investing in advanced forecasting and operational systems, and improving aircraft fleet maintenance.
    """)
    # Rest of the story content...

if __name__ == "__main__":
    main()