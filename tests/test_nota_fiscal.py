import os
import sqlite3
import tempfile
import unittest

import app as app_module


class TestNotaFiscal(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.banco_original = app_module.DATABASE
        app_module.DATABASE = os.path.join(self.pasta.name, "teste.db")
        app_module.inicializar_banco()
        app_module.app.config["TESTING"] = True
        self.client = app_module.app.test_client()
        self.client.post("/login", data={"usuario": "admin",
                                         "senha": "EcoGestao@2026"})
        self.client.post("/clientes", data={
            "nome": "Mercado Verde", "telefone": "31999990000",
            "endereco": "Rua A, 10", "status": "Ativo"})

    def tearDown(self):
        app_module.DATABASE = self.banco_original
        self.pasta.cleanup()

    def registrar(self, nota_fiscal):
        return self.client.post("/coletas", data={
            "cliente_id": 1, "data_coleta": "2026-11-10",
            "tipo_residuo": "Papel", "quantidade": "10",
            "status": "Agendada", "nota_fiscal": nota_fiscal},
            follow_redirects=True)

    def test_nota_fiscal_e_salva_e_exibida_na_lista_e_no_historico(self):
        resposta = self.registrar("NF-12345/2026")
        self.assertIn(b"Coleta registrada com sucesso", resposta.data)
        self.assertIn(b"NF-12345/2026", resposta.data)
        historico = self.client.get("/historico")
        self.assertIn(b"NF-12345/2026", historico.data)

    def test_nota_fiscal_e_opcional(self):
        resposta = self.registrar("")
        self.assertIn(b"Coleta registrada com sucesso", resposta.data)

    def test_nota_fiscal_com_caracteres_invalidos_e_rejeitada(self):
        for valor in ["<script>alert(1)</script>", "NF 123", "x" * 45]:
            with self.subTest(valor=valor):
                resposta = self.registrar(valor)
                self.assertIn("Nota fiscal inválida".encode(), resposta.data)

    def test_chave_de_acesso_de_44_digitos_e_aceita(self):
        resposta = self.registrar("3" * 44)
        self.assertIn(b"Coleta registrada com sucesso", resposta.data)


class TestMigracaoDoBanco(unittest.TestCase):
    def test_banco_antigo_ganha_coluna_sem_perder_dados(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = os.path.join(pasta, "antigo.db")
            antigo = sqlite3.connect(caminho)
            antigo.executescript("""
                CREATE TABLE clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL, telefone TEXT NOT NULL, email TEXT,
                    endereco TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Ativo');
                CREATE TABLE coletas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id INTEGER NOT NULL, data_coleta TEXT NOT NULL,
                    tipo_residuo TEXT NOT NULL, quantidade REAL, observacoes TEXT,
                    status TEXT NOT NULL DEFAULT 'Agendada');
                INSERT INTO clientes (nome, telefone, endereco)
                    VALUES ('Cliente Antigo', '1', 'Rua X');
                INSERT INTO coletas (cliente_id, data_coleta, tipo_residuo, quantidade)
                    VALUES (1, '2026-10-01', 'Vidro', 5);
            """)
            antigo.commit()
            antigo.close()

            original = app_module.DATABASE
            app_module.DATABASE = caminho
            try:
                app_module.inicializar_banco()
                app_module.inicializar_banco()  # idempotente
            finally:
                app_module.DATABASE = original

            banco = sqlite3.connect(caminho)
            colunas = [c[1] for c in banco.execute("PRAGMA table_info(coletas)")]
            registros = banco.execute(
                "SELECT tipo_residuo, nota_fiscal FROM coletas").fetchall()
            banco.close()
            self.assertIn("nota_fiscal", colunas)
            self.assertEqual(registros, [("Vidro", None)])


if __name__ == "__main__":
    unittest.main()
