# pages/3_Resultados_e_Indicadores.py
import streamlit as st
import pandas as pd
from utils import *
import json
import requests
import time

st.set_page_config(page_title="Resultados e Indicadores", layout="wide")

# CSS para configurar a largura do dialog
st.markdown("""
<style>
    /* Essa classe é usada pelo Streamlit para o contêiner do dialog. */
    /* Você pode precisar inspecionar o elemento para verificar se a classe mudou em versões futuras do Streamlit. */
    .st-emotion-cache-1r651z {
        max-width: 1600px;  /* Largura máxima do pop-up */
        width: 90%;       /* Largura responsiva para telas menores */
    }
</style>
""", unsafe_allow_html=True)

if "projeto_info" not in st.session_state:
    st.error("Nenhum projeto carregado. Por favor, selecione um projeto na página inicial.")
    if st.button("Voltar para a seleção de projetos"):
        st.switch_page("Início.py")
    st.stop()

# Passamos uma chave única para a sidebar para evitar erros de chave duplicada
render_sidebar(form_key="sidebar_resultados")

info = st.session_state.projeto_info
st.title("📈 Resultados e Indicadores Chave")

# --- CÁLCULOS GERAIS ---
pavimentos_df = pd.DataFrame(info.get('pavimentos', []))
custos_config = info.get('custos_config', {})
custo_direto_total, area_construida_total = 0, 0
if not pavimentos_df.empty:
    custo_area_privativa = custos_config.get('custo_area_privativa', 4500.0)
    pavimentos_df["area_total"] = pavimentos_df["area"] * pavimentos_df["rep"]
    pavimentos_df["area_eq"] = pavimentos_df["area_total"] * pavimentos_df["coef"]
    pavimentos_df["area_constr"] = pavimentos_df.apply(lambda r: r["area_total"] if r["constr"] else 0.0, axis=1)
    pavimentos_df["custo_direto"] = pavimentos_df["area_eq"] * custo_area_privativa
    custo_direto_total = pavimentos_df["custo_direto"].sum()
    area_construida_total = pavimentos_df["area_constr"].sum()

preco_medio_venda_m2 = custos_config.get('preco_medio_venda_m2', 10000.0)
vgv_total = info.get('area_privativa', 0) * preco_medio_venda_m2

custos_indiretos_percentuais = info.get('custos_indiretos_percentuais', {})
custo_indireto_calculado = 0
if custos_indiretos_percentuais:
    for item, values in custos_indiretos_percentuais.items():
        percentual = values.get('percentual', 0)
        custo_indireto_calculado += vgv_total * (float(percentual) / 100)

custo_terreno_total = info.get('area_terreno', 0) * custos_config.get('custo_terreno_m2', 2500.0)

# Obter o custo indireto de obra da session_state de forma segura
custo_indireto_obra_total = 0
if 'custos_indiretos_obra' in st.session_state and 'duracao_obra' in st.session_state:
    for item, valor_mensal in st.session_state.custos_indiretos_obra.items():
        custo_indireto_obra_total += valor_mensal * st.session_state.duracao_obra

# TOTAIS - incluindo os custos indiretos de obra
valor_total_despesas = custo_direto_total + custo_indireto_calculado + custo_terreno_total + custo_indireto_obra_total
lucratividade_valor = vgv_total - valor_total_despesas
lucratividade_percentual = (lucratividade_valor / vgv_total) * 100 if vgv_total > 0 else 0

