# pages/3_Resultados_e_Indicadores.py
import streamlit as st
import pandas as pd
from utils import *
import json
import requests
import time

st.set_page_config(page_title="Resultados e Indicadores", layout="wide")

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

# Adiciona o botão de análise com IA
if st.button("Gerar Análise de Viabilidade com I.A.", type="primary"):
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
        "area_construida": area_construida_total
    }

    prompt = f"""
    Aja como um analista de viabilidade de empreendimentos imobiliários sênior.
    Sua tarefa é analisar os dados de um projeto e gerar um relatório conciso, em português, com as seguintes seções:
    1.  **Resumo da Viabilidade**: Um parágrafo inicial que resume a saúde financeira do projeto, indicando se é viável, promissor ou de alto risco. Use a margem de lucro como principal indicador.
    2.  **Análise de Desempenho**: Um parágrafo que detalha a performance do projeto, destacando os pontos fortes e fracos. Compare o VGV com o Custo Total e comente sobre o Lucro Bruto e a Margem de Lucro.
    3.  **Recomendações Chave**: Uma lista com 3 a 5 recomendações acionáveis para melhorar a viabilidade do projeto. Pense em estratégias para aumentar a receita (VGV) ou reduzir custos.
    
    Abaixo estão os dados do projeto. Utilize-os para a análise. Os valores estão em Reais (R$).
    
    Dados do Projeto:
    - Nome: {prompt_data['nome_projeto']}
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
    """
    
    # Adiciona a exibição de loading
    with st.spinner("Gerando análise com I.A...."):
        try:
            # Configuração do API do Gemini
            # Verifica se a chave da API está disponível no ambiente
            API_KEY = "AIzaSyB442-xfQtfJWm2wFR6jbeiqAWtHNUu3WM"
            if 'GEMINI_API_KEY' in st.secrets:
                API_KEY = st.secrets['GEMINI_API_KEY']
            
            if not API_KEY:
                st.error("Chave da API não encontrada. Por favor, adicione sua chave Gemini API na configuração do Streamlit (st.secrets).")
            else:
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

                headers = {
                    'Content-Type': 'application/json',
                }
                
                # Tentar a chamada da API com backoff exponencial
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
                
                if response.status_code != 200:
                    st.error("Erro ao se comunicar com a API da I.A. Tente novamente mais tarde.")
                else:
                    analysis = response.json()['candidates'][0]['content']['parts'][0]['text']
                    st.session_state.ai_analysis = analysis

        except requests.exceptions.RequestException as e:
            st.error(f"Erro de conexão com a API da I.A.: {e}")
        except KeyError:
            st.error("Erro ao processar a resposta da I.A. O formato da resposta não é o esperado.")
        except Exception as e:
            st.error(f"Ocorreu um erro inesperado: {e}")

# Exibe o resultado da análise se ela existir na session_state
if "ai_analysis" in st.session_state:
    st.markdown("---")
    st.subheader("🤖 Análise de Viabilidade com I.A.")
    st.info(st.session_state.ai_analysis)

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
