# Sistema de Pontos Ambientais – Lobo-guará Tech

**Challenge 2026 – Sprint 4**
**Disciplina:** Computational Thinking Using Python

Programa de console em Python que registra ações ambientais de um usuário e as grava no banco Oracle da plataforma Lobo-guará Tech (a mesma base usada pela API Java do projeto).

---

## 0. Identificação do grupo

**Equipe:** LOBO-GUARÁ TECH

| Integrante | RM |
|---|---|
| Ana Carolina Orcelli Bautzer | 570281 |
| Eduardo Lima de Souza | 570412 |
| Lucas Costa Serrano | 571016 |
| Lucas Fortunato Brandão | 572860 |
| Nicolas Rodrigues Martins | 573178 |

**Vídeo de apresentação:** `<PREENCHER: colar o link depois de publicar o vídeo>`

**Repositório:** https://github.com/Challenger-2026/python-2.0
**API publicada:** https://guara-api.onrender.com

---

## 1. Visão geral e aderência ao tema

A plataforma Lobo-guará Tech premia pessoas que praticam ações ambientais. Cada ação enviada vira uma "postagem" com link de evidência, que fica **PENDENTE** até a moderação aprovar ou rejeitar, e gera pontos para o usuário.

O programa em Python é um segundo canal de acesso a esses mesmos dados: o que é cadastrado, registrado, alterado ou excluído por ele fica gravado no mesmo banco usado pela API Java, e o que foi cadastrado pela plataforma (usuários, comunidades e postagens) é lido pelo programa. Os dados são relevantes para o projeto porque são exatamente os do desafio: ações sustentáveis, pontuação e ranking.

### Estrutura do código

| Arquivo | Responsabilidade |
|---|---|
| `prog.py` | Programa principal (ponto de entrada); menu de entrada e menu principal com `match/case`. |
| `fluxo.py` | Funções de apoio do `prog.py` (sessão, login e os submenus). |
| `menu.py` | Tudo que aparece na tela e tudo que o usuário digita (menus, tabelas, perguntas). |
| `dados.py` | Estruturas de dados (períodos, níveis de impacto), validações, cálculo de pontos, filtros e ordenações. Não usa `print()` nem `input()`. |
| `banco.py` | Acesso ao Oracle (conexão e CRUD). Não usa `print()` nem `input()`. |
| `api.py` | Consumo da API pública (GET). Não usa `print()` nem `input()`. |
| `exportar.py` | Geração dos arquivos JSON. Não usa `print()` nem `input()`. |

**Bibliotecas:** `oracledb` (banco) e `requests` (API), listadas no `requirements.txt`. `json`, `os`, `datetime` e `textwrap` fazem parte da biblioteca padrão.

---

## 2. Como executar

1. Instalar as dependências:
   ```bash
   pip install -r requirements.txt
   ```

2. Criar um arquivo `.env` (copiar o `.env.example`) com as credenciais do Oracle:
   ```
   DB_HOST=oracle.fiap.com.br
   DB_PORT=1521
   DB_SID=ORCL
   DB_USER=<usuário>
   DB_PASSWORD=<senha>
   ```
   O arquivo `.env` guarda a senha do banco e não é versionado (está no `.gitignore`).

3. Rodar:
   ```bash
   python prog.py
   ```

**Tabelas usadas** (as mesmas da API Java): `T_LGT_USUARIO`, `T_LGT_COMUNIDADE`, `T_LGT_USUARIO_COMUNIDADE` e `T_LGT_POSTAGEM`.

**Para testar:** faça o cadastro (*Cadastrar-se*), entre (*Entrar*) e, em *Minha conta > Minhas comunidades*, entre em uma comunidade para poder registrar pontos.

### Fluxo recomendado para visualizar as funcionalidades

Roteiro sugerido para passar por todas as partes do sistema em poucos minutos:

