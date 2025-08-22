# pages/3_Custos_Indiretos.py

import streamlit as st
import pandas as pd
from utils import *
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

# Configurações de estilo globais
st.set_page_config(
    page_title="Custos Indiretos",
    layout="wide",
    page_icon="💸"
)

# Injeção de CSS para aumentar o tamanho da fonte da tabela AgGrid
st.markdown("""
<style>
    /* Aumenta a fonte do cabeçalho da tabela */
    .ag-theme-streamlit .ag-header-cell {
        font-size: 22px !important;
    }
    /* Aumenta a fonte das células da tabela */
    .ag-theme-streamlit .ag-cell {
        font-size: 22px !important;
    }
</style>
""", unsafe_allow_html=True)


def card_metric_pro(label, value, delta=None, icon_name="cash-coin", bg_color="#f9f9f9", text_color="#007bff"):
    """
    Cartão de métrica profissional com design moderno e cores personalizáveis
    """
    st.markdown(f"""
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
    <div style="
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        background: {bg_color};
        box-shadow: 5px 5px 15px rgba(0,0,0,0.05);
        transition: transform 0.3s ease;
    "
    onmouseover="this.style.transform='scale(1.03)'"
    onmouseout="this.style.transform='scale(1)'"
    >
        <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 10px;">
            <i class="bi bi-{icon_name}" style="font-size: 1.5em; margin-right: 10px; color: {text_color};"></i>
            <h3 style="margin: 0; color: #333; font-size: 1.2em;">{label}</h3>
        </div>
        <p style="font-size: 2.5em; font-weight: bold; margin: 0; color: {text_color};">{value}</p>
        {f'<p style="color: {"green" if delta and delta > 0 else "red"}; font-size: 1em;">{f"+{delta}%" if delta else ""}</p>' if delta is not None else ''}
    </div>
    """, unsafe_allow_html=True)

# Verificação inicial do projeto carregado
if "projeto_info" not in st.session_state:
    st.error("Nenhum projeto carregado. Por favor, selecione um projeto na página inicial.")
    if st.button("Voltar para a seleção de projetos"):
        st.switch_page("Início.py")
    st.stop()

# Passamos uma chave única para a função da sidebar para evitar erros
render_sidebar(form_key="sidebar_custos_indiretos")

info = st.session_state.projeto_info
