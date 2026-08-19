import streamlit as st
import sqlite3
from datetime import datetime, timedelta
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from io import BytesIO
import os
import zipfile
import shutil
from io import BytesIO
import pandas as pd

# ==============================================
# CONFIGURAÇÃO DA PÁGINA
# ==============================================
st.set_page_config(
    page_title="Sistema de Gestão de Academia",
    page_icon="💪",
    layout="wide"
)

# ==============================================
# FUNÇÕES DE BANCO DE DADOS
# ==============================================
def criar_banco():
    conn = sqlite3.connect("academia_web.db")
    c = conn.cursor()
    
    c.execute("""CREATE TABLE IF NOT EXISTS alunos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        cpf TEXT,
        telefone TEXT,
        endereco TEXT,
        dia_vencimento INTEGER,
        status TEXT DEFAULT 'Ativo',
        data_cadastro TEXT
    )""")
    
    c.execute("""CREATE TABLE IF NOT EXISTS pagamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        aluno_id INTEGER,
        valor REAL NOT NULL,
        data_pagamento TEXT NOT NULL,
        referencia TEXT,
        recibo TEXT UNIQUE,
        forma_pagamento TEXT DEFAULT 'Dinheiro',
        observacoes TEXT,
        FOREIGN KEY (aluno_id) REFERENCES alunos(id)
    )""")
    
    conn.commit()
    conn.close()

# ==============================================
# FUNÇÕES DE BACKUP
# ==============================================
def criar_pasta_backups():
    if not os.path.exists("backups"):
        os.makedirs("backups")

def fazer_backup():
    criar_pasta_backups()
    data_agora = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_arquivo = f"backups/backup_academia_{data_agora}.zip"
    
    buffer_zip = BytesIO()
    with zipfile.ZipFile(buffer_zip, "w", zipfile.ZIP_DEFLATED) as arquivo_zip:
        if os.path.exists("academia_web.db"):
            arquivo_zip.write("academia_web.db", "academia_web.db")
        if os.path.exists("recibos"):
            for raiz, pastas, arquivos in os.walk("recibos"):
                for arq in arquivos:
                    caminho_completo = os.path.join(raiz, arq)
                    caminho_dentro_zip = os.path.relpath(caminho_completo, ".")
                    arquivo_zip.write(caminho_completo, caminho_dentro_zip)
    
    with open(nome_arquivo, "wb") as f:
        f.write(buffer_zip.getvalue())
    
    return nome_arquivo, buffer_zip.getvalue()

def restaurar_backup(arquivo_enviado):
    criar_pasta_backups()
    try:
        with zipfile.ZipFile(arquivo_enviado) as arquivo_zip:
            arquivos_na_lista = arquivo_zip.namelist()
            if "academia_web.db" not in arquivos_na_lista:
                return False, "❌ Arquivo inválido! Não contém o banco de dados!"
            if os.path.exists("academia_web.db"):
                backup_seguranca = f"backups/antes_restaurar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db.bak"
                shutil.copy2("academia_web.db", backup_seguranca)
            arquivo_zip.extractall(".")
            return True, "✅ Backup restaurado com sucesso! Reinicie o sistema!"
    except Exception as e:
        return False, f"❌ Erro: {str(e)}"

def listar_backups_salvos():
    criar_pasta_backups()
    if not os.path.exists("backups"):
        return []
    arquivos = []
    for arq in sorted(os.listdir("backups"), reverse=True):
        if arq.startswith("backup_academia_") and arq.endswith(".zip"):
            caminho = os.path.join("backups", arq)
            tamanho = os.path.getsize(caminho) / 1024
            arquivos.append({"nome": arq, "caminho": caminho, "tamanho_kb": round(tamanho, 1)})
    return arquivos

# ==============================================
# DEMAIS FUNÇÕES
# ==============================================
def carregar_alunos():
    conn = sqlite3.connect("academia_web.db")
    c = conn.cursor()
    c.execute("SELECT id, nome, cpf, telefone, endereco, dia_vencimento, status, data_cadastro FROM alunos ORDER BY nome")
    dados = c.fetchall()
    conn.close()
    return dados

def salvar_aluno(nome, cpf, telefone, endereco, dia_vencimento, status):
    conn = sqlite3.connect("academia_web.db")
    c = conn.cursor()
    data_cad = datetime.now().strftime("%d/%m/%Y")
    c.execute("""INSERT INTO alunos (nome, cpf, telefone, endereco, dia_vencimento, status, data_cadastro)
                 VALUES (?, ?, ?, ?, ?, ?, ?)""",
              (nome, cpf, telefone, endereco, dia_vencimento, status, data_cad))
    conn.commit()
    conn.close()

