import os
import sys
import time
from pathlib import Path
 
# Streamlit Cloud ships an old system SQLite that ChromaDB rejects.
# If pysqlite3-binary is installed (see requirements.txt), use it instead.
try:
    __import__("pysqlite3")
    sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
except ImportError:
    pass
 
import streamlit as st
from dotenv import load_dotenv
 
load_dotenv()
 
# ----------------------------------------------------------------------------
# Config - edit these
# ----------------------------------------------------------------------------
APP_NAME = "Quenn: Flipkart Shopping Assistant"
TAGLINE = "Your AI shopping assistant: ask about store policies or find the perfect pair of shoes."
AUTHOR = "Sarthak"
 
FAQ_PATH = Path(__file__).parent / "resources" / "faq_data.csv"
MAX_QUESTIONS = 8  # questions allowed per visitor session
 
ROUTE_BADGES = {
    "faq": ("📘", "Store policies"),
    "sql": ("🛒", "Product search"),
    "error": ("⚠️", "Error"),
}
 
EXAMPLES = [
    ("📦 Defective product policy", "What is your policy on defective products?"),
    ("💳 Card discounts", "On which card there is discount and how much is it?"),
    ("👟 Top Nike shoes", "Show me top 3 Nike shoes with rating higher than 4.5"),
    ("🏷️ Puma under ₹3000", "Show me Puma shoes under Rs. 3000"),
]
 
st.set_page_config(
    page_title=APP_NAME,
    page_icon="🛍️",
    layout="centered",
    initial_sidebar_state="expanded",
)
 
# ----------------------------------------------------------------------------
# Styling (works in light and dark mode)
# ----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {padding-top: 2rem; max-width: 860px;}
 
    .hero {
        padding: 1.5rem 1.75rem;
        border-radius: 18px;
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 55%, #db2777 100%);
        color: #ffffff;
        margin-bottom: 1.25rem;
        box-shadow: 0 8px 24px rgba(79, 70, 229, 0.25);
    }
    .hero-title {font-size: 2rem; font-weight: 800; line-height: 1.2; margin: 0;}
    .hero-sub {margin: 0.4rem 0 0 0; opacity: 0.92; font-size: 1.02rem;}
 
    .badge {
        display: inline-block;
        padding: 2px 10px;
        margin-bottom: 6px;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
        background: rgba(124, 58, 237, 0.14);
        color: #7c3aed;
        border: 1px solid rgba(124, 58, 237, 0.35);
    }
    .stack-pill {
        display: inline-block;
        padding: 2px 9px;
        margin: 2px 3px 2px 0;
        border-radius: 8px;
        font-size: 0.75rem;
        background: rgba(128, 128, 128, 0.16);
    }
    .footer-note {text-align: center; opacity: 0.6; font-size: 0.8rem; margin-top: 2rem;}
    </style>
    """,
    unsafe_allow_html=True,
)
 
# ----------------------------------------------------------------------------
# API key check (Streamlit Cloud secrets are exposed as environment variables)
# ----------------------------------------------------------------------------
if not os.getenv("GROQ_API_KEY"):
    st.error(
        "**GROQ_API_KEY is missing.** Locally, add it to your `.env` file. "
        "On Streamlit Cloud, add it under *App settings → Secrets*."
    )
    st.stop()
 
 
# ----------------------------------------------------------------------------
# Backend (loaded once per server, not on every message)
# ----------------------------------------------------------------------------
@st.cache_resource(show_spinner="Warming up the assistant (the first load can take a minute)...")
def load_backend():
    from faq import faq_chain, ingest_faq_data, vector_store
    from route import router
    from sql import sql_chain
 
    if vector_store._collection.count() == 0:
        ingest_faq_data(FAQ_PATH)
    return router, faq_chain, sql_chain
 
 
def ask(query: str):
    """Returns (answer, route_key)."""
    try:
        router, faq_chain, sql_chain = load_backend()
        route = router(query).name  # None when nothing matches
 
        if route == "sql":
            return sql_chain(query), "sql"
        # "faq" or no match: the FAQ prompt says "I don't know" when nothing fits
        return faq_chain.invoke(query), "faq"
    except Exception as e:
        print(f"Error handling query: {e}")  # visible only in Manage app -> Logs
        return "Sorry, I couldn't process that right now. Please try again in a minute.", "error"
 
 
def badge(route: str):
    icon, label = ROUTE_BADGES.get(route, ROUTE_BADGES["faq"])
    st.markdown(f'<span class="badge">{icon} {label}</span>', unsafe_allow_html=True)
 
 
def stream_text(text: str):
    """Small typing effect for a more polished feel."""
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.012)
 
 
# ----------------------------------------------------------------------------
# Sidebar
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"### 🛍️ {APP_NAME}")
    st.caption("A retrieval-augmented chatbot with intelligent query routing.")
 
    st.markdown("**How it works**")
    st.markdown(
        """
        1. A **semantic router** classifies your question
        2. **Store policies** → RAG over an FAQ vector database
        3. **Product questions** → LLM writes SQL, runs it on a product database
        4. The LLM turns the results into a friendly answer
        """
    )
 
    st.markdown("**Tech stack**")
    st.markdown(
        "".join(
            f'<span class="stack-pill">{t}</span>'
            for t in [
                "Python", "LangChain", "Groq", "ChromaDB", "Semantic Router",
                "Sentence-Transformers", "SQLite", "Pandas", "Streamlit",
            ]
        ),
        unsafe_allow_html=True,
    )
 
    st.divider()
    if st.button("🗑️ Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
 
    
 
# ----------------------------------------------------------------------------
# Main area
# ----------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="hero">
        <div class="hero-title">🛍️ {APP_NAME}</div>
        <p class="hero-sub">{TAGLINE}</p>
    </div>
    """,
    unsafe_allow_html=True,
)
 
