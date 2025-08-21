import streamlit as st
import pandas as pd

# -------------------------------------------------------------------
# 1) Dicionário de tipos de pavimento + intervalo de coeficientes
#    (baseado na NBR 12721 – item 5.7.3)
TIPOS_PAVIMENTO = {
    "Garagem (Subsolo)":             (0.50, 0.75),
    "Área Privativa (Autônoma)":     (1.00, 1.00),
    "Salas com Acabamento":          (1.00, 1.00),
    "Salas sem Acabamento":          (0.75, 0.90),
    "Loja sem Acabamento":           (0.40, 0.60),
    "Varandas":                      (0.75, 1.00),
    "Terraços / Áreas Descobertas":  (0.30, 0.60),
    "Estacionamento (terreno)":      (0.05, 0.10),
    "Projeção Terreno sem Benf.":    (0.00, 0.00),
    "Serviço (unifam. baixa, aberta)": (0.50, 0.50),
    "Barrilete":                     (0.50, 0.75),
    "Caixa D'água":                  (0.50, 0.75),
    "Casa de Máquinas":              (0.50, 0.75),
    "Piscinas":                      (0.50, 0.75),
    "Quintais / Calçadas / Jardins": (0.10, 0.30),
}

# -------------------------------------------------------------------
def main():
    st.set_page_config(page_title="Orçamento Paramétrico", layout="wide")

    # === TELA INICIAL: cadastro do projeto ===
    if "projeto_info" not in st.session_state:
        st.title("📐 Orçamento Paramétrico de Edifícios Residenciais")
        st.markdown("### Informações do Projeto")
        projeto_nome   = st.text_input("Nome do Projeto")
        area_terreno   = st.number_input("Área do Terreno (m²)", min_value=0.0, format="%.2f")
        endereco       = st.text_area("Endereço")
        num_pavimentos = st.number_input(
            "Número de Pavimentos", min_value=1, max_value=50, value=1, step=1
        )

        if st.button("✅ Salvar Projeto"):
            st.session_state.projeto_info = {
                "nome": projeto_nome,
                "area_terreno": area_terreno,
                "endereco": endereco,
                "num_pavimentos": int(num_pavimentos)
            }
            st.experimental_rerun()

    # === TELA DE ORÇAMENTO: depois que o projeto estiver salvo ===
    else:
        info = st.session_state.projeto_info
        st.title("📐 Orçamento Paramétrico de Edifícios Residenciais")
        st.header("🔍 Informações do Projeto")
        st.write(f"**Nome:** {info['nome']}")
        st.write(f"**Área do Terreno:** {info['area_terreno']:,.2f} m²")
        st.write(f"**Endereço:** {info['endereco']}")
        st.write(f"**Pavimentos:** {info['num_pavimentos']}")

        # Sidebar: custo unitário
        st.sidebar.header("⚙️ Parâmetros de Cálculo")
        unit_cost = st.sidebar.number_input(
            "Custo unitário (R$/m²)",
            min_value=0.0,
            value=4500.0,
            step=100.0,
            format="%.2f"
        )
        st.sidebar.markdown("---")
        st.sidebar.markdown("© 2025 Sua Empresa")

        # --- Entrada dos pavimentos ---
        n = info["num_pavimentos"]
        st.markdown("### 🏢 Dados dos Pavimentos")

        # cabeçalho
        h1, h2, h3, h4 = st.columns([2, 2, 1, 1])
        h1.markdown("**Tipo de Pavimento**")
        h2.markdown("**Coeficiente**")
        h3.markdown("**Área (m²)**")
        h4.markdown("**Repetição**")

        tipos, coefs, areas, reps = [], [], [], []

        for i in range(1, n + 1):
            c1, c2, c3, c4 = st.columns([2, 2, 1, 1])

            # 1) seleção do tipo
            tipo = c1.selectbox(
                label=f"", options=list(TIPOS_PAVIMENTO.keys()), key=f"tipo_{i}"
            )

            # 2) ajuste do coeficiente no mesmo fluxo
            min_c, max_c = TIPOS_PAVIMENTO[tipo]
            coef = c2.slider(
                label="",
                min_value=min_c,
                max_value=max_c,
                value=(min_c + max_c) / 2,
                step=0.01,
                format="%.2f",
                key=f"coef_{i}"
            )

            # 3) área
            area = c3.number_input(
                label="",
                value=100.0,
                min_value=0.0,
                step=1.0,
                format="%.2f",
                key=f"area_{i}"
            )

            # 4) repetição
            rep = c4.number_input(
                label="",
                value=1,
                min_value=1,
                step=1,
                key=f"rep_{i}"
            )

            tipos.append(tipo)
            coefs.append(coef)
            areas.append(area)
            reps.append(rep)

        # monta DataFrame
        df = pd.DataFrame({
            "Tipo de Pavimento": tipos,
            "Coeficiente": coefs,
            "Área (m²)": areas,
            "Repetição": reps
        })
        df["Área Equivalente (m²)"] = (
            df["Área (m²)"] * df["Coeficiente"] * df["Repetição"]
        )

        # cálculo final
        total_eq = df["Área Equivalente (m²)"].sum()
        budget   = total_eq * unit_cost

        # resultados
        st.markdown("## 📊 Resultados")
        st.write(f"- **Área equivalente total:** {total_eq:,.2f} m²")
        st.write(f"- **Orçamento estimado:** R$ {budget:,.2f}")

        st.markdown("### 📋 Detalhamento por Pavimento")
        st.dataframe(df, use_container_width=True)

        # botão de download
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Baixar CSV",
            data=csv,
            file_name="orcamento_parametrico.csv",
            mime="text/csv"
        )


if __name__ == "__main__":
    main()