def gerar_recibo(aluno_nome, valor, data_pgto, referencia):
    if not os.path.exists("recibos"):
        os.makedirs("recibos")
    numero_recibo = datetime.now().strftime("%Y%m%d%H%M%S")
    nome_arquivo = f"recibos/recibo_{numero_recibo}.pdf"
    
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    largura, altura = A4
    
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(largura/2, altura - 80, "RECIBO DE PAGAMENTO")
    
    c.setFont("Helvetica", 12)
    c.line(50, altura - 100, largura - 50, altura - 100)
    
    c.drawString(70, altura - 140, f"Recibo Nº: {numero_recibo}")
    c.drawString(70, altura - 170, f"Recebido de: {aluno_nome}")
    c.drawString(70, altura - 200, f"Valor: R$ {valor:.2f}")
    c.drawString(70, altura - 230, f"Referência: {referencia}")
    c.drawString(70, altura - 260, f"Data do Pagamento: {data_pgto}")
    
    c.drawString(70, altura - 320, "Declaro ter recebido o valor acima, sem que nada haja a reclamar.")
    c.line(70, altura - 380, 280, altura - 380)
    c.drawString(70, altura - 400, "Assinatura")
    
    c.drawString(70, altura - 460, f"Cabo Frio - RJ, {datetime.now().strftime('%d/%m/%Y')}")
    
    c.save()
    buffer.seek(0)
    
    with open(nome_arquivo, "wb") as f:
        f.write(buffer.getvalue())
    
    return numero_recibo, nome_arquivo, buffer

def salvar_pagamento(aluno_id, valor, data_pgto, referencia, recibo, forma_pgto, obs):
    conn = sqlite3.connect("academia_web.db")
    c = conn.cursor()
    c.execute("""INSERT INTO pagamentos (aluno_id, valor, data_pagamento, referencia, recibo, forma_pagamento, observacoes)
                 VALUES (?, ?, ?, ?, ?, ?, ?)""",
              (aluno_id, valor, data_pgto, referencia, recibo, forma_pgto, obs))
    conn.commit()
    conn.close()

def listar_pagamentos():
    conn = sqlite3.connect("academia_web.db")
    c = conn.cursor()
    c.execute("""SELECT p.id, a.nome, p.valor, p.data_pagamento, p.referencia, p.recibo, p.forma_pagamento
                 FROM pagamentos p JOIN alunos a ON p.aluno_id = a.id ORDER BY p.data_pagamento DESC""")
    dados = c.fetchall()
    conn.close()
    return dados

def listar_vencimentos(dias=30):
    conn = sqlite3.connect("academia_web.db")
    c = conn.cursor()
    c.execute("SELECT id, nome, dia_vencimento, status FROM alunos WHERE status = 'Ativo'")
    alunos = c.fetchall()
    conn.close()
    
    hoje = datetime.now()
    lista = []
    for aluno in alunos:
        _, nome, dia_venc, status = aluno
        try:
            data_venc = datetime(hoje.year, hoje.month, dia_venc)
            if data_venc < hoje:
                if hoje.month == 12:
                    data_venc = datetime(hoje.year + 1, 1, dia_venc)
                else:
                    data_venc = datetime(hoje.year, hoje.month + 1, dia_venc)
            dias_restantes = (data_venc - hoje).days
            if dias_restantes <= dias:
                lista.append({
                    "nome": nome,
                    "dia_vencimento": dia_venc,
                    "data_vencimento": data_venc.strftime("%d/%m/%Y"),
                    "dias_restantes": dias_restantes,
                    "situacao": "🔴 ATRASADO" if dias_restantes < 0 else "🟡 VENCENDO" if dias_restantes <= 5 else "🟢 Em dia"
                })
        except:
            pass
    return sorted(lista, key=lambda x: x["dias_restantes"])

# ==============================================
# INICIAR BANCO
# ==============================================
criar_banco()

# ==============================================
# MENU LATERAL
# ==============================================
st.sidebar.title("💪 Sistema de Academia")
pagina = st.sidebar.radio("Navegação", [
    "📋 Cadastro de Alunos",
    "📅 Controle de Vencimentos",
    "💰 Registrar Pagamento",
    "📊 Relatório de Pagamentos",
    "📑 NFS-e / Nota Fiscal",
    "💾 Backup e Restauração"
])

