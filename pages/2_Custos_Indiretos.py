# pages/2_Custos_Indiretos.py
import streamlit as st
import pandas as pd
from utils import *
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

st.set_page_config(page_title="Custos Indiretos", layout="wide")

# Função para o card do total.
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
                <i class="bi bi-{icon_name}" style="font-size: 1.2em; margin-right: 8px;"></i>{label}
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

# Passamos uma chave única para a função da sidebar para evitar erros
render_sidebar(form_key="sidebar_custos_indiretos")
info = st.session_state.projeto_info
st.title("💸 Custos Indiretos")

# Cálculos Preliminares
custos_config = info.get('custos_config', {})
preco_medio_venda_m2 = custos_config.get('preco_medio_venda_m2', 10000.0)
vgv_total = info.get('area_privativa', 0) * preco_medio_venda_m2

# Bloco principal com a nova tabela AgGrid
with st.expander("Detalhamento de Custos Indiretos", expanded=True):
    st.subheader("Custos Indiretos (calculados sobre o VGV)")

    # Inicialização do session_state
    if 'custos_indiretos_percentuais' not in st.session_state:
        custos_salvos = info.get('custos_indiretos_percentuais', {})
        if custos_salvos and isinstance(list(custos_salvos.values())[0], (int, float)):
            st.session_state.custos_indiretos_percentuais = {item: {"percentual": val, "fonte": "Manual"} for item, val in custos_salvos.items()}
        else:
            st.session_state.custos_indiretos_percentuais = {item: custos_salvos.get(item, {"percentual": vals[1], "fonte": "Manual"}) for item, vals in DEFAULT_CUSTOS_INDIRETOS.items()}

    # PASSO 1: Preparar os Dados para o AgGrid
    dados_tabela = []
    for item, (min_val, default_val, max_val) in DEFAULT_CUSTOS_INDIRETOS.items():
        percentual_atual = st.session_state.custos_indiretos_percentuais.get(item, {"percentual": default_val})['percentual']
        custo_calculado = vgv_total * (percentual_atual / 100)
        dados_tabela.append({
            "Item": item,
            "Seu Projeto (%)": percentual_atual,
            "Custo (R$)": custo_calculado,
        })
    df = pd.DataFrame(dados_tabela)

    # PASSO 2: Configurar o AgGrid
    st.write("### Edite os percentuais de cada custo abaixo:")
    
    gb = GridOptionsBuilder.from_dataframe(df)
    
    # Código JavaScript para formatar a moeda no padrão brasileiro
    jscode_formatador_moeda = JsCode("""
        function(params) {
            if (params.value === null || params.value === undefined) {
                return '';
            }
            return 'R$ ' + params.value.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
        }
    """)

    gb.configure_column("Item", width=250)
    gb.configure_column("Seu Projeto (%)", editable=True, width=100, type=["numericColumn", "numberColumnFilter", "customNumericFormat"], precision=1)
    gb.configure_column("Custo (R$)", valueFormatter=jscode_formatador_moeda, width=150, type=["numericColumn", "numberColumnFilter"])
    
    gb.configure_default_column(resizable=True, filterable=True, sortable=True)
    
    gridOptions = gb.build()

    # Exibimos a tabela AgGrid
    grid_response = AgGrid(
        df,
        gridOptions=gridOptions,
        height=500,
        width='100%',
        update_mode='MODEL_CHANGED',
        allow_unsafe_jscode=True,
        try_convert_numeric_dtypes=True,
        # Tema visual para a tabela
        theme='streamlit' 
    )
    
    # PASSO 3: Usar os Dados Editados
    edited_df = grid_response['data']
    
    # Recalculamos o custo e o total com base nos dados que o usuário pode ter alterado
    # Usamos pd.to_numeric para garantir que a coluna seja numérica antes de calcular
    edited_df["Custo (R$)"] = vgv_total * (pd.to_numeric(edited_df["Seu Projeto (%)"], errors='coerce').fillna(0) / 100)
    custo_indireto_calculado = edited_df["Custo (R$)"].sum()

    # Atualizamos o session_state para guardar as alterações
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
