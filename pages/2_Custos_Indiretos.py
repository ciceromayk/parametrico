# pages/2_Custos_Indiretos.py
import streamlit as st
import pandas as pd
from utils import *
# A importação do SAC não é mais necessária, pois criamos nosso próprio card.
# import streamlit_antd_components as sac

st.set_page_config(page_title="Custos Indiretos", layout="wide")

# Nossa função aprimorada para o card do total
def card_metric(label, value, icon_name="wallet2"):
    st.markdown(f"""
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
        <div style="
            border: 1px solid #e1e1e1;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            background-color: #f9f9f9;
        ">
            <h3 style="margin: 0; color: #555; font-size: 1.2em;">
                <i class="bi bi-{icon_name}" style="font-size: 1.2em; margin-right: 8px;"></i>
                {label}
            </h3>
            <p style="font-size: 2.5em; font-weight: bold; margin: 10px 0 0 0;">{value}</p>
        </div>
        """, unsafe_allow_html=True)

# Verificação inicial do projeto carregado
if "projeto_info" not in st.session_state:
    st.error("Nenhum projeto carregado. Por favor, selecione um projeto na página inicial.")
    if st.button("Voltar para a seleção de projetos"):
        st.switch_page("Início.py")
    st.stop()

# Renderiza a sidebar e obtém as informações do projeto
render_sidebar()
info = st.session_state.projeto_info
st.title("💸 Custos Indiretos")

# Cálculos Preliminares
custos_config = info.get('custos_config', {})
preco_medio_venda_m2 = custos_config.get('preco_medio_venda_m2', 10000.0)
vgv_total = info.get('area_privativa', 0) * preco_medio_venda_m2

# Bloco principal com a nova tabela editável
with st.expander("Detalhamento de Custos Indiretos", expanded=True):
    st.subheader("Custos Indiretos (calculados sobre o VGV)")

    # Inicialização do session_state (sem alteração)
    if 'custos_indiretos_percentuais' not in st.session_state:
        custos_salvos = info.get('custos_indiretos_percentuais', {})
        if custos_salvos and isinstance(list(custos_salvos.values())[0], (int, float)):
            st.session_state.custos_indiretos_percentuais = {item: {"percentual": val, "fonte": "Manual"} for item, val in custos_salvos.items()}
        else:
            st.session_state.custos_indiretos_percentuais = {item: custos_salvos.get(item, {"percentual": vals[1], "fonte": "Manual"}) for item, vals in DEFAULT_CUSTOS_INDIRETOS.items()}

    # PASSO 1: Preparar os Dados para o Data Editor
    dados_tabela = []
    for item, (min_val, default_val, max_val) in DEFAULT_CUSTOS_INDIRETOS.items():
        percentual_atual = st.session_state.custos_indiretos_percentuais.get(item, {"percentual": default_val})['percentual']
        custo_calculado = vgv_total * (percentual_atual / 100)
        
        dados_tabela.append({
            "Item": item,
            "Seu Projeto (%)": percentual_atual,
            "Custo (R$)": custo_calculado,
            "_min": min_val,
            "_max": max_val
        })
    df = pd.DataFrame(dados_tabela)

# PASSO 2: Exibir e Configurar o Data Editor (versão corrigida)
    st.write("### Edite os percentuais de cada custo abaixo:")
    edited_df = st.data_editor(
        df,
        column_config={
            "Item": st.column_config.TextColumn(
                width="large",
                disabled=True,
            ),
            "Seu Projeto (%)": st.column_config.NumberColumn(
                help="Clique para editar o valor percentual do custo.",
                # CORREÇÃO: Convertemos as colunas para listas
                min_value=df["_min"].tolist(),
                max_value=df["_max"].tolist(),
                step=0.1,
                format="%.1f %%",
            ),
            "Custo (R$)": st.column_config.NumberColumn(
                format="R$ %.2f",
                disabled=True,
            ),
        },
        hide_index=True,
        column_order=("Item", "Seu Projeto (%)", "Custo (R$)"),
        use_container_width=True
    )
    
    # PASSO 3: Usar os Dados Editados para Recalcular e Salvar
    edited_df["Custo (R$)"] = vgv_total * (edited_df["Seu Projeto (%)"] / 100)
    custo_indireto_calculado = edited_df["Custo (R$)"].sum()

    for index, row in edited_df.iterrows():
        item_nome = row["Item"]
        novo_percentual = row["Seu Projeto (%)"]
        st.session_state.custos_indiretos_percentuais[item_nome]['percentual'] = novo_percentual

    st.divider()

    # Exibição do card do total
    _, col_metrica = st.columns([2, 1])
    with col_metrica:
        card_metric(
            label="Custo Indireto Total",
            value=f"R$ {fmt_br(custo_indireto_calculado)}",
            icon_name="cash-coin"
        )# pages/2_Custos_Indiretos.py
