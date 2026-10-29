# EcoGestão Resíduos

Sistema web para controle de clientes, coletas e gerenciamento de resíduos recicláveis.

## Objetivo

Organizar o cadastro de clientes, o registro de coletas, o histórico de serviços e os relatórios básicos de uma empresa de coleta de resíduos recicláveis.

## Tecnologias

- Python 3.12
- Flask 3.0
- SQLite
- HTML5 e CSS3
- Bootstrap 5

## Funcionalidades

- Login de acesso
- Cadastro de clientes
- Registro e agendamento de coletas
- Consulta do histórico de coletas por cliente
- Relatórios por status e tipo de resíduo
- Interface adaptável a diferentes telas

## Como executar no Windows

1. Instale o Python 3.12.
2. Abra o PowerShell na pasta do projeto.
3. Instale as dependências:

   ```powershell
   py -3.12 -m pip install -r requirements.txt
   ```

4. Execute a aplicação:

   ```powershell
   py -3.12 app.py
   ```

5. Abra o navegador no endereço:

   http://127.0.0.1:5000

## Acesso inicial para testes

- Usuário: `admin`
- Senha: `EcoGestao@2026`

A conta inicial é criada automaticamente na primeira execução. Essas credenciais são apenas para testes locais. Não utilize essa configuração em produção.

## Banco de dados

O SQLite é inicializado automaticamente, e o arquivo do banco fica na pasta `instance`.

## Observação

Este projeto é um MVP acadêmico para a Experiência Prática 3 de Projeto de Software.

## Testes automatizados

Para executar os testes:

```powershell
py -3.12 -m unittest discover -s tests -v
```

## Publicação e monitoramento

A aplicação é publicada no Render (plano gratuito) a partir deste repositório,
com o comando de início `gunicorn app:app`.

Variáveis de ambiente no servidor:

- `SECRET_KEY`: chave secreta das sessões.
- `ADMIN_PASSWORD`: senha da conta `admin` criada na primeira execução.

A rota pública `/saude` responde `200` com `{"status": "ok"}` quando o banco
está disponível e `503` quando não está. Ela é consultada a cada 5 minutos por
um monitor externo, que alerta por e-mail se o serviço sair do ar.
