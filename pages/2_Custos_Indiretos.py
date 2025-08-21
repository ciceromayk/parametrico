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

    if 'previous_custos_indiretos_percentuais' not in st.session_state: 
        st.session_state.previous_custos_indiretos_percentuais = {k: v.copy() for k, v in st.session_state.custos_indiretos_percentuais.items()}

    obras_historicas = load_json(HISTORICO_INDIRETO_PATH)
    obra_ref_selecionada = st.selectbox("Usar como Referência (Custos Indiretos):", ["Nenhuma"] + [f"{o['id']} – {o['nome']}" for o in obras_historicas], index=0, key="ref_indireto")
    
    ref_percentuais,
