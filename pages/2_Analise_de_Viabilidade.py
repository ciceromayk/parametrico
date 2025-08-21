# pages/2_Analise_de_Viabilidade.py
import streamlit as st
import pandas as pd
from utils import save_project, fmt_br, render_metric_card

st.set_page_config(page_title="Análise de Viabilidade", layout="wide")

if "projeto_info" not in st.session_state:
    st.error("Nenhum projeto carregado. Por favor, selecione um projeto na página inicial.")
    st.page_link("app.py", label="Voltar para a seleção de projetos")
    st.stop()

info = st.session_state.projeto_info

# Carregar e calcular dados da página 1 (Orçamento Direto)
pavimentos_df = pd.DataFrame(info.get('pavimentos', []))
if not pavimentos_df.empty:
    custos_config = info.get('custos_config', {})
    cub = custos_config.get('cub', 4500.0)
    
    pavimentos_df["area_total"] = pavimentos_df["area"] * pavimentos_df["rep"]
    pavimentos_df["area_eq"] = pavimentos_df["area_total"] * pavimentos_df["coef"]
    pavimentos_df["area_constr"] = pavimentos_df.apply(lambda r: r["area_total"] if r["constr"] else 0.0, axis=1)
    pavimentos_df["custo_direto"] = pavimentos_df["area_eq"] * cub
    
    custo_direto_total = pavimentos_df["custo_direto"].sum()
    area_construida_total = pavimentos_df["area_constr"].sum()
else:
    custo_direto_total = 0
    area_construida_total = 0

st.title("📊 Análise de Viabilidade do Empreendimento")

# --- 1. SEÇÃO DE VGV ---
st.header("Receitas / VGV")
with st.container(border=True):
    st.subheader("Composição de Unidades e VGV")
    
    if 'unidades_vgv' not in info:
        info['unidades_vgv'] = [{"Tipo": "A", "Quant.": 1, "Área Privativa (m²)": 100.0, "Valor Médio de Venda (R$)": 500000.0}]

    # Editor de dados para as unidades
    edited_unidades = st.data_editor(
        pd.DataFrame(info['unidades_vgv']),
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Área Privativa (m²)": st.column_config.NumberColumn(format="%.2f m²"),
            "Valor Médio de Venda (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
        }
    )
    info['unidades_vgv'] = edited_unidades.to_dict('records')
    
    unidades_df = pd.DataFrame(info['unidades_vgv'])
    unidades_df['VGV Esperado'] = unidades_df['Quant.'] * unidades_df['Valor Médio de Venda (R$)']
    vgv_total = unidades_df['VGV Esperado'].sum()
    
    st.metric("VGV (Valor Geral de Vendas) Total", f"R$ {fmt_br(vgv_total)}")


# --- 2. SEÇÃO DE CUSTOS ---
st.header("Detalhamento de Custos")
with st.container(border=True):
    # Custo Direto (puxado da página 1)
    st.subheader("Custo Direto de Construção")
    st.metric("Custo Direto Total (Obra)", f"R$ {fmt_br(custo_direto_total)}")
    
    st.divider()

    # Custos Indiretos
    st.subheader("Custos Indiretos")
    custos_indiretos = info.get('custos_indiretos', {})
    
    cols = st.columns(3)
    i = 0
    for key, value in custos_indiretos.items():
        with cols[i % 3]:
            # Checa se o item é um percentual ou valor fixo
            if "(sobre VGV)" in key or "(sobre o VGV)" in key:
                custos_indiretos[key] = st.number_input(f"{key} (%)", value=float(value), format="%.2f")
            else: # Assumimos que é um valor fixo se não tiver a tag
                custos_indiretos[key] = st.number_input(f"{key} (R$)", value=float(value), format="%.2f")
        i += 1
    info['custos_indiretos'] = custos_indiretos
    
    # Custo do Terreno
    st.divider()
    st.subheader("Custo do Terreno")
    terreno_cols = st.columns(3)
    custos_config = info.get('custos_config', {})
    area_terreno = info.get('area_terreno', 0)
    custos_config['custo_terreno_m2'] = terreno_cols[0].number_input("Custo do Terreno por m² (R$)", value=custos_config.get('custo_terreno_m2', 2500.0), format="%.2f")
    custo_terreno_total = area_terreno * custos_config['custo_terreno_m2']
    terreno_cols[1].metric("Área do Terreno", f"{fmt_br(area_terreno)} m²")
    terreno_cols[2].metric("Custo Total do Terreno", f"R$ {fmt_br(custo_terreno_total)}")
    info['custos_config'] = custos_config

# --- 3. CÁLCULO TOTAL E RESULTADOS ---
custo_indireto_calculado = 0
for key, value in custos_indiretos.items():
    if "(sobre VGV)" in key or "(sobre o VGV)" in key:
        custo_indireto_calculado += vgv_total * (value / 100.0)
    else: # Soma valor fixo
        custo_indireto_calculado += value

valor_total_despesas = custo_direto_total + custo_indireto_calculado + custo_terreno_total
lucratividade_valor = vgv_total - valor_total_despesas
lucratividade_percentual = (lucratividade_valor / vgv_total) * 100 if vgv_total > 0 else 0

st.header("Resultados e Indicadores Chave")
with st.container(border=True):
    res_cols = st.columns(4)
    res_cols[0].metric("VGV Total", f"R$ {fmt_br(vgv_total)}")
    res_cols[1].metric("Custo Total do Empreendimento", f"R$ {fmt_br(valor_total_despesas)}")
    res_cols[2].metric("Lucro Bruto", f"R$ {fmt_br(lucratividade_valor)}", delta=f"{lucratividade_percentual:.2f}%")
    res_cols[3].metric("Margem de Lucro", f"{lucratividade_percentual:.2f}%")

# Salvar alterações no botão
if st.sidebar.button("💾 Salvar Alterações na Análise", use_container_width=True, type="primary"):
    save_project(info)
    st.sidebar.success("Análise salva com sucesso!")
