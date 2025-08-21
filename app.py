import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import plotly.express as px

# --- 1. CONFIGURAÇÃO E GESTÃO DE DADOS (Sem grandes mudanças aqui) ---
JSON_PATH = "projects.json"

def init_storage():
    """Garante que o arquivo JSON de armazenamento exista."""
    if not os.path.exists(JSON_PATH):
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=4)

def load_all_projects() -> list:
    """Carrega todos os projetos do arquivo JSON."""
    init_storage()
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_all_projects(projs: list):
    """Salva a lista completa de projetos no arquivo JSON."""
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(projs, f, ensure_ascii=False, indent=4)

def list_projects() -> list:
    """Retorna uma lista simplificada de projetos para seleção."""
    return [
        {"id": p["id"], "nome": p["nome"], "created_at": p.get("created_at")}
        for p in load_all_projects()
    ]

def save_project(info: dict):
    """Salva ou atualiza um único projeto."""
    projs = load_all_projects()
    if info.get("id"):
        pid = info["id"]
        # Atualiza o projeto existente
        projs = [p if p["id"] != pid else info for p in projs]
    else:
        # Cria um novo projeto
        existing_ids = [p["id"] for p in projs] if projs else []
        pid = max(existing_ids) + 1 if existing_ids else 1
        info["id"] = pid
        info["created_at"] = datetime.utcnow().isoformat()
        projs.append(info)
    
    save_all_projects(projs)
    return pid

def load_project(pid: int) -> dict:
    """Carrega os dados de um projeto específico."""
    for p in load_all_projects():
        if p["id"] == pid:
            return p
    return None

def delete_project(pid: int):
    """Exclui um projeto do arquivo."""
    projs = [p for p in load_all_projects() if p["id"] != pid]
    save_all_projects(projs)

def fmt_br(valor: float) -> str:
    """Formata número para o padrão brasileiro."""
    s = f"{valor:,.2f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")

# --- 2. DADOS E COEFICIENTES DO NEGÓCIO ---
TIPOS_PAVIMENTO = {
    "Área Privativa (Autônoma)": (1.00, 1.00),
    "Varandas": (0.75, 1.00),
    "Terraços / Áreas Descobertas": (0.30, 0.60),
    "Garagem (Subsolo)": (0.50, 0.75),
    "Estacionamento (terreno)": (0.05, 0.10),
    "Salas com Acabamento": (1.00, 1.00),
    "Salas sem Acabamento": (0.75, 0.90),
    "Loja sem Acabamento": (0.40, 0.60),
    "Serviço (unifam. baixa, aberta)": (0.50, 0.50),
    "Barrilete / Cx D'água / Casa Máquinas": (0.50, 0.75),
    "Piscinas": (0.50, 0.75),
    "Quintais / Calçadas / Jardins": (0.10, 0.30),
    "Projeção Terreno sem Benfeitoria": (0.00, 0.00),
}
DEFAULT_PAVIMENTO = {
    "nome": "Pavimento Tipo", "tipo": "Área Privativa (Autônoma)",
    "rep": 1, "coef": 1.00, "area": 100.0, "constr": True
}


# --- 3. TELAS DA APLICAÇÃO (Código refatorado) ---

def page_project_selection():
    """Renderiza a tela de seleção e criação de projetos."""
    st.header("🏢 Orçamento Paramétrico – Gestão de Projetos")
    projetos = list_projects()
    
    escolha = st.selectbox(
        "📂 Selecione um projeto ou crie um novo",
        ["➕ Novo Projeto"] + [f"{p['id']} – {p['nome']}" for p in projetos]
    )
    
    if escolha != "➕ Novo Projeto":
        pid = int(escolha.split("–")[0].strip())
        if st.button("Carregar Projeto", use_container_width=True, type="primary"):
            st.session_state.projeto_info = load_project(pid)
            st.rerun()

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
                "nome": nome, "area_terreno": area_terreno, "area_privativa": area_privativa,
                "num_unidades": num_unidades, "endereco": "",
                "custos_config": {"cub": 4500.0, "bdi": 25.0, "outros": 0.0},
                "pavimentos": [DEFAULT_PAVIMENTO] # Começa com um pavimento padrão
            }
            pid = save_project(info)
            info["id"] = pid
            st.session_state.projeto_info = info
            st.rerun()

