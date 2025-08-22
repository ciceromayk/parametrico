# pages/2_Administracao_da_Obra.py
import streamlit as st
import pandas as pd
from utils import (
    fmt_br, render_metric_card, render_sidebar, DEFAULT_CUSTOS_INDIRETOS_OBRA,
    DEFAULT_CUSTOS_INDIRETOS, ETAPAS_OBRA, DEFAULT_PAVIMENTO,
    list_projects, save_project, load_project, delete_project,
    JSON_PATH, HISTORICO_DIRETO_PATH, HISTORICO_INDIRETO_PATH,
    load_json, save_to_historico
)
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

st.set_page_config(page_title="Administração da Obra", layout="wide", page_icon="📝")

# Injeta CSS para esconder o menu automático
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# Funcao de cartão de métrica profissional com design moderno
def card_metric_pro(label, value, delta=None, icon_name="cash-coin"):
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


if "projeto_info" not in st.session_state:
    st.error("Nenhum projeto carregado. Por favor, selecione um projeto na página inicial.")
    if st.button("Voltar para a seleção de projetos"):
        st.switch_page("Início.py")
    st.stop()

render_sidebar(form_key="sidebar_administracao_obra")

info = st.session_state.projeto_info
st.title("📝 Administração da Obra")
st.subheader("Custos Mensais e Duração do Projeto")

if 'custos_indiretos_obra' not in st.session_state:
    st.session_state.custos_indiretos_obra = info.get('custos_indiretos_obra', {k: v for k, v in DEFAULT_CUSTOS_INDIRETOS_OBRA.items()})
if 'duracao_obra' not in st.session_state:
    st.session_state.duracao_obra = info.get('duracao_obra', 12)


with st.expander("💸 Custos Indiretos de Obra (por Período)", expanded=True):
    st.markdown("---")
    st.subheader("Configuração dos Custos Indiretos da Obra")
    st.markdown("Estes custos são calculados com base na duração do projeto.")

    # Slider para a duracao da obra
    st.session_state.duracao_obra = st.slider(
        "Duração da Obra (meses):",
        min_value=1,
        max_value=60,
        value=st.session_state.duracao_obra
    )

    # Prepara os dados para o AgGrid
    dados_tabela_obra = []
    for item, valor_mensal in st.session_state.custos_indiretos_obra.items():
        dados_tabela_obra.append({
            "Item": item,
            "Custo Mensal (R$)": valor_mensal,
            "Custo Total (R$)": valor_mensal * st.session_state.duracao_obra
        })
    
    df_custos_obra = pd.DataFrame(dados_tabela_obra)

    # Configura o AgGrid
    gb = GridOptionsBuilder.from_dataframe(df_custos_obra)

    jscode_formatador_moeda = JsCode("""
        function(params) {
            if (params.value === null || params.value === undefined) { return ''; }
            return 'R$ ' + params.value.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
        }
    """)
    
    gb.configure_column("Item", headerName="Item", flex=5, resizable=True)
    gb.configure_column("Custo Mensal (R$)",
        headerName="Custo Mensal (R$)",
        editable=True,
        valueFormatter=jscode_formatador_moeda,
        flex=1,
        resizable=False,
        type=["numericColumn", "numberColumnFilter", "customNumericFormat"]
    )
    gb.configure_column("Custo Total (R$)",
        headerName="Custo Total (R$)",
        valueFormatter=jscode_formatador_moeda,
        flex=1,
        resizable=False,
        type=["numericColumn", "numberColumnFilter"]
    )
    
    gridOptions = gb.build()

    # Centraliza a tabela
    _, col_tabela_obra, _ = st.columns([2,9,2])
    with col_tabela_obra:
        grid_response = AgGrid(
            df_custos_obra,
            gridOptions=gridOptions,
            height=450,
            width='200%',
            update_mode='MODEL_CHANGED',
            allow_unsafe_jscode=True,
            try_convert_numeric_dtypes=True,
            theme='streamlit'
        )

    # Usa os dados editados
    edited_df_custos_obra = grid_response['data']
    
    # Recalcula o total
    if not edited_df_custos_obra.empty:
        total_mensal = edited_df_custos_obra["Custo Mensal (R$)"].sum()
        custo_indireto_obra_total_recalculado = total_mensal * st.session_state.duracao_obra
        
        # Salva o estado
        st.session_state.custos_indiretos_obra = {
            row["Item"]: row["Custo Mensal (R$)"]
            for index, row in edited_df_custos_obra.iterrows()
        }
        
        # Adiciona espaçamento vertical
        st.write("<br>", unsafe_allow_html=True)
        
        # Centraliza o card de métricas
        _, col_metrica_obra, _ = st.columns([2, 8, 2])
        
        with col_metrica_obra:
            col_res1, col_res2, col_res3 = st.columns(3)
            with col_res1:
                card_metric_pro(
                    label="Custo Mensal Total",
                    value=f"R$ {fmt_br(total_mensal)}",
                    icon_name="cash-coin"
                )
            with col_res2:
                card_metric_pro(
                    label="Duração da Obra (meses)",
                    value=f"{st.session_state.duracao_obra}",
                    icon_name="clock"
                )
            with col_res3:
                card_metric_pro(
                    label="Custo Indireto de Obra Total",
                    value=f"R$ {fmt_br(custo_indireto_obra_total_recalculado)}",
                    icon_name="building-fill-up"
                )
