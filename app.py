import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import plotly.express as px

# --- 1. CONFIGURAÇÃO E GESTÃO DE DADOS ---
JSON_PATH = "projects.json"
HISTORICO_PATH = "historico_obras.json"

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
    "Serviços Preliminares e Fundações":       (7.0, 8.0, 9.0),
    "Estrutura (Supraestrutura)":              (14.0, 16.0, 22.0),
    "Vedações (Alvenaria)":                    (8.0, 10.0, 15.0),
    "Cobertura e Impermeabilização":           (4.0, 5.0, 8.0),
    "Revestimentos de Fachada":                (5.0, 6.0, 10.0),
    "Instalações (Elétrica e Hidráulica)":      (12.0, 15.0, 18.0),
    "Esquadrias (Portas e Janelas)":           (6.0, 8.0, 12.0),
    "Revestimentos de Piso":                   (8.0, 10.0, 15.0),
    "Revestimentos de Parede":                 (6.0, 8.0, 12.0),
    "Revestimentos de Forro":                  (3.0, 4.0, 6.0),
    "Pintura":                                 (4.0, 5.0, 8.0),
    "Serviços Complementares e Externos":      (3.0, 5.0, 10.0)
}

DEFAULT_CUSTOS_INDIRETOS = {
    "IRPJ/CS/PIS/COFINS":       (3.0, 4.8, 6.5), "Corretagem":                      (3.0, 3.6, 5.0),
    "Publicidade":                       (0.5, 0.9, 2.0), "Manutenção":                      (0.3, 0.5, 1.0),
    "Custo Fixo da Construtora / Incorporadora": (3.0, 4.0, 6.0), "Assessoria Técnica":                (0.5, 0.7, 1.5),
    "Projetos":                          (0.4, 0.5, 1.0), "Licenças e Incorporação":         (0.1, 0.2, 0.5),
}

# --- FUNÇÕES AUXILIARES ---
def init_storage(path):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f: json.dump([], f, ensure_ascii=False, indent=4)
def load_json(path):
    init_storage(path); 
    with open(path, "r", encoding="utf-8") as f: return json.load(f)
def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)
def list_projects():
    return [{"id": p["id"], "nome": p["nome"]} for p in load_json(JSON_PATH)]
def save_project(info):
    projs = load_json(JSON_PATH)
    if info.get("id"):
        projs = [p if p["id"] != info["id"] else info for p in projs]
    else:
        pid = (max(p["id"] for p in projs) + 1) if projs else 1
        info["id"] = pid; info["created_at"] = datetime.utcnow().isoformat(); projs.append(info)
    save_json(projs, JSON_PATH)
def load_project(pid):
    project_data = next((p for p in load_json(JSON_PATH) if p["id"] == pid), None)
    if project_data and 'etapas_percentuais' in project_data:
        etapas = project_data['etapas_percentuais']
        if etapas and isinstance(list(etapas.values())[0], (int, float)):
            project_data['etapas_percentuais'] = {k: {"percentual": v, "fonte": "Manual"} for k, v in etapas.items()}
    return project_data
def delete_project(pid):
    projs = [p for p in load_json(JSON_PATH) if p["id"] != pid]; save_json(projs, JSON_PATH)
def fmt_br(valor):
    s = f"{valor:,.2f}"; return s.replace(",", "X").replace(".", ",").replace("X", ".")
def render_metric_card(title, value, color="#31708f"):
    return f"""<div style="background-color:{color}; border-radius:6px; padding:15px; text-align:center; height:100%;"><div style="color:#fff; font-size:16px; margin-bottom:4px;">{title}</div><div style="color:#fff; font-size:28px; font-weight:bold;">{value}</div></div>"""

