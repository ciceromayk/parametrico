import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import plotly.express as px

# --- 1. CONFIGURAÇÃO E GESTÃO DE DADOS ---
JSON_PATH = "projects.json"

def init_storage():
    if not os.path.exists(JSON_PATH):
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=4)

def load_all_projects() -> list:
    init_storage()
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_all_projects(projs: list):
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(projs, f, ensure_ascii=False, indent=4)

def list_projects() -> list:
    return [{"id": p["id"], "nome": p["nome"]} for p in load_all_projects()]

def save_project(info: dict):
    projs = load_all_projects()
    if info.get("id"):
        pid = info["id"]
        projs = [p if p["id"] != pid else info for p in projs]
    else:
        existing_ids = [p["id"] for p in projs] if projs else []
        pid = max(existing_ids) + 1 if existing_ids else 1
        info["id"] = pid
        info["created_at"] = datetime.utcnow().isoformat()
        projs.append(info)
    save_all_projects(projs)
    return pid

def load_project(pid: int) -> dict:
    for p in load_all_projects():
        if p["id"] == pid:
            return p
    return None

def delete_project(pid: int):
    projs = [p for p in load_all_projects() if p["id"] != pid]
    save_all_projects(projs)

def fmt_br(valor: float) -> str:
    s = f"{valor:,.2f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")

# --- 2. DADOS E COEFICIENTES DO NEGÓCIO ---
TIPOS_PAVIMENTO = {
    "Área Privativa (Autônoma)": (1.00, 1.00),
    "Áreas de lazer ambientadas": (2.00, 4.00), # <<< 5. NOVO TIPO ADICIONADO
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

# --- 3. FUNÇÕES AUXILIARES DE UI ---
def render_metric_card(title, value, color="#31708f"):
    """Renderiza um card de métrica com estilo customizado."""
    return f"""
        <div style="background-color:{color}; border-radius:6px; padding:12px; text-align:center;">
            <div style="color:#fff; font-size:14px; margin-bottom:4px;">{title}</div>
            <div style="color:#fff; font-size:24px; font-weight:bold;">{value}</div>
        </div>
    """

# --- 4. TELAS DA APLICAÇÃO ---
def page_project_selection():
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
                "custos_config": {"cub": 4500.0, "outros": 0.0}, # <<< 1. BDI REMOVIDO
                "pavimentos": [DEFAULT_PAVIMENTO]
            }
            pid = save_project(info)
            info["id"] = pid
            st.session_state.projeto_info = info
            st.rerun()

