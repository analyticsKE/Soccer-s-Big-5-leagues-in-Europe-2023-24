import sys
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import os
from scipy import stats

# Set page config
st.set_page_config(page_title="Big 5 League Stats in Europe 2023/24", layout="wide")

# Load data
@st.cache_data
def load_data():
    file_name = "data/data.csv"
    if not os.path.exists(file_name):
        st.error(f"Error: The file '{file_name}' was not found. Please make sure it's in the 'data' folder.")
        st.stop()
    try:
        return pd.read_csv(file_name)
    except Exception as e:
        st.error(f"Error loading the CSV file: {str(e)}")
        st.stop()

# Load data
try:
    df = load_data()
except Exception as e:
    st.error(f"An unexpected error occurred: {str(e)}")
    st.stop()

# Define color scheme for leagues
league_colors = {
    "England": "#3d195b",  # Premier League purple
    "Spain": "#ee8707",    # La Liga orange
    "Germany": "#d20515",  # Bundesliga red
    "Italy": "#008fd7",    # Serie A blue
    "France": "#091c3e"    # Ligue 1 navy
}

# Title and Instructions
st.title("⚽ Big 5 League Stats in Europe 2023/24")
st.markdown("""
This dashboard provides a comprehensive overview of the top 5 European football leagues for the 2023/24 season. 
Explore team performances, top scorers, and in-depth statistics to gain insights into the beautiful game across Europe.
""")

with st.expander("ℹ️ How to use this dashboard"):
    st.write("""
    1. Use the sidebar to filter by country. You can select multiple countries for comparison.
    2. Explore the league table and top scorers in the first row.
    3. Analyze team performance, expected vs actual goals, and attendance data in the charts below.
    4. Use the Team Analysis section for detailed insights on specific teams.
    5. Hover over data points in charts for more information.
    6. The League-wide Analysis section provides broader trends and comparisons.
    """)

# Sidebar for filtering
st.sidebar.header("Filters")
selected_country = st.sidebar.multiselect("Select Country", options=df["Country"].unique(), default=df["Country"].unique())

# Filter dataframe
df_filtered = df[df["Country"].isin(selected_country)]

# Main content
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 League Table")
    st.dataframe(df_filtered[["Team", "Country", "LeagueRanking", "Matches Played", "Points", "Wins", "Draws", "Losses", "GoalsFor", "GoalsAgainst", "GoalDifference"]]
                 .sort_values(["Country", "LeagueRanking"])
                 .reset_index(drop=True), 
                 use_container_width=True)

with col2:
    st.subheader("🏆 Top Scorers")
    
    # Select a country for top scorers
    scorer_country = st.selectbox("Select a country to view top scorers", options=selected_country)
    
    # Filter top scorers for the selected country
    country_top_scorers = df_filtered[df_filtered["Country"] == scorer_country][["TopScorer", "TopScorerGoals", "Team"]].copy()
    country_top_scorers = country_top_scorers.sort_values("TopScorerGoals", ascending=False).head(10)
    
    fig_top_scorers = px.bar(country_top_scorers, 
                             x="TopScorer", y="TopScorerGoals", 
                             title=f"Top 10 Scorers in {scorer_country}",
                             labels={"TopScorer": "Player", "TopScorerGoals": "Goals"},
                             color="TopScorerGoals",
                             color_continuous_scale=px.colors.sequential.Viridis,
                             hover_data=["Team"])
    fig_top_scorers.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_top_scorers, use_container_width=True)

# Enhanced Team Analysis Section
st.header("🔍 Team Analysis")
st.markdown("""
Select a team to dive deep into their performance metrics, including points, goal difference, 
expected goals (xG), and more. The radar chart provides a quick visual comparison of the team's 
performance across various categories.
""")

selected_team = st.selectbox("Select a team for detailed analysis", options=df_filtered["Team"].unique())
team_data = df_filtered[df_filtered["Team"] == selected_team].iloc[0]

col3, col4, col5, col6 = st.columns(4)
col3.metric("Points", team_data["Points"])
col4.metric("Goal Difference", team_data["GoalDifference"])
col5.metric("xG", round(team_data["xG"], 2))
col6.metric("xGA", round(team_data["xGA"], 2))

# Performance Radar Chart
st.subheader("Performance Radar")
categories = ['Points', 'GoalsFor', 'GoalsAgainst', 'xG', 'xGA', 'Attendance']
fig_radar = go.Figure()

# Calculate percentiles for each category
percentiles = {}
for cat in categories:
    percentiles[cat] = stats.percentileofscore(df_filtered[cat], team_data[cat])

fig_radar.add_trace(go.Scatterpolar(
    r=[percentiles[cat] for cat in categories],
    theta=categories,
    fill='toself',
    name=selected_team
))

fig_radar.update_layout(
    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
    showlegend=True
)

st.plotly_chart(fig_radar, use_container_width=True)

st.markdown(f"""
The radar chart above shows how **{selected_team}** performs across various metrics compared to other teams in the league(s).
A score of 100 in any category means the team is the best in that aspect, while 0 indicates room for improvement.
""")