1. **Consultar a API primeiro** – no menu de entrada, escolha *3. Consultar API pública* → *1. Ranking de usuários*. A primeira chamada pode demorar até 1–2 minutos enquanto o Render "acorda"; as seguintes são rápidas. Depois veja *2. Postagens de uma comunidade* e volte.
2. **Cadastrar-se** – opção *2* do menu de entrada. Preencha os dados, confira o resumo e confirme com `s`.
3. **Entrar** – opção *1*, com o username (ou e-mail) e a senha que acabou de cadastrar.
4. **Entrar em uma comunidade** – *4. Minha conta* → *4. Minhas comunidades* → *2. Entrar em uma comunidade*. Sem isso não é possível registrar pontos.
5. **Registrar pontos (CREATE)** – *1. Registrar pontos*. Escolha o período, responda alguns dias com `s` (nível de impacto, nome da ação e um link começando com `https://`) e alguns com `n`. Pare antes do fim para ver que o progresso fica salvo.
6. **Gerenciar ações (READ / UPDATE / DELETE)** – *2. Gerenciar ações*:
   - *2. Listar* para ver as ações gravadas no banco;
   - *3. Buscar* pelo nome exato de uma ação;
   - *4. Atualizar* para trocar o nome de uma ação;
   - *5. Excluir* para apagar uma ação (confirmando com `s`).
7. **Relatórios e exportação JSON** – *3. Relatórios*: filtre por status, ordene por pontos e use as opções *4* e *5* para gerar os arquivos. Eles ficam na pasta `exportacoes`, na raiz do projeto.
8. **Minha conta (CRUD do cadastro)** – *4. Minha conta*: veja o perfil, altere nome ou username e troque a senha.
9. **Conferir a integração** – volte em *5. Consultar API pública* → *1. Ranking de usuários*: o usuário criado pelo Python aparece na lista, porque o programa e a API usam o mesmo banco.
10. **Sair** – *6. Sair da conta* volta ao menu de entrada; *0* encerra o sistema.

> Observação: *Excluir conta* só funciona para contas sem vínculos. Uma conta que já entrou em comunidade ou registrou ações é recusada pelo banco, e o sistema mostra a mensagem de erro sem apagar nada.

---

## 3. Fluxo de funcionamento

### 3.1. Abertura

O programa abre a conexão com o Oracle e começa direto no menu de entrada (nenhuma pergunta é feita antes dele), como uma rede social. Se o banco não responder ou se faltar o `.env`, mostra a mensagem de erro e encerra. A conexão é fechada no final, no bloco `finally`. Cada menu é um `match/case` (em `prog.py` e `fluxo.py`) que chama a função correspondente a cada opção.

### 3.2. Menu de entrada (ninguém na conta)

```
0. Sair
1. Entrar
2. Cadastrar-se
3. Consultar API pública (submenu)
```

### 3.3. Cadastrar-se (CREATE de usuário)

Cria um novo usuário na tabela `T_LGT_USUARIO`, a mesma da API Java. Pergunta, um por vez:

> CPF (0 volta) → nome completo (nome e sobrenome) → e-mail → username (3 a 50 letras, números ou `_`) → data de nascimento (dd/mm/aaaa) → senha (mínimo 6 caracteres, digitada duas vezes)

- CPF, e-mail e username não podem se repetir: o sistema consulta o banco e pede outro valor se já existir (o banco também tem restrição `UNIQUE` nesses campos).
- Antes de gravar, mostra um resumo (sem CPF e sem senha) e pede confirmação (s/n).
- O usuário entra com perfil **COMUM**, nível 1 e saldo de pontos 0; os perfis CRIADOR e MODERADOR não podem ser escolhidos por aqui.
- O CPF é gravado com pontos e traço (`000.000.000-00`), como cabe na coluna de 14 caracteres.
- Depois do cadastro, o usuário escolhe *Entrar*.
- A senha é gravada como texto, do mesmo jeito que a API Java, então a mesma conta funciona no site e no Python.

### 3.4. Entrar (login)

Pede o username ou o e-mail e a senha, com até 3 tentativas; digitar 0 no login volta. A senha é conferida no próprio `SELECT` (`WHERE ... AND senha = :senha`), sem ser lida do banco. Se der certo, dá boas-vindas e abre o menu principal.

### 3.5. Menu principal (usuário na conta)

```
0. Encerrar o sistema
1. Registrar pontos
2. Gerenciar ações (submenu do CRUD de postagens)
3. Relatórios (submenu)
4. Minha conta (submenu do CRUD do cadastro)
5. Consultar API pública (submenu)
6. Sair da conta (volta ao menu de entrada e limpa a sessão e o progresso)
```

### 3.6. Minha conta (CRUD do cadastro do usuário)