# ==============================================
# PÁGINA 1 — CADASTRO
# ==============================================
if pagina == "📋 Cadastro de Alunos":
    st.title("📋 Cadastro de Alunos")
    st.divider()
    
    aba_cad, aba_lista = st.tabs(["➕ Novo Aluno", "📂 Alunos Cadastrados"])
    
    with aba_cad:
        with st.form("form_aluno"):
            nome = st.text_input("Nome Completo")
            col1, col2 = st.columns(2)
            with col1:
                cpf = st.text_input("CPF", placeholder="000.000.000-00")
            with col2:
                telefone = st.text_input("Telefone", placeholder="(21) 90000-0000")
            endereco = st.text_input("Endereço")
            dia_venc = st.number_input("Dia do Vencimento", min_value=1, max_value=31, value=5)
            status = st.selectbox("Status", ["Ativo", "Inativo", "Suspenso"])
            
            if st.form_submit_button("✅ Cadastrar Aluno", type="primary"):
                if not nome:
                    st.error("⚠️ Digite o nome!")
                else:
                    salvar_aluno(nome, cpf, telefone, endereco, dia_venc, status)
                    st.success(f"✅ Aluno **{nome}** cadastrado com sucesso!")
                    st.balloons()
    
    with aba_lista:
        alunos = carregar_alunos()
        if alunos:
            st.table([{
                "ID": a[0],
                "Nome": a[1],
                "CPF": a[2],
                "Telefone": a[3],
                "Dia Venc": a[5],
                "Status": a[6]
            } for a in alunos])
        else:
            st.info("Nenhum aluno cadastrado ainda.")

# ==============================================
# PÁGINA 2 — VENCIMENTOS
# ==============================================
elif pagina == "📅 Controle de Vencimentos":
    st.title("📅 Controle de Vencimentos")
    st.divider()
    dias = st.slider("Mostrar vencimentos dos próximos quantos dias?", 1, 60, 15)
    st.divider()
    
    lista = listar_vencimentos(dias)
    if lista:
        st.table(lista)
        
        atrasados = sum(1 for x in lista if "ATRASADO" in x["situacao"])
        st.info(f"Total: {len(lista)} alunos | 🔴 {atrasados} em atraso")
    else:
        st.success("✅ Nenhum vencimento próximo!")

# ==============================================
# PÁGINA 3 — REGISTRAR PAGAMENTO
# ==============================================
elif pagina == "💰 Registrar Pagamento":
    st.title("💰 Registrar Pagamento")
    st.divider()
    
    alunos = carregar_alunos()
    if not alunos:
        st.warning("⚠️ Cadastre um aluno primeiro!")
    else:
        aluno_opcoes = {f"{a[0]} — {a[1]}": a[0] for a in alunos if a[6] == "Ativo"}
        escolha = st.selectbox("Selecione o Aluno", list(aluno_opcoes.keys()))
        aluno_id = aluno_opcoes[escolha]
        aluno_nome = escolha.split(" — ", 1)[1]
        
        col1, col2 = st.columns(2)
        with col1:
            valor = st.number_input("Valor R$", min_value=0.0, step=10.0, format="%.2f")
        with col2:
            data_pgto = st.text_input("Data do Pagamento", value=datetime.now().strftime("%d/%m/%Y"))
        
        referencia = st.text_input("Referência (Mês/Ano)", value=datetime.now().strftime("%m/%Y"))
        forma_pgto = st.selectbox("Forma de Pagamento", ["Dinheiro", "PIX", "Cartão", "Transferência", "Outra"])
        obs = st.text_input("Observações (opcional)")
        
        st.divider()
        if st.button("✅ Gerar Recibo e Salvar", type="primary"):
            if valor <= 0:
                st.error("⚠️ Digite o valor!")
            else:
                num_recibo, arquivo_pdf, buffer = gerar_recibo(aluno_nome, valor, data_pgto, referencia)
                salvar_pagamento(aluno_id, valor, data_pgto, referencia, num_recibo, forma_pgto, obs)
                
                st.success(f"✅ Pagamento registrado! Recibo Nº {num_recibo}")
                st.download_button("📄 Baixar Recibo em PDF", data=buffer, file_name=f"recibo_{num_recibo}.pdf")

