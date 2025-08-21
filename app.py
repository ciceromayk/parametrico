import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import plotly.express as px

# --- 1. CONFIGURAÇÃO E GESTÃO DE DADOS ---
JSON_PATH = "projects.json"

# --- DADOS E COEFICIENTES DO NEGÓCIO ---
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
DEFAULT_CUSTOS_INDIRETOS = {
    "IRPJ/CS/PIS/COFINS (sobre VGV)": 4.8, "Corretagem (sobre VGV)": 3.61, "Publicidade (sobre VGV)": 0.9,
    "Manutenção (sobre VGV)": 0.5, "Custo Fixo da Construtora / Incorporadora (sobre VGV)": 4.0, "Assessoria Técnica (sobre VGV)": 0.7,
    "Projetos (sobre VGV)": 0.52, "Licenças e Incorporação (sobre VGV)": 0.2, "Outorga Onerosa (sobre VGV)": 0.0,
    "Condomínio (sobre o VGV)": 0.0, "IPTU (sobre o VGV)": 0.07, "Preparação do Terreno (sobre o VGV)": 0.33,
    "Financiamento Bancário (R$)": 0.0, "Juros Financiamento (R$)": 0.0
}

# --- FUNÇÕES AUXILIARES ---
def init_storage():
    if not os.path.exists(JSON_PATH):
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=4)
def load_all_projects():
    init_storage()
    with open(JSON_PATH, "r", encoding="utf-8") as f: return json.load(f)
def save_all_projects(projs):
    with open(JSON_PATH, "w", encoding="utf-8") as f: json.dump(projs, f, ensure_ascii=False, indent=4)
def list_projects():
    return [{"id": p["id"], "nome": p["nome"]} for p in load_all_projects()]
def save_project(info):
    projs = load_all_projects()
    if info.get("id"):
        projs = [p if p["id"] != info["id"] else info for p in projs]
    else:
        pid = (max(p["id"] for p in projs) + 1) if projs else 1
        info["id"] = pid
        info["created_at"] = datetime.utcnow().isoformat()
        projs.append(info)
    save_all_projects(projs)
def load_project(pid):
    return next((p for p in load_all_projects() if p["id"] == pid), None)
def delete_project(pid):
    projs = [p for p in load_all_projects() if p["id"] != pid]
    save_all_projects(projs)
def fmt_br(valor):
    s = f"{valor:,.2f}"; return s.replace(",", "X").replace(".", ",").replace("X", ".")
def render_metric_card(title, value, color="#31708f"):
    return f"""<div style="background-color:{color}; border-radius:6px; padding:15px; text-align:center; height:100%;"><div style="color:#fff; font-size:16px; margin-bottom:4px;">{title}</div><div style="color:#fff; font-size:28px; font-weight:bold;">{value}</div></div>"""
def handle_percentage_redistribution(etapas_key='etapas_percentuais'):
    if 'previous_etapas' not in st.session_state: st.session_state.previous_etapas = st.session_state[etapas_key].copy()
    current, previous = st.session_state[etapas_key], st.session_state.previous_etapas
    if current == previous: return
    changed_etapa = next((e for e, p in current.items() if p != previous.get(e)), None)
    if changed_etapa:
        delta = current[changed_etapa] - previous[changed_etapa]
        total_others = sum(v for k, v in previous.items() if k != changed_etapa)
        if total_others > 0:
            for e, p in current.items():
                if e != changed_etapa: current[e] = max(0, p - (delta * (previous[e] / total_others)))
        total_sum = sum(current.values())
        if total_sum > 0: factor = 100 / total_sum
        else: factor = 0
        for e in current: current[e] *= factor
    st.session_state.previous_etapas = current.copy(); st.rerun()