| Opção | O que faz | Operação |
|---|---|---|
| 1. Ver perfil | Nome, e-mail, username, nascimento, perfil, nível e pontos; sem CPF e sem senha. | READ |
| 2. Alterar dados | Escolhe nome ou username e grava o novo valor; o username novo não pode repetir o de outra pessoa. | UPDATE |
| 3. Alterar senha | Exige a senha atual. | UPDATE |
| 4. Minhas comunidades | Submenu (ver abaixo). | – |
| 5. Excluir conta | Pede confirmação (s/n) e a senha. O banco recusa se a conta tiver vínculos (postagens, comunidades, resgates...); nesse caso mostra a mensagem de erro e nada é apagado. | DELETE |
| 6. Voltar | – | – |

**Submenu Minhas comunidades:**

1. Ver minhas comunidades (READ)
2. Entrar em uma comunidade – mostra as que o usuário ainda não participa (CREATE em `T_LGT_USUARIO_COMUNIDADE`)
3. Sair de uma comunidade (DELETE)

Só quem participa de uma comunidade pode registrar pontos. A coluna `MEMBROS` dessa tabela é gravada com 1, valor que ela tem em todas as linhas da base.

### 3.7. Registrar pontos (INSERT de postagem)

1. Se a comunidade ainda não foi escolhida na sessão, mostra as comunidades do usuário e pede em qual registrar. Sem comunidade, avisa para entrar em uma em *Minha conta*.
2. Mostra os períodos (1 a 7 dias, 8 a 15 dias, 16 a 30 dias), valendo 10, 20 e 30 pontos por dia, e pede o período inicial. Se havia progresso salvo, pergunta se continua de onde parou ou recomeça.
3. Para cada dia, pergunta se houve ação ambiental:
   - **Não:** o dia vale 0 pontos e não é gravado no banco.
   - **Sim:** pede o nível de impacto (Crítico 10,6 / Estrutural 6,6 / Rotina 1,6), o nome da ação e o link da evidência (precisa começar com `http://` ou `https://`). Calcula os pontos do dia respeitando os limites (1000 no total, 680 pelos dias e 318 pelas ações) e grava a ação no banco como postagem **PENDENTE**.
4. Se o banco recusar o registro, o cálculo do dia é desfeito.
5. O ciclo termina ao chegar em 1000 pontos ou no dia 30 e mostra o resumo final. Se o usuário parar antes, o progresso fica salvo para continuar depois.

### 3.8. Gerenciar ações (CRUD de postagens no banco)

| Opção | O que faz | Operação |
|---|---|---|
| 1. Inserir | Registra uma ação, no mesmo fluxo de *Registrar pontos*. | CREATE |
| 2. Listar | Mostra as postagens do usuário em uma tabela. | READ |
| 3. Buscar | Pede o nome exato da ação, sem diferenciar maiúsculas de minúsculas, e mostra as encontradas. | READ |
| 4. Atualizar | Mostra a lista numerada; o usuário escolhe pela posição e troca o nome da ação. | UPDATE |
| 5. Excluir | Mostra a lista numerada; o usuário escolhe pela posição, vê os dados e confirma com s ou n. | DELETE |
| 6. Voltar | – | – |

**Regra de negócio:** só postagens PENDENTES podem ser atualizadas ou excluídas; depois da moderação os pontos já foram decididos. Os pontos e o link não são editáveis; para mudar, exclui-se e registra-se de novo.

### 3.9. Relatórios

1. **Ver registros** – lista as postagens do usuário.
2. **Filtrar por status** – mostra só as PENDENTE, APROVADO ou REJEITADO.
3. **Ações por pontos** – ordena do maior para o menor.
4. **Exportar ações do banco (JSON)** – gera o arquivo `crud_usuario_<id>.json` com as postagens do usuário.
5. **Exportar minhas respostas (JSON)** – gera o arquivo `respostas_usuario_<id>.json` com o que foi respondido em *Registrar pontos* nesta sessão.
6. **Voltar**

Os arquivos JSON são gravados na pasta `exportacoes` (criada automaticamente), com acentos preservados e indentação. A data da exportação aparece no formato dia/mês/ano hora:minuto:segundo.

### 3.10. Consultar API pública (consumo de API)

1. **Ranking de usuários** – faz `GET /usuarios` e ordena por pontos, do maior para o menor.
2. **Postagens de uma comunidade** – faz `GET /comunidades` e `GET /postagens`; o usuário escolhe a comunidade e vê as postagens dela.
3. **Voltar**