import streamlit as st
import pandas as pd
from utils import *
# A importação do SAC não é mais necessária, pois criamos nosso próprio card.
# import streamlit_antd_components as sac

st.set_page_config(page_title="Custos Indiretos", layout="wide")

# Nossa função aprimorada para o card do total
def card_metric(label, value, icon_name="wallet2"):
    st.markdown(f"""
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
        <div style="
            border: 1px solid #e1e1e1;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            background-color: #f9f9f9;
        ">
            <h3 style="margin: 0; color: #555; font-size: 1.2em;">
                <i class="bi bi-{icon_name}" style="font-size: 1.2em; margin-right: 8px;"></i>
                {label}
            </h3>
            <p style="font-size: 2.5em; font-weight: bold; margin: 10px 0 0 0;">{value}</p>
        </div>
        """, unsafe_allow_html=True)

# Verificação inicial do projeto carregado
if "projeto_info" not in st.session_state:
    st.error("Nenhum projeto carregado. Por favor, selecione um projeto na página inicial.")
    if st.button("Voltar para a seleção de projetos"):
        st.switch_page("Início.py")
    st.stop()

# Renderiza a sidebar e obtém as informações do projeto
render_sidebar()
info = st.session_state.projeto_info
st.title("💸 Custos Indiretos")

# Cálculos Preliminares
custos_config = info.get('custos_config', {})
preco_medio_venda_m2 = custos_config.get('preco_medio_venda_m2', 10000.0)
vgv_total = info.get('area_privativa', 0) * preco_medio_venda_m2

# Bloco principal com a nova tabela editável
with st.expander("Detalhamento de Custos Indiretos", expanded=True):
    st.subheader("Custos Indiretos (calculados sobre o VGV)")

    # Inicialização do session_state (sem alteração)
    if 'custos_indiretos_percentuais' not in st.session_state:
        custos_salvos = info.get('custos_indiretos_percentuais', {})
        if custos_salvos and isinstance(list(custos_salvos.values())[0], (int, float)):
            st.session_state.custos_indiretos_percentuais = {item: {"percentual": val, "fonte": "Manual"} for item, val in custos_salvos.items()}
        else:
            st.session_state.custos_indiretos_percentuais = {item: custos_salvos.get(item, {"percentual": vals[1], "fonte": "Manual"}) for item, vals in DEFAULT_CUSTOS_INDIRETOS.items()}

    # PASSO 1: Preparar os Dados para o Data Editor
    dados_tabela = []
    for item, (min_val, default_val, max_val) in DEFAULT_CUSTOS_INDIRETOS.items():
        percentual_atual = st.session_state.custos_indiretos_percentuais.get(item, {"percentual": default_val})['percentual']
        custo_calculado = vgv_total * (percentual_atual / 100)
        
        dados_tabela.append({
            "Item": item,
            "Seu Projeto (%)": percentual_atual,
            "Custo (R$)": custo_calculado,
            "_min": min_val,
            "_max": max_val
        })
    df = pd.DataFrame(dados_tabela)

    # PASSO 2: Exibir e Configurar o Data Editor
    st.write("### Edite os percentuais de cada custo abaixo:")
    edited_df = st.data_editor(
        df,
        column_config={
            "Item": st.column_config.TextColumn(
                width="large",
                disabled=True,
            ),
            "Seu Projeto (%)": st.column_config.NumberColumn(
                help="Clique para editar o valor percentual do custo.",
                min_value=df["_min"],
                max_value=df["_max"],
                step=0.1,
                format="%.1f %%",
            ),
            "Custo (R$)": st.column_config.NumberColumn(
                format="R$ %.2f",
                disabled=True,
            ),
        },
        hide_index=True,
        column_order=("Item", "Seu Projeto (%)", "Custo (R$)"),
        use_container_width=True
    )
    
    # PASSO 3: Usar os Dados Editados para Recalcular e Salvar
    edited_df["Custo (R$)"] = vgv_total * (edited_df["Seu Projeto (%)"] / 100)
    custo_indireto_calculado = edited_df["Custo (R$)"].sum()

    for index, row in edited_df.iterrows():
        item_nome = row["Item"]
        novo_percentual = row["Seu Projeto (%)"]
        st.session_state.custos_indiretos_percentuais[item_nome]['percentual'] = novo_percentual

    st.divider()

    # Exibição do card do total
    _, col_metrica = st.columns([2, 1])
    with col_metrica:
        card_metric(
            label="Custo Indireto Total",
            value=f"R$ {fmt_br(custo_indireto_calculado)}",
            icon_name="cash-coin"
        )
