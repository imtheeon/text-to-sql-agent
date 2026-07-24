"""Auto-select the best Plotly chart based on DataFrame shape and column types."""
import pandas as pd
import plotly.express as px
from plotly.graph_objects import Figure


def auto_visualize(df: pd.DataFrame, question: str = "") -> Figure | None:
    if df.empty or len(df.columns) < 1:
        return None

    cols = df.columns.tolist()
    date_cols = [c for c in cols if pd.api.types.is_datetime64_any_dtype(df[c])
                 or any(k in c.lower() for k in ("date", "month", "year", "week", "period"))]
    num_cols  = [c for c in cols if pd.api.types.is_numeric_dtype(df[c])]
    cat_cols  = [c for c in cols if c not in date_cols and c not in num_cols]

    # Time series → line chart
    if date_cols and num_cols:
        try:
            df[date_cols[0]] = pd.to_datetime(df[date_cols[0]])
            df = df.sort_values(date_cols[0])
        except Exception:
            pass
        color = cat_cols[0] if cat_cols else None
        fig = px.line(
            df, x=date_cols[0], y=num_cols[0], color=color,
            title=question or "Trend Over Time",
            markers=True
        )
        return fig

    # Two numerics, no categories → scatter
    if len(num_cols) >= 2 and not cat_cols:
        fig = px.scatter(
            df, x=num_cols[0], y=num_cols[1],
            title=question or f"{num_cols[1]} vs {num_cols[0]}",
            trendline="ols"
        )
        return fig

    # Category + numeric → bar chart
    if cat_cols and num_cols:
        orient = "h" if len(df) > 8 else "v"
        if orient == "h":
            fig = px.bar(
                df, x=num_cols[0], y=cat_cols[0], orientation="h",
                title=question or f"{num_cols[0]} by {cat_cols[0]}",
                color=num_cols[0], color_continuous_scale="Blues"
            )
        else:
            fig = px.bar(
                df, x=cat_cols[0], y=num_cols[0],
                title=question or f"{num_cols[0]} by {cat_cols[0]}",
                color=cat_cols[0]
            )
        return fig

    # Single numeric → histogram
    if num_cols:
        fig = px.histogram(
            df, x=num_cols[0],
            title=question or f"Distribution of {num_cols[0]}"
        )
        return fig

    return None
