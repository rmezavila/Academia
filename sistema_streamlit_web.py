import streamlit as st
import sqlite3
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import os
import random

# ==============================================
# CONFIGURAÇÃO DA PÁGINA
# ==============================================
st.set_page_config(
    page_title="Sistema de Academia",
    page_icon="💪",
    layout="wide"
)

# ==============================================
# BANCO DE DADOS
# ==============================================
def criar_banco():
    conn = sqlite3.connect("academia_web.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS alunos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        cpf TEXT,
        telefone TEXT,
        endereco TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS pagamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        aluno_id INTEGER,
        valor REAL NOT NULL,
        data_pagamento TEXT NOT NULL,
        referencia TEXT,
        numero_recibo TEXT UNIQUE,
        FOREIGN KEY(aluno_id) REFERENCES alunos(id)
    )""")
    conn.commit()
    conn.close()

def carregar_alunos():
    conn = sqlite3.connect("academia_web.db")
    c = conn.cursor()
    c.execute("SELECT id, nome, cpf, telefone FROM alunos ORDER BY nome")
    dados = c.fetchall()
    conn.close()
    return dados

def cadastrar_aluno(nome, cpf, telefone, endereco):
    conn = sqlite3.connect("academia_web.db")
    c = conn.cursor()
    c.execute("INSERT INTO alunos (nome, cpf, telefone, endereco) VALUES (?,?,?,?)",
              (nome, cpf, telefone, endereco))
    conn.commit()
    conn.close()

def buscar_aluno(aluno_id):
    conn = sqlite3.connect("academia_web.db")
    c = conn.cursor()
    c.execute("SELECT nome, cpf FROM alunos WHERE id=?", (aluno_id,))
    dados = c.fetchone()
    conn.close()
    return dados

def registrar_pagamento(aluno_id, valor, data_pag, referencia, numero_recibo):
    conn = sqlite3.connect("academia_web.db")
    c = conn.cursor()
    c.execute("""INSERT INTO pagamentos (aluno_id, valor, data_pagamento, referencia, numero_recibo)
                 VALUES (?,?,?,?,?)""", (aluno_id, valor, data_pag, referencia, numero_recibo))
    conn.commit()
    conn.close()

def listar_pagamentos():
    conn = sqlite3.connect("academia_web.db")
    c = conn.cursor()
    c.execute("""SELECT p.numero_recibo, a.nome, p.valor, p.data_pagamento, p.referencia
                 FROM pagamentos p JOIN alunos a ON p.aluno_id = a.id
                 ORDER BY p.data_pagamento DESC""")
    dados = c.fetchall()
    conn.close()
    return dados

# ==============================================
# GERAR RECIBO PDF
# ==============================================
def gerar_recibo_pdf(nome_aluno, cpf, valor, data, referencia, numero_recibo):
    if not os.path.exists("recibos"):
        os.makedirs("recibos")
    
    filename = f"recibos/recibo_{numero_recibo}.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    largura, altura = A4

    # Cabeçalho
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(largura/2, altura - 80, "ACADEMIA")
    c.setFont("Helvetica", 12)
    c.drawCentredString(largura/2, altura - 110, "CNPJ: ___.___.___/____-__ | Rua ______, ___, Cidade - RJ")
    c.drawCentredString(largura/2, altura - 130, "Telefone: (21) ____-____")

    c.line(50, altura - 150, largura - 50, altura - 150)

    # Título
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(largura/2, altura - 190, "RECIBO DE PAGAMENTO")
    c.setFont("Helvetica", 12)
    c.drawRightString(largura - 60, altura - 190, f"Nº: {numero_recibo}")

    # Dados
    y = altura - 240
    c.setFont("Helvetica-Bold", 12)
    c.drawString(60, y, "Cliente:")
    c.setFont("Helvetica", 12)
    c.drawString(140, y, nome_aluno)
    y -= 25
    c.setFont("Helvetica-Bold", 12)
    c.drawString(60, y, "CPF:")
    c.setFont("Helvetica", 12)
    c.drawString(100, y, cpf or "Não informado")
    y -= 25
    c.setFont("Helvetica-Bold", 12)
    c.drawString(60, y, "Referência:")
    c.setFont("Helvetica", 12)
    c.drawString(150, y, referencia)
    y -= 25
    c.setFont("Helvetica-Bold", 12)
    c.drawString(60, y, "Data:")
    c.setFont("Helvetica", 12)
    c.drawString(100, y, data)
    y -= 40

    # Valor
    c.setFont("Helvetica-Bold", 14)
    c.drawString(60, y, "Valor Recebido:")
    c.setFont("Helvetica-Bold", 22)
    c.drawString(200, y, f"R$ {valor:.2f}")
    y -= 50

    # Assinatura
    c.line(60, y, 300, y)
    c.drawString(60, y - 20, "Assinatura / Carimbo")
    y -= 60
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(60, y, "Observação: Este recibo substitui a nota fiscal provisoriamente.")
    c.drawString(60, y - 15, "Para emissão de NFS-e oficial, utilize o portal da prefeitura.")

    c.showPage()
    c.save()
    return filename

# ==============================================
# INICIAR BANCO
# ==============================================
criar_banco()

# ==============================================
# MENU LATERAL
# ==============================================
st.sidebar.title("💪 Sistema de Academia")
pagina = st.sidebar.radio("Navegação", ["Cadastro de Alunos", "Registrar Pagamento", "Histórico de Pagamentos"])

# ==============================================
# PÁGINA 1 — CADASTRO
# ==============================================
if pagina == "Cadastro de Alunos":
    st.title("📋 Cadastro de Alunos")
    st.divider()

    with st.form("form_cadastro"):
        nome = st.text_input("Nome Completo")
        col1, col2 = st.columns(2)
        with col1:
            cpf = st.text_input("CPF")
        with col2:
            telefone = st.text_input("Telefone")
        endereco = st.text_input("Endereço")
        
        if st.form_submit_button("✅ Cadastrar Aluno", type="primary"):
            if not nome:
                st.warning("⚠️ Informe o nome!")
            else:
                cadastrar_aluno(nome, cpf, telefone, endereco)
                st.success(f"✅ Aluno **{nome}** cadastrado com sucesso!")
                st.balloons()

    st.divider()
    st.subheader("📖 Alunos Cadastrados")
    alunos = carregar_alunos()
    if alunos:
        st.table([{"ID": a[0], "Nome": a[1], "CPF": a[2], "Telefone": a[3]} for a in alunos])
    else:
        st.info("Nenhum aluno cadastrado ainda.")

# ==============================================
# PÁGINA 2 — REGISTRAR PAGAMENTO
# ==============================================
elif pagina == "Registrar Pagamento":
    st.title("💳 Registrar Pagamento")
    st.divider()

    alunos = carregar_alunos()
    if not alunos:
        st.warning("⚠️ Cadastre um aluno primeiro!")
    else:
        lista_alunos = [f"{a[0]} | {a[1]}" for a in alunos]
        escolhido = st.selectbox("Selecione o Aluno", lista_alunos)
        aluno_id = int(escolhido.split(" | ")[0])

        col1, col2 = st.columns(2)
        with col1:
            valor = st.number_input("Valor R$", min_value=0.0, format="%.2f")
        with col2:
            data_pag = st.date_input("Data do Pagamento", value=datetime.now(), format="DD/MM/YYYY")
        
        referencia = st.text_input("Referência (Mês/Ano)", value=f"{datetime.now().month:02d}/{datetime.now().year}")

        if st.button("💳 Gerar Recibo PDF", type="primary"):
            if valor <= 0:
                st.error("⚠️ Informe um valor válido!")
            else:
                data_fmt = data_pag.strftime("%d/%m/%Y")
                numero_recibo = f"REC-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000,9999)}"
                
                dados_aluno = buscar_aluno(aluno_id)
                nome_aluno, cpf_aluno = dados_aluno

                arquivo = gerar_recibo_pdf(nome_aluno, cpf_aluno, valor, data_fmt, referencia, numero_recibo)
                registrar_pagamento(aluno_id, valor, data_fmt, referencia, numero_recibo)

                st.success(f"✅ Pagamento registrado! Recibo **{numero_recibo}** gerado!")
                st.info(f"📄 Arquivo salvo: `{arquivo}`")

                with open(arquivo, "rb") as f:
                    st.download_button("📥 Baixar Recibo PDF", data=f, file_name=os.path.basename(arquivo))

# ==============================================
# PÁGINA 3 — HISTÓRICO
# ==============================================
elif pagina == "Histórico de Pagamentos":
    st.title("📊 Histórico de Pagamentos")
    st.divider()

    pagamentos = listar_pagamentos()
    if pagamentos:
        st.table([{
            "Nº Recibo": p[0],
            "Aluno": p[1],
            "Valor": f"R$ {p[2]:.2f}",
            "Data": p[3],
            "Referência": p[4]
        } for p in pagamentos])

        total = sum(p[2] for p in pagamentos)
        st.subheader(f"💰 Total Faturado: R$ {total:.2f}")
    else:
        st.info("Nenhum pagamento registrado ainda.")