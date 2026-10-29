

\# EcoGestão Resíduos



Sistema web para controle de clientes, coletas e gerenciamento de resíduos recicláveis.



\## Objetivo



Organizar o cadastro de clientes, o registro de coletas, o histórico de serviços e os relatórios básicos de uma empresa de coleta de resíduos recicláveis.



\## Tecnologias



\- Python 3.12

\- Flask 3.0

\- SQLite

\- HTML5 e CSS3

\- Bootstrap 5



\## Funcionalidades



\- Login de acesso

\- Cadastro de clientes

\- Registro e agendamento de coletas

\- Consulta do histórico de coletas por cliente

\- Relatórios por status e tipo de resíduo

\- Interface adaptável a diferentes telas



\## Como executar no Windows



1\. Instale o Python 3.12.

2\. Abra o PowerShell na pasta do projeto.

3\. Instale as dependências:



&#x20;  ```powershell

&#x20;  py -3.12 -m pip install -r requirements.txt

&#x20;  ```



4\. Execute a aplicação:



&#x20;  ```powershell

&#x20;  py -3.12 app.py

&#x20;  ```



5\. Abra o navegador no endereço:



&#x20;  http://127.0.0.1:5000



\## Acesso inicial para testes



\- Usuário: `admin`

\- Senha: `EcoGestao@2026`



A conta inicial é criada automaticamente na primeira execução. Essas credenciais são apenas para testes locais. Não utilize essa configuração em produção.



\## Banco de dados



O SQLite é inicializado automaticamente, e o arquivo do banco fica na pasta `instance`.



\## Observação



Este projeto é um MVP acadêmico para a Experiência Prática 3 de Projeto de Software.