Não exige estar na conta (também aparece no menu de entrada). O Render gratuito pode levar mais de 1 minuto para "acordar" na primeira chamada; por isso o tempo limite da requisição é de 120 segundos.

---

## 4. Requisitos da sprint e onde estão no código

**Menus e submenus de acesso ao CRUD**
`prog.py` (`match/case` do menu de entrada e do principal), `fluxo.py` (`executa_menu_crud`, `executa_menu_relatorios`, `executa_menu_conta`, `executa_menu_comunidades`, `executa_menu_api`) e `menu.py` (`menu_*`). Todos os menus usam `match/case` e cada `case` chama a função correspondente.

**Um exemplo de cada operação do CRUD, integrado ao banco**
- Postagens – `banco.py`: `inserir_postagem` (CREATE), `listar_postagens` e `buscar_postagens` (READ), `atualizar_postagem` (UPDATE), `excluir_postagem` (DELETE).
- Cadastro de usuário (`T_LGT_USUARIO`), em *Minha conta* – `banco.py`: `inserir_usuario` (CREATE), `buscar_perfil` (READ), `atualizar_usuario` e `atualizar_senha` (UPDATE), `excluir_usuario` (DELETE); login em `buscar_usuario_por_login`. Telas em `menu.py` (`cadastrar_usuario_interativo`, `entrar_interativo`, `ver_perfil_interativo`, `alterar_dados_interativo`, `alterar_senha_interativo`, `excluir_conta_interativo`).
- Comunidades do usuário: `entrar_na_comunidade`, `sair_da_comunidade`, `listar_comunidades_do_usuario`.

**Sistema iniciado por um menu, sem pedir dados antes**
`prog.py` (abre a conexão e repete o menu de entrada ou o principal até o usuário sair).

**Subalgoritmos com uma única responsabilidade**
As funções longas foram divididas. Exemplos: `banco.py` (`consultar` e `alterar` executam o SQL e tratam o erro; as demais só montam o SQL e os dados), `menu.py` (`quebra_texto`, `mostra_linhas_do_registro` e `mostra_registros_numerados`; `grava_acao`, `monta_resultado`, `guarda_resposta` e `registra_dia`; `escolhe_ciclo` e `registrar_pontos`; `pede_opcao`, usada por todos os menus; cada campo do cadastro tem a sua função `pede_*`), `fluxo.py` (`reinicia_sessao`, `entra_na_conta`, `executa_menu_crud`, `executa_menu_conta` e os demais submenus).

**Funções genéricas, com parâmetros de nome genérico, para reaproveitar código**
`dados.py` (`filtrar_por_campo` serve para qualquer lista de dicionários; `ordenar_por_pontos` serve para registros e usuários; `buscar_item`; `itens_que_faltam`), `menu.py` (`pede_valor_valido` recebe a função de validação como parâmetro; `escolhe_comunidade` serve para qualquer lista de comunidades; `mostra_registros_ou_aviso`) e `banco.py` (`consultar` e `alterar`).

**Exportação dos dados para JSON**
`exportar.py` (`monta_exportacao_crud`, `monta_exportacao_respostas`, `salvar_json`) e `menu.py` (`exportar_*_interativo`).

**Consumo de API pública**
`api.py` (`buscar_json`, `listar_usuarios_api`, `listar_comunidades_api`, `listar_postagens_api`), usando `requests`.

**Funções para organizar, filtrar e ordenar dados em listas de dicionários e tuplas**
`dados.py` (`filtrar_por_campo`, `ordenar_por_pontos`, `buscar_item`, `itens_que_faltam`).

**Tratamento de erros (`try` / `except` / `else` / `finally`)**
`banco.py` (rollback no `except`, commit no `else`, `cursor.close()` no `finally`), `api.py` (Timeout, ConnectionError, HTTPError, JSON inválido e outras falhas do `requests`), `exportar.py` (OSError/TypeError), `prog.py` (erro de conexão com o banco; Ctrl+C e Ctrl+D encerram o sistema com uma mensagem; conexão fechada no `finally`) e `menu.py` (`atualizar_registro_interativo` e `excluir_registro_interativo`). Os erros são convertidos em `RuntimeError` (exceção do próprio Python) com mensagens amigáveis; o programa não fecha por causa delas.

