import streamlit as st
import pandas as pd

# Fatores de correção por tipo de pavimento (NÃO SÃO OS DA NBR 12721 - PREENCHA COM OS VALORES DA NORMA!)
FATORES_CORRECAO = {
    "Subsolo": 1.20,  # Exemplo: 20% mais caro (ver NBR 12721)
    "Térreo": 1.00,  # Custo base
    "Sobressolo": 1.05,  # Exemplo
    "Lazer": 0.90,  # Exemplo
    "Coberta": 0.80,  # Exemplo
    "Pavimento Tipo": 1.00,  # Custo base
}

TIPOS_PAVIMENTO = list(FATORES_CORRECAO.keys())  # Garante sincronia

def main():
    st.set_page_config(page_title="Orçamento Paramétrico", layout="wide")
    st.title("Orçamento Paramétrico de Edifícios Residenciais")

    # === Sidebar ===
    st.sidebar.header("Parâmetros de Cálculo")
    unit_cost = st.sidebar.number_input(
        "Custo unitário (R$/m²)",
        min_value=0.0,
        value=4500.0,
        step=100.0,
        format="%.2f"  # Formata para duas casas decimais
    )
    st.sidebar.markdown("---")
    st.sidebar.markdown("© 2025 Seu Nome ou Empresa")

    # Input de Pavimentos
    n = st.number_input(
        "Quantos pavimentos deseja lançar?",
        min_value=1, max_value=20, value=1, step=1
    )

    st.markdown("### Dados dos Pavimentos")
    cols = st.columns([2, 2, 1, 1])
    cols[0].markdown("**Nome do Pavimento**")
    cols[1].markdown("**Tipo de Pavimento**")
    cols[2].markdown("**Área (m²)**")
    cols[3].markdown("**Repetição**")

    nomes = []
    tipos = []
    areas = []
    reps = []

    for i in range(1, n + 1):
        c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
        nome = c1.text_input("", value=f"Pavimento {i}", key=f"nome_{i}")
        tipo = c2.selectbox("", TIPOS_PAVIMENTO, key=f"tipo_{i}")
        area = c3.number_input(
            "",
            value=100.0,
            min_value=0.0,  # Validação: área não pode ser negativa
            step=1.0,
            format="%.2f",  # Formata para duas casas decimais
            key=f"area_{i}",
        )
        rep = c4.number_input(
            "",
            value=1,
            min_value=1,  # Validação: repetição deve ser pelo menos 1
            step=1,
            key=f"rep_{i}",
        )

        nomes.append(nome)
        tipos.append(tipo)
        areas.append(area)
        reps.append(rep)

    # DataFrame
    df = pd.DataFrame(
        {
            "Nome do Pavimento": nomes,
            "Tipo de Pavimento": tipos,
            "Área (m²)": areas,
            "Repetição": reps,
        }
    )

    # Aplica os fatores de correção
    df["Fator de Correção"] = df["Tipo de Pavimento"].map(FATORES_CORRECAO)
    df["Área Corrigida (m²)"] = (
        df["Área (m²)"] * df["Fator de Correção"] * df["Repetição"]
    )

    # Cálculo do orçamento
    total_area = df["Área Corrigida (m²)"] .sum()
    budget = total_area * unit_cost

    # Resultados
    st.markdown("## Resultados")
    st.write(f"- **Área total corrigida:** {total_area:,.2f} m²")  # Formatação
    st.write(f"- **Orçamento estimado:** R$ {budget:,.2f}")  # Formatação

    st.markdown("## Detalhamento por Pavimento")
    st.dataframe(df, use_container_width=True)

    # Download do DataFrame
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="orcamento_pavimentos.csv",
        mime="text/csv",
    )


if __name__ == "__main__":
    main()
