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


class ErroBanco(Exception):
    """Erro de banco com mensagem amigável para mostrar ao usuário."""



# CONEXÃO

def carregar_env(caminho_env: str = "") -> None:
    """
    Lê linhas CHAVE=valor do arquivo .env e coloca em os.environ. Se não
    for informado, procura o .env na mesma pasta deste arquivo.
    Entrada: caminho_env (str), opcional.
    Saida: não retorna valor.
    """
    if not caminho_env:
        pasta_do_projeto = os.path.dirname(os.path.abspath(__file__))
        caminho_env = os.path.join(pasta_do_projeto, ".env")

    try:
        with open(caminho_env, encoding="utf-8") as arquivo_env:
            linhas_do_arquivo = arquivo_env.readlines()
    except OSError:
        return

    for linha in linhas_do_arquivo:
        linha = linha.strip()

        if not linha or linha.startswith("#") or "=" not in linha:
            continue

        nome_variavel, valor_variavel = linha.split("=", 1)
        # setdefault não sobrescreve uma variável já definida no ambiente
        os.environ.setdefault(nome_variavel.strip(), valor_variavel.strip())


def conectar() -> oracledb.Connection:
    """
    Abre a conexão com o Oracle usando as variáveis DB_*.
    Entrada: não recebe parâmetros.
    Saida: conexão aberta; quem chama deve fechar.
    Erro: ErroBanco se faltar variável ou o banco não responder.
    """
    carregar_env()

    usuario_banco = os.environ.get("DB_USER", "")
    senha_banco = os.environ.get("DB_PASSWORD", "")

    if not usuario_banco or not senha_banco:
        raise ErroBanco("Defina DB_USER e DB_PASSWORD no arquivo .env.")

    try:
        # Monta o endereço do Oracle (host, porta e SID); usa valores padrão se faltar
        endereco_banco = oracledb.makedsn(
            os.environ.get("DB_HOST", "oracle.fiap.com.br"),
            int(os.environ.get("DB_PORT", "1521")),
            sid=os.environ.get("DB_SID", "ORCL"),
        )
        return oracledb.connect(user=usuario_banco, password=senha_banco, dsn=endereco_banco)
    except (oracledb.Error, ValueError) as erro:
        raise ErroBanco(f"Não foi possível conectar ao banco: {erro}")



# USUÁRIO E COMUNIDADE (consulta)


def buscar_usuario_por_cpf(conexao: oracledb.Connection, cpf: str) -> dict | None:
    """
    Procura um usuário pelo CPF (com ou sem pontuação no banco).
    Entrada: conexao (conexão aberta); cpf (str) com 11 números.
    Saida: dict com id e nome, ou None se não existir.
    """
    # REPLACE tira pontos e traço do CPF salvo, para comparar só os números
    sql = """
        SELECT id_usuario, nm_completo
        FROM T_LGT_USUARIO
        WHERE REPLACE(REPLACE(cpf, '.', ''), '-', '') = :cpf
    """
    cursor = conexao.cursor()

    try:
        cursor.execute(sql, cpf=cpf)
        linha_encontrada = cursor.fetchone()
    except oracledb.Error as erro:
        raise ErroBanco(f"Erro ao consultar o usuário: {erro}")
    finally:
        cursor.close()

    if linha_encontrada is None:
        return None

    return {"id": linha_encontrada[0], "nome": linha_encontrada[1]}


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
    cursor = conexao.cursor()

    try:
        cursor.execute(sql, id_usuario=id_usuario)
        linhas_encontradas = cursor.fetchall()
    except oracledb.Error as erro:
        raise ErroBanco(f"Erro ao consultar as comunidades: {erro}")
    finally:
        cursor.close()

    comunidades = []

    for linha in linhas_encontradas:
        comunidades.append({"id": linha[0], "nome": linha[1]})

    return comunidades



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
    postagens = []

    for linha in linhas:
        postagens.append(montar_postagem(linha))

    return postagens


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
    cursor = conexao.cursor()

    try:
        cursor.execute(
            sql,
            acao=acao,
            url=url,
            status=STATUS_PENDENTE,
            pontos=pontos,
            id_usuario=id_usuario,
            id_comunidade=id_comunidade,
        )
    except oracledb.Error as erro:
        conexao.rollback()
        raise ErroBanco(f"Não foi possível registrar a ação: {erro}")
    else:
        # Só confirma (commit) se o INSERT deu certo
        conexao.commit()
    finally:
        cursor.close()


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
    cursor = conexao.cursor()

    try:
        cursor.execute(sql, id_usuario=id_usuario)
        linhas_encontradas = cursor.fetchall()
    except oracledb.Error as erro:
        raise ErroBanco(f"Erro ao listar os registros: {erro}")
    finally:
        cursor.close()

    return montar_lista_de_postagens(linhas_encontradas)


