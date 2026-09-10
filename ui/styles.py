# ui/styles.py
"""
Estilos CSS personalizados - Com suporte a Tema Escuro
"""

import streamlit as st

# ==================== TEMA CLARO (PADRÃO) ====================
CSS_CLARO = """
<style>
    /* ===== GERAL ===== */
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 0.5rem;
        font-weight: 700;
    }
    .main-header small {
        font-size: 1rem;
        color: #666;
        display: block;
        font-weight: 400;
        margin-top: 0.3rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* ===== BOXES ===== */
    .success-box {
        background-color: #d4edda;
        padding: 1rem 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        padding: 1rem 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #17a2b8;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 1rem 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
    }
    
    /* ===== BOTÕES ===== */
    .stButton>button {
        width: 100%;
        background-color: #1E88E5;
        color: white;
        font-weight: 600;
        border-radius: 8px;
        padding: 0.6rem 1rem;
        transition: all 0.3s ease;
        border: none;
    }
    .stButton>button:hover {
        background-color: #1565C0;
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(30, 136, 229, 0.3);
    }
    .stButton>button:active {
        transform: translateY(0);
    }
    
    /* ===== UPLOAD ===== */
    .upload-section {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 2rem;
        border-radius: 1rem;
        border: 2px dashed #adb5bd;
        margin: 1rem 0;
        transition: all 0.3s ease;
    }
    .upload-section:hover {
        border-color: #1E88E5;
        background: linear-gradient(135deg, #f8f9fa 0%, #e3f2fd 100%);
    }
    .upload-section .upload-icon {
        font-size: 3rem;
        text-align: center;
        display: block;
        margin-bottom: 0.5rem;
    }
    
    /* ===== MÉTRICAS / KPIs ===== */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    .kpi-card {
        background: white;
        padding: 1.5rem 1rem;
        border-radius: 1rem;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        text-align: center;
        transition: all 0.3s ease;
        border: 1px solid #f0f0f0;
        position: relative;
        overflow: hidden;
    }
    .kpi-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.12);
    }
    .kpi-card .kpi-icon {
        font-size: 2.2rem;
        display: block;
        margin-bottom: 0.5rem;
    }
    .kpi-card .kpi-value {
        font-size: 2.2rem;
        font-weight: 700;
        line-height: 1.2;
        margin-bottom: 0.2rem;
    }
    .kpi-card .kpi-label {
        font-size: 0.85rem;
        color: #6c757d;
        font-weight: 500;
    }
    .kpi-card .kpi-change {
        font-size: 0.75rem;
        margin-top: 0.3rem;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        display: inline-block;
    }
    .kpi-card .kpi-change.positive {
        background: #d4edda;
        color: #28a745;
    }
    .kpi-card .kpi-change.negative {
        background: #f8d7da;
        color: #dc3545;
    }
    .kpi-card .kpi-change.neutral {
        background: #e9ecef;
        color: #6c757d;
    }
    
    /* Cores dos KPIs */
    .kpi-blue .kpi-value { color: #1E88E5; }
    .kpi-blue .kpi-icon { color: #1E88E5; }
    .kpi-green .kpi-value { color: #28a745; }
    .kpi-green .kpi-icon { color: #28a745; }
    .kpi-red .kpi-value { color: #dc3545; }
    .kpi-red .kpi-icon { color: #dc3545; }
    .kpi-orange .kpi-value { color: #ff8f00; }
    .kpi-orange .kpi-icon { color: #ff8f00; }
    .kpi-purple .kpi-value { color: #7b1fa2; }
    .kpi-purple .kpi-icon { color: #7b1fa2; }
    .kpi-teal .kpi-value { color: #00897b; }
    .kpi-teal .kpi-icon { color: #00897b; }
    
    /* ===== FILTROS ===== */
    .filter-section {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.8rem;
        border: 1px solid #e9ecef;
        margin: 1rem 0;
    }
    .filter-section .filter-title {
        font-weight: 600;
        color: #495057;
        margin-bottom: 1rem;
        font-size: 1.1rem;
    }
    
    /* ===== COLUNAS ===== */
    .column-selector {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.8rem;
        border: 1px solid #e9ecef;
        margin: 1rem 0;
        max-height: 500px;
        overflow-y: auto;
    }
    .column-selector .col-group {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.3rem;
    }
    @media (max-width: 768px) {
        .column-selector .col-group {
            grid-template-columns: repeat(2, 1fr);
        }
    }
    .column-selector label {
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        transition: background 0.2s;
        cursor: pointer;
    }
    .column-selector label:hover {
        background: #e9ecef;
    }
    
    /* ===== TABS ===== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: #f8f9fa;
        padding: 0.5rem;
        border-radius: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: #1E88E5;
        color: white;
        box-shadow: 0 2px 8px rgba(30, 136, 229, 0.3);
    }
    
    /* ===== FOOTER ===== */
    .footer {
        text-align: center;
        color: #adb5bd;
        font-size: 0.8rem;
        margin-top: 3rem;
        padding: 1.5rem;
        border-top: 1px solid #e9ecef;
    }
    
    /* ===== SIDEBAR ===== */
    .sidebar-info {
        background: white;
        padding: 1rem;
        border-radius: 0.8rem;
        margin: 0.5rem 0;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    }
    .sidebar-info h4 {
        color: #1E88E5;
        margin-bottom: 0.5rem;
    }
    .sidebar-info .stat-item {
        display: flex;
        justify-content: space-between;
        padding: 0.3rem 0;
        border-bottom: 1px solid #f0f0f0;
    }
    .sidebar-info .stat-item:last-child {
        border-bottom: none;
    }
    .sidebar-info .stat-label {
        color: #6c757d;
        font-size: 0.9rem;
    }
    .sidebar-info .stat-value {
        font-weight: 600;
        color: #212529;
    }
    
    /* ===== BADGES ===== */
    .badge {
        display: inline-block;
        padding: 0.2rem 0.8rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-blue {
        background: #e3f2fd;
        color: #1E88E5;
    }
    .badge-green {
        background: #d4edda;
        color: #28a745;
    }
    .badge-red {
        background: #f8d7da;
        color: #dc3545;
    }
    .badge-yellow {
        background: #fff3cd;
        color: #ffc107;
    }
    
    /* ===== PROGRESS BAR ===== */
    .progress-container {
        background: #e9ecef;
        border-radius: 20px;
        height: 8px;
        margin: 0.5rem 0;
        overflow: hidden;
    }
    .progress-bar {
        height: 100%;
        border-radius: 20px;
        background: linear-gradient(90deg, #1E88E5, #42a5f5);
        transition: width 1s ease;
    }
    
    /* ===== STATUS ===== */
    .status-dot {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 0.5rem;
    }
    .status-dot.green {
        background: #28a745;
    }
    .status-dot.red {
        background: #dc3545;
    }
    .status-dot.yellow {
        background: #ffc107;
    }
    
    /* ===== RESPONSIVE ===== */
    @media (max-width: 600px) {
        .kpi-grid {
            grid-template-columns: repeat(2, 1fr);
        }
        .main-header {
            font-size: 1.8rem;
        }
    }
</style>
"""

