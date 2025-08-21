import streamlit as st
import pandas as pd

# Tipos de pavimento e seus coeficientes (NBR 12721 - PREENCHA COM OS VALORES DA NORMA)
TIPOS_PAVIMENTO = {
    "Garagem (Subsolo)": (0.50, 0.75),
    "Área Privativa (Unidade Autônoma Padrão)": (1.00, 1.00),
    "Área Privativa (Salas com Acabamento)": (1.00, 1.00),
    "Área Privativa (Salas sem Acabamento)": (0.75, 0.90),
    "Área de Loja sem Acabamento": (0.40, 0.60),
    "Varandas": (0.75, 1.00),
    "Terraços ou Áreas Descobertas sobre Lajes": (0.30, 0.60),
    "Estacionamento sobre Terreno": (0.05, 0.10),
    "Área de Projeção do Terreno sem Benfeitoria": (0.00, 0.00),
    "Área de Serviço - Residência Unifamiliar Padrão Baixo (Aberta)": (0.50, 0.50),
    "Barrilete": (0.50, 0.75),
    "Caixa D'água": (0.50, 0.75),
    "Casa de Máquinas": (0.50, 0.75),
    "Piscinas": (0.50, 0.75),
    "Quintais, Calçadas, Jardins etc.": (0.10, 0.30),
}

def main():
    st.set_page_config(page_title="Orçamento Paramétrico", layout="wide")

    # === Tela Inicial ===
    if "projeto_info" not in st.session_state:
        st.title("Orçamento Paramétrico de Edifícios Residenciais")
        st.markdown("## Informações do Projeto")

        projeto_nome = st.text_input("Nome do Projeto")
        area_terreno = st.number_input("Área do Terreno (m²)", min_value=0.0, format="%.2f")
        endereco = st.text_area("Endereço")
        num_pavimentos = st.number_input("Número Total de Pavimentos", min_value=1, max_value=50, value=1)

        if st.button("Salvar Informações do Projeto"):
            st.session_state.projeto_info = {
                "nome": projeto_nome,
                "area_terreno": area_terreno,
                "endereco": endereco,
                "num_pavimentos": num_pavimentos
            }
            st.rerun()  # Recarrega a página para mostrar a próxima tela

    else:
        # === Tela de Orçamento ===
        st.title("Orçamento Paramétrico de Edifícios Residenciais")
        st.header("Informações do Projeto")
        st.write(f"**Nome do Projeto:** {st.session_state.projeto_info['nome']}")
        st.write(f"**Área do Terreno:** {st.session_state.projeto_info['area_terreno']:,.2f} m²")
        st.write(f"**Endereço:** {st.session_state.projeto_info['endereco']}")
        st.write(f"**Número Total de Pavimentos:** {st.session_state.projeto_info['num_pavimentos']}")

        # Sidebar: custo unitário
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

        # Input de Pavimentos
        n = st.session_state.projeto_info['num_pavimentos']  # Usa número da tela inicial

        st.markdown("### Dados dos Pavimentos")
        cols = st.columns([2, 2, 1])  # Removido "Nome do Pavimento"
        cols[0].markdown("**Tipo de Pavimento**")
        cols[1].markdown("**Área (m²)**")
        cols[2].markdown("**Repetição**")

        tipos = []
        areas = []
        reps = []
        coeficientes = []  # Para armazenar os coeficientes ajustados

        for i in range(1, n + 1):
            c1, c2, c3 = st.columns([2, 2, 1])  # Removido input de nome

            # Dropdown com os tipos de pavimento
            tipo = c1.selectbox("", list(TIPOS_PAVIMENTO.keys()), key=f"tipo_{i}")

            # Slider para ajustar o coeficiente dentro do intervalo
            min_coef, max_coef = TIPOS_PAVIMENTO[tipo]
            coeficiente = c1.slider(
                "Ajuste o Coeficiente",
                min_value=min_coef,
                max_value=max_coef,
                value=(min_coef + max_coef) / 2,  # Valor inicial no meio do intervalo
                step=0.01,
                key=f"coef_{i}",
            )

            area = c2.number_input(
                "",
                value=100.0,
                min_value=0.0,
                step=1.0,
                format="%.2f",
                key=f"area_{i}",
            )
            rep = c3.number_input(
                "",
                value=1,
                min_value=1,
                step=1,
                key=f"rep_{i}",
            )

            tipos.append(tipo)
            areas.append(area)
            reps.append(rep)
            coeficientes.append(coeficiente)  # Armazena o coeficiente ajustado

        # DataFrame
        df = pd.DataFrame(
            {
                "Tipo de Pavimento": tipos,
                "Área (m²)": areas,
                "Repetição": reps,
                "Coeficiente": coeficientes  # Inclui os coeficientes ajustados
            }
        )

        # Aplica os coeficientes
        df["Área Equivalente (m²)"] = df["Área (m²)"] * df["Coeficiente"] * df["Repetição"]

        # Cálculo do orçamento
        total_area = df["Área Equivalente (m²)"] .sum()
        budget = total_area * unit_cost

        # Resultados
        st.markdown("## Resultados")
        st.write(f"- **Área total equivalente:** {total_area:,.2f} m²")
        st.write(f"- **Orçamento estimado:** R$ {budget:,.2f}")

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
