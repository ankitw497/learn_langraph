import streamlit as st

"""
theme.py
Multi-theme support for the Streamlit analytics app. The original TransUnion theme
is preserved (default) and several additional professional, interactive themes
are provided. All themes expose the same utility HTML helper functions so that
the rest of the app code remains unchanged.
"""

# ------------------------- Internal Theme CSS Builders ------------------------- #

def _css_transunion():
    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    :root {
        --accent-1: #1e3a8a; /* primary */
        --accent-2: #3b82f6; /* secondary */
        --accent-3: #0891b2; /* teal */
        --accent-4: #06b6d4; /* light teal */
        --success: #10b981;
        --warn: #f59e0b;
        --danger: #ef4444;
        --special: #7c3aed;
        --bg-grad-start: #f8f9fa;
        --bg-grad-end: #e5e7eb;
        --text-strong: #1e3a8a;
    }
    .stApp { background: linear-gradient(180deg,var(--bg-grad-start) 0%,var(--bg-grad-end) 100%); font-family:'Inter',sans-serif; }
    body, .main .block-container {background:transparent!important;}
    #MainMenu, footer, header {visibility:hidden;}
    [data-testid="stSidebar"] {background:linear-gradient(180deg,var(--accent-1) 0%,var(--accent-2) 100%)!important;}
    [data-testid="stSidebar"] * label {color:#fff!important;font-weight:600;font-size:.9rem;}
    [data-testid="stSidebar"] input, [data-testid="stSidebar"] div[data-baseweb="select"]>div {background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.25);color:#fff;}
    [data-testid="stSidebar"] .stSlider>div>div>div>div {background:var(--accent-4);} 
    .main .block-container {padding-top:2rem;padding-bottom:2rem;}
    .metric-card {padding:1.5rem;border-radius:12px;text-align:center;margin-bottom:1rem;box-shadow:0 4px 20px rgba(0,0,0,.08);transition:.3s;border:1px solid rgba(255,255,255,.2);} 
    .metric-card:hover {transform:translateY(-8px);box-shadow:0 12px 40px rgba(0,0,0,.15);} 
    .metric-value {font-size:2.5rem;font-weight:700;color:#fff;margin:0;text-shadow:0 2px 4px rgba(0,0,0,.1);} 
    .metric-label {color:rgba(255,255,255,.9);margin:.5rem 0 0 0;font-weight:500;font-size:.95rem;} 
    .chart-container {background:#fff;padding:2rem;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,.08);margin-bottom:2rem;border-left:4px solid var(--accent-1);transition:.3s;} 
    .chart-container:hover {box-shadow:0 8px 30px rgba(0,0,0,.12);} 
    .chart-title {color:var(--accent-1);font-size:1.4rem;font-weight:600;margin-bottom:1.5rem;display:flex;align-items:center;gap:.5rem;} 
    .stButton>button {background:linear-gradient(135deg,var(--accent-1) 0%,var(--accent-2) 100%);color:#fff;border:none;border-radius:8px;padding:.75rem 2rem;font-weight:600;font-size:.95rem;transition:.3s;box-shadow:0 4px 12px rgba(30,58,138,.2);} 
    .stButton>button:hover {background:linear-gradient(135deg,var(--accent-2) 0%,var(--accent-1) 100%);transform:translateY(-2px);box-shadow:0 6px 20px rgba(30,58,138,.3);} 
    .stDataFrame {border-radius:12px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,.08);border:1px solid #e5e7eb;} 
    h1,h2,h3 {font-family:'Inter',sans-serif;color:var(--accent-1);} 
    @keyframes fadeInUp {from {opacity:0;transform:translateY(30px);} to {opacity:1;transform:translateY(0);} } .fade-in {animation:fadeInUp .8s ease-out;} 
    ::-webkit-scrollbar {width:8px;} ::-webkit-scrollbar-track {background:#f1f5f9;border-radius:4px;} ::-webkit-scrollbar-thumb {background:var(--accent-1);border-radius:4px;} ::-webkit-scrollbar-thumb:hover {background:var(--accent-2);} 
    @media (max-width:768px){.metric-value{font-size:2rem;} .chart-container{padding:1rem;} .chart-title{font-size:1.2rem;}}
    </style>
    """

def _css_midnight_neon():
    return """
    <style>
    :root {
        --accent-1:#0f172a; --accent-2:#1e293b; --accent-3:#06b6d4; --accent-4:#6366f1; --accent-5:#f59e0b; --accent-6:#10b981; --text-strong:#f1f5f9;
    }
    .stApp {background:radial-gradient(circle at 20% 20%,#1e293b,#0f172a 70%);color:#e2e8f0;font-family:'Inter',sans-serif;}
    body, .main .block-container {background:transparent!important;}
    #MainMenu,footer,header{visibility:hidden;}
    [data-testid="stSidebar"] {background:linear-gradient(180deg,#0f172a,#1e293b)!important;}
    [data-testid="stSidebar"] * label{color:#e2e8f0!important;}
    .metric-card {background:linear-gradient(135deg,#1e293b,#0f172a);border:1px solid #334155;box-shadow:0 0 0 1px #334155, 0 10px 25px -5px rgba(0,0,0,.6);}
    .metric-card:hover {box-shadow:0 0 0 1px #475569,0 15px 35px -5px rgba(0,0,0,.8);} .metric-value{color:#fff;}
    .metric-label{color:#94a3b8;}
    .chart-container {background:#1e293b;border:1px solid #334155;box-shadow:0 8px 30px -8px rgba(0,0,0,.7);} .chart-title{color:#06b6d4;}
    .stButton>button {background:linear-gradient(90deg,#06b6d4,#6366f1);color:#fff;border:none;} .stButton>button:hover{filter:brightness(1.15);}
    h1,h2,h3{color:#e2e8f0;}
    ::-webkit-scrollbar-thumb{background:#6366f1;} ::-webkit-scrollbar-thumb:hover{background:#06b6d4;}
    </style>
    """

def _css_corporate_light():
    return """
    <style>
    :root {--accent-1:#0d3b66;--accent-2:#1d4e89;--accent-3:#159895;--accent-4:#57c5b6;--bg:#ffffff;--panel:#f5f7fa;--border:#e2e8f0;--text-strong:#0d3b66;}
    .stApp {background:linear-gradient(180deg,#ffffff,#f1f5f9);font-family:'Inter',sans-serif;color:#1e293b;}
    body, .main .block-container {background:transparent!important;}
    #MainMenu,footer,header{visibility:hidden;}
    [data-testid="stSidebar"] {background:linear-gradient(180deg,#0d3b66,#1d4e89)!important;} [data-testid="stSidebar"] * label{color:#fff!important;}
    .metric-card {background:linear-gradient(135deg,#1d4e89,#159895);color:#fff;box-shadow:0 6px 18px rgba(13,59,102,.25);}
    .chart-container {background:var(--panel);border:1px solid var(--border);}
    .chart-title {color:var(--accent-1);} h1,h2,h3{color:var(--accent-1);} 
    .stButton>button {background:linear-gradient(90deg,#0d3b66,#159895);color:#fff;} .stButton>button:hover{filter:brightness(1.1);} 
    ::-webkit-scrollbar-thumb{background:#1d4e89;} ::-webkit-scrollbar-thumb:hover{background:#159895;}
    </style>
    """

def _css_slate_dark():
    return """
    <style>
    :root {--accent-1:#334155;--accent-2:#475569;--accent-3:#0ea5e9;--accent-4:#38bdf8;--success:#22c55e;--warn:#fbbf24;--danger:#f87171;--text-strong:#f1f5f9;}
    .stApp {background:linear-gradient(180deg,#1e293b,#0f172a);color:#e2e8f0;font-family:'Inter',sans-serif;}
    body, .main .block-container {background:transparent!important;}
    #MainMenu,footer,header{visibility:hidden;}
    [data-testid="stSidebar"] {background:linear-gradient(180deg,#0f172a,#334155)!important;} [data-testid="stSidebar"] * label{color:#f1f5f9!important;}
    .metric-card {background:linear-gradient(135deg,#334155,#1e293b);border:1px solid #475569;}
    .chart-container {background:#1e293b;border:1px solid #334155;} .chart-title{color:#38bdf8;}
    .stButton>button {background:linear-gradient(90deg,#0ea5e9,#38bdf8);color:#fff;} .stButton>button:hover{filter:brightness(1.15);} h1,h2,h3{color:#e2e8f0;}
    </style>
    """

def _css_emerald():
    return """
    <style>
    :root {--accent-1:#064e3b;--accent-2:#047857;--accent-3:#10b981;--accent-4:#34d399;--accent-5:#a7f3d0;--text-strong:#064e3b;}
    .stApp {background:linear-gradient(180deg,#ecfdf5,#d1fae5);font-family:'Inter',sans-serif;color:#064e3b;}
    body, .main .block-container {background:transparent!important;}
    #MainMenu,footer,header{visibility:hidden;}
    [data-testid="stSidebar"] {background:linear-gradient(180deg,#064e3b,#047857)!important;} [data-testid="stSidebar"] * label{color:#ecfdf5!important;}
    .metric-card {background:linear-gradient(135deg,#047857,#10b981);color:#fff;box-shadow:0 10px 25px -5px rgba(6,78,59,.35);} 
    .chart-container {background:#ffffff;border:1px solid #a7f3d0;} .chart-title{color:#047857;}
    .stButton>button {background:linear-gradient(90deg,#047857,#10b981);color:#fff;} .stButton>button:hover{filter:brightness(1.15);} h1,h2,h3{color:#064e3b;}
    </style>
    """

def _css_royal_purple():
    return """
    <style>
    :root {--accent-1:#3b0764;--accent-2:#6d28d9;--accent-3:#9333ea;--accent-4:#a855f7;--accent-5:#d8b4fe;--text-strong:#f5f3ff;}
    .stApp {background:linear-gradient(180deg,#4c1d95,#2e1065);font-family:'Inter',sans-serif;color:#f5f3ff;}
    body, .main .block-container {background:transparent!important;}
    #MainMenu,footer,header{visibility:hidden;}
    [data-testid="stSidebar"] {background:linear-gradient(180deg,#3b0764,#6d28d9)!important;} [data-testid="stSidebar"] * label{color:#f5f3ff!important;}
    .metric-card {background:linear-gradient(135deg,#6d28d9,#9333ea);color:#fff;box-shadow:0 0 0 1px #a855f7,0 10px 30px -10px rgba(0,0,0,.6);} 
    .chart-container {background:#3b0764;border:1px solid #6d28d9;} .chart-title{color:#d8b4fe;}
    .stButton>button {background:linear-gradient(90deg,#6d28d9,#9333ea);color:#fff;} .stButton>button:hover{filter:brightness(1.2);} h1,h2,h3{color:#f5f3ff;}
    ::-webkit-scrollbar-thumb{background:#9333ea;} ::-webkit-scrollbar-thumb:hover{background:#a855f7;}
    </style>
    """

def _css_minimal_white():
    return """
    <style>
    :root {--accent-1:#111827;--accent-2:#2563eb;--accent-3:#0ea5e9;--accent-4:#9333ea;--success:#16a34a;--warn:#d97706;--danger:#dc2626;}
    .stApp {background:#ffffff;font-family:'Inter',sans-serif;color:#111827;}
    body, .main .block-container {background:transparent!important;}
    [data-testid="stSidebar"] {background:linear-gradient(180deg,#f8fafc,#eef2f7);} 
    .metric-card {background:linear-gradient(135deg,#2563eb,#0ea5e9);color:#fff;box-shadow:0 4px 14px rgba(37,99,235,.35);} 
    .chart-container {background:#ffffff;border:1px solid #e2e8f0;}
    .chart-title {color:#111827;} h1,h2,h3{color:#111827;}
    .stButton>button {background:#2563eb;color:#fff;} .stButton>button:hover{background:#1d4ed8;}
    ::-webkit-scrollbar-thumb{background:#2563eb;} ::-webkit-scrollbar-thumb:hover{background:#1d4ed8;}
    </style>
    """

def _css_ocean_breeze():
    return """
    <style>
    :root {--accent-1:#003049;--accent-2:#0466c8;--accent-3:#00a6fb;--accent-4:#48cae4;--accent-5:#90e0ef;}
    .stApp {background:linear-gradient(180deg,#e0f7ff,#c8f1ff);font-family:'Inter',sans-serif;color:#003049;}
    body, .main .block-container {background:transparent!important;}
    [data-testid="stSidebar"] {background:linear-gradient(180deg,#003049,#0466c8);} [data-testid="stSidebar"] * label{color:#e0f7ff!important;}
    .metric-card {background:linear-gradient(135deg,#0466c8,#00a6fb);color:#fff;box-shadow:0 8px 24px -6px rgba(0,48,73,.45);} 
    .chart-container {background:#ffffff;border:1px solid #90e0ef;} .chart-title{color:#003049;}
    .stButton>button {background:linear-gradient(90deg,#003049,#00a6fb);color:#fff;} .stButton>button:hover{filter:brightness(1.15);} h1,h2,h3{color:#003049;}
    ::-webkit-scrollbar-thumb{background:#00a6fb;} ::-webkit-scrollbar-thumb:hover{background:#0466c8;}
    </style>
    """

def _css_solarized_light():
    return """
    <style>
    :root {--base03:#002b36;--base02:#073642;--base01:#586e75;--base00:#657b83;--base0:#839496;--base1:#93a1a1;--base2:#eee8d5;--base3:#fdf6e3;--yellow:#b58900;--orange:#cb4b16;--red:#dc322f;--magenta:#d33682;--violet:#6c71c4;--blue:#268bd2;--cyan:#2aa198;--green:#859900;}
    .stApp {background:linear-gradient(180deg,var(--base3),var(--base2));font-family:'Inter',sans-serif;color:var(--base02);} 
    body, .main .block-container {background:transparent!important;}
    [data-testid="stSidebar"] {background:linear-gradient(180deg,var(--base02),var(--base03));} [data-testid="stSidebar"] * label{color:var(--base2)!important;}
    .metric-card {background:linear-gradient(135deg,var(--blue),var(--cyan));color:#fff;} .chart-container{background:#fff5dc;border:1px solid var(--base1);} .chart-title{color:var(--base02);} 
    .stButton>button {background:linear-gradient(90deg,var(--blue),var(--cyan));color:#fff;} .stButton>button:hover{filter:brightness(1.1);} h1,h2,h3{color:var(--base02);} 
    ::-webkit-scrollbar-thumb{background:var(--blue);} ::-webkit-scrollbar-thumb:hover{background:var(--cyan);} 
    </style>
    """

def _css_solarized_dark():
    return """
    <style>
    :root {--base03:#002b36;--base02:#073642;--base01:#586e75;--base00:#657b83;--base0:#839496;--base1:#93a1a1;--base2:#eee8d5;--base3:#fdf6e3;--yellow:#b58900;--orange:#cb4b16;--red:#dc322f;--magenta:#d33682;--violet:#6c71c4;--blue:#268bd2;--cyan:#2aa198;--green:#859900;}
    .stApp {background:radial-gradient(circle at 20% 15%,#073642,#002b36 70%);font-family:'Inter',sans-serif;color:var(--base1);} 
    body, .main .block-container {background:transparent!important;}
    [data-testid="stSidebar"] {background:linear-gradient(180deg,#002b36,#073642);} [data-testid="stSidebar"] * label{color:var(--base2)!important;}
    .metric-card {background:linear-gradient(135deg,#268bd2,#2aa198);color:#fff;border:1px solid #2aa198;} .chart-container{background:#002f3a;border:1px solid #2aa198;} .chart-title{color:#2aa198;} 
    .stButton>button {background:linear-gradient(90deg,#268bd2,#2aa198);color:#fff;} .stButton>button:hover{filter:brightness(1.15);} h1,h2,h3{color:var(--base2);} 
    ::-webkit-scrollbar-thumb{background:#268bd2;} ::-webkit-scrollbar-thumb:hover{background:#2aa198;} 
    </style>
    """

def _css_glass_morph():
    return """
    <style>
    :root {--accent-1:#0f172a;--accent-2:#3b82f6;--accent-3:#06b6d4;--accent-4:#10b981;--blur-bg:rgba(255,255,255,0.08);--border:rgba(255,255,255,0.2);} 
    .stApp {background:linear-gradient(135deg,#0f172a 0%, #1e3a8a 60%, #0891b2 100%);font-family:'Inter',sans-serif;color:#f1f5f9;} 
    body, .main .block-container {background:transparent!important;}
    [data-testid="stSidebar"] {background:rgba(255,255,255,0.05);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);border-right:1px solid var(--border);} [data-testid="stSidebar"] * label{color:#f1f5f9!important;} 
    .metric-card {background:var(--blur-bg);backdrop-filter:blur(12px);border:1px solid var(--border);} .metric-card:hover{border:1px solid #3b82f6;} 
    .chart-container {background:var(--blur-bg);backdrop-filter:blur(18px);border:1px solid var(--border);} .chart-title{color:#ffffff;} 
    .stButton>button {background:linear-gradient(90deg,#3b82f6,#06b6d4);color:#fff;border:1px solid rgba(255,255,255,0.3);} .stButton>button:hover{filter:brightness(1.15);} h1,h2,h3{color:#ffffff;} 
    ::-webkit-scrollbar-thumb{background:#3b82f6;} ::-webkit-scrollbar-thumb:hover{background:#06b6d4;} 
    </style>
    """

_THEME_BUILDERS = {
    "TransUnion": _css_transunion,
    "Midnight Neon": _css_midnight_neon,
    "Corporate Light": _css_corporate_light,
    "Slate Dark": _css_slate_dark,
    "Emerald": _css_emerald,
    "Royal Purple": _css_royal_purple,
    "Minimal White": _css_minimal_white,
    "Ocean Breeze": _css_ocean_breeze,
    "Solarized Light": _css_solarized_light,
    "Solarized Dark": _css_solarized_dark,
    "Glass Morph": _css_glass_morph,
}

# Additional professional themes (appended below registry update block later)

def _css_carbon_gray():
    return """
    <style>
    :root {--accent-1:#1c1f24;--accent-2:#2a2f36;--accent-3:#3d444d;--accent-4:#4f5863;--highlight:#00b4d8;}
    .stApp {background:linear-gradient(180deg,#1c1f24,#2a2f36);font-family:'Inter',sans-serif;color:#d1d5db;}
    body, .main .block-container {background:transparent!important;}
    [data-testid="stSidebar"] {background:linear-gradient(180deg,#1c1f24,#2a2f36)!important;}
    [data-testid="stSidebar"] * label {color:#e2e8f0!important;}
    .metric-card {background:linear-gradient(135deg,#2a2f36,#1c1f24);border:1px solid #3d444d;}
    .metric-card:hover {border-color:#00b4d8;}
    .chart-container {background:#242a31;border:1px solid #3d444d;} .chart-title{color:#00b4d8;}
    .stButton>button {background:linear-gradient(90deg,#00b4d8,#4f5863);color:#fff;} .stButton>button:hover{filter:brightness(1.15);}
    h1,h2,h3{color:#f1f5f9;}
    </style>
    """

def _css_indigo_gold():
    return """
    <style>
    :root {--accent-1:#0a0f2d;--accent-2:#162054;--accent-3:#23336f;--accent-4:#2f447f;--accent-5:#d4af37;}
    .stApp {background:linear-gradient(180deg,#0a0f2d,#162054);font-family:'Inter',sans-serif;color:#e5e7eb;}
    body, .main .block-container {background:transparent!important;}
    [data-testid="stSidebar"] {background:linear-gradient(180deg,#162054,#23336f)!important;} [data-testid="stSidebar"] * label{color:#f5f5f5!important;}
    .metric-card {background:linear-gradient(135deg,#23336f,#0a0f2d);border:1px solid #2f447f;} .metric-value{color:#ffd866;}
    .metric-card:hover {box-shadow:0 0 0 1px #d4af37,0 10px 28px -8px rgba(0,0,0,.6);} 
    .chart-container {background:#102049;border:1px solid #2f447f;} .chart-title{color:#d4af37;}
    .stButton>button {background:linear-gradient(90deg,#23336f,#d4af37);color:#fff;} .stButton>button:hover{filter:brightness(1.12);} h1,h2,h3{color:#d4e2ff;}
    </style>
    """

def _css_desert_sand():
    return """
    <style>
    :root {--accent-1:#5e503f;--accent-2:#8a7966;--accent-3:#c6ac8f;--accent-4:#e9dccd;--ink:#3a2f26;}
    .stApp {background:linear-gradient(180deg,#e9dccd,#c6ac8f);font-family:'Inter',sans-serif;color:var(--ink);} 
    body, .main .block-container {background:transparent!important;}
    [data-testid="stSidebar"] {background:linear-gradient(180deg,#5e503f,#8a7966)!important;} [data-testid="stSidebar"] * label{color:#f5f2ef!important;}
    .metric-card {background:linear-gradient(135deg,#8a7966,#5e503f);color:#fff;}
    .chart-container {background:#fff9f3;border:1px solid #dbc5ae;} .chart-title{color:#5e503f;}
    .stButton>button {background:linear-gradient(90deg,#5e503f,#c6ac8f);color:#fff;} .stButton>button:hover{filter:brightness(1.1);} h1,h2,h3{color:#5e503f;}
    </style>
    """

def _css_mint_modern():
    return """
    <style>
    :root {--accent-1:#0f2f35;--accent-2:#155e63;--accent-3:#1b8a85;--accent-4:#6fe7d2;--accent-5:#c7fff5;} 
    .stApp {background:linear-gradient(180deg,#c7fff5,#6fe7d2);font-family:'Inter',sans-serif;color:#0f2f35;} 
    body, .main .block-container {background:transparent!important;}
    [data-testid="stSidebar"] {background:linear-gradient(180deg,#0f2f35,#155e63)!important;} [data-testid="stSidebar"] * label{color:#e8fffc!important;}
    .metric-card {background:linear-gradient(135deg,#155e63,#1b8a85);color:#fff;} .metric-card:hover{box-shadow:0 8px 28px -6px rgba(21,94,99,.5);} 
    .chart-container {background:#ffffff;border:1px solid #6fe7d2;} .chart-title{color:#155e63;}
    .stButton>button {background:linear-gradient(90deg,#155e63,#1b8a85);color:#fff;} .stButton>button:hover{filter:brightness(1.15);} h1,h2,h3{color:#0f2f35;}
    </style>
    """

def _css_high_contrast():
    return """
    <style>
    :root {--accent-1:#000000;--accent-2:#222222;--accent-3:#ffffff;--accent-4:#ffcc00;--danger:#ff3030;} 
    .stApp {background:linear-gradient(180deg,#000,#222);font-family:'Inter',sans-serif;color:#ffffff;} 
    body, .main .block-container {background:transparent!important;}
    [data-testid="stSidebar"] {background:#000!important;} [data-testid="stSidebar"] * label{color:#ffcc00!important;font-weight:600;} 
    .metric-card {background:#111;border:2px solid #ffcc00;color:#fff;} .metric-card:hover{background:#181818;} 
    .chart-container {background:#111;border:2px solid #ffcc00;} .chart-title{color:#ffcc00;} 
    .stButton>button {background:#ffcc00;color:#000;font-weight:700;} .stButton>button:hover{background:#ffd633;} h1,h2,h3{color:#ffffff;} 
    a, .stMarkdown a {color:#ffd633!important;text-decoration:underline;} 
    </style>
    """

# Register additional themes
_THEME_BUILDERS.update({
    "Carbon Gray": _css_carbon_gray,
    "Indigo Gold": _css_indigo_gold,
    "Desert Sand": _css_desert_sand,
    "Mint Modern": _css_mint_modern,
    "High Contrast": _css_high_contrast,
})

def available_themes():
    """List available theme names."""
    return list(_THEME_BUILDERS.keys())

def configure_theme(theme_name: str = "TransUnion"):
    """Apply the chosen theme (defaults to TransUnion)."""
    builder = _THEME_BUILDERS.get(theme_name, _THEME_BUILDERS["TransUnion"])
    # Inject a small base style to unify sidebar targeting across themes
    base_css = """
    <style>
    [data-testid="stSidebar"] section[data-testid="stSidebarContent"] {padding-top:1rem;}
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {margin-top:0;}
    /* Hide Streamlit default header / menu / deploy controls across all themes */
    #MainMenu, header, footer {visibility:hidden !important;}
    header [data-testid="baseButton-header"], header button, .stDeployButton, button[kind="header"] {display:none !important;}
    /* Defensive: hide any toolbar or viewer badge that might inject deploy-related affordances */
    [data-testid="stStatusWidget"], .viewerBadge_container__, .stToolbar {display:none !important;}
    </style>
    """
    st.markdown(base_css + builder(), unsafe_allow_html=True)

def create_metric_card(value, label, gradient_colors, icon=""):
    """Create a styled metric card with TransUnion theme"""
    return f"""
    <div class="metric-card fade-in" style="background: linear-gradient(135deg, {gradient_colors[0]} 0%, {gradient_colors[1]} 100%);">
        <div class="metric-value">{icon} {value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """

def create_header():
    """Create the main header with TransUnion branding"""
    return """
    <div class="fade-in" style="background: linear-gradient(135deg, var(--accent-1,#1e3a8a) 0%, var(--accent-3,#0891b2) 100%); 
         padding: 3rem 2rem; margin: -1rem -1rem 3rem -1rem; border-radius: 15px; 
         box-shadow: 0 10px 40px rgba(30, 58, 138, 0.2);">
        <div style="text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 3rem; font-weight: 700; 
                       text-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);">
                🏦 Analytics Hub
            </h1>
            <p style="color: rgba(255, 255, 255, 0.9); margin: 1rem 0 0 0; font-size: 1.3rem; 
                      font-weight: 400;">
                Advanced Credit Intelligence & Risk Management Platform
            </p>
            <div style="margin-top: 1.5rem; display: flex; justify-content: center; gap: 2rem; flex-wrap: wrap;">
                <div style="background: rgba(255, 255, 255, 0.1); padding: 0.5rem 1rem; border-radius: 20px; backdrop-filter: blur(10px);">
                    <span style="color: white; font-weight: 500;">🔒 Secure</span>
                </div>
                <div style="background: rgba(255, 255, 255, 0.1); padding: 0.5rem 1rem; border-radius: 20px; backdrop-filter: blur(10px);">
                    <span style="color: white; font-weight: 500;">⚡ Real-time</span>
                </div>
                <div style="background: rgba(255, 255, 255, 0.1); padding: 0.5rem 1rem; border-radius: 20px; backdrop-filter: blur(10px);">
                    <span style="color: white; font-weight: 500;">📊 Analytics</span>
                </div>
            </div>
        </div>
    </div>
    """

def create_sidebar_header():
    """Create styled sidebar header"""
    return """
    <div style="background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); 
         padding: 1.5rem; margin: -1rem -1rem 2rem -1rem; border-radius: 12px;
         box-shadow: 0 4px 15px rgba(30, 58, 138, 0.3);">
        <h2 style="color: white; text-align: center; margin: 0; font-weight: 600;">
            ⚙️ Control Center
        </h2>
        <p style="color: rgba(255, 255, 255, 0.8); text-align: center; margin: 0.5rem 0 0 0; font-size: 0.9rem;">
            Configure your analytics view
        </p>
    </div>
    """

def create_chart_container(title, icon="📊"):
    """Create a styled chart container"""
    return f"""
    <div class="chart-container fade-in">
        <div class="chart-title">
            {icon} {title}
        </div>
    """

def create_footer():
    """Create styled footer"""
    return """
    <div style="background: linear-gradient(135deg, var(--accent-1,#1e3a8a) 0%, var(--accent-2,#3b82f6) 100%); 
         padding: 2rem; margin: 3rem -1rem -1rem -1rem; border-radius: 15px; 
         text-align: center; box-shadow: 0 -4px 20px rgba(30, 58, 138, 0.1);">
        <div style="color: rgba(255, 255, 255, 0.9); margin-bottom: 1rem;">
            <h3 style="color: white; margin: 0 0 0.5rem 0; font-weight: 600;">Analytics Platform</h3>
            <p style="margin: 0; font-size: 0.95rem;">Empowering financial decisions through data intelligence</p>
        </div>
        <div style="display: flex; justify-content: center; gap: 2rem; flex-wrap: wrap; margin-top: 1rem;">
            <span style="color: rgba(255, 255, 255, 0.8); font-size: 0.9rem;">🛡️ SOC 2 Compliant</span>
            <span style="color: rgba(255, 255, 255, 0.8); font-size: 0.9rem;">🔐 256-bit Encryption</span>
            <span style="color: rgba(255, 255, 255, 0.8); font-size: 0.9rem;">⚡ 99.9% Uptime</span>
        </div>
        <p style="color: rgba(255, 255, 255, 0.7); margin: 1rem 0 0 0; font-size: 0.85rem;">
            © 2025 Analytics Hub. All rights reserved. | Powered by Streamlit
        </p>
    </div>
    """
