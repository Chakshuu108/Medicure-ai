PURPLE_THEME = """
<style>
/* ── Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=DM+Mono:wght@300;400;500&display=swap');

:root {
    --primary: #7C3AED;
    --primary-light: #A78BFA;
    --primary-dark: #5B21B6;
    --primary-glow: rgba(124, 58, 237, 0.3);
    --accent: #C084FC;
    --bg-deep: #0D0A1E;
    --bg-card: #13102A;
    --bg-elevated: #1A1535;
    --bg-glass: rgba(124, 58, 237, 0.08);
    --text-primary: #F3F0FF;
    --text-secondary: #A89FC8;
    --text-muted: #6B6080;
    --border: rgba(124, 58, 237, 0.25);
    --border-strong: rgba(167, 139, 250, 0.4);
    --success: #34D399;
    --warning: #FBBF24;
    --danger: #F87171;
    --low-risk: #34D399;
    --medium-risk: #FBBF24;
    --high-risk: #F87171;
}

/* ── Base — NO fixed background-attachment (causes repaint/blink) ── */
html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif !important;
    background-color: var(--bg-deep) !important;
    color: var(--text-primary) !important;
}

.stApp {
    background: #0D0A1E !important;
}

.main .block-container {
    padding: 2rem 2rem 4rem !important;
    max-width: 1200px !important;
}

h1, h2, h3, h4, h5, h6 {
    color: var(--text-primary) !important;
    font-family: 'Space Grotesk', sans-serif !important;
}

/* ── Buttons — no transform (causes blink) ── */
.stButton > button {
    background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.92rem !important;
    padding: 0.6rem 1.5rem !important;
    transition: background 0.2s ease, box-shadow 0.2s ease !important;
    box-shadow: 0 4px 15px var(--primary-glow) !important;
    letter-spacing: 0.02em !important;
}

.stButton > button:hover {
    box-shadow: 0 6px 20px var(--primary-glow) !important;
    background: linear-gradient(135deg, var(--primary-light) 0%, var(--primary) 100%) !important;
}

/* ── Inputs ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input,
.stSelectbox > div > div > div {
    background-color: var(--bg-elevated) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 0.95rem !important;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--primary-light) !important;
    box-shadow: 0 0 0 2px var(--primary-glow) !important;
}

/* Input/select labels — was too small/invisible */
.stSelectbox label,
.stTextInput label,
.stNumberInput label,
.stTextArea label,
.stDateInput label,
.stTimeInput label,
.stRadio label,
.stCheckbox label {
    color: var(--text-secondary) !important;
    font-size: 0.9rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.02em !important;
}

/* Radio option text */
.stRadio > div label { color: var(--text-primary) !important; font-size: 0.92rem !important; }

/* Checkbox text */
.stCheckbox > label > div { color: var(--text-primary) !important; font-size: 0.92rem !important; }

/* ── Sidebar ── */
.stSidebar {
    background: linear-gradient(180deg, var(--bg-card) 0%, var(--bg-deep) 100%) !important;
    border-right: 1px solid var(--border) !important;
}

.stSidebar .stButton > button {
    width: 100% !important;
    margin: 0.2rem 0 !important;
    background: var(--bg-glass) !important;
    border: 1px solid var(--border) !important;
    box-shadow: none !important;
}

.stSidebar .stButton > button:hover {
    background: var(--primary-glow) !important;
    border-color: var(--primary-light) !important;
}

.stSidebar label,
section[data-testid="stSidebar"] label {
    font-size: 0.92rem !important;
    color: var(--text-secondary) !important;
}

section[data-testid="stSidebar"] > div {
    padding: 1.5rem 1rem !important;
}

/* ── Metrics ── */
div[data-testid="metric-container"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 14px !important;
    padding: 1.2rem !important;
}

div[data-testid="metric-container"] label {
    color: var(--text-secondary) !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
}

div[data-testid="metric-container"] div[data-testid="metric-value"] {
    color: var(--primary-light) !important;
    font-size: 2rem !important;
    font-weight: 700 !important;
}

/* ── Tables ── */
.stDataFrame, .stTable {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}

/* ════════════════════════════════════════════
   TABS — fill full panel width, no empty space
   ════════════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {
    background: var(--bg-card) !important;
    border-radius: 12px !important;
    padding: 4px !important;
    border: 1px solid var(--border) !important;
    gap: 2px !important;
    /* stretch tabs to fill 100% width */
    display: flex !important;
    width: 100% !important;
    box-sizing: border-box !important;
}

/* Every tab takes equal share — eliminates right-side empty gap */
.stTabs [data-baseweb="tab"] {
    flex: 1 1 0 !important;
    min-width: 0 !important;
    text-align: center !important;
    justify-content: center !important;
    color: var(--text-secondary) !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.95rem !important;
    border-radius: 8px !important;
    padding: 0.55rem 0.5rem !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    transition: background 0.15s, color 0.15s !important;
}

.stTabs [aria-selected="true"] {
    background: var(--primary) !important;
    color: white !important;
    font-weight: 600 !important;
}

/* Hide Streamlit's default tab underline indicator */
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] {
    display: none !important;
}

/* Nested tabs (e.g. OPD sub-tabs) */
.stTabs .stTabs [data-baseweb="tab-list"] {
    background: var(--bg-elevated) !important;
}

.stTabs .stTabs [data-baseweb="tab"] {
    font-size: 0.85rem !important;
}

/* ── Chat ── */
.stChatMessage {
    background: var(--bg-elevated) !important;
    border: 1px solid var(--border) !important;
    border-radius: 14px !important;
    margin-bottom: 0.8rem !important;
}

div[data-testid="stChatMessageContent"] {
    color: var(--text-primary) !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 0.95rem !important;
}

.stChatInputContainer, div[data-testid="stChatInput"] {
    background: var(--bg-elevated) !important;
    border: 1px solid var(--border-strong) !important;
    border-radius: 14px !important;
}

/* ── Alerts ── */
.stAlert {
    border-radius: 12px !important;
    border-left: 4px solid var(--primary) !important;
    background: var(--bg-glass) !important;
    font-size: 0.9rem !important;
}

/* ── Expander ── */
details summary,
.stExpander summary {
    font-size: 0.92rem !important;
    color: var(--text-primary) !important;
    font-weight: 500 !important;
}

/* Patient IDs in expander titles */
details summary code,
.stExpander summary code {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.88rem !important;
    color: var(--primary-light) !important;
    background: rgba(124, 58, 237, 0.14) !important;
    padding: 0.1em 0.35em !important;
    border-radius: 4px !important;
}

/* ── Inline code (IDs, patient codes everywhere) ── */
code {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.88rem !important;
    color: var(--primary-light) !important;
    background: rgba(124, 58, 237, 0.12) !important;
    padding: 0.1em 0.4em !important;
    border-radius: 4px !important;
}

/* ── Body text inside tabs ── */
.stMarkdown p {
    font-size: 1rem !important;
    color: var(--text-primary) !important;
    line-height: 1.7 !important;
}

/* ── Date/time inputs ── */
.stDateInput input,
.stTimeInput input {
    background: var(--bg-elevated) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
    font-size: 0.93rem !important;
}

/* ── Custom component classes ── */
.card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    transition: border-color 0.2s ease;
}

.card:hover { border-color: var(--border-strong); }

.card-header {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--primary-light);
    margin-bottom: 0.5rem;
}

.risk-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

.risk-low    { background: rgba(52, 211, 153, 0.15); color: #34D399; border: 1px solid rgba(52, 211, 153, 0.3); }
.risk-medium { background: rgba(251, 191, 36, 0.15);  color: #FBBF24; border: 1px solid rgba(251, 191, 36, 0.3); }
.risk-high   { background: rgba(248, 113, 113, 0.15); color: #F87171; border: 1px solid rgba(248, 113, 113, 0.3); }

.page-header {
    background: linear-gradient(135deg, var(--primary-dark) 0%, var(--primary) 100%);
    border-radius: 20px;
    padding: 2rem 2.5rem;
    margin-bottom: 2rem;
    border: 1px solid var(--border-strong);
    position: relative;
    overflow: hidden;
}

.page-header::before {
    content: '';
    position: absolute;
    top: -50%; right: -20%;
    width: 300px; height: 300px;
    background: radial-gradient(circle, rgba(255,255,255,0.05) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
}

.page-header h1 {
    margin: 0 !important;
    font-size: 1.8rem !important;
    font-weight: 700 !important;
}

.page-header p {
    color: rgba(255,255,255,0.75) !important;
    margin: 0.5rem 0 0 !important;
    font-size: 0.95rem !important;
}

.page-header code {
    background: rgba(255,255,255,0.15) !important;
    color: #fff !important;
    font-size: 0.85rem !important;
}

.medicine-card {
    background: linear-gradient(135deg, var(--bg-elevated) 0%, var(--bg-card) 100%);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin: 0.5rem 0;
    border-left: 3px solid var(--primary);
    font-size: 0.93rem;
}

.schedule-item {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.8rem 1rem;
    background: var(--bg-glass);
    border: 1px solid var(--border);
    border-radius: 10px;
    margin: 0.3rem 0;
    font-size: 0.92rem;
}

.divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--border), transparent);
    margin: 1.5rem 0;
}

/* ── Scrollbar ── */
::-webkit-scrollbar        { width: 6px; height: 6px; }
::-webkit-scrollbar-track  { background: var(--bg-deep); }
::-webkit-scrollbar-thumb  { background: var(--primary-dark); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--primary); }

.stSpinner { color: var(--primary-light) !important; }

/* ── Anti-blink: prevent full-page flash on widget interaction ── */
.stApp > div { will-change: auto !important; }
[data-testid="stAppViewContainer"] { contain: layout style; }

/* Prevent input focus from triggering layout shift */
.stTextInput > div, .stTextArea > div, .stNumberInput > div,
.stSelectbox > div, .stDateInput > div, .stTimeInput > div {
    will-change: auto !important;
    transform: translateZ(0);
}

/* Prevent the main block from repainting on every keystroke */
[data-testid="block-container"] {
    backface-visibility: hidden;
    -webkit-backface-visibility: hidden;
}

/* Stabilize widget containers so only the changed widget repaints */
.stTextInput, .stTextArea, .stNumberInput, .stSelectbox,
.stDateInput, .stTimeInput, .stRadio, .stCheckbox {
    isolation: isolate;
}

/* Prevent spinner overlay from causing layout blink */
.stSpinner > div {
    position: fixed !important;
}
</style>
"""
