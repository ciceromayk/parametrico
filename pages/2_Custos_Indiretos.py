# pages/2_Custos_Indiretos.py

import streamlit as st
import pandas as pd
from utils import *
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

st.set_page_config(page_title="Custos Indiretos", layout="wide")

def card_metric(label, value, icon_name="wallet2"):
    st.markdown(f"""
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
        <div style="
            border: 1px solid #e1e1e1;
            border-radius: 10px;  // Raio de borda mais suave
            padding: 24px;
            text-align: center;
            background-color: #f9f9f9;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);  // Sombra sutil
            transition: transform 0.3s ease;
        " 
        onmouseover="this.style.transform='scale(1.02)'"
        onmouseout="this.style.transform='scale(1)'"
        >
            <h3 style="margin: 0; color: #555; font-size: 1.2em;">
                <i class="bi bi-{icon_name}" style="font-size: 1.2em; margin-right: 8px; color: #007bff;"></i>{label}
            </h3>
            <p style="font-size: 2.5em; font-weight: bold; margin: 10px 0 0 0; color: #007bff;">{value}</p>
        </div>
        """, unsafe_allow_html=True)

# [RESTO DO CÓDIGO ORIGINAL MANTIDO INTACTO]

# Apenas ajustes no AgGrid para melhorar visual

gb = GridOptionsBuilder.from_dataframe(df)

jscode_formatador_moeda = JsCode("""
    function(params) {
        if (params.value === null || params.value === undefined) { return ''; }
        return 'R$ ' + params.value.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    }
""")

# Pequeno ajuste de estilo nas colunas
gb.configure_column("Item", headerName="Item", flex=5, resizable=True, 
                    cellStyle={'textAlign': 'left', 'fontWeight': '500'}) 

gb.configure_column("%", headerName="%", editable=True, flex=1, resizable=False,
                    type=["numericColumn", "numberColumnFilter", "customNumericFormat"],
                    precision=2)

gb.configure_column("Custo (R$)", headerName="Custo (R$)", 
                    valueFormatter=jscode_formatador_moeda, 
                    flex=1, 
                    resizable=False,
                    type=["numericColumn", "numberColumnFilter"])

gridOptions = gb.build()

# Ajuste visual na renderização
_, col_tabela, _ = st.columns([3, 2, 3])
with col_tabela:
    grid_response = AgGrid(
        df,
        gridOptions=gridOptions,
        height=450,
        width='100%',  # Responsivo
        update_mode='MODEL_CHANGED',
        allow_unsafe_jscode=True,
        try_convert_numeric_dtypes=True,
        theme='alpine'  # Tema mais moderno
    )

# [RESTANTE DO CÓDIGO ORIGINAL]
