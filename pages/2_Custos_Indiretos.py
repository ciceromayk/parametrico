# pages/2_Custos_Indiretos.py
import streamlit as st
import pandas as pd
from utils import * 
st.set_page_config(page_title="Custos Indiretos", layout="wide")

# (A função card_metric e a verificação de session_state continuam as mesmas)
def card_metric(label, value):
    st.markdown(f"""
        <div style="border:1px solid #e1e1e1; border-radius:8px; padding:15px; text-align:center; background-color:#f9f9f9;">
            <h3 style="margin:0; color:#555;">{label}</h3>
            <p style="font-size:24px; font-weight:bold; margin:5px 0 0 0;">{value}</p>
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

    # --- MUDANÇA 1: Cabeçalho Único e Centralizado ---
    header_cols = st.columns([.5, 1, .5, .5, 1, .5]) # Colunas para alinhamento
    header_cols[0].markdown("**Item**")
    header_cols[1].markdown("**Seu Projeto (%)**")
    header_cols[3].markdown("**Item**")
    header_cols[4].markdown("**Seu Projeto (%)**")
    st.divider()

    items_list = list(DEFAULT_CUSTOS_INDIRETOS.items())
    mid_point = (len(items_list) + 1) // 2 # Garante que a primeira coluna não fique menor
    
    col1, col2 = st.columns(2)
    custo_indireto_calculado = 0

    # Função interna para renderizar um item, agora com a barra de progresso
    def render_item(item_tuple, container):
        item, (min_val, default_val, max_val) = item_tuple
        
        # Colunas: Item | Input numérico | Barra de Progresso | Custo
        c = container.columns([2, 1, 1.5, 1])
        c[0].container(height=38, border=False).write(item)
        
        current_percent = st.session_state.custos_indiretos_percentuais.get(item, {"percentual": default_val})['percentual']

        final_percent = c[1].number_input(
            "percentual", min_value=min_val, max_value=max_val, value=float(current_percent),
            step=0.1, format="%.1f", key=f"input_indireto_{item}", label_visibility="collapsed"
        )
        
        # --- MUDANÇA 2: Adicionando a Barra de Progresso ---
        # Normaliza o valor entre 0 e 1 para a barra
        if max_val > min_val:
            progress_value = (final_percent - min_val) / (max_val - min_val)
        else:
            progress_value = 0.0 # Caso min e max sejam iguais
        
        c[2].progress(progress_value)

        if final_percent != current_percent:
            st.session_state.custos_indiretos_percentuais[item]['percentual'] = final_percent
            st.rerun()

        custo_item = vgv_total * (final_percent / 100)
        c[3].markdown(f"<p style='text-align: right; line-height: 2.5;'>R$ {fmt_br(custo_item)}</p>", unsafe_allow_html=True)
        return custo_item

    # Renderiza as colunas
    for item_tuple in items_list[:mid_point]:
        custo_indireto_calculado += render_item(item_tuple, col1)
    
    for item_tuple in items_list[mid_point:]:
        custo_indireto_calculado += render_item(item_tuple, col2)

    st.divider()
    
    _, col_metrica = st.columns([2, 1])
    with col_metrica:
        card_metric(
            label="Custo Indireto Total",
            value=f"R$ {fmt_br(custo_indireto_calculado)}"
        )