# Expected vs Actual Goals Analysis
st.subheader("Expected vs Actual Goals Analysis")
col7, col8 = st.columns(2)

with col7:
    xg_diff = team_data["GoalsFor"] - team_data["xG"]
    delta_text = f"{'Overperforming' if xg_diff > 0 else 'Underperforming'} by {abs(xg_diff):.2f} goals"
    delta_color = "normal" if xg_diff > 0 else "inverse"
    st.metric("Goals vs xG", f"{xg_diff:.2f}", delta=delta_text, delta_color=delta_color)

with col8:
    xga_diff = team_data["GoalsAgainst"] - team_data["xGA"]
    delta_text = f"{'Underperforming' if xga_diff > 0 else 'Overperforming'} by {abs(xga_diff):.2f} goals"
    delta_color = "inverse" if xga_diff > 0 else "normal"
    st.metric("Goals Against vs xGA", f"{xga_diff:.2f}", delta=delta_text, delta_color=delta_color)

st.markdown(f"""
**{selected_team}** is {'overperforming' if xg_diff > 0 else 'underperforming'} in attack, 
scoring **{abs(xg_diff):.2f}** {'more' if xg_diff > 0 else 'fewer'} goals than expected.

Defensively, they are {'underperforming' if xga_diff > 0 else 'overperforming'}, 
conceding **{abs(xga_diff):.2f}** {'more' if xga_diff > 0 else 'fewer'} goals than expected.
""")

# Form Analysis
st.subheader("Form Analysis")
form_data = df_filtered[df_filtered["Team"] == selected_team][["Wins", "Draws", "Losses"]].iloc[0]
fig_form = go.Figure(data=[go.Pie(labels=["Wins", "Draws", "Losses"], values=form_data, hole=.3)])
fig_form.update_layout(title="Match Outcomes Distribution")
st.plotly_chart(fig_form, use_container_width=True)

st.markdown(f"""
**{selected_team}**'s season so far:
- Wins: {form_data['Wins']}
- Draws: {form_data['Draws']}
- Losses: {form_data['Losses']}

This distribution gives insight into the team's consistency and ability to secure points throughout the season.
""")

# League-wide Analysis
st.header("📊 League-wide Analysis")
st.markdown("""
This section provides a broader perspective on team performances across the selected leagues. 
Explore how teams compare in terms of expected points, actual points, and the relationship between attendance and performance.
""")

# Points vs Expected Points
st.subheader("Points vs Expected Points")
df_filtered['xPoints'] = df_filtered['xG'] * 3 - df_filtered['xGA'] * 3

# Ensure size parameter is non-negative
size_values = df_filtered['GoalDifference'].abs()  # Taking absolute values

fig_xpoints = px.scatter(df_filtered, x="xPoints", y="Points", 
                         hover_name="Team", size=size_values, color="Country",
                         color_discrete_map=league_colors,
                         labels={"xPoints": "Expected Points", "Points": "Actual Points"},
                         title="Actual Points vs Expected Points")

# Add y=x line
fig_xpoints.add_trace(go.Scatter(x=[df_filtered['xPoints'].min(), df_filtered['xPoints'].max()], 
                                 y=[df_filtered['xPoints'].min(), df_filtered['xPoints'].max()],
                                 mode='lines', name='y=x', line=dict(dash='dash')))

st.plotly_chart(fig_xpoints, use_container_width=True)

st.markdown("""
This scatter plot compares each team's actual points against their expected points based on xG and xGA. 
Teams above the dashed line are overperforming, while those below are underperforming relative to expectations.
The size of each point represents the absolute value of the team's goal difference, providing additional context to their performance.
""")

# Attendance vs Performance
st.subheader("Attendance vs Performance")
fig_att_perf = px.scatter(df_filtered, x="Attendance", y="Points", 
                          hover_name="Team", size="GoalsFor", color="Country",
                          color_discrete_map=league_colors,
                          labels={"Attendance": "Average Attendance", "Points": "Points"},
                          title="Team Performance vs Average Attendance")
st.plotly_chart(fig_att_perf, use_container_width=True)

st.markdown("""
This chart explores the relationship between a team's average attendance and their performance (measured in points). 
The size of each point represents the number of goals scored by the team.

Interesting observations:   
- Teams with higher attendance often (but not always) perform better.
- Some teams overperform despite lower attendance, while others underperform despite high attendance.
- Goal-scoring (indicated by point size) doesn't always correlate directly with points or attendance.
""")

# Performance Efficiency Analysis
st.subheader("Performance Efficiency Analysis")

# Add country filter for this specific chart
countries_for_efficiency = st.multiselect(
    "Select countries for efficiency analysis",
    options=df['Country'].unique(),
    default=df['Country'].unique()
)

# Filter data based on selected countries
df_efficiency = df_filtered[df_filtered['Country'].isin(countries_for_efficiency)]

