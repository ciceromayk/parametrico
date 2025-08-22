# pages/2_Custos_Indiretos.py

import streamlit as st
import pandas as pd
from utils import *
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
import plotly.express as px
import plotly.graph_objects as go

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

# Verificação inicial do projeto carregado
if "projeto_info" not in st.session_state:
    st.error("Nenhum projeto carregado. Por favor, selecione um projeto na página inicial.")
    if st.button("Voltar para a seleção de projetos"):
        st.switch_page("Início.py")
    st.stop()

# Passamos uma chave única para a função da sidebar para evitar erros
render_sidebar(form_key="sidebar_custos_indiretos")

info = st.session_state.projeto_info

st.title("💸 Custos Indiretos")

# Cálculos Preliminares
custos_config = info.get('custos_config', {})
preco_medio_venda_m2 = custos_config.get('preco_medio_venda_m2', 10000.0)
vgv_total = info.get('area_privativa', 0) * preco_medio_venda_m2

# Bloco principal com a nova tabela AgGrid e Gráficos
with st.expander("Análise Detalhada de Custos Indiretos", expanded=True):
    st.subheader("Configuração e Análise de Custos Indiretos")

    # Inicialização do session_state
    if 'custos_indiretos_percentuais' not in st.session_state:
        custos_salvos = info.get('custos_indiretos_percentuais', {})
        
        if custos_salvos and isinstance(list(custos_salvos.values())[0], (int, float)):
            st.session_state.custos_indiretos_percentuais = {item: {"percentual": val, "fonte": "Manual"} for item, val in custos_salvos.items()}
        else:
            st.session_state.custos_indiretos_percentuais = {item: custos_salvos.get(item, {"percentual": vals[1], "fonte": "Manual"}) for item, vals in DEFAULT_CUSTOS_INDIRETOS.items()}

    # Preparar os Dados para o AgGrid e Gráficos
    dados_tabela = []
    for item, (min_val, default_val, max_val) in DEFAULT_CUSTOS_INDIRETOS.items():
        percentual_atual = st.session_state.custos_indiretos_percentuais.get(item, {"percentual": default_val})['percentual']
        custo_calculado = vgv_total * (percentual_atual / 100)
        
        dados_tabela.append({
            "Item": item,
            "Percentual (%)": percentual_atual,
            "Custo (R$)": custo_calculado,
        })

    df = pd.DataFrame(dados_tabela)

    # Configurar o AgGrid
    gb = GridOptionsBuilder.from_dataframe(df)
    
    jscode_formatador_moeda = JsCode("""
        function(params) {
            if (params.value === null || params.value === undefined) { return ''; }
            return 'R$ ' + params.value.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
        }
    """)

    gb.configure_column("Item", headerName="Item", flex=5, resizable=True)
    gb.configure_column("Percentual (%)",
        headerName="Percentual (%)",
        editable=True,
        flex=1,
        resizable=False,
        type=["numericColumn", "numberColumnFilter", "customNumericFormat"],
        precision=2
    )
    gb.configure_column("Custo (R$)",
        headerName="Custo (R$)",
        valueFormatter=jscode_formatador_moeda,
        flex=1,
        resizable=False,
        type=["numericColumn", "numberColumnFilter"]
    )
    
    gridOptions = gb.build()

    col1, col2 = st.columns([1, 1])

    with col1:
        st.write("### Ajuste os Percentuais")
        grid_response = AgGrid(
            df,
            gridOptions=gridOptions,
            height=350,
            width='100%',
            update_mode='MODEL_CHANGED',
            allow_unsafe_jscode=True,
            try_convert_numeric_dtypes=True,
            theme='streamlit'
        )
        
    with col2:
        st.write("### Participação no VGV")
        df_sorted = df.sort_values(by='Percentual (%)', ascending=False)
        fig_pie = px.pie(df_sorted, values='Percentual (%)', names='Item',
                         title='Composição dos Custos Indiretos')
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(showlegend=False, margin=dict(l=20, r=20, t=40, b=20),
                              height=350)
        st.plotly_chart(fig_pie, use_container_width=True)

    # Usar os Dados Editados
    edited_df = grid_response['data']
    
    # Recalcular "Custo (R$)" baseado no percentual editado
    edited_df["Custo (R$)"] = vgv_total * (pd.to_numeric(edited_df["Percentual (%)"], errors='coerce').fillna(0) / 100)
    custo_indireto_calculado = edited_df["Custo (R$)"].sum()
    
    for index, row in edited_df.iterrows():
        item_nome = row["Item"]
        novo_percentual = row["Percentual (%)"]
        st.session_state.custos_indiretos_percentuais[item_nome]['percentual'] = novo_percentual

    # Adicionar espaçamento vertical
    st.write("<br>", unsafe_allow_html=True)

    st.subheader("Resumo Financeiro")
    col3, col4, col5 = st.columns([1, 1, 1])
    
    with col3:
        card_metric_pro(
            label="VGV Total",
            value=f"R$ {fmt_br(vgv_total)}",
            icon_name="building-fill-up"
        )
    with col4:
        card_metric_pro(
            label="Custo Indireto Total",
            value=f"R$ {fmt_br(custo_indireto_calculado)}",
            icon_name="cash-coin"
        )
    with col5:
        card_metric_pro(
            label="% do Custo Indireto",
            value=f"{((custo_indireto_calculado / vgv_total) * 100):.2f}%",
            icon_name="percent"
        )

