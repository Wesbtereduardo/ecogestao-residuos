import os
import tempfile
import unittest

import app as app_module


class TestRecursosDeAcessibilidade(unittest.TestCase):
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

    def test_pagina_de_login_tem_controles_de_acessibilidade(self):
        html = self.client.get("/login").data.decode()
        for trecho in ['id="fonte-maior"', 'id="fonte-menor"',
                       'id="alto-contraste"', 'aria-pressed="false"',
                       'id="restaurar-padrao"', 'role="status"']:
            with self.subTest(trecho=trecho):
                self.assertIn(trecho, html)

    def test_link_para_pular_ao_conteudo_aponta_para_a_area_principal(self):
        html = self.client.get("/login").data.decode()
        self.assertIn('href="#conteudo"', html)
        self.assertIn('id="conteudo"', html)

    def test_idioma_da_pagina_declarado_para_leitores_de_tela(self):
        html = self.client.get("/login").data.decode()
        self.assertIn('<html lang="pt-BR">', html)


if __name__ == "__main__":
    unittest.main()