if "messages" not in st.session_state:
    st.session_state.messages = []
 
# Example prompts (only shown before the first message)
example_area = st.empty()
if not st.session_state.messages:
    with example_area.container():
        with st.chat_message("assistant", avatar="🛍️"):
            st.markdown(
                "Hi! I can answer questions about **returns, delivery, payments and offers**, "
                "and help you **find products** by brand, price, rating or discount. "
                "Try one of these:"
            )
        cols = st.columns(2)
        for i, (label, prompt_text) in enumerate(EXAMPLES):
            if cols[i % 2].button(label, key=f"example_{i}", use_container_width=True):
                st.session_state["pending_query"] = prompt_text
 
# Replay history
for message in st.session_state.messages:
    avatar = "🧑‍💻" if message["role"] == "user" else "🛍️"
    with st.chat_message(message["role"], avatar=avatar):
        if message["role"] == "assistant":
            badge(message.get("route", "faq"))
        st.markdown(message["content"])
 
typed = st.chat_input("Ask about store policies or search for products...")
query = typed or st.session_state.pop("pending_query", None)

OWNER_CODE = os.getenv("OWNER_CODE")
is_owner = bool(OWNER_CODE) and st.query_params.get("owner") == OWNER_CODE
 
if query:
    if not is_owner and st.session_state.get("question_count", 0) >= MAX_QUESTIONS:
        st.info("Demo limit reached for this session. Refresh the page to continue.")
        st.stop()
    st.session_state["question_count"] = st.session_state.get("question_count", 0) + 1

    example_area.empty()
 
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(query)
    st.session_state.messages.append({"role": "user", "content": query})
 
    with st.chat_message("assistant", avatar="🛍️"):
        with st.spinner("Thinking..."):
            answer, route = ask(query)
        badge(route)
        st.write_stream(stream_text(answer))
 
    st.session_state.messages.append({"role": "assistant", "content": answer, "route": route})
 
st.markdown(
    f'<div class="footer-note">Built by {AUTHOR} · Powered by LangChain, Groq and ChromaDB</div>',
    unsafe_allow_html=True,
)