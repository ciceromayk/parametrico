# app.py
import streamlit as st
from utils import (
    init_storage, list_projects, save_project, load_project,
    DEFAULT_PAVIMENTO, ETAPAS_OBRA, DEFAULT_CUSTOS_INDIRETOS, DEFAULT_CUSTOS_INDIRETOS_FIXOS
)

st.set_page_config(page_title="Gestão de Projetos", layout="wide")
init_storage("projects.json")

def page_project_selection():
    """Renderiza a tela de seleção e criação de projetos."""
    st.header("🏢 Orçamento Paramétrico – Gestão de Projetos")
    st.markdown("Selecione um projeto existente para analisar ou crie um novo para começar.")
    
    projetos = list_projects()
    escolha = st.selectbox(
        "📂 Selecione um projeto ou crie um novo",
        ["➕ Novo Projeto"] + [f"{p['id']} – {p['nome']}" for p in projetos],
        label_visibility="collapsed"
    )
    
    if escolha != "➕ Novo Projeto":
        pid = int(escolha.split("–")[0].strip())
        if st.button("Carregar Projeto", use_container_width=True, type="primary"):
            st.session_state.projeto_info = load_project(pid)
            st.switch_page("pages/1_Orcamento_Direto.py")

    st.markdown("---")
    st.subheader("Criar Novo Projeto")
    with st.form("new_project_form"):
        nome = st.text_input("Nome do Projeto")
        c1, c2, c3 = st.columns(3)
        area_terreno = c1.number_input("Área Terreno (m²)", min_value=0.0, format="%.2f")
        area_privativa = c2.number_input("Área Privativa Total (m²)", min_value=0.0, format="%.2f")
        num_unidades = c3.number_input("Nº de Unidades", min_value=1, step=1)
        
        if st.form_submit_button("💾 Criar e Carregar Projeto", use_container_width=True):
            if not nome:
                st.error("O nome do projeto é obrigatório.")
                return
            
            info = {
                "nome": nome, "area_terreno": area_terreno, "area_privativa": area_privativa, "num_unidades": num_unidades, "endereco": "",
                "custos_config": {"custo_terreno_m2": 2500.0, "custo_area_privativa": 4500.0, "preco_medio_venda_m2": 10000.0},
                "etapas_percentuais": {etapa: {"percentual": vals[1], "fonte": "Manual"} for etapa, vals in ETAPAS_OBRA.items()},
                "pavimentos": [DEFAULT_PAVIMENTO.copy()],
                "custos_indiretos_percentuais": {item: {"percentual": vals[1], "fonte": "Manual"} for item, vals in DEFAULT_CUSTOS_INDIRETOS.items()},
                "custos_indiretos_fixos": DEFAULT_CUSTOS_INDIRETOS_FIXOS.copy()
            }
            save_project(info)
            st.session_state.projeto_info = info
            st.switch_page("pages/1_Orcamento_Direto.py")

# Roteamento inicial
if "projeto_info" in st.session_state:
    st.switch_page("pages/1_Orcamento_Direto.py")
else:
    page_project_selection()