# --- PÁGINA 1: ORÇAMENTO DIRETO ---
def page_budget_tool():
    st.title("🏗️ Orçamento Paramétrico de Edifícios")
    info = st.session_state.projeto_info
    
    # Inicializa o estado da sessão para os pavimentos se não existir
    if 'pavimentos' not in st.session_state:
        st.session_state.pavimentos = [p.copy() for p in info.get('pavimentos', [DEFAULT_PAVIMENTO.copy()])]
    
    # CARDS SUPERIORES
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

    # INPUTS DOS PAVIMENTOS
    col_widths = [3, 3, 1, 1.2, 1.5, 1.5, 1.5, 1.5]
    headers = ["Nome", "Tipo", "Rep.", "Coef.", "Área (m²)", "Área Eq. Total", "Área Constr.", "Considerar A.C?"]
    header_cols = st.columns(col_widths)
    for hc, title in zip(header_cols, headers): hc.markdown(f'**{title}**')

    for i, pav in enumerate(st.session_state.pavimentos):
        cols = st.columns(col_widths)
        pav['nome'] = cols[0].text_input("nome", pav['nome'], key=f"nome_{i}", label_visibility="collapsed")
        pav['tipo'] = cols[1].selectbox("tipo", list(TIPOS_PAVIMENTO.keys()), list(TIPOS_PAVIMENTO.keys()).index(pav.get('tipo', next(iter(TIPOS_PAVIMENTO)))), key=f"tipo_{i}", label_visibility="collapsed")
        pav['rep'] = cols[2].number_input("rep", min_value=1, value=pav['rep'], step=1, key=f"rep_{i}", label_visibility="collapsed")
        min_c, max_c = TIPOS_PAVIMENTO[pav['tipo']]
        pav['coef'] = min_c if min_c == max_c else cols[3].slider("coef", min_c, max_c, float(pav.get('coef', min_c)), 0.01, format="%.2f", key=f"coef_{i}", label_visibility="collapsed")
        if min_c == max_c: cols[3].markdown(f"<div style='text-align:center; padding-top: 8px;'>{pav['coef']:.2f}</div>", unsafe_allow_html=True)
        pav['area'] = cols[4].number_input("area", min_value=0.0, value=float(pav['area']), step=10.0, format="%.2f", key=f"area_{i}", label_visibility="collapsed")
        pav['constr'] = cols[7].selectbox("incluir", ["Sim", "Não"], 0 if pav.get('constr', True) else 1, key=f"constr_{i}", label_visibility="collapsed") == "Sim"
        total_i, area_eq_i = pav['area'] * pav['rep'], (pav['area'] * pav['rep']) * pav['coef']
        cols[5].markdown(f"<div style='text-align:center; padding-top: 8px;'>{fmt_br(area_eq_i)}</div>", unsafe_allow_html=True)
        cols[6].markdown(f"<div style='text-align:center; padding-top: 8px;'>{fmt_br(total_i)}</div>", unsafe_allow_html=True)

    info['pavimentos'] = st.session_state.pavimentos # Atualiza info com os dados da tela

    # CÁLCULOS E RESULTADOS
    df = pd.DataFrame(info['pavimentos'])
    if not df.empty:
        custos_config = info.get('custos_config', {})
        df["area_total"] = df["area"] * df["rep"]
        df["area_eq"] = df["area_total"] * df["coef"]
        df["area_constr"] = df.apply(lambda r: r["area_total"] if r["constr"] else 0.0, axis=1)
        df["custo_direto"] = df["area_eq"] * custos_config.get('cub', 4500.0)
        area_subsolo = df[df['tipo'].str.contains("Garagem \(Subsolo\)", regex=True)]["area_total"].sum()
        custo_contencao = area_subsolo * custos_config.get('custo_contencao_m2', 400.0)
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