# ==================== TEMA ESCURO ====================
CSS_ESCURO = """
<style>
    /* ===== FUNDO GERAL ===== */
    .stApp {
        background-color: #0e1117 !important;
    }
    .stApp > header {
        background-color: #0e1117 !important;
    }
    .stApp > header:after {
        background: none !important;
    }
    
    /* ===== MAIN ===== */
    .main-header {
        font-size: 2.5rem;
        color: #4FC3F7;
        text-align: center;
        margin-bottom: 0.5rem;
        font-weight: 700;
    }
    .main-header small {
        font-size: 1rem;
        color: #9e9e9e;
        display: block;
        font-weight: 400;
        margin-top: 0.3rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #9e9e9e;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* ===== BOXES ===== */
    .success-box {
        background-color: #1a3a2a;
        padding: 1rem 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
        color: #a8e6cf;
    }
    .info-box {
        background-color: #1a2a3a;
        padding: 1rem 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #17a2b8;
        margin: 1rem 0;
        color: #a8d8ea;
    }
    .warning-box {
        background-color: #3a2a1a;
        padding: 1rem 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
        color: #f0d8a8;
    }
    
    /* ===== BOTÕES ===== */
    .stButton>button {
        width: 100%;
        background-color: #1E88E5;
        color: white;
        font-weight: 600;
        border-radius: 8px;
        padding: 0.6rem 1rem;
        transition: all 0.3s ease;
        border: none;
    }
    .stButton>button:hover {
        background-color: #1565C0;
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(30, 136, 229, 0.3);
    }
    
    /* ===== UPLOAD ===== */
    .upload-section {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 2rem;
        border-radius: 1rem;
        border: 2px dashed #4a4a6a;
        margin: 1rem 0;
        transition: all 0.3s ease;
        color: #e0e0e0;
    }
    .upload-section:hover {
        border-color: #4FC3F7;
        background: linear-gradient(135deg, #1a1a2e 0%, #1a2a4a 100%);
    }
    .upload-section .upload-icon {
        font-size: 3rem;
        text-align: center;
        display: block;
        margin-bottom: 0.5rem;
    }
    
    /* ===== KPI CARDS ===== */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    .kpi-card {
        background: #1a1a2e;
        padding: 1.5rem 1rem;
        border-radius: 1rem;
        box-shadow: 0 2px 12px rgba(0,0,0,0.3);
        text-align: center;
        transition: all 0.3s ease;
        border: 1px solid #2a2a4a;
        color: #e0e0e0;
    }
    .kpi-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.4);
        border-color: #4FC3F7;
    }
    .kpi-card .kpi-icon {
        font-size: 2.2rem;
        display: block;
        margin-bottom: 0.5rem;
    }
    .kpi-card .kpi-value {
        font-size: 2.2rem;
        font-weight: 700;
        line-height: 1.2;
        margin-bottom: 0.2rem;
    }
    .kpi-card .kpi-label {
        font-size: 0.85rem;
        color: #9e9e9e;
        font-weight: 500;
    }
    .kpi-card .kpi-change {
        font-size: 0.75rem;
        margin-top: 0.3rem;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        display: inline-block;
    }
    .kpi-card .kpi-change.positive {
        background: #1a3a2a;
        color: #4CAF50;
    }
    .kpi-card .kpi-change.negative {
        background: #3a1a1a;
        color: #f44336;
    }
    .kpi-card .kpi-change.neutral {
        background: #2a2a2a;
        color: #9e9e9e;
    }
    
    /* Cores dos KPIs no tema escuro */
    .kpi-blue .kpi-value { color: #4FC3F7; }
    .kpi-blue .kpi-icon { color: #4FC3F7; }
    .kpi-green .kpi-value { color: #66BB6A; }
    .kpi-green .kpi-icon { color: #66BB6A; }
    .kpi-red .kpi-value { color: #ef5350; }
    .kpi-red .kpi-icon { color: #ef5350; }
    .kpi-orange .kpi-value { color: #ffa726; }
    .kpi-orange .kpi-icon { color: #ffa726; }
    .kpi-purple .kpi-value { color: #ab47bc; }
    .kpi-purple .kpi-icon { color: #ab47bc; }
    .kpi-teal .kpi-value { color: #26a69a; }
    .kpi-teal .kpi-icon { color: #26a69a; }
    
    /* ===== FILTROS ===== */
    .filter-section {
        background: #1a1a2e;
        padding: 1.5rem;
        border-radius: 0.8rem;
        border: 1px solid #2a2a4a;
        margin: 1rem 0;
        color: #e0e0e0;
    }
    .filter-section .filter-title {
        font-weight: 600;
        color: #e0e0e0;
        margin-bottom: 1rem;
        font-size: 1.1rem;
    }
    
    /* ===== COLUNAS ===== */
    .column-selector {
        background: #1a1a2e;
        padding: 1.5rem;
        border-radius: 0.8rem;
        border: 1px solid #2a2a4a;
        margin: 1rem 0;
        max-height: 500px;
        overflow-y: auto;
        color: #e0e0e0;
    }
    .column-selector .col-group {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.3rem;
    }
    @media (max-width: 768px) {
        .column-selector .col-group {
            grid-template-columns: repeat(2, 1fr);
        }
    }
    .column-selector label {
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        transition: background 0.2s;
        cursor: pointer;
        color: #e0e0e0;
    }
    .column-selector label:hover {
        background: #2a2a4a;
    }
    
    /* ===== TABS ===== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: #1a1a2e;
        padding: 0.5rem;
        border-radius: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
        transition: all 0.3s ease;
        color: #9e9e9e !important;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: #1E88E5;
        color: white !important;
        box-shadow: 0 2px 8px rgba(30, 136, 229, 0.3);
    }
    
    /* ===== FOOTER ===== */
    .footer {
        text-align: center;
        color: #4a4a6a;
        font-size: 0.8rem;
        margin-top: 3rem;
        padding: 1.5rem;
        border-top: 1px solid #2a2a4a;
    }
    
    /* ===== SIDEBAR ===== */
    .sidebar-info {
        background: #1a1a2e;
        padding: 1rem;
        border-radius: 0.8rem;
        margin: 0.5rem 0;
        box-shadow: 0 1px 4px rgba(0,0,0,0.2);
        border: 1px solid #2a2a4a;
        color: #e0e0e0;
    }
    .sidebar-info h4 {
        color: #4FC3F7;
        margin-bottom: 0.5rem;
    }
    .sidebar-info .stat-item {
        display: flex;
        justify-content: space-between;
        padding: 0.3rem 0;
        border-bottom: 1px solid #2a2a4a;
    }
    .sidebar-info .stat-item:last-child {
        border-bottom: none;
    }
    .sidebar-info .stat-label {
        color: #9e9e9e;
        font-size: 0.9rem;
    }
    .sidebar-info .stat-value {
        font-weight: 600;
        color: #e0e0e0;
    }
    
    /* ===== BADGES ===== */
    .badge {
        display: inline-block;
        padding: 0.2rem 0.8rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-blue {
        background: #1a2a4a;
        color: #4FC3F7;
    }
    .badge-green {
        background: #1a3a2a;
        color: #66BB6A;
    }
    .badge-red {
        background: #3a1a1a;
        color: #ef5350;
    }
    .badge-yellow {
        background: #3a2a1a;
        color: #ffa726;
    }
    
    /* ===== PROGRESS BAR ===== */
    .progress-container {
        background: #2a2a4a;
        border-radius: 20px;
        height: 8px;
        margin: 0.5rem 0;
        overflow: hidden;
    }
    .progress-bar {
        height: 100%;
        border-radius: 20px;
        background: linear-gradient(90deg, #1E88E5, #4FC3F7);
        transition: width 1s ease;
    }
    
    /* ===== STATUS ===== */
    .status-dot {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 0.5rem;
    }
    .status-dot.green {
        background: #66BB6A;
    }
    .status-dot.red {
        background: #ef5350;
    }
    .status-dot.yellow {
        background: #ffa726;
    }
    
    /* ===== SELECTBOX, INPUTS ===== */
    .stSelectbox > div > div {
        background-color: #1a1a2e !important;
        color: #e0e0e0 !important;
        border-color: #2a2a4a !important;
    }
    .stTextInput > div > div > input {
        background-color: #1a1a2e !important;
        color: #e0e0e0 !important;
        border-color: #2a2a4a !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #4FC3F7 !important;
    }
    
    /* ===== DATAFRAME ===== */
    .stDataFrame {
        background: #1a1a2e !important;
    }
    .stDataFrame > div {
        background: #1a1a2e !important;
    }
    
    /* ===== METRIC ===== */
    [data-testid="metric-container"] {
        background: #1a1a2e !important;
        border: 1px solid #2a2a4a !important;
        border-radius: 0.8rem !important;
        padding: 1rem !important;
    }
    [data-testid="metric-container"] label {
        color: #9e9e9e !important;
    }
    [data-testid="metric-container"] [data-testid="metric-value"] {
        color: #e0e0e0 !important;
    }
    
    /* ===== RESPONSIVE ===== */
    @media (max-width: 600px) {
        .kpi-grid {
            grid-template-columns: repeat(2, 1fr);
        }
        .main-header {
            font-size: 1.8rem;
        }
    }
</style>
"""


def aplicar_estilos():
    """Aplica os estilos CSS à página baseado no tema"""
    tema = st.session_state.get('tema', 'claro')
    
    if tema == 'escuro':
        st.markdown(CSS_ESCURO, unsafe_allow_html=True)
        # Configuração adicional para tema escuro no Streamlit
        st.markdown("""
        <style>
            .stApp {
                background-color: #0e1117 !important;
            }
            .stApp > header {
                background-color: #0e1117 !important;
            }
            .st-emotion-cache-1r6slb0 {
                background-color: #0e1117 !important;
            }
            .st-emotion-cache-1r6slb0 p {
                color: #e0e0e0 !important;
            }
            .st-emotion-cache-1v0mbdj {
                background-color: #1a1a2e !important;
            }
            .st-emotion-cache-1v0mbdj p {
                color: #e0e0e0 !important;
            }
            .st-emotion-cache-1v0mbdj label {
                color: #9e9e9e !important;
            }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown(CSS_CLARO, unsafe_allow_html=True)


def toggle_tema():
    """Alterna entre tema claro e escuro"""
    tema_atual = st.session_state.get('tema', 'claro')
    st.session_state.tema = 'escuro' if tema_atual == 'claro' else 'claro'
    st.rerun()