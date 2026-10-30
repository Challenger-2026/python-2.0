"""
Camada de acesso ao banco Oracle do Sistema de Pontos Ambientais.

Usa as mesmas tabelas da API Java (T_LGT_USUARIO, T_LGT_COMUNIDADE,
T_LGT_USUARIO_COMUNIDADE e T_LGT_POSTAGEM). Cada ação ambiental
registrada vira uma postagem:
    acao   -> ct_texto      url    -> ct_url
    status -> st_validacao  pontos -> pt_gerado
Nenhuma função aqui usa print() ou input().
"""

import os

import oracledb

oracledb.defaults.fetch_lobs = False   # CLOB volta como texto normal

STATUS_PENDENTE: str = "PENDENTE"
PERFIL_COMUM: str = "COMUM"   # todo cadastro feito pelo Python entra como usuário comum
MEMBRO: int = 1   # valor da coluna MEMBROS: na base inteira ela vale 1 em todas as linhas


class ErroBanco(Exception):
    """Erro de banco com mensagem amigável para mostrar ao usuário."""



# CONEXÃO

def carregar_env(caminho: str = "") -> None:
    """
    Lê linhas CHAVE=valor do arquivo .env e coloca em os.environ. Se não
    for informado, procura o .env na mesma pasta deste arquivo.
    Entrada: caminho (str), opcional.
    Saida: não retorna valor.
    """
    if not caminho:
        pasta = os.path.dirname(os.path.abspath(__file__))
        caminho = os.path.join(pasta, ".env")

    try:
        with open(caminho, encoding="utf-8") as arquivo:
            linhas = arquivo.readlines()
    except OSError:
        return

    for linha in linhas:
        linha = linha.strip()

        if not linha or linha.startswith("#") or "=" not in linha:
            continue

        chave, valor = linha.split("=", 1)
        # setdefault não sobrescreve uma variável já definida no ambiente
        os.environ.setdefault(chave.strip(), valor.strip())


def conectar() -> oracledb.Connection:
    """
    Abre a conexão com o Oracle usando as variáveis DB_*.
    Entrada: não recebe parâmetros.
    Saida: conexão aberta; quem chama deve fechar.
    Erro: ErroBanco se faltar variável ou o banco não responder.
    """
    carregar_env()

    usuario = os.environ.get("DB_USER", "")
    senha = os.environ.get("DB_PASSWORD", "")

    if not usuario or not senha:
        raise ErroBanco("Defina DB_USER e DB_PASSWORD no arquivo .env.")

    try:
        # Monta o endereço do Oracle (host, porta e SID); usa valores padrão se faltar
        endereco = oracledb.makedsn(
            os.environ.get("DB_HOST", "oracle.fiap.com.br"),
            int(os.environ.get("DB_PORT", "1521")),
            sid=os.environ.get("DB_SID", "ORCL"),
        )
        return oracledb.connect(user=usuario, password=senha, dsn=endereco)
    except (oracledb.Error, ValueError) as erro:
        raise ErroBanco(f"Não foi possível conectar ao banco: {erro}")


# EXECUÇÃO DE SQL (usadas por todas as funções abaixo)

def consultar(conexao: oracledb.Connection, sql: str, mensagem: str, **parametros) -> list:
    """
    Executa um SELECT e devolve todas as linhas.
    Entrada: conexao (conexão aberta); sql (str) com parâmetros nomeados
             (:nome); mensagem (str) que começa o texto do erro; parametros
             com os valores de cada :nome.
    Saida: lista de tuplas, podendo estar vazia.
    Erro: ErroBanco se o banco recusar.
    """
    cursor = conexao.cursor()

    try:
        cursor.execute(sql, **parametros)
        linhas = cursor.fetchall()
    except oracledb.Error as erro:
        raise ErroBanco(f"{mensagem}: {erro}")
    finally:
        cursor.close()

    return linhas


