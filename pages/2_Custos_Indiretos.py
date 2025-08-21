# pages/2_Custos_Indiretos.py
import streamlit as st
import pandas as pd
import streamlit_antd_components as sac
from utils import *

st.set_page_config(page_title="Custos Indiretos", layout="wide")

# Aumentamos a fonte do valor aqui na função do card
def card_metric(label, value):
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

# Substitua todo o seu bloco 'with st.expander(...)' por este

with st.expander("Detalhamento de Custos Indiretos", expanded=True):
    st.subheader("Custos Indiretos (calculados sobre o VGV)")

    # (A lógica de inicialização do session_state continua a mesma)
    if 'custos_indiretos_percentuais' not in st.session_state:
        custos_salvos = info.get('custos_indiretos_percentuais', {})
        if custos_salvos and isinstance(list(custos_salvos.values())[0], (int, float)):
            st.session_state.custos_indiretos_percentuais = {item: {"percentual": val, "fonte": "Manual"} for item, val in custos_salvos.items()}
        else:
            st.session_state.custos_indiretos_percentuais = {item: custos_salvos.get(item, {"percentual": vals[1], "fonte": "Manual"}) for item, vals in DEFAULT_CUSTOS_INDIRETOS.items()}

    # --- PASSO 1: Preparar os Dados para o Data Editor ---

    # Criamos uma lista de dicionários, que é um formato perfeito para o Pandas
    dados_tabela = []
    for item, (min_val, default_val, max_val) in DEFAULT_CUSTOS_INDIRETOS.items():
        percentual_atual = st.session_state.custos_indiretos_percentuais.get(item, {"percentual": default_val})['percentual']
        custo_calculado = vgv_total * (percentual_atual / 100)
        
        dados_tabela.append({
            "Item": item,
            "Seu Projeto (%)": percentual_atual,
            "Custo (R$)": custo_calculado,
            # Adicionamos colunas "escondidas" para guardar os limites
            "_min": min_val,
            "_max": max_val
        })

    # Criamos o DataFrame do Pandas
    df = pd.DataFrame(dados_tabela)

    st.write("### Dados Preparados (visão de teste):")
    st.dataframe(df) # Apenas para a gente ver como o DataFrame ficou

    custo_indireto_calculado = df["Custo (R$)"].sum()

    st.divider()

    # (O card do total continua o mesmo por enquanto)
    _, col_metrica = st.columns([2, 1])
    with col_metrica:
        card_metric(
            label="Custo Indireto Total",
            value=f"R$ {fmt_br(custo_indireto_calculado)}",
            icon_name="cash-coin"
        )
