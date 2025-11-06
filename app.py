# delhi_metro_dashboard.py
# Requirements: pandas, plotly, dash
# Install if needed: pip install pandas plotly dash

import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output
import numpy as np

# -----------------------------
# Load & clean dataset
# -----------------------------
FILE = "delhi_metro.csv"
df = pd.read_csv(FILE)

app= Dash()
server = app.server

# Normalize and coerce types
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df["Distance_km"] = pd.to_numeric(df.get("Distance_km", pd.Series()), errors="coerce")
df["Fare"] = pd.to_numeric(df.get("Fare", pd.Series()), errors="coerce")
df["Passengers"] = pd.to_numeric(df.get("Passengers", pd.Series()), errors="coerce")

# Fill ticket type for safe dropdown handling
df["Ticket_Type"] = df["Ticket_Type"].astype(str).str.strip().replace({"nan": "Unknown"})
df["From_Station"] = df["From_Station"].astype(str)

# Remove rows without a valid date for time series charts
df_time = df.dropna(subset=["Date"]).copy()

# Precompute some helper columns
df_time["Month"] = df_time["Date"].dt.to_period("M").astype(str)
df_time["Day"] = df_time["Date"].dt.date

# -----------------------------
# Create Dash app & layout
# -----------------------------
app = Dash(__name__)
app.title = "Delhi Metro Analytics"

# Some light CSS for a pleasant landscape layout
CARD_STYLE = {
    "padding": "14px",
    "borderRadius": "8px",
    "background": "#0f172a",  # dark navy
    "color": "white",
    "boxShadow": "0 2px 6px rgba(0,0,0,0.2)",
}
KPI_NUM_STYLE = {"fontSize": "28px", "fontWeight": "700", "marginTop": "6px"}