def buscar_postagens(conexao: oracledb.Connection, id_usuario: int, nome_da_acao: str) -> list[dict]:
    """
    READ: busca as postagens do usuário com o nome de ação exato (sem
    diferenciar maiúsculas/minúsculas).
    Entrada: conexao; id_usuario (int); nome_da_acao (str).
    Saida: lista de dicts, podendo estar vazia.
    """
    # ct_texto é CLOB; DBMS_LOB.SUBSTR converte para texto para poder comparar
    sql = f"""
        SELECT {COLUNAS_POSTAGEM}
        FROM T_LGT_POSTAGEM
        WHERE T_LGT_USUARIO_id_usuario = :id_usuario
          AND UPPER(DBMS_LOB.SUBSTR(ct_texto, 4000, 1)) = UPPER(:nome_da_acao)
        ORDER BY id_postagem
    """
    cursor = conexao.cursor()

    try:
        cursor.execute(sql, id_usuario=id_usuario, nome_da_acao=nome_da_acao)
        linhas_encontradas = cursor.fetchall()
    except oracledb.Error as erro:
        raise ErroBanco(f"Erro ao buscar os registros: {erro}")
    finally:
        cursor.close()

    return montar_lista_de_postagens(linhas_encontradas)


def atualizar_postagem(conexao: oracledb.Connection, id_postagem: int,
                       id_usuario: int, novo_nome: str) -> bool:
    """
    UPDATE: troca o nome da ação. Só altera postagens PENDENTES do próprio
    usuário (depois da moderação os pontos já foram decididos).
    Entrada: conexao; id_postagem (int); id_usuario (int); novo_nome (str).
    Saida: True se atualizou; False se não existe, não é do usuário ou já
           foi moderada.
    Erro: ErroBanco se o banco recusar.
    """
    sql = """
        UPDATE T_LGT_POSTAGEM
        SET ct_texto = :novo_nome
        WHERE id_postagem = :id_postagem
          AND T_LGT_USUARIO_id_usuario = :id_usuario
          AND st_validacao = :status
    """
    cursor = conexao.cursor()

    try:
        cursor.execute(
            sql,
            novo_nome=novo_nome,
            id_postagem=id_postagem,
            id_usuario=id_usuario,
            status=STATUS_PENDENTE,
        )
        # rowcount é 0 se o registro não existe, não é do usuário ou não está PENDENTE
        quantidade_alterada = cursor.rowcount
    except oracledb.Error as erro:
        conexao.rollback()
        raise ErroBanco(f"Não foi possível atualizar o registro: {erro}")
    else:
        conexao.commit()
        return quantidade_alterada > 0
    finally:
        cursor.close()


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
    cursor = conexao.cursor()

    try:
        cursor.execute(sql, id_postagem=id_postagem, id_usuario=id_usuario, status=STATUS_PENDENTE)
        # rowcount é 0 se o registro não existe, não é do usuário ou não está PENDENTE
        quantidade_excluida = cursor.rowcount
    except oracledb.Error as erro:
        conexao.rollback()
        raise ErroBanco(f"Não foi possível excluir o registro: {erro}")
    else:
        conexao.commit()
        return quantidade_excluida > 0
    finally:
        cursor.close()