# --- PÁGINA 2: ANÁLISE DE VIABILIDADE ---
def page_viability_analysis():
    st.title("📊 Análise de Viabilidade do Empreendimento")
    info = st.session_state.projeto_info
    
    # Cálculos Puxados do Orçamento Direto
    pavimentos_df = pd.DataFrame(info.get('pavimentos', []))
    custos_config = info.get('custos_config', {})
    custo_direto_total, area_construida_total = 0, 0
    if not pavimentos_df.empty:
        cub, custo_contencao_m2 = custos_config.get('cub', 4500.0), custos_config.get('custo_contencao_m2', 400.0)
        pavimentos_df["area_total"] = pavimentos_df["area"] * pavimentos_df["rep"]
        pavimentos_df["area_eq"] = pavimentos_df["area_total"] * pavimentos_df["coef"]
        pavimentos_df["area_constr"] = pavimentos_df.apply(lambda r: r["area_total"] if r["constr"] else 0.0, axis=1)
        pavimentos_df["custo_direto"] = pavimentos_df["area_eq"] * cub
        custo_direto_obra = pavimentos_df["custo_direto"].sum()
        area_subsolo = pavimentos_df[pavimentos_df['tipo'].str.contains("Garagem \(Subsolo\)", regex=True)]["area_total"].sum()
        custo_contencao = area_subsolo * custo_contencao_m2
        custo_direto_total = custo_direto_obra + custos_config.get('outros', 0.0) + custo_contencao
        area_construida_total = pavimentos_df["area_constr"].sum()

    st.header("Receitas / VGV"); 
    with st.container(border=True):
        st.subheader("Composição de Unidades e VGV")
        if 'unidades_vgv' not in info: info['unidades_vgv'] = []
        edited_unidades = st.data_editor(
            pd.DataFrame(info['unidades_vgv']), num_rows="dynamic", use_container_width=True, key="editor_unidades",
            column_config={
                "Tipo": st.column_config.TextColumn(required=True), "Quant.": st.column_config.NumberColumn(required=True, min_value=1, step=1),
                "Área Privativa (m²)": st.column_config.NumberColumn(required=True, format="%.2f m²"),
                "Valor Médio de Venda (R$)": st.column_config.NumberColumn(required=True, format="R$ %.2f"),
            })
        info['unidades_vgv'] = edited_unidades.to_dict('records')
        unidades_df = pd.DataFrame(info['unidades_vgv'])
        vgv_total = (unidades_df['Quant.'] * unidades_df['Valor Médio de Venda (R$)']).sum() if not unidades_df.empty else 0
        st.metric("VGV (Valor Geral de Vendas) Total", f"R$ {fmt_br(vgv_total)}")

    st.header("Detalhamento de Custos Totais"); 
    with st.container(border=True):
        st.metric("Custo Direto Total (Obra + Contenção + Outros)", f"R$ {fmt_br(custo_direto_total)}")
        st.divider()
        st.subheader("Custos Indiretos")
        if 'custos_indiretos' not in info: info['custos_indiretos'] = DEFAULT_CUSTOS_INDIRETOS.copy()
        custos_indiretos = info['custos_indiretos']
        cols, i, custo_indireto_calculado = st.columns(3), 0, 0
        for key, value in custos_indiretos.items():
            with cols[i % 3]:
                label, base = (key.split('(')[0].strip(), key.split('(')[1].split(')')[0]) if '(' in key else (key, None)
                if base and "VGV" in base:
                    percent = st.number_input(f"{label} (%)", value=float(value), format="%.2f", key=key)
                    custos_indiretos[key] = percent; custo_indireto_calculado += vgv_total * (percent / 100.0)
                else:
                    valor_fixo = st.number_input(label, value=float(value), format="%.2f", key=key)
                    custos_indiretos[key] = valor_fixo; custo_indireto_calculado += valor_fixo
            i += 1
        st.metric("Custo Indireto Total (Calculado)", f"R$ {fmt_br(custo_indireto_calculado)}")
        st.divider()
        st.subheader("Custo do Terreno")
        custos_config['custo_terreno_m2'] = st.number_input("Custo do Terreno por m² (R$)", value=custos_config.get('custo_terreno_m2', 2500.0), format="%.2f")
        custo_terreno_total = info.get('area_terreno', 0) * custos_config['custo_terreno_m2']
        st.metric("Custo Total do Terreno", f"R$ {fmt_br(custo_terreno_total)}")
        info['custos_config'] = custos_config

    valor_total_despesas = custo_direto_total + custo_indireto_calculado + custo_terreno_total
    lucratividade_valor = vgv_total - valor_total_despesas
    lucratividade_percentual = (lucratividade_valor / vgv_total) * 100 if vgv_total > 0 else 0
    st.header("Resultados e Indicadores Chave"); 
    with st.container(border=True):
        res_cols = st.columns(4)
        res_cols[0].metric("VGV Total", f"R$ {fmt_br(vgv_total)}")
        res_cols[1].metric("Custo Total do Empreendimento", f"R$ {fmt_br(valor_total_despesas)}")
        res_cols[2].metric("Lucro Bruto", f"R$ {fmt_br(lucratividade_valor)}")
        res_cols[3].metric("Margem de Lucro", f"{lucratividade_percentual:.2f}%")
        st.divider()
        st.subheader("Indicadores por Área Construída")
        indicadores_data = {
            'TERRENO %': [f"{(custo_terreno_total / valor_total_despesas * 100 if valor_total_despesas > 0 else 0):.2f}%"],
            'CUSTO DIRETO (R$/m²)': [f"R$ {fmt_br(custo_direto_total / area_construida_total if area_construida_total > 0 else 0)}"],
            'CUSTO INDIRETO (R$/m²)': [f"R$ {fmt_br(custo_indireto_calculado / area_construida_total if area_construida_total > 0 else 0)}"],
            'CUSTO TOTAL (R$/m²)': [f"R$ {fmt_br(valor_total_despesas / area_construida_total if area_construida_total > 0 else 0)}"]
        }
        st.table(pd.DataFrame(indicadores_data))

