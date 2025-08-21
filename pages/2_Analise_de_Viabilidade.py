# pages/2_Analise_de_Viabilidade.py
import streamlit as st
import pandas as pd
from utils import *

st.set_page_config(page_title="Análise de Viabilidade", layout="wide")

if "projeto_info" not in st.session_state:
    st.error("Nenhum projeto carregado. Por favor, selecione um projeto na página inicial.")
    if st.button("Voltar para a seleção de projetos"):
        st.switch_page("app.py")
    st.stop()

# Renderiza a barra lateral comum a todas as páginas
render_sidebar()

# Conteúdo específico da página
info = st.session_state.projeto_info
st.title("📊 Análise de Viabilidade do Empreendimento")

# Cálculos Puxados do Orçamento Direto
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

with st.expander("Detalhamento de Custos Totais", expanded=True):
    st.metric("Custo Direto Total da Obra", f"R$ {fmt_br(custo_direto_total)}")
    st.divider()
    st.subheader("Custos Indiretos (calculados sobre o VGV)")

    if 'custos_indiretos_percentuais' not in st.session_state:
        custos_salvos = info.get('custos_indiretos_percentuais', {})
        st.session_state.custos_indiretos_percentuais = {item: {"percentual": custos_salvos.get(item, vals[1]), "fonte": "Manual"} for item, vals in DEFAULT_CUSTOS_INDIRETOS.items()}

    if 'previous_custos_indiretos_percentuais' not in st.session_state: 
        st.session_state.previous_custos_indiretos_percentuais = {k: v.copy() for k, v in st.session_state.custos_indiretos_percentuais.items()}

    obras_historicas = load_json(HISTORICO_INDIRETO_PATH)
    obra_ref_selecionada = st.selectbox("Usar como Referência (Custos Indiretos):", ["Nenhuma"] + [f"{o['id']} – {o['nome']}" for o in obras_historicas], index=0, key="ref_indireto")
    
    ref_percentuais, ref_nome = {}, None
    if obra_ref_selecionada != "Nenhuma":
        ref_id = int(obra_ref_selecionada.split("–")[0].strip())
        ref_nome = obra_ref_selecionada.split("–")[1].strip()
        obra_ref_data = next((o for o in obras_historicas if o['id'] == ref_id), None)
        if obra_ref_data: ref_percentuais = obra_ref_data['percentuais']
    
    st.divider()
    cols = st.columns([2, 1.5, 1, 2, 1.5, 1])
    cols[0].markdown("**Item**"); cols[1].markdown("**Fonte**"); cols[2].markdown("**Ref. (%)**")
    cols[3].markdown("**Seu Projeto (%)**"); cols[4].markdown("<p style='text-align: center;'>Custo (R$)</p>", unsafe_allow_html=True); cols[5].markdown("<p style='text-align: center;'>Ação</p>", unsafe_allow_html=True)

    custo_indireto_calculado = 0
    for item, (min_val, default_val, max_val) in DEFAULT_CUSTOS_INDIRETOS.items():
        c = st.columns([2, 1.5, 1, 2, 1.5, 1])
        c[0].container(height=38, border=False).write(item)
        item_info = st.session_state.custos_indiretos_percentuais.get(item, {"percentual": default_val, "fonte": "Manual"})
        c[1].container(height=38, border=False).write(item_info['fonte'])
        ref_val = ref_percentuais.get(item, 0)
        c[2].container(height=38, border=False).write(f"{ref_val:.2f}%" if obra_ref_selecionada != "Nenhuma" else "-")
        current_percent = item_info['percentual']
        percent_atual = c[3].slider("slider", min_val, max_val, float(current_percent), 0.1, key=f"slider_indireto_{item}", label_visibility="collapsed")
        
        if abs(percent_atual - st.session_state.previous_custos_indiretos_percentuais.get(item, {}).get('percentual', -1)) > 0.01:
            st.session_state.custos_indiretos_percentuais[item]['fonte'] = "Manual"
        st.session_state.custos_indiretos_percentuais[item]['percentual'] = percent_atual

        custo_item = vgv_total * (percent_atual / 100)
        c[4].markdown(f"<p style='text-align: center;'>R$ {fmt_br(custo_item)}</p>", unsafe_allow_html=True)
        custo_indireto_calculado += custo_item

        if c[5].button("⬅️", key=f"apply_indireto_{item}", help=f"Aplicar percentual de referência ({ref_val:.2f}%)", use_container_width=True):
                if ref_nome:
                    st.session_state.custos_indiretos_percentuais[item]['percentual'] = ref_val
                    st.session_state.custos_indiretos_percentuais[item]['fonte'] = ref_nome
                    st.rerun()
    
    if 'custos_indiretos_fixos' not in info: info['custos_indiretos_fixos'] = DEFAULT_CUSTOS_INDIRETOS_FIXOS.copy()
    custos_indiretos_fixos = info['custos_indiretos_fixos']
    for item, valor in custos_indiretos_fixos.items():
        custos_indiretos_fixos[item] = st.number_input(item, value=float(valor), format="%.2f")
        custo_indireto_calculado += custos_indiretos_fixos[item]
    
    st.divider()
    st.metric("Custo Indireto Total (Calculado)", f"R$ {fmt_br(custo_indireto_calculado)}")
    st.divider()
    
    custo_terreno_total = info.get('area_terreno', 0) * custos_config.get('custo_terreno_m2', 2500.0)
    st.metric("Custo Total do Terreno", f"R$ {fmt_br(custo_terreno_total)}")

