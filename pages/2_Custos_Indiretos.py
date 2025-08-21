# pages/2_Custos_Indiretos.py
import streamlit as st
import pandas as pd
from utils import *

st.set_page_config(page_title="Custos Indiretos", layout="wide")

# --- MUDANÇA 1: Bloco de CSS Centralizado ---
# Este bloco injeta os estilos para o cabeçalho, linha vertical e cores de linha alternadas.
st.markdown("""
<style>
/* Melhora o cabeçalho e adiciona espaçamento */
.header-style {
    font-size: 16px;
    font-weight: bold;
    padding-bottom: 10px;
    border-bottom: 2px solid #f0f2f6;
}

/* Cria a linha vertical entre as colunas principais */
/* Acessamos o container da primeira coluna e adicionamos uma borda à direita */
section[data-testid="stSidebar"] + section div[data-testid="stHorizontalBlock"] > div:nth-child(1) {
    border-right: 1px solid #e1e1e1;
    padding-right: 20px;
}
/* Adiciona um espaçamento à esquerda da segunda coluna para equilibrar */
section[data-testid="stSidebar"] + section div[data-testid="stHorizontalBlock"] > div:nth-child(2) {
    padding-left: 20px;
}

/* Cria as cores alternadas (estilo "zebra") para as linhas de itens */
/* Acessamos cada 'bloco horizontal' que o Streamlit cria para uma linha */
.main .st-emotion-cache-1yycg5d > div[data-testid="stHorizontalBlock"]:nth-of-type(even) {
    background-color: #f9f9f9;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)


def card_metric(label, value):
    # --- MUDANÇA 2: Aumentar a fonte do valor ---
    st.markdown(f"""
        <div style="border:1px solid #e1e1e1; border-radius:8px; padding:15px; text-align:center; background-color:#f9f9f9;">
            <h3 style="margin:0; color:#555;">{label}</h3>
            <p style="font-size:32px; font-weight:bold; margin:5px 0 0 0;">{value}</p>
        </div>""", unsafe_allow_html=True)

if "projeto_info" not in st.session_state:
    st.error("Nenhum projeto carregado...")
    if st.button("Voltar para a seleção de projetos"):
        st.switch_page("Início.py")
    st.stop()

render_sidebar()
info = st.session_state.projeto_info
st.title("💸 Custos Indiretos")

custos_config = info.get('custos_config', {})
preco_medio_venda_m2 = custos_config.get('preco_medio_venda_m2', 10000.0)
vgv_total = info.get('area_privativa', 0) * preco_medio_venda_m2

with st.expander("Detalhamento de Custos Indiretos", expanded=True):
    st.subheader("Custos Indiretos (calculados sobre o VGV)")

    if 'custos_indiretos_percentuais' not in st.session_state:
        # (Lógica de inicialização do session_state... sem alteração)
        custos_salvos = info.get('custos_indiretos_percentuais', {})
        if custos_salvos and isinstance(list(custos_salvos.values())[0], (int, float)):
            st.session_state.custos_indiretos_percentuais = {item: {"percentual": val, "fonte": "Manual"} for item, val in custos_salvos.items()}
        else:
            st.session_state.custos_indiretos_percentuais = {item: custos_salvos.get(item, {"percentual": vals[1], "fonte": "Manual"}) for item, vals in DEFAULT_CUSTOS_INDIRETOS.items()}

    # --- MUDANÇA 3: Cabeçalho com o novo estilo CSS ---
    header_cols = st.columns(2)
    header_cols[0].markdown('<p class="header-style">Item / Seu Projeto (%)</p>', unsafe_allow_html=True)
    header_cols[1].markdown('<p class="header-style">Item / Seu Projeto (%)</p>', unsafe_allow_html=True)
    
    items_list = list(DEFAULT_CUSTOS_INDIRETOS.items())
    mid_point = (len(items_list) + 1) // 2
    
    col1, col2 = st.columns(2)
    custo_indireto_calculado = 0

    def render_item(item_tuple, container):
        # (Função render_item... sem alteração)
        item, (min_val, default_val, max_val) = item_tuple
        c = container.columns([2, 1, 1.5, 1])
        c[0].container(height=38, border=False).write(item)
        current_percent = st.session_state.custos_indiretos_percentuais.get(item, {"percentual": default_val})['percentual']
        final_percent = c[1].number_input(
            "percentual", min_value=min_val, max_value=max_val, value=float(current_percent),
            step=0.1, format="%.1f", key=f"input_indireto_{item}", label_visibility="collapsed"
        )
        if max_val > min_val:
            progress_value = (final_percent - min_val) / (max_val - min_val)
        else:
            progress_value = 0.0
        c[2].progress(progress_value)
        if final_percent != current_percent:
            st.session_state.custos_indiretos_percentuais
