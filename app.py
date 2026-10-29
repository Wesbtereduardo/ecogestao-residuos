
import os
import sqlite3
from functools import wraps
from datetime import date
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, g
)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, instance_relative_config=True)
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "chave-temporaria-trocar-em-producao"
)
os.makedirs(app.instance_path, exist_ok=True)
DATABASE = os.path.join(app.instance_path, "ecogestao.db")


def conectar():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def fechar_conexao(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def inicializar_banco():
    db = sqlite3.connect(DATABASE)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT NOT NULL,
            email TEXT,
            endereco TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Ativo'
                CHECK (status IN ('Ativo', 'Inativo'))
        );

        CREATE TABLE IF NOT EXISTS coletas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            data_coleta TEXT NOT NULL,
            tipo_residuo TEXT NOT NULL,
            quantidade REAL,
            observacoes TEXT,
            status TEXT NOT NULL DEFAULT 'Agendada'
                CHECK (status IN ('Agendada', 'Concluída', 'Cancelada')),
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        );
    """)
    # Conta inicial para o primeiro acesso.
    usuario = db.execute(
        "SELECT id FROM usuarios WHERE usuario = ?", ("admin",)
    ).fetchone()
    if not usuario:
        db.execute(
            "INSERT INTO usuarios (usuario, senha_hash) VALUES (?, ?)",
            ("admin", generate_password_hash(
                os.environ.get("ADMIN_PASSWORD", "EcoGestao@2026")
            ))
        )
    db.commit()
    db.close()


def login_obrigatorio(funcao):
    @wraps(funcao)
    def decorada(*args, **kwargs):
        if "usuario_id" not in session:
            return redirect(url_for("login"))
        return funcao(*args, **kwargs)
    return decorada


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        senha = request.form.get("senha", "")
        db = conectar()
        conta = db.execute(
            "SELECT * FROM usuarios WHERE usuario = ?", (usuario,)
        ).fetchone()
        if conta and check_password_hash(conta["senha_hash"], senha):
            session.clear()
            session["usuario_id"] = conta["id"]
            session["usuario"] = conta["usuario"]
            return redirect(url_for("inicio"))
        flash("Usuário ou senha inválidos.", "danger")
    return render_template("login.html")


@app.route("/sair")
def sair():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_obrigatorio
def inicio():
    db = conectar()
    total_clientes = db.execute(
        "SELECT COUNT(*) FROM clientes"
    ).fetchone()[0]
    total_coletas = db.execute(
        "SELECT COUNT(*) FROM coletas"
    ).fetchone()[0]
    agendadas = db.execute(
        "SELECT COUNT(*) FROM coletas WHERE status = ?", ("Agendada",)
    ).fetchone()[0]
    concluidas = db.execute(
        "SELECT COUNT(*) FROM coletas WHERE status = ?", ("Concluída",)
    ).fetchone()[0]
    return render_template(
        "dashboard.html",
        total_clientes=total_clientes,
        total_coletas=total_coletas,
        agendadas=agendadas,
        concluidas=concluidas
    )


@app.route("/clientes", methods=["GET", "POST"])
@login_obrigatorio
def clientes():
    db = conectar()
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        telefone = request.form.get("telefone", "").strip()
        email = request.form.get("email", "").strip()
        endereco = request.form.get("endereco", "").strip()
        status = request.form.get("status", "Ativo")
        if not nome or not telefone or not endereco:
            flash("Preencha nome, telefone e endereço.", "danger")
        elif status not in ("Ativo", "Inativo"):
            flash("Situação de cliente inválida.", "danger")
        else:
            db.execute(
                """INSERT INTO clientes
                   (nome, telefone, email, endereco, status)
                   VALUES (?, ?, ?, ?, ?)""",
                (nome, telefone, email or None, endereco, status)
            )
            db.commit()
            flash("Cliente cadastrado com sucesso!", "success")
            return redirect(url_for("clientes"))
    lista = db.execute(
        "SELECT * FROM clientes ORDER BY nome"
    ).fetchall()
    return render_template("clientes.html", clientes=lista)


@app.route("/coletas", methods=["GET", "POST"])
@login_obrigatorio
def coletas():
    db = conectar()
    if request.method == "POST":
        cliente_id = request.form.get("cliente_id", type=int)
        data_coleta = request.form.get("data_coleta", "").strip()
        tipo = request.form.get("tipo_residuo", "").strip()
        quantidade_texto = request.form.get("quantidade", "").strip()
        observacoes = request.form.get("observacoes", "").strip()
        status = request.form.get("status", "Agendada")
        try:
            quantidade = float(quantidade_texto) if quantidade_texto else None
            if quantidade is not None and quantidade <= 0:
                raise ValueError
        except ValueError:
            quantidade = None
            flash("A quantidade deve ser um número positivo.", "danger")
            return redirect(url_for("coletas"))

        cliente = db.execute(
            "SELECT id FROM clientes WHERE id = ? AND status = ?",
            (cliente_id, "Ativo")
        ).fetchone() if cliente_id else None

        if not cliente or not data_coleta or not tipo:
            flash("Selecione um cliente ativo e preencha data e resíduo.", "danger")
        elif status not in ("Agendada", "Concluída", "Cancelada"):
            flash("Status de coleta inválido.", "danger")
        else:
            db.execute(
                """INSERT INTO coletas
                   (cliente_id, data_coleta, tipo_residuo, quantidade,
                    observacoes, status)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (cliente_id, data_coleta, tipo, quantidade,
                 observacoes or None, status)
            )
            db.commit()
            flash("Coleta registrada com sucesso!", "success")
            return redirect(url_for("coletas"))

    clientes_ativos = db.execute(
        "SELECT id, nome FROM clientes WHERE status = ? ORDER BY nome",
        ("Ativo",)
    ).fetchall()
    lista = db.execute("""
        SELECT coletas.*, clientes.nome AS cliente_nome
        FROM coletas JOIN clientes ON clientes.id = coletas.cliente_id
        ORDER BY data_coleta DESC, coletas.id DESC
    """).fetchall()
    return render_template(
        "coletas.html", clientes=clientes_ativos, coletas=lista,
        hoje=date.today().isoformat()
    )


