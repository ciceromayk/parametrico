# pages/3_Resultados_e_Indicadores.py
import streamlit as st
import pandas as pd
from utils import *

st.set_page_config(page_title="Resultados e Indicadores", layout="wide")

if "projeto_info" not in st.session_state:
    st.error("Nenhum projeto carregado. Por favor, selecione um projeto na página inicial.")
    if st.button("Voltar para a seleção de projetos"):
        st.switch_page("Início.py")
    st.stop()

# Passamos uma chave única para a sidebar para evitar erros de chave duplicada
render_sidebar(form_key="sidebar_resultados")

info = st.session_state.projeto_info
st.title("📈 Resultados e Indicadores Chave")

# --- CÁLCULOS GERAIS ---
# Custo Direto
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

# VGV
preco_medio_venda_m2 = custos_config.get('preco_medio_venda_m2', 10000.0)
vgv_total = info.get('area_privativa', 0) * preco_medio_venda_m2

# Custo Indireto
custos_indiretos_percentuais = info.get('custos_indiretos_percentuais', {})
custo_indireto_calculado = 0
if custos_indiretos_percentuais:
    for item, values in custos_indiretos_percentuais.items():
        percentual = values.get('percentual', 0)
        custo_indireto_calculado += vgv_total * (float(percentual) / 100)

# Custo do Terreno
custo_terreno_total = info.get('area_terreno', 0) * custos_config.get('custo_terreno_m2', 2500.0)

# TOTAIS
valor_total_despesas = custo_direto_total + custo_indireto_calculado + custo_terreno_total
lucratividade_valor = vgv_total - valor_total_despesas
lucratividade_percentual = (lucratividade_valor / vgv_total) * 100 if vgv_total > 0 else 0

# --- APRESENTAÇÃO DOS RESULTADOS ---
with st.container(border=True):
    cores = ["#00829d", "#6a42c1", "#3c763d", "#a94442", "#fd7e14", "#20c997", "#31708f", "#8a6d3b"]
    
    st.subheader("Resultados Financeiros")
    res_cols = st.columns(4)
    res_cols[0].markdown(render_metric_card("VGV Total", f"R$ {fmt_br(vgv_total)}", cores[0]), unsafe_allow_html=True)
    res_cols[1].markdown(render_metric_card("Custo Total", f"R$ {fmt_br(valor_total_despesas)}", cores[1]), unsafe_allow_html=True)
    res_cols[2].markdown(render_metric_card("Lucro Bruto", f"R$ {fmt_br(lucratividade_valor)}", cores[2]), unsafe_allow_html=True)
    res_cols[3].markdown(render_metric_card("Margem de Lucro", f"{lucratividade_percentual:.2f}%", cores[3]), unsafe_allow_html=True)
    
    st.divider()

    st.subheader("Composição do Custo Total")
    comp_cols = st.columns(3)
    if valor_total_despesas > 0:
        p_direto = (custo_direto_total / valor_total_despesas * 100)
        p_indireto = (custo_indireto_calculado / valor_total_despesas * 100)
        p_terreno = (custo_terreno_total / valor_total_despesas * 100)
        comp_cols[0].markdown(render_metric_card(f"Custo Direto ({p_direto:.2f}%)", f"R$ {fmt_br(custo_direto_total)}", cores[6]), unsafe_allow_html=True)
        comp_cols[1].markdown(render_metric_card(f"Custo Indireto ({p_indireto:.2f}%)", f"R$ {fmt_br(custo_indireto_calculado)}", cores[7]), unsafe_allow_html=True)
        comp_cols[2].markdown(render_metric_card(f"Custo do Terreno ({p_terreno:.2f}%)", f"R$ {fmt_br(custo_terreno_total)}", cores[1]), unsafe_allow_html=True)

    st.divider()
    
    st.subheader("Indicadores por Área Construída")
    ind_cols = st.columns(4)
    ind_cols[0].markdown(render_metric_card("Terreno / Custo Total", f"{(custo_terreno_total / valor_total_despesas * 100 if valor_total_despesas > 0 else 0):.2f}%", cores[4]), unsafe_allow_html=True)
    ind_cols[1].markdown(render_metric_card("Custo Direto / m²", f"R$ {fmt_br(custo_direto_total / area_construida_total if area_construida_total > 0 else 0)}", cores[5]), unsafe_allow_html=True)
    ind_cols[2].markdown(render_metric_card("Custo Indireto / m²", f"R$ {fmt_br(custo_indireto_calculado / area_construida_total if area_construida_total > 0 else 0)}", cores[6]), unsafe_allow_html=True)
    ind_cols[3].markdown(render_metric_card("Custo Total / m²", f"R$ {fmt_br(valor_total_despesas / area_construida_total if area_construida_total > 0 else 0)}", cores[7]), unsafe_allow_html=True)

st.divider()

# Botão para gerar o relatório em PDF
if st.button("Gerar Relatório em PDF", type="primary"):
    with st.spinner("Gerando seu relatório..."):
        pdf_data = generate_pdf_report(
            info, vgv_total, valor_total_despesas, lucratividade_valor, lucratividade_percentual,
            custo_direto_total, custo_indireto_calculado, custo_terreno_total, area_construida_total, custos_config
        )
        st.download_button(
            label="Baixar Relatório PDF",
            data=pdf_data,
            file_name=f"Relatorio_{info['nome']}.pdf",
            mime="application/pdf"
        )
