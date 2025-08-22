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

st.set_page_config(page_title="Administração da Obra", layout="wide", page_icon="📝")

if "projeto_info" not in st.session_state:
    st.error("Nenhum projeto carregado. Por favor, selecione um projeto na página inicial.")
    if st.button("Voltar para a seleção de projetos"):
        st.switch_page("Início.py")
    st.stop()

# Passamos uma chave única para a sidebar
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
    st.session_state.duracao_obra = st.slider(
        "Duração da Obra (meses):",
        min_value=1,
        max_value=60,
        value=st.session_state.duracao_obra
    )

    df_custos_obra = pd.DataFrame([
        {"Item": item, "Custo Mensal (R$)": valor}
        for item, valor in st.session_state.custos_indiretos_obra.items()
    ])

    edited_df_custos_obra = st.data_editor(df_custos_obra, use_container_width=True, num_rows="dynamic")

    if not edited_df_custos_obra.empty:
        total_mensal = edited_df_custos_obra["Custo Mensal (R$)"].sum()
        custo_indireto_obra_total_recalculado = total_mensal * st.session_state.duracao_obra
        st.subheader("Resumo dos Custos Indiretos de Obra")
        col_res1, col_res2, col_res3 = st.columns(3)
        col_res1.metric(
            "Custo Mensal Total",
            f"R$ {fmt_br(total_mensal)}"
        )
        col_res2.metric(
            "Duração da Obra (meses)",
            st.session_state.duracao_obra
        )
        col_res3.metric(
            "Custo Indireto de Obra Total",
            f"R$ {fmt_br(custo_indireto_obra_total_recalculado)}"
        )
        st.session_state.custos_indiretos_obra = {
            row["Item"]: row["Custo Mensal (R$)"]
            for index, row in edited_df_custos_obra.iterrows()
        }