def handle_percentage_redistribution(session_key, constants_dict):
    previous_key = f"previous_{session_key}"
    if previous_key not in st.session_state: st.session_state[previous_key] = {k: v.copy() for k, v in st.session_state[session_key].items()}
    current, previous = st.session_state[session_key], st.session_state[previous_key]
    if current == previous: return
    
    changed_item_key = next((k for k, v in current.items() if v['percentual'] != previous.get(k, {}).get('percentual')), None)
    if not changed_item_key: return
    
    st.session_state.redistribution_occured = True
    delta = current[changed_item_key]['percentual'] - previous[changed_item_key]['percentual']
    total_others = sum(v['percentual'] for k, v in previous.items() if k != changed_item_key)
    if total_others > 0:
        for item, values in current.items():
            if item != changed_item_key:
                min_val, _, max_val = constants_dict[item]
                proportion = previous[item]['percentual'] / total_others
                new_percent = values['percentual'] - (delta * proportion)
                current[item]['percentual'] = max(min_val, min(new_percent, max_val))
    
    st.session_state[previous_key] = {k: v.copy() for k, v in current.items()}; st.rerun()

def save_to_historico(info):
    historico = load_json(HISTORICO_PATH)
    percentuais = {k: v['percentual'] for k, v in info['etapas_percentuais'].items()}
    nova_entrada = {
        "id": (max(p["id"] for p in historico) + 1) if historico else 1,
        "nome": info["nome"],
        "data": datetime.now().strftime("%Y-%m-%d"),
        "etapas_percentuais": percentuais
    }
    historico.append(nova_entrada)
    save_json(historico, HISTORICO_PATH)
    st.toast(f"'{info['nome']}' arquivado no histórico!", icon="📚")

