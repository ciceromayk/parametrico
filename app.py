import json
import streamlit as st
import pandas as pd
from pathlib import Path

# --- Carregamento dos parâmetros de custo ---
@st.cache_data
def load_cost_params(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

# --- Função de cálculo de área equivalente ---
def compute_equivalent_area(area_m2: float, floors: int, factor: float) -> float:
    """
    area_m2: área construída base em m²
    floors: número de pavimentos
    factor: fator de área equivalente (ajuste por padrão/conceito)
    """
    # Exemplo de refinamento: penalizar/descontar por pavimentos extras
    piso_penalty = 1 + (floors - 1) * 0.02  # +2% de custo para cada pavimento extra
    return area_m2 * factor * piso_penalty

# --- Função de cálculo de orçamento ---
def estimate_budget(area_eq: float, unit_cost: float) -> float:
    return area_eq * unit_cost

# --- Streamlit App ---
def main():
    st.set_page_config(page_title="Orçamento Paramétrico", layout="centered")
    st.title("Orçamento Paramétrico de Edifícios Residenciais")

    # Carregar parâmetros
    data_dir = Path(__file__).parent / "data"
    params = load_cost_params(str(data_dir / "cost_parameters.json"))

    # Sidebar: entrada de parâmetros
    st.sidebar.header("Dados do Projeto")
    floors    = st.sidebar.number_input("Número de pavimentos", min_value=1, max_value=50, value=2, step=1)
    area_m2   = st.sidebar.number_input("Área construída (m²)", min_value=10.0, value=100.0, step=5.0, format="%.1f")
    standard  = st.sidebar.selectbox("Padrão de Acabamento", list(params.keys()), index=0)

    # Botão para calcular
    if st.sidebar.button("Calcular Orçamento"):
        p = params[standard]
        area_eq = compute_equivalent_area(area_m2, floors, p["equivalent_area_factor"])
        budget  = estimate_budget(area_eq, p["unit_cost_per_m2"])

        # Exibir resultados
        st.subheader("Resultados")
        st.write(f"Área equivalente: **{area_eq:,.2f} m²**")
        st.write(f"Custo unitário (m²): **R$ {p['unit_cost_per_m2']:,.2f}**")
        st.write(f"Orçamento estimado: **R$ {budget:,.2f}**")

        # Detalhamento em tabela
        df = pd.DataFrame({
            "Descrição": ["Área base (m²)", "Fator equiv.", "Piso penalty", "Área equivalente (m²)", "Custo unitário (R$/m²)", "Orçamento (R$)"],
            "Valor": [area_m2, p["equivalent_area_factor"], 1 + (floors - 1)*0.02, area_eq, p["unit_cost_per_m2"], budget]
        })
        st.table(df)

    st.sidebar.markdown("---")
    st.sidebar.markdown("© 2025 Seu Nome ou Empresa")

if __name__ == "__main__":
    main()