def alterar(conexao: oracledb.Connection, sql: str, mensagem: str, **parametros) -> int:
    """
    Executa um INSERT, UPDATE ou DELETE. Confirma (commit) se deu certo e
    desfaz (rollback) se o banco recusar.
    Entrada: mesmos parâmetros de consultar.
    Saida: quantidade de linhas alteradas (int); 0 se nenhuma bateu com o
           WHERE.
    Erro: ErroBanco se o banco recusar.
    """
    cursor = conexao.cursor()

    try:
        cursor.execute(sql, **parametros)
        quantidade = cursor.rowcount
    except oracledb.Error as erro:
        conexao.rollback()
        raise ErroBanco(f"{mensagem}: {erro}")
    else:
        # Só confirma (commit) se o comando deu certo
        conexao.commit()
        return quantidade
    finally:
        cursor.close()


# USUÁRIO (CRUD DA CONTA)

def buscar_usuario_por_login(conexao: oracledb.Connection, login: str, senha: str) -> dict | None:
    """
    Procura o usuário pelo username ou e-mail e confere a senha, tudo no
    próprio SELECT (a senha não é lida do banco).
    Entrada: conexao (conexão aberta); login (str), username ou e-mail;
             senha (str) já preparada com dados.preparar_senha.
    Saida: dict com id e nome, ou None se o login ou a senha não conferem.
    """
    sql = """
        SELECT id_usuario, nm_completo
        FROM T_LGT_USUARIO
        WHERE (UPPER(username) = UPPER(:login) OR UPPER(email) = UPPER(:login))
          AND senha = :senha
    """
    linhas = consultar(conexao, sql, "Erro ao entrar", login=login, senha=senha)

    if not linhas:
        return None

    return {"id": linhas[0][0], "nome": linhas[0][1]}


def campo_ja_cadastrado(conexao: oracledb.Connection, campo: str, valor: str, id_usuario: int = 0) -> bool:
    """
    Diz se já existe usuário com o mesmo CPF, e-mail ou username (o banco
    não aceita repetidos).
    Entrada: conexao (conexão aberta); campo (str): "cpf", "email" ou
             "username"; valor (str) a procurar (CPF só com números);
             id_usuario (int), usuário a ignorar na busca (use ao alterar os
             dados de alguém, para não acusar o próprio valor); 0 não ignora
             ninguém.
    Saida: True se já existe; False se está livre.
    """
    if campo == "cpf":
        condicao = "REPLACE(REPLACE(cpf, '.', ''), '-', '') = :valor"
    elif campo == "email":
        condicao = "UPPER(email) = UPPER(:valor)"
    else:
        condicao = "UPPER(username) = UPPER(:valor)"

    sql = f"SELECT COUNT(*) FROM T_LGT_USUARIO WHERE {condicao} AND id_usuario <> :id_usuario"
    linhas = consultar(conexao, sql, "Erro ao verificar o cadastro", valor=valor, id_usuario=id_usuario)

    return linhas[0][0] > 0


def inserir_usuario(
    conexao: oracledb.Connection,
    nome: str,
    cpf: str,
    email: str,
    username: str,
    senha: str,
    nascimento,
) -> None:
    """
    CREATE: cadastra um usuário comum, com nível 1 e saldo 0. O id é gerado
    pelo banco. Perfil de moderador ou criador não é dado por aqui.
    Entrada: conexao; nome, cpf (formatado, 14 caracteres), email, username
             e senha (str); nascimento (datetime).
    Saida: não retorna valor.
    Erro: ErroBanco se o banco recusar (por exemplo, CPF repetido).
    """
    sql = """
        INSERT INTO T_LGT_USUARIO
            (nm_completo, cpf, email, username, senha, dt_nascimento,
             sd_ponto, nv_usuario, tipo_perfil)
        VALUES (:nome, :cpf, :email, :username, :senha, :nascimento,
                0, 1, :perfil)
    """
    alterar(
        conexao, sql, "Não foi possível cadastrar o usuário",
        nome=nome, cpf=cpf, email=email, username=username,
        senha=senha, nascimento=nascimento, perfil=PERFIL_COMUM,
    )