# --- CONTROLE PRINCIPAL DA APLICAÇÃO ---
def main():
    st.set_page_config(page_title="Orçamento Paramétrico", layout="wide")
    init_storage()

    if "projeto_info" not in st.session_state:
        # TELA DE SELEÇÃO DE PROJETO
        st.header("🏢 Orçamento Paramétrico – Gestão de Projetos")
        st.markdown("Selecione um projeto existente para analisar ou crie um novo para começar.")
        projetos = list_projects()
        escolha = st.selectbox("📂 Selecione um projeto ou crie um novo", ["➕ Novo Projeto"] + [f"{p['id']} – {p['nome']}" for p in projetos], label_visibility="collapsed")
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
                    "custos_config": {"cub": 4500.0, "outros": 0.0, "custo_contencao_m2": 400.0, "custo_terreno_m2": 2500.0},
                    "etapas_percentuais": ETAPAS_OBRA.copy(), "pavimentos": [DEFAULT_PAVIMENTO.copy()],
                    "unidades_vgv": [{"Tipo": "Padrão", "Quant.": num_unidades, "Área Privativa (m²)": (area_privativa / num_unidades if num_unidades > 0 else 0), "Valor Médio de Venda (R$)": 500000.0}],
                    "custos_indiretos": DEFAULT_CUSTOS_INDIRETOS.copy()
                }
                save_project(info); st.session_state.projeto_info = info; st.rerun()
    else:
        info = st.session_state.projeto_info
        st.sidebar.title(f"Projeto: {info['nome']}")
        st.sidebar.markdown(f"ID: {info['id']}")
        page = st.sidebar.radio("Navegar", ["Orçamento Direto", "Análise de Viabilidade"])
        st.sidebar.divider()
        if st.sidebar.button("💾 Salvar Todas as Alterações", use_container_width=True, type="primary"):
            save_project(st.session_state.projeto_info); st.sidebar.success("Projeto salvo com sucesso!")
        if st.sidebar.button("Mudar de Projeto", use_container_width=True):
            keys_to_delete = ["projeto_info", "pavimentos", "etapas_percentuais", "previous_etapas"]
            for key in keys_to_delete:
                if key in st.session_state: del st.session_state[key]
            st.rerun()

        if page == "Orçamento Direto":
            page_budget_tool()
        elif page == "Análise de Viabilidade":
            page_viability_analysis()

if __name__ == "__main__":
    main()