# --- PÁGINA 1: ORÇAMENTO DIRETO ---
def page_budget_tool():
    st.title("🏗️ Orçamento de Custo Direto")
    info = st.session_state.projeto_info
    if 'pavimentos' not in st.session_state:
        st.session_state.pavimentos = [p.copy() for p in info.get('pavimentos', [DEFAULT_PAVIMENTO.copy()])]
    
    with st.expander("Dados Gerais do Projeto", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        cores = ["#31708f", "#3c763d", "#8a6d3b", "#a94442"]
        c1.markdown(render_metric_card("Nome", info["nome"], cores[0]), unsafe_allow_html=True)
        c2.markdown(render_metric_card("Área Terreno", f"{fmt_br(info['area_terreno'])} m²", cores[1]), unsafe_allow_html=True)
        c3.markdown(render_metric_card("Área Privativa", f"{fmt_br(info['area_privativa'])} m²", cores[2]), unsafe_allow_html=True)
        c4.markdown(render_metric_card("Nº Unidades", str(info["num_unidades"]), cores[3]), unsafe_allow_html=True)

    with st.expander("🏢 Dados dos Pavimentos", expanded=True):
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
            pav['rep'] = cols[2].number_input("rep", min_value=1, value=pav['rep'], step=1, key=f"rep_{i}", label_visibility="collapsed")
            min_c, max_c = TIPOS_PAVIMENTO[pav['tipo']]
            pav['coef'] = min_c if min_c == max_c else cols[3].slider("coef", min_c, max_c, float(pav.get('coef', min_c)), 0.01, format="%.2f", key=f"coef_{i}", label_visibility="collapsed")
            if min_c == max_c: cols[3].markdown(f"<div style='text-align:center; padding-top: 8px;'>{pav['coef']:.2f}</div>", unsafe_allow_html=True)
            pav['area'] = cols[4].number_input("area", min_value=0.0, value=float(pav['area']), step=10.0, format="%.2f", key=f"area_{i}", label_visibility="collapsed")
            pav['constr'] = cols[7].selectbox("incluir", ["Sim", "Não"], 0 if pav.get('constr', True) else 1, key=f"constr_{i}", label_visibility="collapsed") == "Sim"
            total_i, area_eq_i = pav['area'] * pav['rep'], (pav['area'] * pav['rep']) * pav['coef']
            cols[5].markdown(f"<div style='text-align:center; padding-top: 8px;'>{fmt_br(area_eq_i)}</div>", unsafe_allow_html=True)
            cols[6].markdown(f"<div style='text-align:center; padding-top: 8px;'>{fmt_br(total_i)}</div>", unsafe_allow_html=True)

    info['pavimentos'] = st.session_state.pavimentos
    df = pd.DataFrame(info['pavimentos'])
    
    if not df.empty:
        custos_config = info.get('custos_config', {})
        df["area_total"] = df["area"] * df["rep"]
        df["area_eq"] = df["area_total"] * df["coef"]
        df["area_constr"] = df.apply(lambda r: r["area_total"] if r["constr"] else 0.0, axis=1)
        df["custo_direto"] = df["area_eq"] * custos_config.get('custo_area_privativa', 4500.0)
        custo_direto_total = df["custo_direto"].sum()
        
        with st.expander("📊 Análise e Resumo Financeiro", expanded=True):
            total_constr = df["area_constr"].sum()
            custo_por_ac = custo_direto_total / total_constr if total_constr > 0 else 0.0
            custo_med_unit = custo_direto_total / info["num_unidades"] if info["num_unidades"] > 0 else 0.0
            card_cols = st.columns(4)
            card_cols[0].markdown(render_metric_card("Custo Direto do Projeto", f"R$ {fmt_br(custo_direto_total)}", cores[3]), unsafe_allow_html=True)
            card_cols[1].markdown(render_metric_card("Custo Médio / Unidade", f"R$ {fmt_br(custo_med_unit)}", "#337ab7"), unsafe_allow_html=True)
            card_cols[2].markdown(render_metric_card("Custo / m² (Área Constr.)", f"R$ {fmt_br(custo_por_ac)}", cores[1]), unsafe_allow_html=True)
            card_cols[3].markdown(render_metric_card("Área Construída Total", f"{fmt_br(total_constr)} m²", cores[2]), unsafe_allow_html=True)
            
            custo_por_tipo = df.groupby("tipo")["custo_direto"].sum().reset_index()
            fig = px.bar(custo_por_tipo, x='tipo', y='custo_direto', text_auto='.2s', title="Custo Direto por Tipo de Pavimento")
            fig.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False); fig.update_layout(xaxis_title=None, yaxis_title="Custo (R$)")
            st.plotly_chart(fig, use_container_width=True)

        with st.expander("📑 Detalhamento do Empreendimento", expanded=True):
            df_display = df.rename(columns={"nome": "Nome", "tipo": "Tipo", "rep": "Rep.", "coef": "Coef.", "area": "Área (m²)", "area_eq": "Área Eq. Total (m²)", "area_constr": "Área Constr. (m²)", "custo_direto": "Custo Direto (R$)"})
            colunas_a_exibir = ["Nome", "Tipo", "Rep.", "Coef.", "Área (m²)", "Área Eq. Total (m²)", "Área Constr. (m²)", "Custo Direto (R$)"]
            st.dataframe(df_display[colunas_a_exibir], use_container_width=True, hide_index=True,
                column_config={
                    "Área (m²)": st.column_config.NumberColumn(format="%.2f"), "Área Eq. Total (m²)": st.column_config.NumberColumn(format="%.2f"),
                    "Área Constr. (m²)": st.column_config.NumberColumn(format="%.2f"), "Custo Direto (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                })

        with st.expander("💸 Custo Direto por Etapa da Obra", expanded=True):
            if 'etapas_percentuais' not in st.session_state:
                etapas_salvas = info.get('etapas_percentuais', {})
                if etapas_salvas and isinstance(list(etapas_salvas.values())[0], (int, float)):
                    st.session_state.etapas_percentuais = {etapa: {"percentual": val, "fonte": "Manual"} for etapa, val in etapas_salvas.items()}
                else:
                    st.session_state.etapas_percentuais = {etapa: etapas_salvas.get(etapa, {"percentual": vals[1], "fonte": "Manual"}) for etapa, vals in ETAPAS_OBRA.items()}

            if 'previous_etapas_percentuais' not in st.session_state: 
                st.session_state.previous_etapas_percentuais = {k: v.copy() for k, v in st.session_state.etapas_percentuais.items()}
            
            st.markdown("##### Comparativo com Histórico de Obras")
            obras_historicas = load_json(HISTORICO_PATH)
            obra_ref_selecionada = st.selectbox("Usar como Referência:", ["Nenhuma"] + [f"{o['id']} – {o['nome']}" for o in obras_historicas], index=0)
            
            ref_percentuais, ref_nome = {}, None
            if obra_ref_selecionada != "Nenhuma":
                ref_id = int(obra_ref_selecionada.split("–")[0].strip())
                ref_nome = obra_ref_selecionada.split("–")[1].strip()
                obra_ref_data = next((o for o in obras_historicas if o['id'] == ref_id), None)
                if obra_ref_data: ref_percentuais = obra_ref_data['etapas_percentuais']
            
            st.divider()
            cols = st.columns([2, 1.5, 1, 2, 1.5, 1])
            cols[0].markdown("**Etapa**"); cols[1].markdown("**Fonte**"); cols[2].markdown("**Ref. (%)**")
            cols[3].markdown("**Seu Projeto (%)**"); cols[4].markdown("<p style='text-align: center;'>Custo (R$)</p>", unsafe_allow_html=True); cols[5].markdown("<p style='text-align: center;'>Ação</p>", unsafe_allow_html=True)

            for etapa, (min_val, default_val, max_val) in ETAPAS_OBRA.items():
                c = st.columns([2, 1.5, 1, 2, 1.5, 1])
                c[0].container(height=38, border=False).write(etapa)
                etapa_info = st.session_state.etapas_percentuais.get(etapa, {"percentual": default_val, "fonte": "Manual"})
                c[1].container(height=38, border=False).write(etapa_info['fonte'])
                ref_val = ref_percentuais.get(etapa, 0)
                c[2].container(height=38, border=False).write(f"{ref_val:.2f}%" if obra_ref_selecionada != "Nenhuma" else "-")
                current_percent = etapa_info['percentual']
                percent_atual = c[3].slider("slider", min_val, max_val, float(current_percent), 0.5, key=f"slider_etapa_{etapa}", label_visibility="collapsed")
                
                if abs(percent_atual - st.session_state.previous_etapas_percentuais.get(etapa, {}).get('percentual', -1)) > 0.01:
                    st.session_state.etapas_percentuais[etapa]['fonte'] = "Manual"
                st.session_state.etapas_percentuais[etapa]['percentual'] = percent_atual
                
                custo_etapa = custo_direto_total * (percent_atual / 100)
                c[4].markdown(f"<p style='text-align: center;'>R$ {fmt_br(custo_etapa)}</p>", unsafe_allow_html=True)
                
                if c[5].button("⬅️", key=f"apply_{etapa}", help=f"Aplicar percentual de referência ({ref_val:.2f}%)", use_container_width=True):
                    if ref_nome:
                        st.session_state.etapas_percentuais[etapa]['percentual'] = ref_val
                        st.session_state.etapas_percentuais[etapa]['fonte'] = ref_nome
                        handle_percentage_redistribution('etapas_percentuais', ETAPAS_OBRA)
                        st.rerun()

            handle_percentage_redistribution('etapas_percentuais', ETAPAS_OBRA)

# --- PÁGINA 2: ANÁLISE DE VIABILIDADE ---
def page_viability_analysis():
    st.title("📊 Análise de Viabilidade do Empreendimento")
    info = st.session_state.projeto_info
    
    pavimentos_df = pd.DataFrame(info.get('pavimentos', []))
    custos_config = info.get('custos_config', {})
    custo_direto_total, area_construida_total = 0, 0
    if not pavimentos_df.empty:
        custo_area_privativa = custos_config.get('custo_area_privativa', 4500.0)
        pavimentos_df["area_total"] = pavimentos_df["area"] * pavimentos_df["rep"]
        pavimentos_df["area_eq"] = pavimentos_df["area_total"] * pavimentos_df["coef"]
        pavimentos_df["area_constr"] = pavimentos_df.apply(lambda r: r["area_total"] if r["constr"] else 0.0, axis=1)
        pavimentos_df["custo_direto"] = pavimentos_df["area_eq"] * custo_area_privativa
        custo_direto_total = pavimentos_df["custo_direto"].sum()
        area_construida_total = pavimentos_df["area_constr"].sum()

    preco_medio_venda_m2 = custos_config.get('preco_medio_venda_m2', 10000.0)
    vgv_total = info.get('area_privativa', 0) * preco_medio_venda_m2

    st.header("Detalhamento de Custos Totais")
    with st.container(border=True):
        st.metric("Custo Direto Total da Obra", f"R$ {fmt_br(custo_direto_total)}")
        st.divider()
        st.subheader("Custos Indiretos (calculados sobre o VGV)")
        
        if 'custos_indiretos_percentuais' not in st.session_state:
            custos_salvos = info.get('custos_indiretos_percentuais', {})
            st.session_state.custos_indiretos_percentuais = {item: custos_salvos.get(item, vals[1]) for item, vals in DEFAULT_CUSTOS_INDIRETOS.items()}

        custo_indireto_calculado = 0
        for item, (min_val, default_val, max_val) in DEFAULT_CUSTOS_INDIRETOS.items():
            current_percent = st.session_state.custos_indiretos_percentuais.get(item, default_val)
            percent_atual = st.slider(f"{item} (%)", min_value=min_val, max_value=max_val, value=float(current_percent), step=0.1, key=f"indireto_{item}")
            st.session_state.custos_indiretos_percentuais[item] = percent_atual
            custo_indireto_calculado += vgv_total * (percent_atual / 100.0)
        
        st.divider()
        st.metric("Custo Indireto Total (Calculado)", f"R$ {fmt_br(custo_indireto_calculado)}")
        st.divider()
        
        custo_terreno_total = info.get('area_terreno', 0) * custos_config.get('custo_terreno_m2', 2500.0)
        st.metric("Custo Total do Terreno", f"R$ {fmt_br(custo_terreno_total)}")

    valor_total_despesas = custo_direto_total + custo_indireto_calculado + custo_terreno_total
    lucratividade_valor = vgv_total - valor_total_despesas
    lucratividade_percentual = (lucratividade_valor / vgv_total) * 100 if vgv_total > 0 else 0
    st.header("Resultados e Indicadores Chave")
    with st.container(border=True):
        res_cols = st.columns(4)
        res_cols[0].metric("VGV Total", f"R$ {fmt_br(vgv_total)}")
        res_cols[1].metric("Custo Total do Empreendimento", f"R$ {fmt_br(valor_total_despesas)}")
        res_cols[2].metric("Lucro Bruto", f"R$ {fmt_br(lucratividade_valor)}")
        res_cols[3].metric("Margem de Lucro", f"{lucratividade_percentual:.2f}%")
        st.divider()
        st.subheader("Indicadores por Área Construída")
        indicadores_data = {
            'TERRENO % Custo Total': [f"{(custo_terreno_total / valor_total_despesas * 100 if valor_total_despesas > 0 else 0):.2f}%"],
            'CUSTO DIRETO (R$/m²)': [f"R$ {fmt_br(custo_direto_total / area_construida_total if area_construida_total > 0 else 0)}"],
            'CUSTO INDIRETO (R$/m²)': [f"R$ {fmt_br(custo_indireto_calculado / area_construida_total if area_construida_total > 0 else 0)}"],
            'CUSTO TOTAL (R$/m²)': [f"R$ {fmt_br(valor_total_despesas / area_construida_total if area_construida_total > 0 else 0)}"]
        }
        st.table(pd.DataFrame(indicadores_data))

# --- CONTROLE PRINCIPAL DA APLICAÇÃO ---
def main():
    st.set_page_config(page_title="Orçamento Paramétrico", layout="wide")
    init_storage(JSON_PATH); init_storage(HISTORICO_PATH)

    if "projeto_info" not in st.session_state:
        st.header("🏢 Orçamento Paramétrico – Gestão de Projetos")
        st.markdown("Selecione um projeto existente para analisar ou crie um novo para começar.")
        projetos = list_projects()
        escolha = st.selectbox("📂 Selecione ou crie um novo", ["➕ Novo Projeto"] + [f"{p['id']} – {p['nome']}" for p in projetos], label_visibility="collapsed")
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
                    "custos_config": {"custo_terreno_m2": 2500.0, "custo_area_privativa": 4500.0, "preco_medio_venda_m2": 10000.0},
                    "etapas_percentuais": {etapa: {"percentual": vals[1], "fonte": "Manual"} for etapa, vals in ETAPAS_OBRA.items()},
                    "pavimentos": [DEFAULT_PAVIMENTO.copy()],
                    "custos_indiretos_percentuais": {item: vals[1] for item, vals in DEFAULT_CUSTOS_INDIRETOS.items()}
                }
                save_project(info); st.session_state.projeto_info = info; st.rerun()
    else:
        info = st.session_state.projeto_info
        st.sidebar.title(f"Projeto: {info['nome']}")
        st.sidebar.markdown(f"ID: {info['id']}")
        page = st.sidebar.radio("Navegar", ["Orçamento Direto", "Análise de Viabilidade"])
        
        with st.sidebar.expander("📝 Editar Dados Gerais"):
            with st.form("edit_form_sidebar"):
                info['nome'] = st.text_input("Nome", value=info['nome'])
                info['area_terreno'] = st.number_input("Área Terreno (m²)", value=info['area_terreno'], format="%.2f")
                info['area_privativa'] = st.number_input("Área Privativa (m²)", value=info['area_privativa'], format="%.2f")
                info['num_unidades'] = st.number_input("Unidades", value=info['num_unidades'], step=1)
                st.form_submit_button("Atualizar")

        with st.sidebar.expander("📈 Configurações de Mercado"):
             custos_config = info.get('custos_config', {})
             custos_config['preco_medio_venda_m2'] = st.number_input("Preço Médio Venda (R$/m² privativo)", min_value=0.0, value=custos_config.get('preco_medio_venda_m2', 10000.0), format="%.2f")
             info['custos_config'] = custos_config
        
        with st.sidebar.expander("💰 Configuração de Custos"):
            custos_config = info.get('custos_config', {})
            custos_config['custo_terreno_m2'] = st.number_input("Custo do Terreno por m² (R$)", min_value=0.0, value=custos_config.get('custo_terreno_m2', 2500.0), format="%.2f")
            custos_config['custo_area_privativa'] = st.number_input("Custo de Construção (R$/m² privativo)", min_value=0.0, value=custos_config.get('custo_area_privativa', 4500.0), step=100.0, format="%.2f")
            info['custos_config'] = custos_config

        st.sidebar.divider()
        if st.sidebar.button("💾 Salvar Todas as Alterações", use_container_width=True, type="primary"):
            info['etapas_percentuais'] = st.session_state.etapas_percentuais
            info['custos_indiretos_percentuais'] = st.session_state.custos_indiretos_percentuais
            save_project(st.session_state.projeto_info); st.sidebar.success("Projeto salvo com sucesso!")
        
        if st.sidebar.button("📚 Arquivar Custos no Histórico", use_container_width=True):
            # Sincroniza os dados da sessão antes de arquivar
            info['etapas_percentuais'] = st.session_state.etapas_percentuais
            save_to_historico(info)
        
        if st.sidebar.button("Mudar de Projeto", use_container_width=True):
            keys_to_delete = ["projeto_info", "pavimentos", "etapas_percentuais", "previous_etapas_percentuais", "previous_custos_indiretos_percentuais"]
            for key in keys_to_delete:
                if key in st.session_state: del st.session_state[key]
            st.rerun()
        
        if st.session_state.get("redistribution_occured", False):
            st.toast("Percentuais reajustados!", icon="👍")
            del st.session_state.redistribution_occured

        if page == "Orçamento Direto":
            page_budget_tool()
        elif page == "Análise de Viabilidade":
            page_viability_analysis()

if __name__ == "__main__":
    main()
