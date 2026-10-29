"""
Camada de acesso à API pública (Java/Spring Boot) do Sistema de Pontos
Ambientais, publicada no Render.

A API devolve JSON em camelCase (ctTexto, stValidacao, ptGerado...). Aqui
esses dados são convertidos para os mesmos dicts usados no resto do sistema
(acao, url, status, pontos), para que menu.py e dados.py reaproveitem as
mesmas funções de exibição e filtro. Nenhuma função aqui usa print() ou
input().
"""

import requests

URL_BASE: str = "https://guara-api.onrender.com"
TEMPO_LIMITE: int = 120   # segundos; o Render gratuito pode levar mais de 1 min para "acordar"


class ErroApi(Exception):
    """Erro de API com mensagem amigável para mostrar ao usuário."""


# ---------------------------------------------------------------------------
# REQUISIÇÃO
# ---------------------------------------------------------------------------

def buscar_json(caminho: str) -> list[dict]:
    """
    Faz um GET na API e devolve o JSON da resposta.
    Entrada: caminho (str), por exemplo "/usuarios".
    Saida: lista de dicts com o conteúdo do JSON.
    Erro: ErroApi se a API não responder, devolver erro HTTP ou um JSON
          que não seja uma lista.
    """
    try:
        resposta = requests.get(URL_BASE + caminho, timeout=TEMPO_LIMITE)
        # Transforma status HTTP de erro (4xx/5xx) em exceção
        resposta.raise_for_status()
        conteudo = resposta.json()
    except requests.Timeout:
        raise ErroApi("A API demorou demais para responder. Tente de novo.")
    except requests.ConnectionError:
        raise ErroApi("Não foi possível conectar à API. Verifique a internet.")
    except requests.HTTPError as erro:
        raise ErroApi(f"A API devolveu erro {erro.response.status_code} em {caminho}.")
    except ValueError:
        raise ErroApi("A API devolveu uma resposta que não é JSON.")
    except requests.RequestException:
        raise ErroApi("Não foi possível consultar a API.")

    # A API deve devolver uma lista; outra coisa é resposta inesperada
    if not isinstance(conteudo, list):
        raise ErroApi(f"Resposta inesperada da API em {caminho}.")

    return conteudo



# CONSULTAS

def listar_usuarios_api() -> list[dict]:
    """
    GET /usuarios: lista os usuários cadastrados na plataforma.
    Entrada: não recebe parâmetros.
    Saida: lista de dicts com id, nome, username, pontos e perfil.
    Erro: ErroApi se a consulta falhar.
    """
    usuarios_da_api = buscar_json("/usuarios")
    usuarios = []

    try:
        # Converte os campos em camelCase da API para os nomes usados no sistema
        for usuario in usuarios_da_api:
            usuarios.append({
                "id": usuario["id"],
                "nome": usuario["nmCompleto"],
                "username": usuario["username"],
                "pontos": float(usuario["sdPonto"]),
                "perfil": usuario["tipoPerfil"],
            })
    except (KeyError, TypeError, ValueError):
        raise ErroApi("Os usuários vieram da API em formato inesperado.")

    return usuarios


def listar_comunidades_api() -> list[dict]:
    """
    GET /comunidades: lista as comunidades da plataforma.
    Entrada: não recebe parâmetros.
    Saida: lista de dicts com id, nome e descricao.
    Erro: ErroApi se a consulta falhar.
    """
    comunidades_da_api = buscar_json("/comunidades")
    comunidades = []

    try:
        # Converte os campos da API para os nomes usados no sistema
        for comunidade in comunidades_da_api:
            comunidades.append({
                "id": comunidade["id"],
                "nome": comunidade["nmComunidade"],
                "descricao": comunidade["descricao"],
            })
    except (KeyError, TypeError):
        raise ErroApi("As comunidades vieram da API em formato inesperado.")

    return comunidades


def listar_postagens_api() -> list[dict]:
    """
    GET /postagens: lista as postagens (ações registradas) de todos os
    usuários, no mesmo formato de banco.montar_postagem.
    Entrada: não recebe parâmetros.
    Saida: lista de dicts com id, acao, url, status, pontos, id_usuario e
           id_comunidade.
    Erro: ErroApi se a consulta falhar.
    """
    postagens_da_api = buscar_json("/postagens")
    postagens = []

    try:
        # Converte os campos da API para os nomes usados no sistema
        for postagem in postagens_da_api:
            postagens.append({
                "id": postagem["id"],
                "acao": postagem["ctTexto"],
                "url": postagem["ctUrl"],
                "status": postagem["stValidacao"],
                "pontos": float(postagem["ptGerado"]),
                "id_usuario": postagem["idUsuario"],
                "id_comunidade": postagem["idComunidade"],
            })
    except (KeyError, TypeError, ValueError):
        raise ErroApi("As postagens vieram da API em formato inesperado.")

    return postagens
