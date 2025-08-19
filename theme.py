import streamlit as st

# TransUnion theme configuration
def configure_theme():
    """Configure the TransUnion theme for Streamlit"""
    
    # Custom CSS with TransUnion color palette
    st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* TransUnion Color Variables */
    :root {
        --tu-primary-blue: #1e3a8a;
        --tu-secondary-blue: #3b82f6;
        --tu-teal: #0891b2;
        --tu-light-teal: #06b6d4;
        --tu-success-green: #10b981;
        --tu-warning-yellow: #f59e0b;
        --tu-danger-red: #ef4444;
        --tu-purple: #7c3aed;
        --tu-gray-light: #f8f9fa;
        --tu-gray-medium: #6b7280;
        --tu-gray-dark: #374151;
        --tu-white: #ffffff;
    }
    
    /* Main App Background */
    .stApp {
        background: linear-gradient(180deg, #f8f9fa 0%, #e5e7eb 100%);
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Sidebar Styling */
    .css-1d391kg {
        background: linear-gradient(180deg, var(--tu-primary-blue) 0%, var(--tu-secondary-blue) 100%);
    }
    
    .css-1d391kg .stSelectbox label,
    .css-1d391kg .stDateInput label,
    .css-1d391kg .stSlider label,
    .css-1d391kg .stMultiSelect label {
        color: white !important;
        font-weight: 600;
        font-size: 0.9rem;
    }
    
    /* Sidebar inputs */
    .css-1d391kg .stSelectbox div[data-baseweb="select"] > div,
    .css-1d391kg .stDateInput input,
    .css-1d391kg .stMultiSelect div[data-baseweb="select"] > div {
        background-color: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        color: white;
    }
    
    /* Slider styling */
    .css-1d391kg .stSlider .stSlider > div > div > div > div {
        background-color: var(--tu-light-teal);
    }
    
    /* Main content area */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Custom metric cards */
    .metric-card {
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 1rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        transition: all 0.3s ease;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .metric-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: white;
        margin: 0;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .metric-label {
        color: rgba(255, 255, 255, 0.9);
        margin: 0.5rem 0 0 0;
        font-weight: 500;
        font-size: 0.95rem;
    }
    
    /* Chart containers */
    .chart-container {
        background: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        margin-bottom: 2rem;
        border-left: 4px solid var(--tu-primary-blue);
        transition: all 0.3s ease;
    }
    
    .chart-container:hover {
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
    }
    
    .chart-title {
        color: var(--tu-primary-blue);
        font-size: 1.4rem;
        font-weight: 600;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, var(--tu-primary-blue) 0%, var(--tu-secondary-blue) 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(30, 58, 138, 0.2);
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, var(--tu-secondary-blue) 0%, var(--tu-primary-blue) 100%);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(30, 58, 138, 0.3);
    }
    
    /* Data tables */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        border: 1px solid #e5e7eb;
    }
    
    /* Headers */
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
        color: var(--tu-primary-blue);
    }
    
    /* Animations */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .fade-in {
        animation: fadeInUp 0.8s ease-out;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f5f9;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--tu-primary-blue);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--tu-secondary-blue);
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .metric-value {
            font-size: 2rem;
        }
        
        .chart-container {
            padding: 1rem;
        }
        
        .chart-title {
            font-size: 1.2rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)

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
    <div class="fade-in" style="background: linear-gradient(135deg, #1e3a8a 0%, #0891b2 100%); 
         padding: 3rem 2rem; margin: -1rem -1rem 3rem -1rem; border-radius: 15px; 
         box-shadow: 0 10px 40px rgba(30, 58, 138, 0.2);">
        <div style="text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 3rem; font-weight: 700; 
                       text-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);">
                🏦 TransUnion Analytics Hub
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
    <div style="background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); 
         padding: 2rem; margin: 3rem -1rem -1rem -1rem; border-radius: 15px; 
         text-align: center; box-shadow: 0 -4px 20px rgba(30, 58, 138, 0.1);">
        <div style="color: rgba(255, 255, 255, 0.9); margin-bottom: 1rem;">
            <h3 style="color: white; margin: 0 0 0.5rem 0; font-weight: 600;">TransUnion Analytics</h3>
            <p style="margin: 0; font-size: 0.95rem;">Empowering financial decisions through data intelligence</p>
        </div>
        <div style="display: flex; justify-content: center; gap: 2rem; flex-wrap: wrap; margin-top: 1rem;">
            <span style="color: rgba(255, 255, 255, 0.8); font-size: 0.9rem;">🛡️ SOC 2 Compliant</span>
            <span style="color: rgba(255, 255, 255, 0.8); font-size: 0.9rem;">🔐 256-bit Encryption</span>
            <span style="color: rgba(255, 255, 255, 0.8); font-size: 0.9rem;">⚡ 99.9% Uptime</span>
        </div>
        <p style="color: rgba(255, 255, 255, 0.7); margin: 1rem 0 0 0; font-size: 0.85rem;">
            © 2024 TransUnion LLC. All rights reserved. | Powered by Streamlit
        </p>
    </div>
    """