@app.route("/historico")
@login_obrigatorio
def historico():
    db = conectar()
    cliente_id = request.args.get("cliente_id", type=int)
    clientes_lista = db.execute(
        "SELECT id, nome FROM clientes ORDER BY nome"
    ).fetchall()
    if cliente_id:
        lista = db.execute("""
            SELECT coletas.*, clientes.nome AS cliente_nome
            FROM coletas JOIN clientes ON clientes.id = coletas.cliente_id
            WHERE clientes.id = ?
            ORDER BY data_coleta DESC
        """, (cliente_id,)).fetchall()
    else:
        lista = db.execute("""
            SELECT coletas.*, clientes.nome AS cliente_nome
            FROM coletas JOIN clientes ON clientes.id = coletas.cliente_id
            ORDER BY data_coleta DESC
        """).fetchall()
    return render_template(
        "historico.html", clientes=clientes_lista,
        coletas=lista, cliente_selecionado=cliente_id
    )


@app.route("/relatorios")
@login_obrigatorio
def relatorios():
    db = conectar()
    por_status = db.execute("""
        SELECT status, COUNT(*) AS total
        FROM coletas GROUP BY status ORDER BY status
    """).fetchall()
    por_residuo = db.execute("""
        SELECT tipo_residuo, COUNT(*) AS total,
               COALESCE(SUM(quantidade), 0) AS quantidade_total
        FROM coletas GROUP BY tipo_residuo ORDER BY tipo_residuo
    """).fetchall()
    return render_template(
        "relatorios.html", por_status=por_status, por_residuo=por_residuo
    )


@app.route("/saude")
def saude():
    """Verificação de saúde usada pelo monitoramento (não exige login)."""
    try:
        conectar().execute("SELECT 1").fetchone()
    except sqlite3.Error:
        return {"status": "erro", "banco": "indisponivel"}, 503
    return {"status": "ok", "banco": "disponivel"}


with app.app_context():
    inicializar_banco()


if __name__ == "__main__":
    app.run(debug=True)