**Validação de dados (entrada e processamento)**
`dados.py` (`cpf_formato_valido`, `url_valida`, `nome_valido`, `inteiro_valido`, `periodo_valido`, `nivel_impacto_valido` e, do cadastro, `nome_completo_valido`, `email_valido`, `username_valido`, `senha_valida` e `converte_data_nascimento`) e os `pede_*` de `menu.py`, que repetem a pergunta até receber um valor válido. As consultas ao banco usam parâmetros nomeados (`:cpf`, `:id_usuario`...), nunca texto concatenado, evitando SQL injection.

---

## 5. Resumo das funções

### 5.1. `dados.py` (dados e regras de negócio – sem print/input)

**Dados:** `periodos`, `niveis_impacto`, `respostas_usuario`, `progresso`, `LIMITE_TOTAL`, `LIMITE_DIAS` e `LIMITE_ACOES`.

| Função | Descrição |
|---|---|
| `nome_valido` | Texto não pode ser vazio. |
| `cpf_formato_valido` | 11 números, não todos iguais. |
| `formata_cpf` | Coloca pontos e traço no CPF. |
| `nome_completo_valido` | Nome e sobrenome, até 150 letras. |
| `email_valido` | Formato básico de e-mail. |
| `username_valido` | 3 a 50 letras, números ou `_`. |
| `senha_valida` | 6 a 150 caracteres, sem espaços. |
| `preparar_senha` | Prepara a senha para gravar (hoje, texto). |
| `converte_data_nascimento` | Texto dd/mm/aaaa → `datetime`, ou `None`. |
| `inteiro_valido` | Diz se um texto vira inteiro. |
| `periodo_valido` | Período é 1, 2 ou 3. |
| `buscar_item` | Procura numa lista de tuplas pelo número. |
| `nivel_impacto_valido` | O nível de impacto existe. |
| `url_valida` | Link começa com `http(s)://` e não tem espaços. |
| `base_diaria` | Pontos básicos do dia (10, 20 ou 30). |
| `peso_do_nivel` | Peso de um nível de impacto. |
| `nome_do_nivel` | Nome de um nível de impacto. |
| `calcula_pontos_dia` | Pontos do dia respeitando os limites. |
| `filtrar_por_campo` | Itens de uma lista de dicts em que um campo tem certo valor (status, id da comunidade...). |
| `pega_pontos` | Pontos de um item (chave de ordenação). |
| `ordenar_por_pontos` | Ordena do maior para o menor ponto (registros e ranking de usuários). |
| `itens_que_faltam` | Itens de uma lista que não estão em outra (comparando o id). |
| `buscar_item_por_id` | Procura um dict pelo id. |

### 5.2. `banco.py` (Oracle – sem print/input)

| Função | Descrição |
|---|---|
| `carregar_env` | Lê o `.env` para as variáveis de ambiente. |
| `conectar` | Abre a conexão (`RuntimeError` se falhar). |
| `consultar` | Executa um `SELECT` com tratamento de erro (usada pelas funções de leitura). |
| `alterar` | Executa `INSERT`/`UPDATE`/`DELETE` com commit no `else` e rollback no `except` (usada pelas funções de escrita). |
| `buscar_usuario_por_login` | Login por username ou e-mail e senha. |
| `campo_ja_cadastrado` | Diz se CPF, e-mail ou username já existe (ignorando o próprio usuário, se pedido). |
| `inserir_usuario` | CREATE de usuário (perfil COMUM). |
| `buscar_perfil` | READ do perfil (sem CPF e sem senha). |
| `atualizar_usuario` | UPDATE de nome e username. |
| `atualizar_senha` | UPDATE da senha (exige a senha atual). |
| `excluir_usuario` | DELETE da conta (exige a senha). |
| `listar_comunidades` | Todas as comunidades. |
| `entrar_na_comunidade` | CREATE da participação do usuário. |
| `sair_da_comunidade` | DELETE da participação do usuário. |
| `listar_comunidades_do_usuario` | Comunidades em que ele é membro. |
| `inserir_postagem` | CREATE (postagem PENDENTE). |
| `listar_postagens` | READ de todas as postagens do usuário. |
| `buscar_postagens` | READ por nome exato da ação. |
| `atualizar_postagem` | UPDATE do nome (só PENDENTE). |
| `excluir_postagem` | DELETE (só PENDENTE). |
| `montar_postagem` | Converte uma linha do `SELECT` em dict. |
| `montar_lista_de_postagens` | Converte várias linhas em uma lista de dicts, usando `montar_postagem`. |

