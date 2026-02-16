import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# =========================================================
# CONFIGURAÇÃO DA PÁGINA
# =========================================================
st.set_page_config(page_title="Chef Digital Cloud", page_icon="🍳", layout="wide")
st.title("👨‍🍳 Chef Digital Cloud")

# =========================================================
# CSS PROFISSIONAL
# =========================================================
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display:none;}
.block-container {padding-top: 2rem;}
button[kind="secondary"] {
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# CONEXÃO GOOGLE SHEETS
# =========================================================
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1hfVSL4PwUk2OdVl4On-xtzzxfdWj5QEj52qsXxYsvgs/edit?usp=sharing"

conn = st.connection("gsheets", type=GSheetsConnection)

COLUNAS = [
    "nome",
    "categoria",
    "ingredientes",
    "preparo",
    "video",
    "favorito"
]

def carregar_dados():
    try:
        df = conn.read(spreadsheet=URL_PLANILHA, ttl=0)
        for col in COLUNAS:
            if col not in df.columns:
                df[col] = ""
        return df
    except:
        return pd.DataFrame(columns=COLUNAS)

def salvar_dados(df):
    conn.update(spreadsheet=URL_PLANILHA, data=df)

df = carregar_dados()

# =========================================================
# SESSION STATE
# =========================================================
if "receita_selecionada" not in st.session_state:
    st.session_state.receita_selecionada = None

if "modo_edicao" not in st.session_state:
    st.session_state.modo_edicao = False

# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.title("📌 Navegação")
menu = st.sidebar.radio(
    "Ir para:",
    ["📖 Ver Receitas", "➕ Nova Receita", "🛒 Lista de Compras"]
)

LISTA_CATEGORIAS = ["Bolos", "Pães", "Roscas", "Outros"]

# =========================================================
# NOVA RECEITA
# =========================================================
if menu == "➕ Nova Receita":

    st.header("Cadastrar Nova Receita")

    with st.form("nova_receita"):
        nome = st.text_input("Nome da Receita")
        categoria = st.selectbox("Categoria", LISTA_CATEGORIAS)
        video = st.text_input("Link do Vídeo")
        ingredientes = st.text_area("Ingredientes (1 por linha)")
        preparo = st.text_area("Modo de Preparo")

        if st.form_submit_button("💾 Salvar Receita"):

            if nome and ingredientes:

                nova = pd.DataFrame([{
                    "nome": nome,
                    "categoria": categoria,
                    "ingredientes": ingredientes,
                    "preparo": preparo,
                    "video": video,
                    "favorito": False
                }])

                df_final = pd.concat([df, nova], ignore_index=True)
                salvar_dados(df_final)

                st.success("Receita salva com sucesso!")
                st.balloons()

            else:
                st.error("Preencha nome e ingredientes!")

# =========================================================
# VER RECEITAS (PROFISSIONAL)
# =========================================================
elif menu == "📖 Ver Receitas":

    st.header("Minhas Receitas")

    if df.empty:
        st.info("Nenhuma receita cadastrada.")
    else:

        # FILTROS
        busca = st.sidebar.text_input("🔎 Buscar receita")
        somente_favoritos = st.sidebar.checkbox("⭐ Apenas Favoritos")

        categorias = sorted(df["categoria"].dropna().unique())
        filtro_categoria = st.sidebar.multiselect(
            "Filtrar Categoria",
            categorias,
            default=categorias
        )

        df_filtrado = df[df["categoria"].isin(filtro_categoria)]

        if busca:
            df_filtrado = df_filtrado[
                df_filtrado["nome"].str.contains(busca, case=False, na=False)
            ]

        if somente_favoritos:
            df_filtrado = df_filtrado[df_filtrado["favorito"] == True]

        col_lista, col_receita = st.columns([1, 2])

        # =================================================
        # LISTA CLICÁVEL
        # =================================================
        with col_lista:
            st.subheader("Receitas")

            for _, row in df_filtrado.iterrows():

                label = f"⭐ {row['nome']}" if row["favorito"] else row["nome"]

                if st.button(label, key=row["nome"]):
                    st.session_state.receita_selecionada = row["nome"]
                    st.session_state.modo_edicao = False

        # =================================================
        # EXIBIÇÃO
        # =================================================
        with col_receita:

            if st.session_state.receita_selecionada:

                rec = df[df["nome"] == st.session_state.receita_selecionada].iloc[0]

                if not st.session_state.modo_edicao:

                    st.subheader(f"{rec['nome']}  |  {rec['categoria']}")
                    st.divider()

                    st.markdown("### 🛒 Ingredientes")
                    for ing in str(rec["ingredientes"]).split("\n"):
                        if ing.strip():
                            st.write(f"⬜ {ing.strip()}")

                    st.markdown("### 👨‍🍳 Preparo")
                    st.info(rec["preparo"])

                    if rec["video"]:
                        st.link_button("📺 Assistir Vídeo", rec["video"])
                        if "youtube" in rec["video"]:
                            st.video(rec["video"])

                    col1, col2, col3 = st.columns(3)

                    # FAVORITO
                    with col1:
                        if st.button("⭐ Favoritar / Desfavoritar"):
                            df.loc[df["nome"] == rec["nome"], "favorito"] = not rec["favorito"]
                            salvar_dados(df)
                            st.rerun()

                    # EDITAR
                    with col2:
                        if st.button("✏️ Editar"):
                            st.session_state.modo_edicao = True
                            st.rerun()

                    # EXCLUIR
                    with col3:
                        if st.button("🗑️ Excluir"):
                            df_novo = df[df["nome"] != rec["nome"]]
                            salvar_dados(df_novo)
                            st.session_state.receita_selecionada = None
                            st.success("Receita excluída!")
                            st.rerun()

                # =================================================
                # MODO EDIÇÃO
                # =================================================
                else:

                    st.subheader("Editando Receita")

                    with st.form("editar_receita"):

                        novo_nome = st.text_input("Nome", rec["nome"])
                        nova_categoria = st.selectbox(
                            "Categoria",
                            LISTA_CATEGORIAS,
                            index=LISTA_CATEGORIAS.index(rec["categoria"])
                        )
                        novo_video = st.text_input("Vídeo", rec["video"])
                        novos_ingredientes = st.text_area("Ingredientes", rec["ingredientes"])
                        novo_preparo = st.text_area("Preparo", rec["preparo"])

                        col_salvar, col_cancelar = st.columns(2)

                        salvar_btn = col_salvar.form_submit_button("💾 Salvar")
                        cancelar_btn = col_cancelar.form_submit_button("Cancelar")

                        if salvar_btn:

                            df.loc[df["nome"] == rec["nome"]] = [
                                novo_nome,
                                nova_categoria,
                                novos_ingredientes,
                                novo_preparo,
                                novo_video,
                                rec["favorito"]
                            ]

                            salvar_dados(df)

                            st.session_state.modo_edicao = False
                            st.session_state.receita_selecionada = novo_nome

                            st.success("Receita atualizada!")
                            st.rerun()

                        if cancelar_btn:
                            st.session_state.modo_edicao = False
                            st.rerun()

# =========================================================
# LISTA DE COMPRAS
# =========================================================
elif menu == "🛒 Lista de Compras":

    st.header("Gerador de Lista de Compras")

    if df.empty:
        st.info("Adicione receitas primeiro.")
    else:

        selecionadas = []

        for nome in df["nome"]:
            if st.checkbox(nome):
                selecionadas.append(nome)

        if selecionadas:

            receitas = df[df["nome"].isin(selecionadas)]

            lista_total = []
            for texto in receitas["ingredientes"]:
                lista_total.extend(str(texto).split("\n"))

            lista_limpa = sorted(
                list(set([i.strip().capitalize() for i in lista_total if i.strip()]))
            )

            st.subheader("Sua Lista Final")

            texto_download = ""

            for item in lista_limpa:
                st.write(f"⬜ {item}")
                texto_download += f"- {item}\n"

            st.download_button(
                "📥 Baixar Lista",
                texto_download,
                "lista_compras.txt"
            )
