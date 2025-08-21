# pages/2_Custos_Indiretos.py
import streamlit as st
import pandas as pd
from utils import *

st.set_page_config(page_title="Custos Indiretos", layout="wide")

if "projeto_info" not in st.session_state:
    st.error("Nenhum projeto carregado. Por favor, selecione um projeto na página inicial.")
    if st.button("Voltar para a seleção de projetos"):
        st.switch_page("app.py")
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
    
    ref_percentuais, ref_nome = {}, None
    if obra_ref_selecionada != "Nenhuma":
        ref_id = int(obra_ref_selecionada.split("–")[0].strip())
        ref_nome = obra_ref_selecionada.split("–")[1].strip()
        obra_ref_data = next((o for o in obras_historicas if o['id'] == ref_id), None)
        if obra_ref_data: ref_percentuais = obra_ref_data['percentuais']
    
    st.divider()
    cols = st.columns([2.5, 1.5, 1, 1.5, 1, 1.5, 1])
    cols[0].markdown("**Item**"); cols[1].markdown("**Fonte**"); cols[2].markdown("**Ref. (%)**")
    cols[3].markdown("**Seu Projeto (%)**"); cols[5].markdown("<p style='text-align: center;'>Custo (R$)</p>", unsafe_allow_html=True); cols[6].markdown("<p style='text-align: center;'>Ação</p>", unsafe_allow_html=True)

    custo_indireto_calculado = 0
    for item, (min_val, default_val, max_val) in DEFAULT_CUSTOS_INDIRETOS.items():
        c = st.columns([2.5, 1.5, 1, 1.5, 1, 1.5, 1])
        c[0].container(height=38, border=False).write(item)
        item_info = st.session_state.custos_indiretos_percentuais.get(item, {"percentual": default_val, "fonte": "Manual"})
        c[1].container(height=38, border=False).write(item_info['fonte'])
        ref_val = ref_percentuais.get(item, 0)
        c[2].container(height=38, border=False).write(f"{ref_val:.2f}%" if obra_ref_selecionada != "Nenhuma" else "-")
        
        slider_col, input_col = c[3], c[4]
        current_percent = item_info['percentual']
        current_percent_clipped = max(min_val, min(current_percent, max_val))

        percent_slider = slider_col.slider("slider", min_val, max_val, float(current_percent_clipped), 0.1, key=f"slider_indireto_{item}", label_visibility="collapsed")
        percent_input = input_col.number_input("input", min_val, max_val, percent_slider, 0.1, key=f"input_indireto_{item}", label_visibility="collapsed")
        
        if percent_input != current_percent:
            st.session_state.custos_indiretos_percentuais[item]['percentual'] = percent_input
            st.session_state.custos_indiretos_percentuais[item]['fonte'] = "Manual"
            st.rerun()

        custo_item = vgv_total * (percent_input / 100)
        c[5].markdown(f"<p style='text-align: center;'>R$ {fmt_br(custo_item)}</p>", unsafe_allow_html=True)
        custo_indireto_calculado += custo_item

        if c[6].button("⬅️", key=f"apply_indireto_{item}", help=f"Aplicar percentual de referência ({ref_val:.2f}%)", use_container_width=True):
                if ref_nome:
                    st.session_state.custos_indiretos_percentuais[item]['percentual'] = ref_val
                    st.session_state.custos_indiretos_percentuais[item]['fonte'] = ref_nome
                    st.rerun()