# --- APRESENTAÇÃO DOS RESULTADOS ---
with st.container(border=True):
    cores = ["#00829d", "#6a42c1", "#3c763d", "#a94442", "#fd7e14", "#20c997", "#31708f", "#8a6d3b"]
    st.subheader("Resultados Financeiros")
    res_cols = st.columns(4)
    res_cols[0].markdown(render_metric_card("VGV Total", f"R$ {fmt_br(vgv_total)}", cores[0]), unsafe_allow_html=True)
    res_cols[1].markdown(render_metric_card("Custo Total", f"R$ {fmt_br(valor_total_despesas)}", cores[1]), unsafe_allow_html=True)
    res_cols[2].markdown(render_metric_card("Lucro Bruto", f"R$ {fmt_br(lucratividade_valor)}", cores[2]), unsafe_allow_html=True)
    res_cols[3].markdown(render_metric_card("Margem de Lucro", f"{lucratividade_percentual:.2f}%", cores[3]), unsafe_allow_html=True)
    st.divider()
    st.subheader("Composição do Custo Total")
    comp_cols = st.columns(4) # Alterado para 4 colunas
    if valor_total_despesas > 0:
        p_direto = (custo_direto_total / valor_total_despesas * 100)
        p_indireto_venda = (custo_indireto_calculado / valor_total_despesas * 100)
        p_indireto_obra = (custo_indireto_obra_total / valor_total_despesas * 100)
        p_terreno = (custo_terreno_total / valor_total_despesas * 100)

        comp_cols[0].markdown(render_metric_card(f"Custo Direto ({p_direto:.2f}%)", f"R$ {fmt_br(custo_direto_total)}", cores[6]), unsafe_allow_html=True)
        comp_cols[1].markdown(render_metric_card(f"Indiretos Venda ({p_indireto_venda:.2f}%)", f"R$ {fmt_br(custo_indireto_calculado)}", cores[7]), unsafe_allow_html=True)
        comp_cols[2].markdown(render_metric_card(f"Indiretos Obra ({p_indireto_obra:.2f}%)", f"R$ {fmt_br(custo_indireto_obra_total)}", "#ff7f0e"), unsafe_allow_html=True) # Novo card
        comp_cols[3].markdown(render_metric_card(f"Custo do Terreno ({p_terreno:.2f}%)", f"R$ {fmt_br(custo_terreno_total)}", cores[1]), unsafe_allow_html=True)
    st.divider()
    st.subheader("Indicadores por Área Construída")
    ind_cols = st.columns(4)
    ind_cols[0].markdown(render_metric_card("Terreno / Custo Total", f"{(custo_terreno_total / valor_total_despesas * 100 if valor_total_despesas > 0 else 0):.2f}%", cores[4]), unsafe_allow_html=True)
    ind_cols[1].markdown(render_metric_card("Custo Direto / m²", f"R$ {fmt_br(custo_direto_total / area_construida_total if area_construida_total > 0 else 0)}", cores[5]), unsafe_allow_html=True)
    ind_cols[2].markdown(render_metric_card("Custo Indireto / m²", f"R$ {fmt_br((custo_indireto_calculado + custo_indireto_obra_total) / area_construida_total if area_construida_total > 0 else 0)}", cores[6]), unsafe_allow_html=True)
    ind_cols[3].markdown(render_metric_card("Custo Total / m²", f"R$ {fmt_br(valor_total_despesas / area_construida_total if area_construida_total > 0 else 0)}", cores[7]), unsafe_allow_html=True)

st.divider()

# --- DEFINIÇÃO DA LÓGICA DE GERAÇÃO DA ANÁLISE ---
def generate_ai_analysis():
    """Gera a análise de viabilidade com IA e exibe o resultado."""
    # Prepara o prompt com os dados mais importantes
    prompt_data = {
        "nome_projeto": info.get('nome', 'Projeto Sem Nome'),
        "vgv_total": vgv_total,
        "custo_total": valor_total_despesas,
        "lucro_bruto": lucratividade_valor,
        "margem_lucro_percentual": lucratividade_percentual,
        "custo_direto": custo_direto_total,
        "custo_indireto_venda": custo_indireto_calculado,
        "custo_indireto_obra": custo_indireto_obra_total,
        "custo_terreno": custo_terreno_total,
        "area_privativa": info.get('area_privativa', 0),
        "area_terreno": info.get('area_terreno', 0),
        "area_construida": area_construida_total,
        "composicao_custos": {
            "Custo Direto": p_direto,
            "Custo Indireto de Venda": p_indireto_venda,
            "Custo Indireto de Obra": p_indireto_obra,
            "Custo do Terreno": p_terreno
        }
    }

    prompt = f"""
    Act as a senior real estate development viability analyst. Your task is to analyze a project's data and generate a detailed and analytical report in Portuguese.

    The report should have the following sections:
    1.  **Avaliação da Viabilidade Financeira**: Start with a paragraph summarizing the financial health of the project. Base your conclusion on the Gross Profit Margin, comparing it with market benchmarks (e.g., a margin above 15% is generally considered promising) and comment on the Gross Profit and the attractiveness of the investment.
    2.  **Análise Detalhada dos Custos**: Analyze the composition of the Total Cost. Present the absolute values and percentages of each cost type (Direct Cost, Indirect Sales Cost, Indirect Construction Cost, and Land Cost). Comment on the proportion of each cost, identifying which one represents the largest share and how this might impact the project.
    3.  **Análise de Desempenho por Área**: Provide and interpret the cost per square meter (m²) indicators for Direct Cost, Indirect Cost, and Total Cost. Comment on how competitive or high these costs are for the type of development.
    4.  **Recomendações Estratégicas**: Provide a list of 3 to 5 actionable strategic recommendations to improve the project's viability. The recommendations should be specific. For example, cite examples of where cost reduction can occur or how revenue can be increased.
    5.  **Conclusão e Próximos Passos**: A final paragraph that summarizes the analysis and offers a perspective on the next steps, such as conducting deeper market studies or starting the detailing phase.

    Below is the project data. Use it for the analysis. The values are in Brazilian Reais (R$).
    
    Project Data:
    - Name: {prompt_data['nome_projeto']}
    - VGV Total: R$ {prompt_data['vgv_total']:.2f}
    - Custo Total: R$ {prompt_data['custo_total']:.2f}
    - Lucro Bruto: R$ {prompt_data['lucro_bruto']:.2f}
    - Margem de Lucro: {prompt_data['margem_lucro_percentual']:.2f}%
    - Custo Direto: R$ {prompt_data['custo_direto']:.2f}
    - Custo Indireto de Venda: R$ {prompt_data['custo_indireto_venda']:.2f}
    - Custo Indireto de Obra: R$ {prompt_data['custo_indireto_obra']:.2f}
    - Custo do Terreno: R$ {prompt_data['custo_terreno']:.2f}
    - Área Privativa: {prompt_data['area_privativa']:.2f} m²
    - Área Construída: {prompt_data['area_construida']:.2f} m²
    - Composição do Custo (%): {prompt_data['composicao_custos']}
    """
    
    # Adiciona a exibição de loading
    with st.spinner("Gerando análise com I.A...."):
        try:
            API_KEY = st.session_state.gemini_api_key
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={API_KEY}"
            
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.5,
                    "topK": 1,
                    "topP": 1,
                    "maxOutputTokens": 2048,
                    "responseMimeType": "text/plain"
                }
            }

            headers = {'Content-Type': 'application/json'}
            
            max_retries = 5
            base_delay = 1.0
            for i in range(max_retries):
                response = requests.post(url, headers=headers, data=json.dumps(payload))
                if response.status_code == 200:
                    break
                elif response.status_code == 429 and i < max_retries - 1:
                    delay = base_delay * (2 ** i)
                    st.warning(f"Limite de taxa atingido. Tentando novamente em {delay:.1f} segundos...")
                    time.sleep(delay)
                else:
                    response.raise_for_status()
            
            if response.status_code == 200:
                result = response.json()
                if result and 'candidates' in result and len(result['candidates']) > 0 and 'content' in result['candidates'][0] and 'parts' in result['candidates'][0]['content'] and len(result['candidates'][0]['content']['parts']) > 0:
                    analysis = result['candidates'][0]['content']['parts'][0]['text']
                    return analysis
                else:
                    st.error("A I.A. não conseguiu gerar uma resposta válida. Por favor, tente novamente com dados diferentes ou ajuste o prompt.")
            else:
                st.error(f"Erro ao se comunicar com a API da I.A.: {response.status_code} - {response.text}. Tente novamente mais tarde.")

        except requests.exceptions.RequestException as e:
            st.error(f"Erro de conexão com a API da I.A.: {e}")
        except Exception as e:
            st.error(f"Ocorreu um erro inesperado: {e}")
    return None