valor_total_despesas = custo_direto_total + custo_indireto_calculado + custo_terreno_total
lucratividade_valor = vgv_total - valor_total_despesas
lucratividade_percentual = (lucratividade_valor / vgv_total) * 100 if vgv_total > 0 else 0

with st.expander("Resultados e Indicadores Chave", expanded=True):
    cores = ["#00829d", "#6a42c1", "#3c763d", "#a94442", "#fd7e14", "#20c997", "#31708f", "#8a6d3b" ]
    st.subheader("Resultados Financeiros")
    res_cols = st.columns(4)
    res_cols[0].markdown(render_metric_card("VGV Total", f"R$ {fmt_br(vgv_total)}", cores[0]), unsafe_allow_html=True)
    res_cols[1].markdown(render_metric_card("Custo Total", f"R$ {fmt_br(valor_total_despesas)}", cores[1]), unsafe_allow_html=True)
    res_cols[2].markdown(render_metric_card("Lucro Bruto", f"R$ {fmt_br(lucratividade_valor)}", cores[2]), unsafe_allow_html=True)
    res_cols[3].markdown(render_metric_card("Margem de Lucro", f"{lucratividade_percentual:.2f}%", cores[3]), unsafe_allow_html=True)
    
    st.divider()
    st.subheader("Indicadores por Área")
    ind_cols = st.columns(4)
    ind_cols[0].markdown(render_metric_card("Terreno / Custo Total", f"{(custo_terreno_total / valor_total_despesas * 100 if valor_total_despesas > 0 else 0):.2f}%", cores[4]), unsafe_allow_html=True)
    ind_cols[1].markdown(render_metric_card("Custo Direto / m² constr.", f"R$ {fmt_br(custo_direto_total / area_construida_total if area_construida_total > 0 else 0)}", cores[5]), unsafe_allow_html=True)
    ind_cols[2].markdown(render_metric_card("Custo Indireto / m² constr.", f"R$ {fmt_br(custo_indireto_calculado / area_construida_total if area_construida_total > 0 else 0)}", cores[6]), unsafe_allow_html=True)
    ind_cols[3].markdown(render_metric_card("Custo Total / m² constr.", f"R$ {fmt_br(valor_total_despesas / area_construida_total if area_construida_total > 0 else 0)}", cores[7]), unsafe_allow_html=True)