def page_budget_tool():
    """Renderiza a interface principal de orçamento do projeto carregado."""
    info = st.session_state.projeto_info

    # Inicializa os pavimentos no session_state se não existirem
    if 'pavimentos' not in st.session_state:
        st.session_state.pavimentos = info.get('pavimentos', [DEFAULT_PAVIMENTO.copy()])
    
    # --- BARRA LATERAL (SIDEBAR) ---
    with st.sidebar:
        st.title(f"Projeto: {info['nome']}")
        
        # Expander para editar dados do projeto
        with st.expander("📝 Editar Dados Gerais do Projeto", expanded=False):
            with st.form("edit_form"):
                info['nome'] = st.text_input("Nome", value=info['nome'])
                info['area_terreno'] = st.number_input("Área Terreno (m²)", value=info['area_terreno'])
                info['area_privativa'] = st.number_input("Área Privativa (m²)", value=info['area_privativa'])
                info['num_unidades'] = st.number_input("Unidades", value=info['num_unidades'], step=1)
                st.form_submit_button("Atualizar Dados")

        # Configuração de Custos
        st.markdown("---")
        st.header("💰 Configuração de Custos")
        custos_config = info.get('custos_config', {"cub": 4500.0, "bdi": 25.0, "outros": 0.0})
        
        custos_config['cub'] = st.number_input("Custo Unit. Básico (CUB) R$/m²", min_value=0.0, value=custos_config['cub'], step=100.0, format="%.2f")
        custos_config['bdi'] = st.slider("BDI (%)", 0.0, 50.0, value=custos_config['bdi'], step=0.5)
        custos_config['outros'] = st.number_input("Outros Custos Fixos (R$)", min_value=0.0, value=custos_config['outros'], format="%.2f")
        info['custos_config'] = custos_config

        # Botão para salvar todas as alterações
        st.markdown("---")
        if st.button("💾 Salvar Todas as Alterações", use_container_width=True, type="primary"):
            info['pavimentos'] = st.session_state.pavimentos
            save_project(info)
            st.success("Projeto salvo com sucesso!")

        if st.button(" Mudar de Projeto", use_container_width=True):
            del st.session_state.projeto_info
            if 'pavimentos' in st.session_state: del st.session_state.pavimentos
            st.rerun()

    # --- TELA PRINCIPAL ---
    st.title("🏗️ Orçamento Paramétrico de Edifícios")
    
    # Métricas principais usando st.metric
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Nome", info["nome"])
    c2.metric("Área Terreno", f"{fmt_br(info['area_terreno'])} m²")
    c3.metric("Área Privativa", f"{fmt_br(info['area_privativa'])} m²")
    c4.metric("Nº Unidades", info["num_unidades"])

    st.markdown("---")
    
    # --- Seção de Pavimentos Dinâmica ---
    st.markdown("#### 🏢 Dados dos Pavimentos")
    
    b1, b2, _ = st.columns([0.2, 0.2, 0.6])
    if b1.button("➕ Adicionar Pavimento"):
        st.session_state.pavimentos.append(DEFAULT_PAVIMENTO.copy())
        st.rerun()
    if b2.button("➖ Remover Último"):
        if st.session_state.pavimentos:
            st.session_state.pavimentos.pop()
            st.rerun()

    # Cabeçalhos da tabela de pavimentos
    col_widths = [3, 3, 1, 1.2, 1.5, 1.5, 1.5, 1]
    headers = ["Nome", "Tipo", "Rep.", "Coef.", "Área (m²)", "Área Eq. Total", "Área Constr.", "Incluir?"]
    header_cols = st.columns(col_widths)
    for hc, title in zip(header_cols, headers):
        hc.markdown(f'**{title}**')

    # Loop para criar os campos de cada pavimento
    registros = []
    for i, pav in enumerate(st.session_state.pavimentos):
        c1, c2, c3, c4, c5, c6, c7, c8 = st.columns(col_widths)
        pav['nome'] = c1.text_input("nome", value=pav['nome'], key=f"nome_{i}", label_visibility="collapsed")
        pav['tipo'] = c2.selectbox("tipo", list(TIPOS_PAVIMENTO.keys()), index=list(TIPOS_PAVIMENTO.keys()).index(pav['tipo']), key=f"tipo_{i}", label_visibility="collapsed")
        pav['rep'] = c3.number_input("rep", min_value=1, value=pav['rep'], step=1, key=f"rep_{i}", label_visibility="collapsed")
        
        min_c, max_c = TIPOS_PAVIMENTO[pav['tipo']]
        if min_c == max_c:
            pav['coef'] = min_c
            c4.markdown(f"<div style='text-align:center; padding-top: 8px;'>{pav['coef']:.2f}</div>", unsafe_allow_html=True)
        else:
            pav['coef'] = c4.slider("coef", min_c, max_c, value=float(pav['coef']), step=0.01, format="%.2f", key=f"coef_{i}", label_visibility="collapsed")
        
        pav['area'] = c5.number_input("area", min_value=0.0, value=pav['area'], step=1.0, format="%.2f", key=f"area_{i}", label_visibility="collapsed")
        pav['constr'] = c8.selectbox("incluir", ["Sim", "Não"], index=0 if pav['constr'] else 1, key=f"constr_{i}", label_visibility="collapsed") == "Sim"

        total_i = pav['area'] * pav['rep']
        area_eq_i = total_i * pav['coef']
        c6.markdown(f"<div style='text-align:center; padding-top: 8px;'>{fmt_br(area_eq_i)}</div>", unsafe_allow_html=True)
        c7.markdown(f"<div style='text-align:center; padding-top: 8px;'>{fmt_br(total_i)}</div>", unsafe_allow_html=True)

    # --- CÁLCULOS E EXIBIÇÃO DOS RESULTADOS ---
    df = pd.DataFrame(st.session_state.pavimentos)
    if not df.empty:
        df["area_eq"] = df["area"] * df["coef"] * df["rep"]
        df["area_constr"] = df.apply(lambda row: row["area"] * row["rep"] if row["constr"] else 0.0, axis=1)
        df["custo_direto"] = df["area_eq"] * custos_config['cub']
        
        # Totais
        total_eq = df["area_eq"].sum()
        total_constr = df["area_constr"].sum()
        custo_direto_total = df["custo_direto"].sum()
        custo_com_bdi = custo_direto_total * (1 + custos_config['bdi'] / 100)
        custo_final_projeto = custo_com_bdi + custos_config['outros']

        # --- Gráfico e Resumo ---
        st.markdown("---")
        st.markdown("## 📊 Análise e Resumo Financeiro")
        
        resumo_col1, chart_col2 = st.columns([0.4, 0.6])
        
        with resumo_col1:
            st.markdown("#### 🔢 Indicadores Chave")
            priv_area = info["area_privativa"] or 1.0
            razao_ac_pri = total_constr / priv_area if priv_area > 0 else 0.0
            custo_por_ac = custo_final_projeto / total_constr if total_constr > 0 else 0.0
            custo_med_unit = custo_final_projeto / info["num_unidades"] if info["num_unidades"] > 0 else 0.0

            st.metric("Custo Final do Projeto", f"R$ {fmt_br(custo_final_projeto)}")
            st.metric("Custo Médio / Unidade", f"R$ {fmt_br(custo_med_unit)}")
            st.metric("Custo / m² (Área Constr.)", f"R$ {fmt_br(custo_por_ac)}")
            st.metric("Razão A.C / A.Privativa", f"{razao_ac_pri:.2f}")
            st.metric("Área Constr. Total", f"{fmt_br(total_constr)} m²")
            st.metric("Área Eq. Total", f"{fmt_br(total_eq)} m²")

        with chart_col2:
            st.markdown("#### 🍰 Composição do Custo Direto")
            custo_por_tipo = df.groupby("tipo")["custo_direto"].sum().reset_index()
            fig = px.pie(custo_por_tipo, names='tipo', values='custo_direto', hole=.4)
            fig.update_layout(showlegend=False, margin=dict(l=10, r=10, t=10, b=10))
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)

        # --- Tabela Detalhada ---
        st.markdown("---")
        st.markdown("### 📑 Detalhamento por Pavimento")
        
        df_display = df.rename(columns={
            "nome": "Nome", "tipo": "Tipo", "rep": "Rep.", "coef": "Coef.", 
            "area": "Área (m²)", "area_eq": "Área Eq. Total",
            "area_constr": "Área Constr.", "custo_direto": "Custo Direto (R$)"
        })
        
        for col in ["Área (m²)", "Área Eq. Total", "Área Constr."]:
            df_display[col] = df_display[col].apply(fmt_br)
        df_display["Custo Direto (R$)"] = df_display["Custo Direto (R$)"].apply(lambda v: f"R$ {fmt_br(v)}")

        st.dataframe(df_display[["Nome", "Tipo", "Rep.", "Coef.", "Área (m²)", "Área Eq. Total", "Área Constr.", "Custo Direto (R$)"]], use_container_width=True)
        
        # --- Botão de Exclusão ---
        st.markdown("---")
        if st.button("🗑️ Excluir Projeto", help="Apaga o projeto atual e retorna à tela inicial"):
            delete_project(info["id"])
            del st.session_state.projeto_info
            if 'pavimentos' in st.session_state: del st.session_state.pavimentos
            st.rerun()

# --- 4. ROTEADOR PRINCIPAL DA APLICAÇÃO ---
def main():
    """Função principal que controla qual página exibir."""
    st.set_page_config(
        page_title="Orçamento Paramétrico",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    init_storage()

    if "projeto_info" not in st.session_state:
        page_project_selection()
    else:
        page_budget_tool()

if __name__ == "__main__":
    main()
