import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Chef Digital Cloud", page_icon="🍳", layout="centered")
st.title("👨‍🍳 Meu Livro de Receitas Cloud")

# --- CONEXÃO COM GOOGLE SHEETS ---
# Aqui o Streamlit usa o link que você forneceu
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1hfVSL4PwUk2OdVl4On-xtzzxfdWj5QEj52qsXxYsvgs/edit?usp=sharing"

conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        # ttl=0 garante que ele busque dados novos toda vez que carregar
        return conn.read(spreadsheet=URL_PLANILHA, ttl=0)
    except:
        return pd.DataFrame(columns=["nome", "categoria", "ingredientes", "preparo", "video"])

def salvar_dados(df_atualizado):
    conn.update(spreadsheet=URL_PLANILHA, data=df_atualizado)

# Carregando os dados
df = carregar_dados()

# --- NAVEGAÇÃO LATERAL ---
st.sidebar.title("📌 Navegação")
menu = st.sidebar.radio("Ir para:", ["Ver Receitas", "Adicionar Nova", "Gerar Lista de Compras"])

LISTA_CATEGORIAS = ["Bolos", "Pães", "Roscas", "Outros"]

# --- LÓGICA: ADICIONAR NOVA ---
if menu == "Adicionar Nova":
    st.header("📝 Cadastrar Receita")
    
    with st.form("nova_receita"):
        nome = st.text_input("Nome da Receita")
        categoria = st.selectbox("Categoria", LISTA_CATEGORIAS)
        link_video = st.text_input("Link do Vídeo (Insta/TikTok/YouTube)")
        ingredientes = st.text_area("Ingredientes (um por linha)")
        preparo = st.text_area("Modo de Preparo")
        
        if st.form_submit_button("💾 Salvar na Nuvem"):
            if nome and ingredientes:
                # Criar nova linha no formato de DataFrame
                nova_linha = pd.DataFrame([{
                    "nome": nome,
                    "categoria": categoria,
                    "ingredientes": ingredientes, # Mantemos como texto para o Sheets
                    "preparo": preparo,
                    "video": link_video
                }])
                
                # Adicionar ao DataFrame existente
                df_final = pd.concat([df, nova_linha], ignore_index=True)
                salvar_dados(df_final)
                st.success(f"Receita '{nome}' salva com sucesso!")
                st.balloons()
            else:
                st.error("Preencha o nome e os ingredientes!")

# --- LÓGICA: VER RECEITAS ---
elif menu == "Ver Receitas":
    st.header("📖 Minhas Receitas")
    
    if df.empty:
        st.info("O livro está vazio.")
    else:
        categorias_existentes = sorted(df['categoria'].unique().tolist())
        filtro = st.sidebar.multiselect("Filtrar Categoria:", categorias_existentes, default=categorias_existentes)
        
        df_filtrado = df[df['categoria'].isin(filtro)]
        
        if not df_filtrado.empty:
            escolha = st.selectbox("Selecione a receita:", df_filtrado['nome'].tolist())
            rec = df_filtrado[df_filtrado['nome'] == escolha].iloc[0]
            
            st.divider()
            st.subheader(f"{escolha} | ✨ {rec['categoria']}")
            
            # Layout otimizado para celular (uma coluna embaixo da outra)
            st.write("**🛒 Ingredientes:**")
            for ing in rec['ingredientes'].split('\n'):
                if ing.strip():
                    st.write(f"⬜ {ing.strip()}")
            
            st.write("**👨‍🍳 Preparo:**")
            st.info(rec['preparo'])
            
            if rec['video']:
                st.link_button("📺 Ver Vídeo", rec['video'])
                if "youtube.com" in rec['video'] or "youtu.be" in rec['video']:
                    st.video(rec['video'])
            
            st.divider()
            if st.button("🗑️ Excluir esta Receita"):
                df_novo = df[df['nome'] != escolha]
                salvar_dados(df_novo)
                st.warning("Receita removida!")
                st.rerun()
        else:
            st.warning("Nenhuma receita encontrada.")

# --- LÓGICA: LISTA DE COMPRAS ---
elif menu == "Gerar Lista de Compras":
    st.header("🛒 Gerador de Compras")
    if df.empty:
        st.info("Adicione receitas primeiro.")
    else:
        selecionadas = []
        for r in df['nome'].tolist():
            if st.checkbox(r, key=f"check_{r}"):
                selecionadas.append(r)
        
        if selecionadas:
            st.subheader("📋 Sua Lista:")
            todas_linhas = df[df['nome'].isin(selecionadas)]
            
            lista_total = []
            for ing_texto in todas_linhas['ingredientes']:
                lista_total.extend(ing_texto.split('\n'))
            
            lista_limpa = sorted(list(set([i.strip().capitalize() for i in lista_total if i.strip()])))
            
            texto_lista = ""
            for item in lista_limpa:
                st.write(f"⬜ {item}")
                texto_lista += f"- {item}\n"
            
            st.download_button("📩 Baixar Lista em TXT", texto_lista, "lista_compras.txt")