### 5.3. `api.py` (consumo da API – sem print/input)

| Função | Descrição |
|---|---|
| `buscar_json` | GET genérico com tratamento de erros. |
| `listar_usuarios_api` | `GET /usuarios` |
| `listar_comunidades_api` | `GET /comunidades` |
| `listar_postagens_api` | `GET /postagens` |

A API devolve JSON em camelCase (`nmCompleto`, `ctTexto`, `ptGerado`...); as funções convertem para os mesmos dicts usados no resto do sistema (`nome`, `acao`, `pontos`...).

### 5.4. `exportar.py` (JSON – sem print/input)

| Função | Descrição |
|---|---|
| `monta_exportacao_crud` | Dict com usuário, data, total de registros, total de pontos e a lista. |
| `monta_exportacao_respostas` | Dict com usuário, comunidade, resumo e respostas dia a dia. |
| `salvar_json` | Grava o arquivo em `exportacoes`. |

### 5.5. `menu.py` (interface – telas, input() e mensagens)

- `pausar`, `pergunta_sim_nao`, `pede_numero_da_lista`, `pede_opcao`, `pede_valor_valido`: perguntas reutilizáveis (`pede_valor_valido` recebe a função de validação como parâmetro).
- `cadastrar_usuario_interativo` e suas auxiliares (`pede_cpf_novo`, `pede_nome_completo`, `pede_email_novo`, `pede_username_novo`, `pede_data_nascimento`, `pede_senha_nova`, `pede_dados_do_cadastro`, `mostra_resumo_do_cadastro`, `grava_cadastro`): cadastro de usuário.
- `entrar_interativo`: login por username/e-mail e senha.
- `ver_perfil_interativo`, `alterar_dados_interativo`, `alterar_senha_interativo`, `excluir_conta_interativo`: CRUD da conta (`mostra_perfil`, `pede_novo_valor`).
- `listar_minhas_comunidades_interativo`, `entrar_comunidade_interativo`, `sair_comunidade_interativo` e `escolhe_comunidade` / `escolhe_comunidade_ou_aviso` / `escolhe_comunidade_do_usuario`: comunidades do usuário.
- `mostra_*`: tabelas com borda (períodos, níveis, registros). A tabela de registros usa `quebra_texto` (`textwrap`) para quebrar ações longas sem desalinhar a borda; `mostra_registros_ou_aviso` mostra a tabela ou uma mensagem quando a lista está vazia.
- `registrar_pontos` e suas auxiliares (`escolhe_ciclo`, `inicia_novo_ciclo`, `retoma_ciclo`, `registra_dia`, `registra_dia_com_acao`, `grava_acao`, `monta_resultado`, `guarda_resposta`, `decide_proximo_passo`...): fluxo de registro dia a dia.
- `*_registro_interativo`: listar, buscar, atualizar e excluir.
- `relatorio_*_interativo` e `exportar_*_interativo`: relatórios e JSON.
- `ranking_api_interativo` e `postagens_da_comunidade_api_interativo`: telas da API.
- `menu_inicial`, `menu_principal`, `menu_conta`, `menu_alterar_dados`, `menu_comunidades`, `menu_crud`, `menu_relatorios`, `menu_api`: menus.

### 5.6. `fluxo.py` (funções de apoio do prog.py)

| Função | Descrição |
|---|---|
| `entra_na_conta` | Faz o login e guarda o usuário na sessão. |
| `reinicia_sessao` | Zera usuário, progresso e respostas. |
| `limpa_tela` | Limpa o terminal ao abrir. |
| `registra_pontos_da_sessao` | Abre *Registrar pontos*, escolhendo a comunidade se ainda não houver. |
| `executa_menu_crud` / `executa_menu_relatorios` / `executa_menu_conta` / `executa_menu_comunidades` / `executa_menu_api` | Loops dos submenus, cada um com `match/case`. |

### 5.7. `prog.py` (programa principal)

Não tem funções: é o código que roda ao executar `python prog.py`. Limpa a tela, abre a conexão, repete o menu de entrada ou o principal (`match/case` chamando as funções de `fluxo.py` e `menu.py`) até o usuário sair e fecha a conexão no `finally`.
