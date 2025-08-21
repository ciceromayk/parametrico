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

# Substitua o seu bloco 'with st.expander(...)' por este
with st.expander("Detalhamento de Custos Indiretos", expanded=True):
    st.subheader("Custos Indiretos (calculados sobre o VGV)")

    # A inicialização do session_state continua a mesma
    if 'custos_indiretos_percentuais' not in st.session_state:
        custos_salvos = info.get('custos_indiretos_percentuais', {})
        if custos_salvos and isinstance(list(custos_salvos.values())[0], (int, float)):
            st.session_state.custos_indiretos_percentuais = {item: {"percentual": val, "fonte": "Manual"} for item, val in custos_salvos.items()}
        else:
            st.session_state.custos_indiretos_percentuais = {item: custos_salvos.get(item, {"percentual": vals[1], "fonte": "Manual"}) for item, vals in DEFAULT_CUSTOS_INDIRETOS.items()}

    # --- MUDANÇA 1: Cabeçalho simplificado ---
    cols_header = st.columns([4, 2, 2])
    cols_header[0].markdown("**Item**")
    cols_header[1].markdown("<p style='text-align: left;'><strong>Seu Projeto (%)</strong></p>", unsafe_allow_html=True)
    cols_header[2].markdown("<p style='text-align: right;'><strong>Custo (R$)</strong></p>", unsafe_allow_html=True)
    st.divider()

    custo_indireto_calculado = 0
    for item, (min_val, default_val, max_val) in DEFAULT_CUSTOS_INDIRETOS.items():
        
        # --- MUDANÇA 2: Layout da linha e controle único ---
        c = st.columns([4, 2, 2])
        c[0].container(height=38, border=False).write(item)
        
        # Pega o valor atual do session_state
        current_percent = st.session_state.custos_indiretos_percentuais.get(item, {"percentual": default_val})['percentual']

        # Controle numérico único
        final_percent = c[1].number_input(
            "percentual",
            min_value=min_val,
            max_value=max_val,
            value=float(current_percent), # Garante que o valor seja float
            step=0.1,
            format="%.1f", # Formatação para uma casa decimal
            key=f"input_indireto_{item}",
            label_visibility="collapsed"
        )
        
        # Se o valor mudou, atualiza o estado e roda de novo
        if final_percent != current_percent:
            st.session_state.custos_indiretos_percentuais[item]['percentual'] = final_percent
            st.rerun()

        custo_item = vgv_total * (final_percent / 100)
        c[2].markdown(f"<p style='text-align: right; line-height: 2.5;'>R$ {fmt_br(custo_item)}</p>", unsafe_allow_html=True)
        custo_indireto_calculado += custo_item
    
    st.divider()
    
    # --- MUDANÇA 3: Usando st.metric para o total ---
    _, col_metrica = st.columns([2,1]) # Usamos a primeira coluna como espaçador
    
    col_metrica.metric(
        label="**Custo Indireto Total**",
        value=f"R$ {fmt_br(custo_indireto_calculado)}"
    )