# --- DEFINIÇÃO DO DIALOG (POP-UP) ---
@st.dialog("Análise de Viabilidade com I.A.")
def ai_analysis_dialog():
    if "ai_analysis" in st.session_state:
        st.info(st.session_state.ai_analysis)
    else:
        st.warning("Não há análise para ser exibida.")

@st.dialog("Adicionar Chave da API")
def api_key_dialog():
    st.write("Para usar a análise de I.A., por favor, insira sua chave da API do Google Gemini.")
    st.markdown("Se você não tem uma, pode obter uma [aqui](https://makersuite.google.com/app/apikey).")
    
    with st.form("api_key_form"):
        api_key = st.text_input("Chave da API", type="password")
        if st.form_submit_button("Salvar e Gerar Análise"):
            if api_key:
                st.session_state.gemini_api_key = api_key
                st.rerun()
            else:
                st.error("Por favor, insira uma chave da API.")

# Adiciona o botão de análise com IA
if st.button("Gerar Análise de Viabilidade com I.A.", type="primary"):
    if "gemini_api_key" not in st.session_state or not st.session_state.gemini_api_key:
        api_key_dialog()
    else:
        # Tenta gerar a análise
        analysis_text = generate_ai_analysis()
        if analysis_text:
            st.session_state.ai_analysis = analysis_text
            ai_analysis_dialog()

# Botão de download do relatório PDF
if st.button("Gerar e Baixar Relatório PDF", type="primary"):
    with st.spinner("Gerando seu relatório..."):
        pdf_data = generate_pdf_report(
            info, vgv_total, valor_total_despesas, lucratividade_valor, lucratividade_percentual,
            custo_direto_total, custo_indireto_calculado, custo_terreno_total, area_construida_total,
            custos_config, custos_indiretos_percentuais, pavimentos_df, custo_indireto_obra_total
        )
        st.download_button(
            label="Relatório Concluído! Clique aqui para baixar.",
            data=pdf_data,
            file_name=f"Relatorio_{info['nome']}.pdf",
            mime="application/pdf"
        )

# Para reabrir o diálogo com a análise, caso o usuário feche
if "ai_analysis" in st.session_state and st.button("Reexibir Análise de I.A."):
    ai_analysis_dialog()