def buscar_perfil(conexao: oracledb.Connection, id_usuario: int) -> dict | None:
    """
    READ: busca os dados do perfil de um usuário (sem CPF e sem senha).
    Entrada: conexao (conexão aberta); id_usuario (int).
    Saida: dict com nome, email, username, nascimento (datetime), nivel,
           perfil e pontos; ou None se o usuário não existir.
    """
    sql = """
        SELECT nm_completo, email, username, dt_nascimento,
               nv_usuario, tipo_perfil, sd_ponto
        FROM T_LGT_USUARIO
        WHERE id_usuario = :id_usuario
    """
    linhas = consultar(conexao, sql, "Erro ao buscar o perfil", id_usuario=id_usuario)

    if not linhas:
        return None

    linha = linhas[0]

    return {
        "nome": linha[0],
        "email": linha[1],
        "username": linha[2],
        "nascimento": linha[3],
        "nivel": linha[4],
        "perfil": linha[5],
        "pontos": float(linha[6]),
    }


def atualizar_usuario(conexao: oracledb.Connection, id_usuario: int, nome: str, username: str) -> bool:
    """
    UPDATE: troca nome e username. E-mail, data de nascimento, CPF, perfil,
    nível e pontos não são alterados por aqui.
    Entrada: conexao; id_usuario (int); nome e username (str).
    Saida: True se atualizou; False se o usuário não existe.
    Erro: ErroBanco se o banco recusar (por exemplo, username repetido).
    """
    sql = """
        UPDATE T_LGT_USUARIO
        SET nm_completo = :nome, username = :username
        WHERE id_usuario = :id_usuario
    """
    quantidade = alterar(
        conexao, sql, "Não foi possível atualizar o perfil",
        nome=nome, username=username, id_usuario=id_usuario,
    )

    return quantidade > 0


def atualizar_senha(conexao: oracledb.Connection, id_usuario: int, senha_atual: str, senha_nova: str) -> bool:
    """
    UPDATE: troca a senha, desde que a senha atual esteja certa.
    Entrada: conexao; id_usuario (int); senha_atual e senha_nova (str), já
             preparadas com dados.preparar_senha.
    Saida: True se trocou; False se a senha atual não confere.
    Erro: ErroBanco se o banco recusar.
    """
    sql = """
        UPDATE T_LGT_USUARIO
        SET senha = :senha_nova
        WHERE id_usuario = :id_usuario AND senha = :senha_atual
    """
    quantidade = alterar(
        conexao, sql, "Não foi possível trocar a senha",
        senha_nova=senha_nova, id_usuario=id_usuario, senha_atual=senha_atual,
    )

    return quantidade > 0


def excluir_usuario(conexao: oracledb.Connection, id_usuario: int, senha: str) -> bool:
    """
    DELETE: exclui a conta, desde que a senha esteja certa. O banco recusa
    se a conta tiver vínculos (postagens, comunidades, resgates...).
    Entrada: conexao; id_usuario (int); senha (str) já preparada com
             dados.preparar_senha.
    Saida: True se excluiu; False se a senha não confere.
    Erro: ErroBanco se o banco recusar.
    """
    sql = "DELETE FROM T_LGT_USUARIO WHERE id_usuario = :id_usuario AND senha = :senha"
    quantidade = alterar(
        conexao, sql,
        "Não foi possível excluir a conta (contas com postagens, comunidades ou outros vínculos não podem ser excluídas)",
        id_usuario=id_usuario, senha=senha,
    )

    return quantidade > 0


# COMUNIDADES

def listar_comunidades(conexao: oracledb.Connection) -> list[dict]:
    """
    Lista todas as comunidades da plataforma.
    Entrada: conexao (conexão aberta).
    Saida: lista de dicts com id e nome, podendo estar vazia.
    """
    sql = "SELECT id_comunidade, nm_comunidade FROM T_LGT_COMUNIDADE ORDER BY id_comunidade"
    linhas = consultar(conexao, sql, "Erro ao consultar as comunidades")
    lista = []

    for linha in linhas:
        lista.append({"id": linha[0], "nome": linha[1]})

    return lista


