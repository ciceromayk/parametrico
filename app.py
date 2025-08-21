import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import plotly.express as px

from utils import (
    save_project, delete_project, fmt_br, render_metric_card, 
    handle_percentage_redistribution, TIPOS_PAVIMENTO, DEFAULT_PAVIMENTO, ETAPAS_OBRA
)

st.set_page_config(page_title="Orçamento Direto", layout="wide")

if "projeto_info" not in st.session_state:
    st.error("Nenhum projeto carregado. Por favor, selecione um projeto na página inicial.")
    st.page_link("app.py", label="Voltar para a seleção de projetos")
    st.stop()

def page_budget_tool():
    info = st.session_state.projeto_info
    if 'pavimentos' not in st.session_state:
        st.session_state.pavimentos = [p.copy() for p in info.get('pavimentos', [DEFAULT_PAVIMENTO.copy()])]
    

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
    "Área Privativa (Autônoma)": (1.00, 1.00), "Áreas de lazer ambientadas": (2.00, 4.00), "Varandas": (0.75, 1.00),
    "Terraços / Áreas Descobertas": (0.30, 0.60), "Garagem (Subsolo)": (0.50, 0.75), "Estacionamento (terreno)": (0.05, 0.10),
    "Salas com Acabamento": (1.00, 1.00), "Salas sem Acabamento": (0.75, 0.90), "Loja sem Acabamento": (0.40, 0.60),
    "Serviço (unifam. baixa, aberta)": (0.50, 0.50), "Barrilete / Cx D'água / Casa Máquinas": (0.50, 0.75),
    "Piscinas": (0.50, 0.75), "Quintais / Calçadas / Jardins": (0.10, 0.30), "Projeção Terreno sem Benfeitoria": (0.00, 0.00),
}
DEFAULT_PAVIMENTO = {"nome": "Pavimento Tipo", "tipo": "Área Privativa (Autônoma)", "rep": 1, "coef": 1.00, "area": 100.0, "constr": True}
ETAPAS_OBRA = {
    "Serviços Preliminares e Fundações": 8.0, "Estrutura (Supraestrutura)": 16.0, "Vedações (Alvenaria)": 10.0,
    "Cobertura e Impermeabilização": 5.0, "Revestimentos de Fachada": 6.0, "Instalações (Elétrica e Hidráulica)": 15.0,
    "Esquadrias (Portas e Janelas)": 8.0, "Revestimentos de Piso": 10.0, "Revestimentos de Parede": 8.0,
    "Revestimentos de Forro": 4.0, "Pintura": 5.0, "Serviços Complementares e Externos": 5.0
}

# --- 3. FUNÇÕES AUXILIARES DE UI E LÓGICA ---
def render_metric_card(title, value, color="#31708f"):
    return f"""
        <div style="background-color:{color}; border-radius:6px; padding:15px; text-align:center; height:100%;">
            <div style="color:#fff; font-size:16px; margin-bottom:4px;">{title}</div>
            <div style="color:#fff; font-size:28px; font-weight:bold;">{value}</div>
        </div>
    """

def handle_percentage_redistribution(etapas_key='etapas_percentuais'):
    if 'previous_etapas' not in st.session_state:
        st.session_state.previous_etapas = st.session_state[etapas_key].copy()
    current_percentages = st.session_state[etapas_key]
    previous_percentages = st.session_state.previous_etapas
    if current_percentages == previous_percentages: return
    changed_etapa = None
    for etapa, percent in current_percentages.items():
        if percent != previous_percentages.get(etapa): changed_etapa = etapa; break
    if changed_etapa:
        delta = current_percentages[changed_etapa] - previous_percentages[changed_etapa]
        total_others = sum(v for k, v in previous_percentages.items() if k != changed_etapa)
        if total_others > 0:
            for etapa, percent in current_percentages.items():
                if etapa != changed_etapa:
                    proportion = previous_percentages[etapa] / total_others
                    new_percent = percent - (delta * proportion)
                    current_percentages[etapa] = max(0, new_percent)
        total_sum = sum(current_percentages.values())
        if total_sum > 0:
            factor = 100 / total_sum
            for etapa in current_percentages: current_percentages[etapa] *= factor
    st.session_state.previous_etapas = current_percentages.copy()
    st.rerun()

