# pages/2_Custos_Indiretos.py

import streamlit as st
import pandas as pd
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
        type=["numericColumn"]
    )
    
    gb.configure_column("Custo(R$)", 
        headerName="Custo (R$)", 
        valueFormatter=jscode_formatador_moeda,
        type=["numericColumn"]
    )
    
    gb.configure_grid_options(
        enableRangeSelection=True,
        enableCellTextSelection=True
    )
    
    return gb.build()

def main():
    st.title("📊 Custos Indiretos")
    
    # Dados de Custos Indiretos
    dados_custos = {
        "Item": [
            "IRPJ/CS/PIS/COFINS", "Contratação", "Publicidade", 
            "Manutenção", "Custo Fixo Incorporadora", "Assessoria Técnica", 
            "Projetos", "Licença e Incorporação", "Outorga Onerosa", 
            "Condomínio", "IPTU", "Preparação de Terreno", 
            "Financiamento Bancário"
        ],
        "%": [
            4.00, 3.51, 0.90, 0.50, 4.00, 0.70, 
            0.52, 0.30, 0.00, 0.00, 0.07, 0.33, 
            1.90
        ],
        "Custo(R$)": [
            2460000.00, 2156000.00, 552000.00, 
            308000.00, 2460000.00, 430000.00, 
            320000.00, 184000.00, 0.00, 
            0.00, 43000.00, 203000.00, 
            1168000.00
        ]
    }
    
    df_custos = pd.DataFrame(dados_custos)
    
    # Grid interativo com AgGrid
    grid_options = configurar_grid(df_custos)
    AgGrid(df_custos, gridOptions=grid_options, theme='alpine')
    
    # Métrica de Custo Indireto Total
    custo_total = df_custos['Custo(R$)'].sum()
    card_metric_pro(
        "Custo Indireto Total", 
        f"R$ {custo_total:,.2f}", 
        icon_name="pie-chart"
    )

if __name__ == "__main__":
    main()