# Calculate performance metrics
df_efficiency['Offensive_Efficiency'] = df_efficiency['GoalsFor'] / df_efficiency['xG']
df_efficiency['Defensive_Efficiency'] = df_efficiency['xGA'] / df_efficiency['GoalsAgainst']
df_efficiency['Overall_Efficiency'] = (df_efficiency['Offensive_Efficiency'] + df_efficiency['Defensive_Efficiency']) / 2

# Create custom hover text
df_efficiency['hover_text'] = df_efficiency.apply(lambda row: 
    f"Team: {row['Team']}<br>" +
    f"League: {row['Country']}<br>" +
    f"Points: {row['Points']}<br>" +
    f"Offensive Efficiency: {row['Offensive_Efficiency']:.2f}<br>" +
    f"Defensive Efficiency: {row['Defensive_Efficiency']:.2f}<br>" +
    f"Overall Efficiency: {row['Overall_Efficiency']:.2f}", axis=1)

fig_efficiency = px.scatter(df_efficiency, 
                            x="Offensive_Efficiency", 
                            y="Defensive_Efficiency", 
                            size="Points",
                            color="Country",
                            hover_name="Team",
                            hover_data={
                                "Offensive_Efficiency": ":.2f",
                                "Defensive_Efficiency": ":.2f",
                                "Points": True,
                                "Country": True,
                                "Team": False  # Hide team name from hover (it's already in hover_name)
                            },
                            custom_data=["hover_text"],
                            color_discrete_map=league_colors,
                            labels={
                                "Offensive_Efficiency": "Offensive Efficiency (Goals / xG)",
                                "Defensive_Efficiency": "Defensive Efficiency (xGA / Goals Against)",
                            },
                            title="Team Performance Efficiency")

# Add quadrant lines
fig_efficiency.add_hline(y=1, line_dash="dash", line_color="gray")
fig_efficiency.add_vline(x=1, line_dash="dash", line_color="gray")

# Update layout for better readability and spread
fig_efficiency.update_layout(
    xaxis=dict(range=[0.6, 1.4], dtick=0.1),
    yaxis=dict(range=[0.6, 1.4], dtick=0.1),
    xaxis_title="Offensive Efficiency (Goals / xG)",
    yaxis_title="Defensive Efficiency (xGA / Goals Against)",
    hovermode="closest"
)

# Update hover template
fig_efficiency.update_traces(
    hovertemplate="%{customdata[0]}<extra></extra>"
)

st.plotly_chart(fig_efficiency, use_container_width=True)

st.markdown("""
This Performance Efficiency Chart provides a comprehensive view of team performance across the selected leagues:

- **Offensive Efficiency** (x-axis): Ratio of actual goals scored to expected goals (xG). Values > 1 indicate overperformance.
- **Defensive Efficiency** (y-axis): Ratio of expected goals against (xGA) to actual goals conceded. Values > 1 indicate overperformance.
- **Bubble Size**: Represents the total points earned by the team.
- **Color**: Indicates the country/league of each team.

Quadrant Interpretation:
- **Top-Right**: Teams overperforming in both offense and defense.
- **Top-Left**: Defensively strong but offensively underperforming.
- **Bottom-Right**: Offensively strong but defensively underperforming.
- **Bottom-Left**: Underperforming in both offense and defense.

Hover over data points to see detailed information for each team.
""")

# Top Performers Table
st.subheader("Top Overall Performers")
top_performers = df_efficiency.sort_values("Overall_Efficiency", ascending=False).head(10)
st.dataframe(top_performers[["Team", "Country", "Points", "Offensive_Efficiency", "Defensive_Efficiency", "Overall_Efficiency"]]
             .style.format({
                 "Offensive_Efficiency": "{:.2f}",
                 "Defensive_Efficiency": "{:.2f}",
                 "Overall_Efficiency": "{:.2f}"
             }),
             use_container_width=True)

st.markdown("""
The table above shows the top 10 teams in terms of overall performance efficiency, 
combining both offensive and defensive metrics. This provides insight into which teams 
are most effectively converting their expected performance into actual results.
""")

# Top Performers Table
st.subheader("Top Overall Performers")
top_performers = df_efficiency.sort_values("Overall_Efficiency", ascending=False).head(10)
st.dataframe(top_performers[["Team", "Country", "Points", "Offensive_Efficiency", "Defensive_Efficiency", "Overall_Efficiency"]]
             .style.format({
                 "Offensive_Efficiency": "{:.2f}",
                 "Defensive_Efficiency": "{:.2f}",
                 "Overall_Efficiency": "{:.2f}"
             }),
             use_container_width=True)

st.markdown("""
The table above shows the top 10 teams in terms of overall performance efficiency, 
combining both offensive and defensive metrics. This provides insight into which teams 
are most effectively converting their expected performance into actual results.
""")

# Footer
st.markdown("---")
st.markdown("Data last updated: 2024-07-08")
st.markdown("""
Created by [Dennis Seroney] | [analyticske.github.io]

Data source: [FBREF]
""")