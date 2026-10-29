import os
import tempfile
import unittest

import app as app_module


class TestSaude(unittest.TestCase):
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

    def test_saude_responde_ok_sem_login(self):
        resposta = self.client.get("/saude")
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.get_json()["status"], "ok")

    def test_saude_responde_503_quando_o_banco_esta_indisponivel(self):
        app_module.DATABASE = os.path.join(self.pasta.name, "nao-existe", "x.db")
        resposta = self.client.get("/saude")
        self.assertEqual(resposta.status_code, 503)
        self.assertEqual(resposta.get_json()["status"], "erro")

    def test_senha_do_admin_pode_vir_de_variavel_de_ambiente(self):
        os.environ["ADMIN_PASSWORD"] = "SenhaDeProducao!1"
        try:
            outra = os.path.join(self.pasta.name, "prod.db")
            app_module.DATABASE = outra
            app_module.inicializar_banco()
            ok = self.client.post("/login", data={
                "usuario": "admin", "senha": "SenhaDeProducao!1"})
            self.assertEqual(ok.status_code, 302)
            self.client.get("/sair")
            padrao = self.client.post("/login", data={
                "usuario": "admin", "senha": "EcoGestao@2026"},
                follow_redirects=True)
            self.assertIn("Usuário ou senha inválidos".encode(), padrao.data)
        finally:
            del os.environ["ADMIN_PASSWORD"]


if __name__ == "__main__":
    unittest.main()