app.layout = html.Div(
    style={"fontFamily": "Arial, sans-serif", "backgroundColor": "#f7f8fb", "padding": "18px"},
    children=[
        # Header
        html.Div(
            style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"},
            children=[
                html.H2("🚇 Delhi Metro Analytics Dashboard", style={"margin": "0"}),
                html.Div("Interactive Dashboard With added filters", style={"color": "#555"})
            ],
        ),

        html.Br(),

        # KPI row
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "repeat(5, 1fr)", "gap": "12px"},
            children=[
                html.Div([
                    html.Div("Total Trips", style={"color": "#aab7d6", "fontSize": "13px"}),
                    html.Div(id="kpi_total_trips", style=KPI_NUM_STYLE)
                ], style=CARD_STYLE),
                html.Div([
                    html.Div("Total Passengers", style={"color": "#aab7d6", "fontSize": "13px"}),
                    html.Div(id="kpi_total_passengers", style=KPI_NUM_STYLE)
                ], style=CARD_STYLE),
                html.Div([
                    html.Div("Total Revenue (Fare)", style={"color": "#aab7d6", "fontSize": "13px"}),
                    html.Div(id="kpi_total_revenue", style=KPI_NUM_STYLE)
                ], style=CARD_STYLE),
                html.Div([
                    html.Div("Avg Fare", style={"color": "#aab7d6", "fontSize": "13px"}),
                    html.Div(id="kpi_avg_fare", style=KPI_NUM_STYLE)
                ], style=CARD_STYLE),
                html.Div([
                    html.Div("Avg Distance (km)", style={"color": "#aab7d6", "fontSize": "13px"}),
                    html.Div(id="kpi_avg_distance", style=KPI_NUM_STYLE)
                ], style=CARD_STYLE),
            ],
        ),

        html.Br(),

        # Filters row
        html.Div(
            style={"display": "flex", "gap": "12px", "alignItems": "center"},
            children=[
                html.Div([
                    html.Div("Date range", style={"fontSize": "13px", "color": "#333"}),
                    dcc.DatePickerRange(
                        id="date-range",
                        display_format="YYYY-MM-DD",
                        start_date=df_time["Date"].min(),
                        end_date=df_time["Date"].max(),
                        min_date_allowed=df_time["Date"].min(),
                        max_date_allowed=df_time["Date"].max(),
                    ),
                ], style={"flex": "0 0 360px", "background": "white", "padding": "8px", "borderRadius": "8px"}),

                html.Div([
                    html.Div("From Station", style={"fontSize": "13px", "color": "#333"}),
                    dcc.Dropdown(
                        id="from-station-filter",
                        options=[{"label": s, "value": s} for s in sorted(df["From_Station"].unique())],
                        multi=True,
                        placeholder="Select from-stations (or leave all)"
                    )
                ], style={"flex": "1", "background": "white", "padding": "8px", "borderRadius": "8px"}),

                html.Div([
                    html.Div("Ticket Type", style={"fontSize": "13px", "color": "#333"}),
                    dcc.Dropdown(
                        id="ticket-filter",
                        options=[{"label": t, "value": t} for t in sorted(df["Ticket_Type"].unique())],
                        multi=True,
                        placeholder="Select ticket types (or leave all)"
                    )
                ], style={"flex": "0 0 360px", "background": "white", "padding": "8px", "borderRadius": "8px"}),
            ],
        ),

        html.Br(),

        # Top charts row (two side-by-side)
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "12px"},
            children=[
                html.Div(dcc.Graph(id="chart_passengers_trend"), style={"background": "white", "padding": "8px", "borderRadius": "8px"}),
                html.Div(dcc.Graph(id="chart_revenue_tickettype"), style={"background": "white", "padding": "8px", "borderRadius": "8px"}),
            ],
        ),

        html.Br(),

        # Middle charts row (two side-by-side)
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "12px"},
            children=[
                html.Div(dcc.Graph(id="chart_ticket_pie"), style={"background": "white", "padding": "8px", "borderRadius": "8px"}),
                html.Div(dcc.Graph(id="chart_top_stations"), style={"background": "white", "padding": "8px", "borderRadius": "8px"}),
            ],
        ),

        html.Br(),

        # Bottom charts row (wide + side)
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "2fr 1fr", "gap": "12px"},
            children=[
                html.Div(dcc.Graph(id="chart_revenue_trend"), style={"background": "white", "padding": "8px", "borderRadius": "8px"}),
                html.Div(dcc.Graph(id="chart_scatter"), style={"background": "white", "padding": "8px", "borderRadius": "8px"}),
            ],
        ),

        html.Br(),
        html.Div("Data source: delhi_metro.csv", style={"color": "#555", "fontSize": "12px"}),
    ]
)