# ==============================================
# PÁGINA 4 — RELATÓRIOS
# ==============================================
# ==============================================
# PÁGINA 4 — RELATÓRIOS COM FILTRO DE PERÍODO
# ==============================================
elif pagina == "📊 Relatório de Pagamentos":
    st.title("📊 Relatório de Pagamentos")
    st.divider()

    # 🆕 FILTRO POR PERÍODO
    st.subheader("📅 Filtrar por Período")
    hoje = datetime.now()
    col1, col2 = st.columns(2)
    with col1:
        data_inicial = st.date_input("Data Inicial", value=hoje - timedelta(days=30), format="DD/MM/YYYY")
    with col2:
        data_final = st.date_input("Data Final", value=hoje, format="DD/MM/YYYY")

    st.divider()

    # Converte datas para formato do banco
    dt_inicial = data_inicial.strftime("%d/%m/%Y")
    dt_final = data_final.strftime("%d/%m/%Y")

    # Busca pagamentos filtrados
    conn = sqlite3.connect("academia_web.db")
    c = conn.cursor()
    c.execute("""SELECT p.id, a.nome, p.valor, p.data_pagamento, p.referencia, p.recibo, p.forma_pagamento
                 FROM pagamentos p JOIN alunos a ON p.aluno_id = a.id
                 WHERE p.data_pagamento BETWEEN ? AND ?
                 ORDER BY p.data_pagamento DESC""", (dt_inicial, dt_final))
    pagamentos = c.fetchall()
    conn.close()

    # Exibe resultado
    if pagamentos:
        st.info(f"📋 Encontrados **{len(pagamentos)}** pagamentos no período de {dt_inicial} a {dt_final}")
        
        st.table([{
            "Data": p[3],
            "Aluno": p[1],
            "Valor": f"R$ {p[2]:.2f}",
            "Referência": p[4],
            "Recibo": p[5],
            "Forma de Pagamento": p[6]
        } for p in pagamentos])

        total = sum(p[2] for p in pagamentos)
        st.subheader(f"💰 Total do Período: **R$ {total:.2f}**")

        # 📥 Botão de exportar Excel
        st.divider()
        st.subheader("📥 Exportar para Excel")
        df = pd.DataFrame(pagamentos, columns=["ID", "Aluno", "Valor (R$)", "Data", "Referência", "Recibo", "Forma de Pagamento"])
        df["Valor (R$)"] = df["Valor (R$)"].apply(lambda x: f"R$ {x:.2f}")
        arquivo_excel = f"Relatorio_Periodo_{dt_inicial.replace('/','-')}_a_{dt_final.replace('/','-')}.xlsx"
        df.to_excel(arquivo_excel, index=False)
        with open(arquivo_excel, "rb") as f:
            st.download_button("📊 Baixar Planilha Excel", data=f, file_name=arquivo_excel, type="primary")

    else:
        st.info(f"📭 Nenhum pagamento encontrado entre {dt_inicial} e {dt_final}")
# ==============================================
# PÁGINA 5 — NFS-e / NOTA FISCAL (COM SIMULAÇÃO!)
# ==============================================
elif pagina == "📑 NFS-e / Nota Fiscal":
    st.title("📑 Dados para Emissão de NFS-e")
    st.divider()
    st.info("Copie os dados abaixo e cole no site da NFS-e Nacional para emitir a Nota Fiscal!")
    
    alunos = carregar_alunos()
    if not alunos:
        st.warning("⚠️ Cadastre um aluno primeiro!")
    else:
        aluno_opcoes = {f"{a[0]} — {a[1]}": a for a in alunos}
        escolha = st.selectbox("Selecione o Aluno", list(aluno_opcoes.keys()))
        a = aluno_opcoes[escolha]
        
        nome = a[1]
        cpf = a[2]
        endereco = a[4]
        telefone = a[3]
        
        col1, col2 = st.columns(2)
        with col1:
            valor_nf = st.number_input("Valor da Nota R$", min_value=0.0, step=10.0, format="%.2f")
        with col2:
            comp_nf = st.text_input("Competência (Mês/Ano)", value=datetime.now().strftime("%m/%Y"))
        
        st.divider()
        st.subheader("📋 Dados Prontos para Copiar")
        texto_nf = f"""
TOMADOR DO SERVIÇO:
Nome / Razão Social: {nome}
CPF / CNPJ: {cpf or "Não informado"}
Endereço: {endereco or "Não informado"}
Telefone: {telefone or "Não informado"}

SERVIÇO PRESTADO:
Descrição: Mensalidade de Academia — competência {comp_nf}
Código do Serviço: 08.01 — Educação / Instrução / Treinamento
Valor Total: R$ {valor_nf:.2f}
Local de Prestação: Cabo Frio - RJ
Competência: {comp_nf}
        """
        st.code(texto_nf, language="text")
        st.success("✅ Copie o texto acima e cole direto no site da NFS-e!")
        
        st.divider()
        # 🆕 AMBIENTE DE TESTES — SIMULAÇÃO
        st.subheader("🔬 Ambiente de Testes — Praticar sem Emitir Nota Real")
        st.info("""
✅ Aqui você pratica PREENCHER e PRÉ-VISUALIZAR sem emitir nota de verdade!
⚠️ As notas emitidas neste ambiente são apenas de TESTE e NÃO têm valor fiscal!
        """)
        st.markdown("""
👉 **[Clique aqui para abrir o Ambiente Oficial de Testes da NFS-e](https://www.producaorestrita.nfse.gov.br/EmissorNacional/)**

💡 **Como usar o ambiente de testes:**
1. Clique no link acima → entra com sua conta Gov.br normalmente
2. Use os dados prontos que aparecem abaixo (copie e cole lá!)
3. Preencha tudo → clique em **Pré-visualizar** para ver como fica
4. Pode até clicar em "Emitir" — é só teste, não vale de verdade! ✅
        """)
        
        st.divider()
        st.subheader("📋 DADOS PRONTOS PARA SIMULAR")
        st.code(f"""
TOMADOR DO SERVIÇO (TESTE):
Nome: {nome}
CPF: {cpf or "000.000.000-00"}
Endereço: {endereco or "Rua de Teste, 123 — Centro"}
Telefone: {telefone or "(21) 90000-0000"}

SERVIÇO:
Descrição: Mensalidade de Academia — Competência {comp_nf}
Valor: R$ {valor_nf:.2f}
Código Serviço: 08.01 - Educação / Instrução / Treinamento
Local de Prestação: Cabo Frio - RJ
        """, language="text")
        st.success("✅ Copie o texto acima e cole no ambiente de testes! Pratique à vontade!")