# --- 4. TELAS DA APLICAÇÃO ---
def page_project_selection():
    st.header("🏢 Orçamento Paramétrico – Gestão de Projetos")
    projetos = list_projects()
    escolha = st.selectbox("📂 Selecione ou crie um projeto", ["➕ Novo Projeto"] + [f"{p['id']} – {p['nome']}" for p in projetos])
    if escolha != "➕ Novo Projeto":
        pid = int(escolha.split("–")[0].strip())
        if st.button("Carregar Projeto", use_container_width=True, type="primary"):
            st.session_state.projeto_info = load_project(pid); st.rerun()
    st.markdown("---")
    st.subheader("Criar Novo Projeto")
    with st.form("new_project_form"):
        nome = st.text_input("Nome do Projeto")
        c1, c2, c3 = st.columns(3)
        area_terreno = c1.number_input("Área Terreno (m²)", min_value=0.0, format="%.2f")
        area_privativa = c2.number_input("Área Privativa Total (m²)", min_value=0.0, format="%.2f")
        num_unidades = c3.number_input("Nº de Unidades", min_value=1, step=1)
        if st.form_submit_button("💾 Criar e Carregar Projeto", use_container_width=True):
            if not nome: st.error("O nome do projeto é obrigatório."); return
            info = {
                "nome": nome, "area_terreno": area_terreno, "area_privativa": area_privativa, "num_unidades": num_unidades, "endereco": "",
                "custos_config": {"cub": 4500.0, "outros": 0.0, "custo_contencao_m2": 400.0},
                "etapas_percentuais": ETAPAS_OBRA, "pavimentos": [DEFAULT_PAVIMENTO]
            }
            pid = save_project(info); info["id"] = pid
            st.session_state.projeto_info = info; st.rerun()