# -----------------------------
# Callbacks: update all charts and KPIs
# -----------------------------
@app.callback(
    [
        Output("kpi_total_trips", "children"),
        Output("kpi_total_passengers", "children"),
        Output("kpi_total_revenue", "children"),
        Output("kpi_avg_fare", "children"),
        Output("kpi_avg_distance", "children"),
        Output("chart_passengers_trend", "figure"),
        Output("chart_revenue_tickettype", "figure"),
        Output("chart_ticket_pie", "figure"),
        Output("chart_top_stations", "figure"),
        Output("chart_revenue_trend", "figure"),
        Output("chart_scatter", "figure"),
    ],
    [
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
        Input("from-station-filter", "value"),
        Input("ticket-filter", "value"),
    ],
)
def update_all(start_date, end_date, selected_stations, selected_tickets):
    # Filter time window
    dff = df_time.copy()
    if start_date:
        dff = dff[dff["Date"] >= pd.to_datetime(start_date)]
    if end_date:
        dff = dff[dff["Date"] <= pd.to_datetime(end_date)]

    # Filter stations and ticket types if provided
    if selected_stations:
        dff = dff[dff["From_Station"].isin(selected_stations)]
    if selected_tickets:
        dff = dff[dff["Ticket_Type"].isin(selected_tickets)]

    # KPIs
    total_trips = int(dff.shape[0])
    total_passengers = int(dff["Passengers"].sum(skipna=True)) if "Passengers" in dff else "N/A"
    total_revenue = float(dff["Fare"].sum(skipna=True)) if "Fare" in dff else np.nan
    avg_fare = float(dff["Fare"].mean(skipna=True)) if "Fare" in dff else np.nan
    avg_distance = float(dff["Distance_km"].mean(skipna=True)) if "Distance_km" in dff else np.nan

    # Format KPI strings
    kp_total_trips = f"{total_trips:,}"
    kp_total_passengers = f"{total_passengers:,}" if total_passengers != "N/A" else "N/A"
    kp_total_revenue = f"₹ {total_revenue:,.2f}" if not pd.isna(total_revenue) else "N/A"
    kp_avg_fare = f"₹ {avg_fare:,.2f}" if not pd.isna(avg_fare) else "N/A"
    kp_avg_distance = f"{avg_distance:.2f} km" if not pd.isna(avg_distance) else "N/A"

    # Chart 1: Passengers trend (line)
    passengers_by_day = dff.groupby("Date")["Passengers"].sum().reset_index()
    fig_passengers_trend = px.line(passengers_by_day, x="Date", y="Passengers",
                                  title="Passengers Trend (by Day)", markers=True)
    fig_passengers_trend.update_layout(margin=dict(t=40, b=20))

    # Chart 2: Revenue by Ticket Type (grouped bar)
    if "Fare" in dff.columns:
        rev_by_ticket = dff.groupby("Ticket_Type")["Fare"].sum().reset_index().sort_values("Fare", ascending=False)
        fig_revenue_ticket = px.bar(rev_by_ticket, x="Ticket_Type", y="Fare", title="Revenue by Ticket Type",
                                   labels={"Fare": "Total Fare (₹)", "Ticket_Type": "Ticket Type"})
    else:
        fig_revenue_ticket = px.bar(title="No Fare column available")
    fig_revenue_ticket.update_layout(margin=dict(t=40, b=20))

    # Chart 3: Ticket Type share (donut)
    ticket_counts = dff["Ticket_Type"].value_counts().reset_index()
    ticket_counts.columns = ["Ticket_Type", "Count"]
    fig_ticket_pie = px.pie(ticket_counts, names="Ticket_Type", values="Count", hole=0.45, title="Ticket Type Share")
    fig_ticket_pie.update_traces(textposition="inside", textinfo="percent+label")
    fig_ticket_pie.update_layout(margin=dict(t=40, b=20))

    # Chart 4: Top 10 From_Stations by boarding count (horizontal bar)
    top_stations = dff["From_Station"].value_counts().nlargest(10).reset_index()
    top_stations.columns = ["From_Station", "Count"]
    fig_top_stations = px.bar(top_stations.sort_values("Count"), x="Count", y="From_Station", orientation="h",
                              title="Top 10 Boarding Stations")
    fig_top_stations.update_layout(margin=dict(t=40, b=20))

    # Chart 5: Revenue trend (area)
    if "Fare" in dff.columns:
        revenue_trend = dff.groupby("Date")["Fare"].sum().reset_index()
        fig_revenue_trend = px.area(revenue_trend, x="Date", y="Fare", title="Revenue Trend (by Day)")
        fig_revenue_trend.update_layout(margin=dict(t=40, b=20))
    else:
        fig_revenue_trend = px.area(title="No Fare column available")

    # Chart 6: Scatter -> Passengers vs Distance (size by Fare)
    scatter_df = dff.dropna(subset=["Passengers", "Distance_km"], how="any").copy()
    if not scatter_df.empty:
        size_col = "Fare" if "Fare" in scatter_df else None
        fig_scatter = px.scatter(scatter_df, x="Distance_km", y="Passengers", size=size_col, color="Ticket_Type",
                                 title="Passengers vs Distance (size=Fare)",
                                 labels={"Distance_km": "Distance (km)", "Passengers": "Passengers"})
        fig_scatter.update_layout(margin=dict(t=40, b=20))
    else:
        fig_scatter = px.scatter(title="Not enough data for scatter chart")

    return (
        kp_total_trips,
        kp_total_passengers,
        kp_total_revenue,
        kp_avg_fare,
        kp_avg_distance,
        fig_passengers_trend,
        fig_revenue_ticket,
        fig_ticket_pie,
        fig_top_stations,
        fig_revenue_trend,
        fig_scatter,
    )


# -----------------------------
# Run server
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True, port=8051)
