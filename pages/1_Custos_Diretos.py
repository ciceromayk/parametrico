# pages/1_Custos_Diretos.py
import streamlit as st
import pandas as pd
import plotly.express as px
from utils import *

st.set_page_config(page_title="Custos Diretos", layout="wide")

if "projeto_info" not in st.session_state:
    st.error("Nenhum projeto carregado. Por favor, selecione um projeto na página inicial.")
    if st.button("Voltar para a seleção de projetos"):
        st.switch_page("app.py")
    st.stop()

render_sidebar()

info = st.session_state.projeto_info
# <<< 2. TÍTULO DA PÁGINA ATUALIZADO
st.title("🏗️ Custos Diretos")

if 'pavimentos' not in st.session_state:
    st.session_state.pavimentos = [p.copy() for p in info.get('pavimentos', [DEFAULT_PAVIMENTO.copy()])]

# <<< 3. ÍCONE ADICIONADO
with st.expander("📝 Dados Gerais do Projeto", expanded=True):
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
        obras_historicas = load_json(HISTORICO_DIRETO_PATH)
        obra_ref_selecionada = st.selectbox("Usar como Referência:", ["Nenhuma"] + [f"{o['id']} – {o['nome']}" for o in obras_historicas], index=0, key="ref_direto")
        
        ref_percentuais, ref_nome = {}, None
        if obra_ref_selecionada != "Nenhuma":
            ref_id = int(obra_ref_selecionada.split("–")[0].strip())
            ref_nome = obra_ref_selecionada.split("–")[1].strip()
            obra_ref_data = next((o for o in obras_historicas if o['id'] == ref_id), None)
            if obra_ref_data: ref_percentuais = obra_ref_data['percentuais']
        
        st.divider()
        cols = st.columns([2.5, 1.5, 1, 1.5, 1, 1.5, 1])
        cols[0].markdown("**Etapa**"); cols[1].markdown("**Fonte**"); cols[2].markdown("**Ref. (%)**")
        cols[3].markdown("**Seu Projeto (%)**"); cols[5].markdown("<p style='text-align: center;'>Custo (R$)</p>", unsafe_allow_html=True); cols[6].markdown("<p style='text-align: center;'>Ação</p>", unsafe_allow_html=True)

        for etapa, (min_val, default_val, max_val) in ETAPAS_OBRA.items():
            c = st.columns([2.5, 1.5, 1, 1.5, 1, 1.5, 1])
            c[0].container(height=38, border=False).write(etapa)
            etapa_info = st.session_state.etapas_percentuais.get(etapa, {"percentual": default_val, "fonte": "Manual"})
            c[1].container(height=38, border=False).write(etapa_info['fonte'])
            ref_val = ref_percentuais.get(etapa, 0)
            c[2].container(height=38, border=False).write(f"{ref_val:.2f}%" if obra_ref_selecionada != "Nenhuma" else "-")
            
            slider_col, input_col = c[3], c[4]
            current_percent = etapa_info['percentual']
            
            percent_slider = slider_col.slider("slider", min_val, max_val, float(current_percent), 0.1, key=f"slider_etapa_{etapa}", label_visibility="collapsed")
            percent_input = input_col.number_input("input", min_val, max_val, percent_slider, 0.1, key=f"input_etapa_{etapa}", label_visibility="collapsed")

            if percent_input != current_percent:
                st.session_state.etapas_percentuais[etapa]['percentual'] = percent_input
                st.session_state.etapas_percentuais[etapa]['fonte'] = "Manual"
                handle_percentage_redistribution('etapas_percentuais', ETAPAS_OBRA)
                st.rerun()

            custo_etapa = custo_direto_total * (percent_input / 100)
            c[5].markdown(f"<p style='text-align: center;'>R$ {fmt_br(custo_etapa)}</p>", unsafe_allow_html=True)
            
            if c[6].button("⬅️", key=f"apply_{etapa}", help=f"Aplicar percentual de referência ({ref_val:.2f}%)", use_container_width=True):
                if ref_nome:
                    st.session_state.etapas_percentuais[etapa]['percentual'] = ref_val
                    st.session_state.etapas_percentuais[etapa]['fonte'] = ref_nome
                    handle_percentage_redistribution('etapas_percentuais', ETAPAS_OBRA)
                    st.rerun()
