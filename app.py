import streamlit as st
import pandas as pd

def main():
    st.set_page_config(page_title="Orçamento Paramétrico", layout="centered")
    st.title("Orçamento Paramétrico de Edifícios Residenciais")

    # Sidebar: custo unitário por m²
    st.sidebar.header("Parâmetros de Cálculo")
    unit_cost = st.sidebar.number_input(
        "Custo unitário (R$/m²)",
        min_value=0.0,
        value=4500.0,
        step=100.0,
        format="%.2f"
    )
    st.sidebar.markdown("---")
    st.sidebar.markdown("© 2025 Seu Nome ou Empresa")

    # Seção de dados dos pavimentos
    st.header("Dados dos Pavimentos")
    st.markdown("Preencha a tabela abaixo com os pavimentos do projeto:")

    # Dados iniciais da tabela
    default_data = {
        "Nome do Pavimento": ["Térreo"],
        "Tipo de Pavimento": ["Térreo"],  # Opções: Subsolo, Térreo, Sobressolo, Lazer, Coberta, etc.
        "Área (m²)": [100.0],
        "Repetição": [1]
    }
    df = pd.DataFrame(default_data)

    # Editor de dados dinâmico
    edited_df = st.experimental_data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True
    )

    # Cálculo de área considerando repetições
    edited_df["Área x Repetição (m²)"] = (
        edited_df["Área (m²)"] * edited_df["Repetição"]
    )

    # Cálculo do orçamento
    total_area = edited_df["Área x Repetição (m²)"].sum()
    budget = total_area * unit_cost

    # Exibição de resultados
    st.subheader("Resultados")
    st.write(f"Área total (com repetições): **{total_area:,.2f} m²**")
    st.write(f"Orçamento estimado: **R$ {budget:,.2f}**")

    # Detalhamento por pavimento
    st.subheader("Detalhamento por Pavimento")
    st.dataframe(
        edited_df[[
            "Nome do Pavimento",
            "Tipo de Pavimento",
            "Área (m²)",
            "Repetição",
            "Área x Repetição (m²)"
        ]],
        use_container_width=True
    )

if __name__ == "__main__":
    main()