def entrar_na_comunidade(conexao: oracledb.Connection, id_usuario: int, id_comunidade: int) -> None:
    """
    CREATE: coloca o usuário como membro de uma comunidade.
    Entrada: conexao; id_usuario (int); id_comunidade (int).
    Saida: não retorna valor.
    Erro: ErroBanco se o banco recusar (por exemplo, já é membro).
    """
    sql = """
        INSERT INTO T_LGT_USUARIO_COMUNIDADE
            (T_LGT_USUARIO_id_usuario, T_LGT_COMUNIDADE_id_comunidade, membros)
        VALUES (:id_usuario, :id_comunidade, :membro)
    """
    alterar(
        conexao, sql, "Não foi possível entrar na comunidade",
        id_usuario=id_usuario, id_comunidade=id_comunidade, membro=MEMBRO,
    )


def sair_da_comunidade(conexao: oracledb.Connection, id_usuario: int, id_comunidade: int) -> bool:
    """
    DELETE: tira o usuário da comunidade (as postagens dele continuam).
    Entrada: conexao; id_usuario (int); id_comunidade (int).
    Saida: True se saiu; False se ele não era membro.
    Erro: ErroBanco se o banco recusar.
    """
    sql = """
        DELETE FROM T_LGT_USUARIO_COMUNIDADE
        WHERE T_LGT_USUARIO_id_usuario = :id_usuario
          AND T_LGT_COMUNIDADE_id_comunidade = :id_comunidade
    """
    quantidade = alterar(
        conexao, sql, "Não foi possível sair da comunidade",
        id_usuario=id_usuario, id_comunidade=id_comunidade,
    )

    return quantidade > 0


def listar_comunidades_do_usuario(conexao: oracledb.Connection, id_usuario: int) -> list[dict]:
    """
    Lista as comunidades em que o usuário é membro (só nelas ele pode
    registrar ações, como na API).
    Entrada: conexao (conexão aberta); id_usuario (int).
    Saida: lista de dicts com id e nome, podendo estar vazia.
    """
    # O JOIN com a tabela de associação traz só as comunidades do usuário
    sql = """
        SELECT c.id_comunidade, c.nm_comunidade
        FROM T_LGT_COMUNIDADE c
        JOIN T_LGT_USUARIO_COMUNIDADE uc
          ON uc.T_LGT_COMUNIDADE_id_comunidade = c.id_comunidade
        WHERE uc.T_LGT_USUARIO_id_usuario = :id_usuario
        ORDER BY c.id_comunidade
    """
    linhas = consultar(conexao, sql, "Erro ao consultar as comunidades", id_usuario=id_usuario)
    lista = []

    for linha in linhas:
        lista.append({"id": linha[0], "nome": linha[1]})

    return lista


# CRUD DE POSTAGENS

COLUNAS_POSTAGEM = """
    id_postagem, ct_texto, ct_url, st_validacao, pt_gerado,
    T_LGT_USUARIO_id_usuario, T_LGT_COMUNIDADE_id_comunidade
"""


def montar_postagem(linha: tuple) -> dict:
    """
    Converte uma linha do SELECT de postagens em dicionário.
    Entrada: linha (tuple) na ordem de COLUNAS_POSTAGEM.
    Saida: dict com id, acao, url, status, pontos, id_usuario e id_comunidade.
    """
    return {
        "id": linha[0],
        "acao": linha[1],
        "url": linha[2],
        "status": linha[3],
        "pontos": float(linha[4]),
        "id_usuario": linha[5],
        "id_comunidade": linha[6],
    }


def montar_lista_de_postagens(linhas: list) -> list[dict]:
    """
    Converte várias linhas do SELECT de postagens em uma lista de dicts.
    Entrada: linhas (list) de tuplas na ordem de COLUNAS_POSTAGEM.
    Saida: lista de dicts (ver montar_postagem), podendo estar vazia.
    """
    lista = []

    for linha in linhas:
        lista.append(montar_postagem(linha))

    return lista


def inserir_postagem(
    conexao: oracledb.Connection,
    acao: str,
    url: str,
    pontos: float,
    id_usuario: int,
    id_comunidade: int,
) -> None:
    """
    CREATE: grava uma ação como postagem PENDENTE (a moderação decide depois).
    Entrada: conexao; acao (str); url (str); pontos (float); id_usuario (int);
             id_comunidade (int).
    Saida: não retorna valor; o id da postagem é gerado pelo banco.
    Erro: ErroBanco se o banco recusar.
    """
    sql = """
        INSERT INTO T_LGT_POSTAGEM
            (ct_texto, ct_url, st_validacao, pt_gerado,
             T_LGT_USUARIO_id_usuario, T_LGT_COMUNIDADE_id_comunidade)
        VALUES (:acao, :url, :status, :pontos, :id_usuario, :id_comunidade)
    """
    alterar(
        conexao, sql, "Não foi possível registrar a ação",
        acao=acao, url=url, status=STATUS_PENDENTE, pontos=pontos,
        id_usuario=id_usuario, id_comunidade=id_comunidade,
    )


