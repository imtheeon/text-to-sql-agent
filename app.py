"""Streamlit chat interface for the Text-to-SQL Auto-Viz Analytics Agent."""
import os
import streamlit as st
from dotenv import load_dotenv

from data.setup_db import setup_database
from agents.sql_agent import ask
from agents.viz_agent import auto_visualize

load_dotenv()

st.set_page_config(
    page_title="Analytics Agent",
    page_icon="🤖",
    layout="wide"
)


@st.cache_resource
def init_db():
    setup_database()
    return True


init_db()

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🤖 Analytics Agent")
    st.caption("Ask business questions in plain English.")
    st.divider()
    st.subheader("Example questions")

    examples = [
        "Show monthly revenue trend for 2023",
        "Which 5 products generated the most revenue?",
        "What percentage of customers have churned by tier?",
        "Which marketing channel has the highest conversion rate?",
        "Show total orders and revenue by region",
        "Compare profit margin across product categories",
        "Which campaigns had the best ROI?",
        "Show revenue by customer tier over time",
    ]

    for ex in examples:
        if st.button(ex, use_container_width=True):
            st.session_state.pending_question = ex

    st.divider()
    st.caption("Powered by Claude Haiku + DuckDB")

# ── Main ────────────────────────────────────────────────────────────────────
st.title("📊 Text-to-SQL Analytics Agent")
st.caption("Type a business question below — I'll write the SQL and pick the right chart.")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

# Render chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "user":
            st.write(msg["content"])
        else:
            st.code(msg["sql"], language="sql")
            col1, col2 = st.columns([3, 2])
            with col1:
                if msg.get("fig"):
                    st.plotly_chart(msg["fig"], use_container_width=True)
            with col2:
                st.dataframe(msg["df"], use_container_width=True)

# Accept input
user_input = st.chat_input("Ask a question about your data...")
if st.session_state.pending_question:
    user_input = st.session_state.pending_question
    st.session_state.pending_question = None

if user_input:
    if not os.getenv("ANTHROPIC_API_KEY"):
        st.error("⚠️ ANTHROPIC_API_KEY not found. Create a .env file with your key.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                sql, df = ask(user_input)
                fig = auto_visualize(df, user_input)

                st.code(sql, language="sql")
                col1, col2 = st.columns([3, 2])
                with col1:
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No chart generated for this result shape.")
                with col2:
                    st.dataframe(df, use_container_width=True)

                st.session_state.messages.append({
                    "role": "assistant",
                    "sql": sql,
                    "fig": fig,
                    "df": df
                })
            except Exception as e:
                st.error(f"❌ Error: {e}")