def page_budget_tool():
    info = st.session_state.projeto_info
    if 'pavimentos' not in st.session_state:
        st.session_state.pavimentos = info.get('pavimentos', [DEFAULT_PAVIMENTO.copy()])

    with st.sidebar:
        st.title(f"Projeto: {info['nome']}")
        with st.expander("📝 Editar Dados Gerais"):
            with st.form("edit_form"):
                info['nome'] = st.text_input("Nome", value=info['nome'])
                info['area_terreno'] = st.number_input("Área Terreno (m²)", value=info['area_terreno'])
                info['area_privativa'] = st.number_input("Área Privativa (m²)", value=info['area_privativa'])
                info['num_unidades'] = st.number_input("Unidades", value=info['num_unidades'], step=1)
                st.form_submit_button("Atualizar Dados")

        st.markdown("---")
        st.header("💰 Configuração de Custos")
        custos_config = info.get('custos_config', {"cub": 4500.0, "outros": 0.0, "custo_contencao_m2": 400.0})
        # <<< 2. REINTRODUZIDO: Inputs para CUB e Custo de Contenção
        custos_config['cub'] = st.number_input("CUB (R$/m²)", min_value=0.0, value=custos_config.get('cub', 4500.0), step=100.0, format="%.2f")
        custos_config['outros'] = st.number_input("Outros Custos Diretos (R$)", min_value=0.0, value=custos_config.get('outros', 0.0), format="%.2f")
        custos_config['custo_contencao_m2'] = st.number_input("Custo Contenção (R$/m² subsolo)", min_value=0.0, value=custos_config.get('custo_contencao_m2', 400.0), format="%.2f")
        info['custos_config'] = custos_config

        st.markdown("---")
        if st.button("💾 Salvar Alterações", use_container_width=True, type="primary"):
            info['pavimentos'] = st.session_state.pavimentos
            if 'etapas_percentuais' in st.session_state: info['etapas_percentuais'] = st.session_state.etapas_percentuais
            save_project(info); st.success("Projeto salvo!")
        if st.button(" Mudar de Projeto"):
            del st.session_state.projeto_info
            if 'pavimentos' in st.session_state: del st.session_state.pavimentos
            if 'etapas_percentuais' in st.session_state: del st.session_state.etapas_percentuais
            if 'previous_etapas' in st.session_state: del st.session_state.previous_etapas
            st.rerun()

    st.title("🏗️ Orçamento Paramétrico de Edifícios")
    c1, c2, c3, c4 = st.columns(4)
    cores = ["#31708f", "#3c763d", "#8a6d3b", "#a94442"]
    c1.markdown(render_metric_card("Nome", info["nome"], cores[0]), unsafe_allow_html=True)
    c2.markdown(render_metric_card("Área Terreno", f"{fmt_br(info['area_terreno'])} m²", cores[1]), unsafe_allow_html=True)
    c3.markdown(render_metric_card("Área Privativa", f"{fmt_br(info['area_privativa'])} m²", cores[2]), unsafe_allow_html=True)
    c4.markdown(render_metric_card("Nº Unidades", str(info["num_unidades"]), cores[3]), unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 🏢 Dados dos Pavimentos")
    b1, b2, _ = st.columns([0.2, 0.2, 0.6])
    if b1.button("➕ Adicionar Pavimento"): st.session_state.pavimentos.append(DEFAULT_PAVIMENTO.copy()); st.rerun()
    if b2.button("➖ Remover Último"): 
        if st.session_state.pavimentos: st.session_state.pavimentos.pop(); st.rerun()

    col_widths = [3, 3, 1, 1.2, 1.5, 1.5, 1.5, 1.5]
    headers = ["Nome", "Tipo", "Rep.", "Coef.", "Área (m²)", "Área Eq. Total", "Área Constr.", "Considerar A.C?"]
    header_cols = st.columns(col_widths)
    for hc, title in zip(header_cols, headers): hc.markdown(f'**{title}**')

    for i, pav in enumerate(st.session_state.pavimentos):
        cols = st.columns(col_widths)
        pav['nome'] = cols[0].text_input("nome", pav['nome'], key=f"nome_{i}", label_visibility="collapsed")
        pav['tipo'] = cols[1].selectbox("tipo", list(TIPOS_PAVIMENTO.keys()), list(TIPOS_PAVIMENTO.keys()).index(pav.get('tipo', next(iter(TIPOS_PAVIMENTO)))), key=f"tipo_{i}", label_visibility="collapsed")
        # <<< 1. CORREÇÃO: Usando argumentos nomeados para evitar erros
        pav['rep'] = cols[2].number_input("rep", min_value=1, value=pav['rep'], step=1, key=f"rep_{i}", label_visibility="collapsed")
        min_c, max_c = TIPOS_PAVIMENTO[pav['tipo']]
        pav['coef'] = min_c if min_c == max_c else cols[3].slider("coef", min_c, max_c, float(pav.get('coef', min_c)), 0.01, format="%.2f", key=f"coef_{i}", label_visibility="collapsed")
        if min_c == max_c: cols[3].markdown(f"<div style='text-align:center; padding-top: 8px;'>{pav['coef']:.2f}</div>", unsafe_allow_html=True)
        # <<< 1. CORREÇÃO: Usando argumentos nomeados para evitar erros
        pav['area'] = cols[4].number_input("area", min_value=0.0, value=pav['area'], step=10.0, format="%.2f", key=f"area_{i}", label_visibility="collapsed")
        pav['constr'] = cols[7].selectbox("incluir", ["Sim", "Não"], 0 if pav.get('constr', True) else 1, key=f"constr_{i}", label_visibility="collapsed") == "Sim"
        total_i, area_eq_i = pav['area'] * pav['rep'], (pav['area'] * pav['rep']) * pav['coef']
        cols[5].markdown(f"<div style='text-align:center; padding-top: 8px;'>{fmt_br(area_eq_i)}</div>", unsafe_allow_html=True)
        cols[6].markdown(f"<div style='text-align:center; padding-top: 8px;'>{fmt_br(total_i)}</div>", unsafe_allow_html=True)

    df = pd.DataFrame(st.session_state.pavimentos)
    if not df.empty:
        df["area_total"] = df["area"] * df["rep"]
        df["area_eq"] = df["area_total"] * df["coef"]
        df["area_constr"] = df.apply(lambda r: r["area_total"] if r["constr"] else 0.0, axis=1)
        # <<< 2. REINTRODUZIDO: Usando CUB da configuração
        df["custo_direto"] = df["area_eq"] * custos_config['cub']
        
        area_subsolo = df[df['tipo'].str.contains("Garagem \(Subsolo\)", regex=True)]["area_total"].sum()
        # <<< 2. REINTRODUZIDO: Usando Custo de Contenção da configuração
        custo_contencao = area_subsolo * custos_config['custo_contencao_m2']
        
        custo_direto_total = df["custo_direto"].sum()
        custo_final_projeto = custo_direto_total + custos_config.get('outros', 0.0) + custo_contencao

        st.markdown("---")
        st.markdown("## 📊 Análise e Resumo Financeiro")
        
        total_constr = df["area_constr"].sum()
        custo_por_ac = custo_final_projeto / total_constr if total_constr > 0 else 0.0
        custo_med_unit = custo_final_projeto / info["num_unidades"] if info["num_unidades"] > 0 else 0.0
        
        card_cols = st.columns(4)
        card_cols[0].markdown(render_metric_card("Custo Final do Projeto", f"R$ {fmt_br(custo_final_projeto)}", cores[3]), unsafe_allow_html=True)
        card_cols[1].markdown(render_metric_card("Custo Médio / Unidade", f"R$ {fmt_br(custo_med_unit)}", "#337ab7"), unsafe_allow_html=True)
        card_cols[2].markdown(render_metric_card("Custo / m² (Área Constr.)", f"R$ {fmt_br(custo_por_ac)}", cores[1]), unsafe_allow_html=True)
        card_cols[3].markdown(render_metric_card("Área Construída Total", f"{fmt_br(total_constr)} m²", cores[2]), unsafe_allow_html=True)
        
        custo_por_tipo = df.groupby("tipo")["custo_direto"].sum().reset_index()
        fig = px.bar(custo_por_tipo, x='tipo', y='custo_direto', text_auto='.2s', title="Custo Direto por Tipo de Pavimento")
        fig.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False); fig.update_layout(xaxis_title=None, yaxis_title="Custo (R$)")
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.markdown("### 📑 Detalhamento do Empreendimento")
        df_display = df.rename(columns={"nome": "Nome", "tipo": "Tipo", "rep": "Rep.", "coef": "Coef.", "area": "Área (m²)", "area_eq": "Área Eq. Total (m²)", "area_constr": "Área Constr. (m²)", "custo_direto": "Custo Direto (R$)"})
        colunas_a_exibir = ["Nome", "Tipo", "Rep.", "Coef.", "Área (m²)", "Área Eq. Total (m²)", "Área Constr. (m²)", "Custo Direto (R$)"]
        st.dataframe(df_display[colunas_a_exibir], use_container_width=True)

        st.markdown("---")
        with st.expander("💸 Custo Direto por Etapa da Obra", expanded=True):
            if 'etapas_percentuais' not in st.session_state: st.session_state.etapas_percentuais = info.get('etapas_percentuais', ETAPAS_OBRA).copy()
            if 'previous_etapas' not in st.session_state: st.session_state.previous_etapas = st.session_state.etapas_percentuais.copy()

            col1, col2, col3 = st.columns([2, 2, 1.5]); col1.markdown("**Etapa**"); col2.markdown("**Percentual (%)**"); col3.markdown("**Custo da Etapa (R$)**")
            etapas_data = []
            for etapa, percent_padrao in st.session_state.etapas_percentuais.items():
                col1, col2, col3 = st.columns([2, 2, 1.5])
                col1.container(height=38, border=False).write(etapa)
                percent_atual = col2.slider(etapa, 0.0, 100.0, float(percent_padrao), 0.5, key=f"etapa_{etapa.replace(' ', '_')}", label_visibility="collapsed")
                st.session_state.etapas_percentuais[etapa] = percent_atual
                custo_etapa = custo_direto_total * (percent_atual / 100)
                col3.container(height=38, border=False).write(f"R$ {fmt_br(custo_etapa)}")
                etapas_data.append({"Etapa": etapa, "Percentual (%)": f"{percent_atual:.1f}%", "Custo da Etapa (R$)": custo_etapa})
            
            handle_percentage_redistribution()

            if custo_contencao > 0:
                etapas_data.append({"Etapa": "Contenções de Subsolo", "Percentual (%)": "-", "Custo da Etapa (R$)": custo_contencao})
            
            df_etapas = pd.DataFrame(etapas_data)
            custo_total_etapas = df_etapas["Custo da Etapa (R$)"].sum()
            df_etapas["Custo da Etapa (R$)"] = df_etapas["Custo da Etapa (R$)"].apply(lambda v: f"R$ {fmt_br(v)}")
            total_row = pd.DataFrame([{"Etapa": "<strong>TOTAL</strong>", "Percentual (%)": "<strong>-</strong>", "Custo da Etapa (R$)": f"<strong>R$ {fmt_br(custo_total_etapas)}</strong>"}])
            df_final_etapas = pd.concat([df_etapas, total_row], ignore_index=True)
            st.markdown(df_final_etapas.to_html(escape=False, index=False, justify="right", header=False), unsafe_allow_html=True)
            
        st.markdown("---")
        if st.button("🗑️ Excluir Projeto"):
            delete_project(info["id"]); del st.session_state.projeto_info
            if 'pavimentos' in st.session_state: del st.session_state.pavimentos
            if 'etapas_percentuais' in st.session_state: del st.session_state.etapas_percentuais
            if 'previous_etapas' in st.session_state: del st.session_state.previous_etapas
            st.rerun()

def main():
    st.set_page_config(page_title="Orçamento Paramétrico", layout="wide", initial_sidebar_state="expanded")
    init_storage()
    if "projeto_info" not in st.session_state: page_project_selection()
    else: page_budget_tool()

if __name__ == "__main__":
    main()