def listar_postagens(conexao: oracledb.Connection, id_usuario: int) -> list[dict]:
    """
    READ: lista as postagens de um usuário, da mais antiga para a mais nova.
    Entrada: conexao; id_usuario (int).
    Saida: lista de dicts (ver montar_postagem), podendo estar vazia.
    """
    sql = f"""
        SELECT {COLUNAS_POSTAGEM}
        FROM T_LGT_POSTAGEM
        WHERE T_LGT_USUARIO_id_usuario = :id_usuario
        ORDER BY id_postagem
    """
    linhas = consultar(conexao, sql, "Erro ao listar os registros", id_usuario=id_usuario)

    return montar_lista_de_postagens(linhas)


def buscar_postagens(conexao: oracledb.Connection, id_usuario: int, nome: str) -> list[dict]:
    """
    READ: busca as postagens do usuário com o nome de ação exato (sem
    diferenciar maiúsculas/minúsculas).
    Entrada: conexao; id_usuario (int); nome (str).
    Saida: lista de dicts, podendo estar vazia.
    """
    # ct_texto é CLOB; DBMS_LOB.SUBSTR converte para texto para poder comparar
    sql = f"""
        SELECT {COLUNAS_POSTAGEM}
        FROM T_LGT_POSTAGEM
        WHERE T_LGT_USUARIO_id_usuario = :id_usuario
          AND UPPER(DBMS_LOB.SUBSTR(ct_texto, 4000, 1)) = UPPER(:nome)
        ORDER BY id_postagem
    """
    linhas = consultar(conexao, sql, "Erro ao buscar os registros", id_usuario=id_usuario, nome=nome)

    return montar_lista_de_postagens(linhas)


def atualizar_postagem(conexao: oracledb.Connection, id_postagem: int,
                       id_usuario: int, nome: str) -> bool:
    """
    UPDATE: troca o nome da ação. Só altera postagens PENDENTES do próprio
    usuário (depois da moderação os pontos já foram decididos).
    Entrada: conexao; id_postagem (int); id_usuario (int); nome (str).
    Saida: True se atualizou; False se não existe, não é do usuário ou já
           foi moderada.
    Erro: ErroBanco se o banco recusar.
    """
    sql = """
        UPDATE T_LGT_POSTAGEM
        SET ct_texto = :nome
        WHERE id_postagem = :id_postagem
          AND T_LGT_USUARIO_id_usuario = :id_usuario
          AND st_validacao = :status
    """
    quantidade = alterar(
        conexao, sql, "Não foi possível atualizar o registro",
        nome=nome, id_postagem=id_postagem, id_usuario=id_usuario, status=STATUS_PENDENTE,
    )

    # 0 se o registro não existe, não é do usuário ou não está PENDENTE
    return quantidade > 0


def excluir_postagem(conexao: oracledb.Connection, id_postagem: int, id_usuario: int) -> bool:
    """
    DELETE: remove uma postagem PENDENTE do próprio usuário.
    Entrada: conexao; id_postagem (int); id_usuario (int).
    Saida: True se excluiu; False se não existe, não é do usuário ou já
           foi moderada.
    Erro: ErroBanco se o banco recusar.
    """
    sql = """
        DELETE FROM T_LGT_POSTAGEM
        WHERE id_postagem = :id_postagem
          AND T_LGT_USUARIO_id_usuario = :id_usuario
          AND st_validacao = :status
    """
    quantidade = alterar(
        conexao, sql, "Não foi possível excluir o registro",
        id_postagem=id_postagem, id_usuario=id_usuario, status=STATUS_PENDENTE,
    )

    # 0 se o registro não existe, não é do usuário ou não está PENDENTE
    return quantidade > 0
