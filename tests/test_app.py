import os
import tempfile
import unittest

import app as app_module


class EcoGestaoTestCase(unittest.TestCase):
    """Base: cada teste usa um banco SQLite temporário e isolado."""

    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.banco_original = app_module.DATABASE
        app_module.DATABASE = os.path.join(self.pasta.name, "teste.db")
        app_module.inicializar_banco()
        app_module.app.config["TESTING"] = True
        self.client = app_module.app.test_client()

    def tearDown(self):
        app_module.DATABASE = self.banco_original
        self.pasta.cleanup()

    def entrar(self, usuario="admin", senha="EcoGestao@2026"):
        return self.client.post(
            "/login", data={"usuario": usuario, "senha": senha},
            follow_redirects=True,
        )

    def cadastrar_cliente(self, nome="Mercado Verde", status="Ativo"):
        return self.client.post(
            "/clientes",
            data={"nome": nome, "telefone": "31999990000",
                  "endereco": "Rua A, 10", "status": status},
            follow_redirects=True,
        )

    def registrar_coleta(self, **dados):
        base = {"cliente_id": 1, "data_coleta": "2026-11-10",
                "tipo_residuo": "Papel", "quantidade": "12.5",
                "status": "Agendada"}
        base.update(dados)
        return self.client.post("/coletas", data=base, follow_redirects=True)


class TestAutenticacao(EcoGestaoTestCase):
    def test_rotas_protegidas_redirecionam_para_login(self):
        for rota in ["/", "/clientes", "/coletas", "/historico", "/relatorios"]:
            resposta = self.client.get(rota)
            self.assertEqual(resposta.status_code, 302)
            self.assertIn("/login", resposta.headers["Location"])

    def test_login_valido_acessa_o_painel(self):
        resposta = self.entrar()
        self.assertEqual(resposta.status_code, 200)
        self.assertNotIn("Usuário ou senha inválidos".encode(), resposta.data)

    def test_login_invalido_mostra_mensagem_de_erro(self):
        resposta = self.entrar(senha="senha-errada")
        self.assertIn("Usuário ou senha inválidos".encode(), resposta.data)


class TestClientes(EcoGestaoTestCase):
    def test_cadastro_de_cliente_valido(self):
        self.entrar()
        resposta = self.cadastrar_cliente()
        self.assertIn(b"Cliente cadastrado com sucesso", resposta.data)
        self.assertIn(b"Mercado Verde", resposta.data)

    def test_cadastro_sem_nome_e_rejeitado(self):
        self.entrar()
        resposta = self.client.post(
            "/clientes", data={"nome": "", "telefone": "1", "endereco": "x"},
            follow_redirects=True,
        )
        self.assertIn("Preencha nome, telefone e endereço".encode(), resposta.data)


class TestColetas(EcoGestaoTestCase):
    def test_registro_de_coleta_valida(self):
        self.entrar()
        self.cadastrar_cliente()
        resposta = self.registrar_coleta()
        self.assertIn(b"Coleta registrada com sucesso", resposta.data)

    def test_coleta_para_cliente_inativo_e_rejeitada(self):
        self.entrar()
        self.cadastrar_cliente(nome="Cliente Inativo", status="Inativo")
        resposta = self.registrar_coleta(tipo_residuo="Vidro")
        self.assertIn("Selecione um cliente ativo".encode(), resposta.data)

    def test_quantidade_invalida_e_rejeitada(self):
        self.entrar()
        self.cadastrar_cliente()
        for valor in ["-3", "0", "abc"]:
            with self.subTest(valor=valor):
                resposta = self.registrar_coleta(quantidade=valor)
                self.assertIn(
                    "A quantidade deve ser um número positivo".encode(),
                    resposta.data,
                )

    def test_data_de_coleta_invalida_e_rejeitada(self):
        self.entrar()
        self.cadastrar_cliente()
        for data in ["2026-13-45", "amanha", "31/10/2026"]:
            with self.subTest(data=data):
                resposta = self.registrar_coleta(data_coleta=data)
                self.assertIn(
                    "Informe uma data de coleta válida".encode(),
                    resposta.data,
                )


class TestHistorico(EcoGestaoTestCase):
    def test_historico_filtra_por_cliente(self):
        self.entrar()
        self.cadastrar_cliente(nome="Cliente Um")
        self.cadastrar_cliente(nome="Cliente Dois")
        self.registrar_coleta(cliente_id=1, tipo_residuo="Papel")
        self.registrar_coleta(cliente_id=2, tipo_residuo="Vidro")
        filtrado = self.client.get("/historico?cliente_id=2")
        self.assertIn(b"Vidro", filtrado.data)
        self.assertNotIn("<td>Papel</td>".encode(), filtrado.data)
        todos = self.client.get("/historico")
        self.assertIn(b"Vidro", todos.data)
        self.assertIn(b"Papel", todos.data)


class TestRelatorios(EcoGestaoTestCase):
    def test_relatorios_agrupam_por_status_e_residuo(self):
        self.entrar()
        self.cadastrar_cliente()
        self.registrar_coleta(tipo_residuo="Plástico", status="Concluída")
        resposta = self.client.get("/relatorios")
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("Plástico".encode(), resposta.data)
        self.assertIn("Concluída".encode(), resposta.data)


if __name__ == "__main__":
    unittest.main()