# ==============================================
# PÁGINA 6 — BACKUP E RESTAURAÇÃO
# ==============================================
elif pagina == "💾 Backup e Restauração":
    st.title("💾 Backup e Restauração de Dados")
    st.divider()
    st.info("Faça backup dos seus dados e leve para outro computador ou guarde em segurança! 🔒")
    
    aba_backup, aba_restaurar, aba_lista = st.tabs(["💾 Criar Backup", "🔄 Restaurar Backup", "📂 Backups Salvos"])
    
    with aba_backup:
        st.subheader("💾 Criar Backup Completo")
        st.write("""O backup vai salvar:
- ✅ Todo o cadastro de alunos
- ✅ Todos os pagamentos
- ✅ Todos os recibos em PDF

Arquivo compactado em .zip, fácil de guardar ou enviar!""")
        if st.button("💾 GERAR BACKUP AGORA", type="primary"):
            with st.spinner("Criando backup..."):
                nome_arquivo, conteudo = fazer_backup()
                st.success(f"✅ Backup criado com sucesso!")
                st.info(f"📁 Arquivo: {nome_arquivo}")
                st.download_button("📥 BAIXAR BACKUP (.zip)", data=conteudo, file_name=os.path.basename(nome_arquivo), type="primary")
    
    with aba_restaurar:
        st.subheader("🔄 Restaurar Backup")
        st.warning("""⚠️ **ATENÇÃO!**
- A restauração vai **SUBSTITUIR** os dados atuais pelos do backup!
- Antes de restaurar, o sistema cria um backup automático dos dados atuais!
- Use apenas backups criados por este sistema (arquivo .zip)""")
        arquivo_enviado = st.file_uploader("Selecione o arquivo de backup (.zip)", type="zip")
        if arquivo_enviado and st.button("🔄 RESTAURAR BACKUP", type="primary"):
            with st.spinner("Restaurando..."):
                sucesso, mensagem = restaurar_backup(arquivo_enviado)
                if sucesso:
                    st.success(mensagem)
                    st.balloons()
                    st.info("🔄 Reinicie o sistema para carregar os dados restaurados!")
                else:
                    st.error(mensagem)
    
    with aba_lista:
        st.subheader("📂 Backups Salvos neste Computador")
        backups = listar_backups_salvos()
        if backups:
            st.info(f"Encontrados {len(backups)} backup(s) salvos na pasta 'backups'")
            for bkp in backups:
                with st.expander(f"📄 {bkp['nome']} — {bkp['tamanho_kb']} KB"):
                    with open(bkp["caminho"], "rb") as f:
                        st.download_button("📥 Baixar este backup", data=f, file_name=bkp["nome"])
        else:
            st.info("Nenhum backup salvo ainda. Vá na aba 'Criar Backup' e crie o primeiro!")
