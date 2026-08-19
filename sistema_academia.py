import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import os
import random

# ------------------- BANCO DE DADOS -------------------
def criar_banco():
    conn = sqlite3.connect("academia.db")
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

# ------------------- GERAR NOTA/RECIBO PDF -------------------
def gerar_recibo_pdf(nome_aluno, cpf, valor, data, referencia, numero_recibo):
    if not os.path.exists("recibos"):
        os.makedirs("recibos")
    
    filename = f"recibos/recibo_{numero_recibo}.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    largura, altura = A4

    # Cabeçalho
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(largura/2, altura - 80, "ACADEMIA [INSIRA SEU NOME]")
    c.setFont("Helvetica", 12)
    c.drawCentredString(largura/2, altura - 110, "CNPJ: ___.___.___/____-__ | Rua ______, ___, Cidade - UF")
    c.drawCentredString(largura/2, altura - 130, "Telefone: (___) ____-____")

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
    c.drawString(60, y - 15, "Para emissão de NFS-e oficial, utilize o portal da prefeitura ou certificado digital.")

    c.showPage()
    c.save()
    return filename

# ------------------- INTERFACE PRINCIPAL -------------------
class SistemaAcademia:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Pagamentos - Academia")
        self.root.geometry("750x550")
        criar_banco()

        # --- ABA CADASTRO ---
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(pady=10, padx=10, fill="both", expand=True)

        self.frame_cad = ttk.Frame(self.notebook, width=700, height=400)
        self.frame_pag = ttk.Frame(self.notebook, width=700, height=400)
        self.notebook.add(self.frame_cad, text="Cadastro de Alunos")
        self.notebook.add(self.frame_pag, text="Registrar Pagamento")

        self.tela_cadastro()
        self.tela_pagamento()

    def tela_cadastro(self):
        f = self.frame_cad
        ttk.Label(f, text="Nome Completo:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.e_nome = ttk.Entry(f, width=50)
        self.e_nome.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(f, text="CPF:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.e_cpf = ttk.Entry(f, width=50)
        self.e_cpf.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(f, text="Telefone:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.e_tel = ttk.Entry(f, width=50)
        self.e_tel.grid(row=2, column=1, padx=5, pady=5)

        ttk.Button(f, text="✅ Cadastrar Aluno", command=self.cadastrar_aluno).grid(row=3, column=1, padx=5, pady=15)

        # Lista
        self.tree = ttk.Treeview(f, columns=("id","nome","cpf","tel"), show="headings", height=8)
        self.tree.heading("id", text="ID")
        self.tree.heading("nome", text="Nome")
        self.tree.heading("cpf", text="CPF")
        self.tree.heading("tel", text="Telefone")
        self.tree.column("id", width=40)
        self.tree.column("nome", width=280)
        self.tree.column("cpf", width=120)
        self.tree.column("tel", width=120)
        self.tree.grid(row=4, column=0, columnspan=2, padx=5, pady=5)
        self.carregar_alunos()

    def tela_pagamento(self):
        f = self.frame_pag
        ttk.Label(f, text="Selecione o Aluno:").grid(row=0, column=0, padx=5, pady=10, sticky="w")
        self.combo_aluno = ttk.Combobox(f, width=45, state="readonly")
        self.combo_aluno.grid(row=0, column=1, padx=5, pady=10)
        self.carregar_combo_alunos()

        ttk.Label(f, text="Valor R$:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.e_valor = ttk.Entry(f, width=20)
        self.e_valor.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(f, text="Referência (Mês/Ano):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.e_ref = ttk.Entry(f, width=20)
        self.e_ref.insert(0, f"{datetime.now().month:02d}/{datetime.now().year}")
        self.e_ref.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        # === BOTÃO DE PAGAMENTO + NOTA FISCAL ===
        btn = tk.Button(f, text="💳 REGISTRAR PAGAMENTO\n📄 Gerar Recibo/Nota",
                       bg="#2ecc71", fg="white", font=("Arial",12,"bold"),
                       command=self.registrar_pagamento)
        btn.grid(row=3, column=0, columnspan=2, padx=10, pady=20, sticky="nsew")

        self.label_status = ttk.Label(f, text="")
        self.label_status.grid(row=4, column=0, columnspan=2, pady=10)

    def carregar_alunos(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        conn = sqlite3.connect("academia.db")
        c = conn.cursor()
        for linha in c.execute("SELECT id,nome,cpf,telefone FROM alunos ORDER BY nome"):
            self.tree.insert("", "end", values=linha)
        conn.close()

    def carregar_combo_alunos(self):
        conn = sqlite3.connect("academia.db")
        c = conn.cursor()
        c.execute("SELECT id,nome FROM alunos ORDER BY nome")
        dados = [f"{row[0]} | {row[1]}" for row in c.fetchall()]
        self.combo_aluno["values"] = dados
        conn.close()
        if dados: self.combo_aluno.current(0)

    def cadastrar_aluno(self):
        nome = self.e_nome.get().strip()
        if not nome:
            messagebox.showwarning("Aviso", "Informe o nome!")
            return
        conn = sqlite3.connect("academia.db")
        c = conn.cursor()
        c.execute("INSERT INTO alunos (nome,cpf,telefone) VALUES (?,?,?)",
                  (nome, self.e_cpf.get().strip(), self.e_tel.get().strip()))
        conn.commit()
        conn.close()
        messagebox.showinfo("Sucesso", "Aluno cadastrado!")
        self.e_nome.delete(0, "end"); self.e_cpf.delete(0, "end"); self.e_tel.delete(0, "end")
        self.carregar_alunos()
        self.carregar_combo_alunos()

    def registrar_pagamento(self):
        selecionado = self.combo_aluno.get()
        if not selecionado:
            messagebox.showwarning("Aviso", "Cadastre um aluno primeiro!")
            return
        aluno_id = selecionado.split(" | ")[0]
        valor_txt = self.e_valor.get().strip()
        try:
            valor = float(valor_txt.replace(",","."))
        except:
            messagebox.showerror("Erro", "Informe um valor válido!")
            return
        referencia = self.e_ref.get().strip()
        data_pag = datetime.now().strftime("%d/%m/%Y")
        numero_recibo = f"REC-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000,9999)}"

        # Pegar dados do aluno
        conn = sqlite3.connect("academia.db")
        c = conn.cursor()
        c.execute("SELECT nome,cpf FROM alunos WHERE id=?", (aluno_id,))
        nome_aluno, cpf_aluno = c.fetchone()

        # Salvar pagamento
        c.execute("""INSERT INTO pagamentos (aluno_id,valor,data_pagamento,referencia,numero_recibo)
                     VALUES (?,?,?,?,?)""",
                  (aluno_id, valor, data_pag, referencia, numero_recibo))
        conn.commit()
        conn.close()

        # Gerar PDF
        arquivo = gerar_recibo_pdf(nome_aluno, cpf_aluno, valor, data_pag, referencia, numero_recibo)
        self.label_status.config(text=f"✅ Pagamento registrado!\n📄 Recibo salvo em: {arquivo}")
        messagebox.showinfo("Pagamento Concluído!",
                            f"Recibo gerado!\nNúmero: {numero_recibo}\nArquivo: {arquivo}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SistemaAcademia(root)
    root.mainloop()