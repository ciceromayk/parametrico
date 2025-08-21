# pages/2_Custos_Indiretos.py
import streamlit as st
import pandas as pd
from utils import *

st.set_page_config(page_title="Custos Indiretos", layout="wide")

if "projeto_info" not in st.session_state:
    st.error("Nenhum projeto carregado. Por favor, selecione um projeto na página inicial.")
    if st.button("Voltar para a seleção de projetos"):
        st.switch_page("Início.py")
    st.stop()

render_sidebar()

info = st.session_state.projeto_info
st.title("💸 Custos Indiretos")

# Cálculos Preliminares
custos_config = info.get('custos_config', {})
preco_medio_venda_m2 = custos_config.get('preco_medio_venda_m2', 10000.0)
vgv_total = info.get('area_privativa', 0) * preco_medio_venda_m2

with st.expander("Detalhamento de Custos Indiretos", expanded=True):
    st.subheader("Custos Indiretos (calculados sobre o VGV)")

    if 'custos_indiretos_percentuais' not in st.session_state:
        custos_salvos = info.get('custos_indiretos_percentuais', {})
        if custos_salvos and isinstance(list(custos_salvos.values())[0], (int, float)):
             st.session_state.custos_indiretos_percentuais = {item: {"percentual": val, "fonte": "Manual"} for item, val in custos_salvos.items()}
        else:
            st.session_state.custos_indiretos_percentuais = {item: custos_salvos.get(item, {"percentual": vals[1], "fonte": "Manual"}) for item, vals in DEFAULT_CUSTOS_INDIRETOS.items()}

    cols = st.columns([4, 2, 1])
    cols[0].markdown("**Item**")
    cols[1].markdown("<p style='text-align: center;'><strong>Seu Projeto (%)</strong></p>", unsafe_allow_html=True)
    cols[2].markdown("<p style='text-align: center;'><strong>Custo (R$)</strong></p>", unsafe_allow_html=True)

    custo_indireto_calculado = 0
    for item, (min_val, default_val, max_val) in DEFAULT_CUSTOS_INDIRETOS.items():
        c = st.columns([4, 1.5, 0.5, 1])
        c[0].container(height=38, border=False).write(item)
        
        item_info = st.session_state.custos_indiretos_percentuais.get(item, {"percentual": default_val})
        
        slider_col, input_col = c[1], c[2]
        current_percent = item_info['percentual']
        current_percent_clipped = max(min_val, min(current_percent, max_val))

        percent_slider = slider_col.slider("slider", min_val, max_val, float(current_percent_clipped), 0.1, key=f"slider_indireto_{item}", label_visibility="collapsed")
        percent_input = input_col.number_input("input", min_val, max_val, percent_slider, 0.1, key=f"input_indireto_{item}", label_visibility="collapsed")
        
        final_percent = current_percent
        if percent_input != current_percent:
            final_percent = percent_input
            st.session_state.custos_indiretos_percentuais[item]['percentual'] = final_percent
            st.rerun()

        custo_item = vgv_total * (final_percent / 100)
        c[3].markdown(f"<p style='text-align: center;'>R$ {fmt_br(custo_item)}</p>", unsafe_allow_html=True)
        custo_indireto_calculado += custo_item
    
    st.divider()
    
    # <<< 2. TOTAL APRESENTADO EM UM CARD
    col1, col2 = st.columns([2,1])
    with col1:
        st.markdown("") # Espaçador
    with col2:
        st.markdown(render_metric_card("Custo Indireto Total", f"R$ {fmt_br(custo_indireto_calculado)}", color="#6a42c1"), unsafe_allow_html=True)
