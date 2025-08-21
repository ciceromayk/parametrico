import streamlit as st
import pandas as pd

TIPOS_PAVIMENTO = [
    "Subsolo", "Térreo", "Sobressolo",
    "Lazer", "Coberta", "Pavimento Tipo"  # Alterado "Outro" para "Pavimento Tipo"
]

def main():
    st.set_page_config(page_title="Orçamento Paramétrico", layout="centered")
    st.title("Orçamento Paramétrico de Edifícios Residenciais")

    # Parâmetro de custo
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

    # Quantos pavimentos o usuário quer cadastrar?
    n = st.number_input(
        "Quantos pavimentos deseja lançar?",
        min_value=1, max_value=20, value=1, step=1
    )

    st.header("Dados dos Pavimentos")

    # Inicializa o DataFrame com n linhas
    data = {
        "Nome do Pavimento": [f"Pavimento {i+1}" for i in range(n)],
        "Tipo de Pavimento": ["Térreo" for _ in range(n)],  # Valor padrão
        "Área (m²)": [100.0 for _ in range(n)],  # Valor padrão
        "Repetição": [1 for _ in range(n)]  # Valor padrão
    }
    df = pd.DataFrame(data)

    # Editor de dados dinâmico
    edited_df = st.data_editor(  # Usando st.data_editor
        df,
        column_config={
            "Tipo de Pavimento": st.column_config.selectbox(options=TIPOS_PAVIMENTO)
        },
        num_rows="dynamic",
        use_container_width=True
    )

    # Cálculo de área
    edited_df["Área x Repetição (m²)"] = edited_df["Área (m²)"] * edited_df["Repetição"]
    total_area = edited_df["Área x Repetição (m²)"] .sum()
    budget = total_area * unit_cost

    # Resultados
    st.subheader("Resultados")
    st.write(f"- Área total (com repetições): **{total_area:,.2f} m²**")
    st.write(f"- Orçamento estimado: **R$ {budget:,.2f}**")

    st.subheader("Detalhamento por Pavimento")
    st.dataframe(edited_df, use_container_width=True)


if __name__ == "__main__":
    main()