def page_budget_tool():
    info = st.session_state.projeto_info
    if 'pavimentos' not in st.session_state:
        st.session_state.pavimentos = info.get('pavimentos', [DEFAULT_PAVIMENTO.copy()])

    with st.sidebar:
        st.title(f"Projeto: {info['nome']}")
        with st.expander("📝 Editar Dados Gerais", expanded=False):
            with st.form("edit_form"):
                info['nome'] = st.text_input("Nome", value=info['nome'])
                info['area_terreno'] = st.number_input("Área Terreno (m²)", value=info['area_terreno'])
                info['area_privativa'] = st.number_input("Área Privativa (m²)", value=info['area_privativa'])
                info['num_unidades'] = st.number_input("Unidades", value=info['num_unidades'], step=1)
                st.form_submit_button("Atualizar Dados")

        st.markdown("---")
        st.header("💰 Configuração de Custos")
        custos_config = info.get('custos_config', {"cub": 4500.0, "outros": 0.0})
        custos_config['cub'] = st.number_input("Custo Unit. Básico (CUB) R$/m²", min_value=0.0, value=custos_config.get('cub', 4500.0), step=100.0, format="%.2f")
        custos_config['outros'] = st.number_input("Outros Custos Diretos (R$)", min_value=0.0, value=custos_config.get('outros', 0.0), format="%.2f")
        info['custos_config'] = custos_config

        st.markdown("---")
        if st.button("💾 Salvar Todas as Alterações", use_container_width=True, type="primary"):
            info['pavimentos'] = st.session_state.pavimentos
            save_project(info)
            st.success("Projeto salvo com sucesso!")
        if st.button(" Mudar de Projeto", use_container_width=True):
            del st.session_state.projeto_info
            if 'pavimentos' in st.session_state: del st.session_state.pavimentos
            st.rerun()

    st.title("🏗️ Orçamento Paramétrico de Edifícios")
    
    # <<< 2. CARDS DE MÉTRICAS RESTAURADOS
    c1, c2, c3, c4 = st.columns(4)
    cores = ["#31708f", "#3c763d", "#8a6d3b", "#a94442"]
    c1.markdown(render_metric_card("Nome", info["nome"], cores[0]), unsafe_allow_html=True)
    c2.markdown(render_metric_card("Área Terreno", f"{fmt_br(info['area_terreno'])} m²", cores[1]), unsafe_allow_html=True)
    c3.markdown(render_metric_card("Área Privativa", f"{fmt_br(info['area_privativa'])} m²", cores[2]), unsafe_allow_html=True)
    c4.markdown(render_metric_card("Nº Unidades", str(info["num_unidades"]), cores[3]), unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 🏢 Dados dos Pavimentos")
    b1, b2, _ = st.columns([0.2, 0.2, 0.6])
    if b1.button("➕ Adicionar Pavimento"):
        st.session_state.pavimentos.append(DEFAULT_PAVIMENTO.copy())
        st.rerun()
    if b2.button("➖ Remover Último"):
        if st.session_state.pavimentos:
            st.session_state.pavimentos.pop()
            st.rerun()

    col_widths = [3, 3, 1, 1.2, 1.5, 1.5, 1.5, 1.5]
    # <<< 3. CABEÇALHO DA TABELA ATUALIZADO
    headers = ["Nome", "Tipo", "Rep.", "Coef.", "Área (m²)", "Área Eq. Total", "Área Constr.", "Considerar A.C?"]
    header_cols = st.columns(col_widths)
    for hc, title in zip(header_cols, headers):
        hc.markdown(f'**{title}**')

    for i, pav in enumerate(st.session_state.pavimentos):
        c1, c2, c3, c4, c5, c6, c7, c8 = st.columns(col_widths)
        pav['nome'] = c1.text_input("nome", value=pav['nome'], key=f"nome_{i}", label_visibility="collapsed")
        pav['tipo'] = c2.selectbox("tipo", list(TIPOS_PAVIMENTO.keys()), index=list(TIPOS_PAVIMENTO.keys()).index(pav.get('tipo', next(iter(TIPOS_PAVIMENTO)))), key=f"tipo_{i}", label_visibility="collapsed")
        pav['rep'] = c3.number_input("rep", min_value=1, value=pav['rep'], step=1, key=f"rep_{i}", label_visibility="collapsed")
        min_c, max_c = TIPOS_PAVIMENTO[pav['tipo']]
        if min_c == max_c:
            pav['coef'] = min_c
            c4.markdown(f"<div style='text-align:center; padding-top: 8px;'>{pav['coef']:.2f}</div>", unsafe_allow_html=True)
        else:
            pav['coef'] = c4.slider("coef", min_c, max_c, value=float(pav.get('coef', min_c)), step=0.01, format="%.2f", key=f"coef_{i}", label_visibility="collapsed")
        pav['area'] = c5.number_input("area", min_value=0.0, value=pav['area'], step=1.0, format="%.2f", key=f"area_{i}", label_visibility="collapsed")
        pav['constr'] = c8.selectbox("incluir", ["Sim", "Não"], index=0 if pav.get('constr', True) else 1, key=f"constr_{i}", label_visibility="collapsed") == "Sim"
        total_i = pav['area'] * pav['rep']
        area_eq_i = total_i * pav['coef']
        c6.markdown(f"<div style='text-align:center; padding-top: 8px;'>{fmt_br(area_eq_i)}</div>", unsafe_allow_html=True)
        c7.markdown(f"<div style='text-align:center; padding-top: 8px;'>{fmt_br(total_i)}</div>", unsafe_allow_html=True)

    df = pd.DataFrame(st.session_state.pavimentos)
    if not df.empty:
        df["area_total"] = df["area"] * df["rep"]
        df["area_eq"] = df["area_total"] * df["coef"]
        df["area_constr"] = df.apply(lambda row: row["area_total"] if row["constr"] else 0.0, axis=1)
        df["custo_direto"] = df["area_eq"] * custos_config['cub']
        
        custo_direto_total = df["custo_direto"].sum()
        custo_final_projeto = custo_direto_total + custos_config['outros']

        st.markdown("---")
        st.markdown("## 📊 Análise e Resumo Financeiro")
        resumo_col1, chart_col2 = st.columns([0.4, 0.6])
        with resumo_col1:
            st.markdown("#### 🔢 Indicadores Chave")
            total_constr = df["area_constr"].sum()
            priv_area = info["area_privativa"] or 1.0
            custo_por_ac = custo_final_projeto / total_constr if total_constr > 0 else 0.0
            custo_med_unit = custo_final_projeto / info["num_unidades"] if info["num_unidades"] > 0 else 0.0
            
            # <<< 2. CARDS DE MÉTRICAS RESTAURADOS NO RESUMO
            st.markdown(render_metric_card("Custo Final do Projeto", f"R$ {fmt_br(custo_final_projeto)}", cores[3]), unsafe_allow_html=True)
            st.markdown(render_metric_card("Custo Médio / Unidade", f"R$ {fmt_br(custo_med_unit)}", "#337ab7"), unsafe_allow_html=True)
            st.markdown(render_metric_card("Custo / m² (Área Constr.)", f"R$ {fmt_br(custo_por_ac)}", cores[1]), unsafe_allow_html=True)
            st.markdown(render_metric_card("Área Construída Total", f"{fmt_br(total_constr)} m²", cores[2]), unsafe_allow_html=True)
        
        with chart_col2:
            st.markdown("#### 🍰 Composição do Custo Direto")
            custo_por_tipo = df.groupby("tipo")["custo_direto"].sum().reset_index()
            # <<< 4. GRÁFICO DE PIZZA TROCADO POR GRÁFICO DE BARRAS
            fig = px.bar(custo_por_tipo, x='tipo', y='custo_direto', text_auto='.2s', title="Custo Direto por Tipo de Pavimento")
            fig.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
            fig.update_layout(xaxis_title=None, yaxis_title="Custo (R$)")
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        # <<< 6. TÍTULO DA SEÇÃO ATUALIZADO
        st.markdown("### 📑 Detalhamento do Empreendimento")
        
        # <<< 7. CABEÇALHOS DA TABELA ATUALIZADOS
        df_display = df.rename(columns={
            "nome": "Nome", "tipo": "Tipo", "rep": "Rep.", "coef": "Coef.", 
            "area": "Área (m²)", "area_eq": "Área Eq. Total (m²)",
            "area_constr": "Área Constr. (m²)", "custo_direto": "Custo Direto (R$)"
        })
        
        # <<< 6. LÓGICA PARA ADICIONAR LINHA DE TOTAIS
        total_area_eq = df["area_eq"].sum()
        total_area_constr = df["area_constr"].sum()
        total_custo_direto = df["custo_direto"].sum()

        df_display_formatted = df_display.copy()
        for col in ["Área (m²)", "Área Eq. Total (m²)", "Área Constr. (m²)"]:
            df_display_formatted[col] = df_display[col].apply(fmt_br)
        df_display_formatted["Custo Direto (R$)"] = df_display["Custo Direto (R$)"].apply(lambda v: f"R$ {fmt_br(v)}")

        soma_row = pd.DataFrame([{
            "Nome": "<strong>TOTAL</strong>", "Tipo": "", "Rep.": "", "Coef.": "", "Área (m²)": "",
            "Área Eq. Total (m²)": f"<strong>{fmt_br(total_area_eq)}</strong>",
            "Área Constr. (m²)": f"<strong>{fmt_br(total_area_constr)}</strong>",
            "Custo Direto (R$)": f"<strong>R$ {fmt_br(total_custo_direto)}</strong>"
        }])
        
        df_final = pd.concat([df_display_formatted, soma_row], ignore_index=True)
        
        # <<< 7. CENTRALIZAÇÃO DE TODOS OS DADOS
        st.markdown(df_final.to_html(escape=False, index=False, justify="center"), unsafe_allow_html=True)

        st.markdown("---")
        if st.button("🗑️ Excluir Projeto", help="Apaga o projeto atual e retorna à tela inicial"):
            delete_project(info["id"])
            del st.session_state.projeto_info
            if 'pavimentos' in st.session_state: del st.session_state.pavimentos
            st.rerun()

def main():
    st.set_page_config(page_title="Orçamento Paramétrico", layout="wide", initial_sidebar_state="expanded")
    init_storage()
    if "projeto_info" not in st.session_state:
        page_project_selection()
    else:
        page_budget_tool()

if __name__ == "__main__":
    main()
