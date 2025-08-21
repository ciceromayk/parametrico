# Início.py
import streamlit as st
from datetime import datetime
from utils import (
    init_storage, list_projects, save_project, load_project, delete_project,
    DEFAULT_PAVIMENTO, ETAPAS_OBRA, DEFAULT_CUSTOS_INDIRETOS, DEFAULT_CUSTOS_INDIRETOS_FIXOS
)

st.set_page_config(page_title="Estudo de Viabilidade", layout="wide")
init_storage("projects.json")

# <<< 2. CSS PARA AUMENTAR O TEXTO DO MENU NA SIDEBAR
st.markdown("""
<style>
    div[data-testid="stSidebarNav"] li a {
        font-size: 18px;
    }
</style>
""", unsafe_allow_html=True)


def page_project_selection():
    """Renderiza a tela de seleção e criação de projetos."""
    st.title("Estudo de Viabilidade")
    st.markdown("Selecione um projeto existente para analisar ou crie um novo para começar.")
    
    st.divider()

    st.subheader("📂 Projetos Existentes")
    
    projetos = list_projects()
    if not projetos:
        st.info("Nenhum projeto encontrado. Crie um novo abaixo.")
    else:
        # Cabeçalho da tabela
        cols = st.columns((1, 4, 2, 1, 1))
        cols[0].markdown("**ID**")
        cols[1].markdown("**Nome do Projeto**")
        cols[2].markdown("**Data de Criação**")
        cols[3].markdown("**Ação**")
        cols[4].markdown("**Excluir**")

        # Linhas da tabela
        for proj in sorted(projetos, key=lambda p: p['id']):
            cols = st.columns((1, 4, 2, 1, 1))
            cols[0].write(proj['id'])
            cols[1].write(proj['nome'])
            
            # Formata a data para o padrão brasileiro
            data_criacao = datetime.fromisoformat(proj.get('created_at', '1970-01-01T00:00:00')).strftime('%d/%m/%Y')
            cols[2].write(data_criacao)
            
            if cols[3].button("Carregar", key=f"load_{proj['id']}", use_container_width=True):
                st.session_state.projeto_info = load_project(proj['id'])
                st.switch_page("pages/1_Custos_Diretos.py")

            if cols[4].button("🗑️", key=f"delete_{proj['id']}", use_container_width=True, help=f"Excluir projeto '{proj['nome']}'"):
                delete_project(proj['id'])
                st.rerun()

    st.divider()
    
    with st.expander("➕ Criar Novo Projeto"):
        with st.form("new_project_form"):
            nome = st.text_input("Nome do Novo Projeto")
            c1, c2, c3 = st.columns(3)
            area_terreno = c1.number_input("Área Terreno (m²)", min_value=0.0, format="%.2f")
            area_privativa = c2.number_input("Área Privativa Total (m²)", min_value=0.0, format="%.2f")
            num_unidades = c3.number_input("Nº de Unidades", min_value=1, step=1)
            
            if st.form_submit_button("💾 Criar e Carregar Projeto", use_container_width=True, type="primary"):
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
                st.switch_page("pages/1_Custos_Diretos.py")

# Roteamento inicial
if "projeto_info" in st.session_state:
    st.switch_page("pages/1_Custos_Diretos.py")
else:
    page_project_selection()
