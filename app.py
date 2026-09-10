# app.py - Na RAIZ do projeto
"""
Ponto de entrada da aplicação Streamlit
"""

import streamlit as st
from ui.pages import MainPage


def main():
    """Função principal da aplicação"""
    # Configuração da página
    st.set_page_config(
        page_title="Sistema de Tratamento de Dados - Ergon",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Renderizar página
    page = MainPage()
    page.render()


if __name__ == "__main__":
    main()