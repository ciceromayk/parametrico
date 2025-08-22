# pages/2_Custos_Indiretos.py

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

def card_metric_pro(label, value, delta=None, icon_name="cash-coin"):
    """
    Cartão de métrica profissional com design moderno
    """
    st.markdown(f"""
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
    <div style="
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        background: linear-gradient(145deg, #f9f9f9, #ffffff);
        box-shadow: 5px 5px 15px rgba(0,0,0,0.05);
        transition: transform 0.3s ease;
    " 
    onmouseover="this.style.transform='scale(1.03)'"
    onmouseout="this.style.transform='scale(1)'"
    >
        <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 10px;">
            <i class="bi bi-{icon_name}" style="font-size: 1.5em; margin-right: 10px; color: #007bff;"></i>
            <h3 style="margin: 0; color: #333; font-size: 1.2em;">{label}</h3>
        </div>
        <p style="font-size: 2.5em; font-weight: bold; margin: 0; color: #007bff;">{value}</p>
        {f'<p style="color: {"green" if delta and delta > 0 else "red"}; font-size: 1em;">{f"+{delta}%" if delta else ""}</p>' if delta is not None else ''}
    </div>
    """, unsafe_allow_html=True)

def configurar_grid(df):
    """
    Configuração avançada do AgGrid com formatações personalizadas
    """
    gb = GridOptionsBuilder.from_dataframe(df)
    
    # Formatador de moeda
    jscode_formatador_moeda = JsCode("""
        function(params) {
            if (params.value === null || params.value === undefined) { return ''; }
            return 'R$ ' + params.value.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
        }
    """)
    
    # Estilizador condicional de percentuais
    jscode_estilo_percentual = JsCode("""
        function(params) {
            if (params.value < 3) return {'color': 'green', 'fontWeight': 'bold'};
            if (params.value >= 3 && params.value < 6) return {'color': 'orange', 'fontWeight': 'bold'};
            return {'color': 'red', 'fontWeight': 'bold'};
        }
    """)
    
    gb.configure_column("Item", 
        headerName="Item de Custo", 
        flex=5, 
        resizable=True,
        cellStyle={'textAlign': 'left'}
    ) 
    
    gb.configure_column("%", 
        headerName="% VGV", 
        editable=True, 
        cellStyle=jscode_estilo_percentual,
        type=
