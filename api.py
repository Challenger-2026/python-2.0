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
    dados = buscar_json("/usuarios")
    lista = []

    try:
        # Converte os campos em camelCase da API para os nomes usados no sistema
        for item in dados:
            lista.append({
                "id": item["id"],
                "nome": item["nmCompleto"],
                "username": item["username"],
                "pontos": float(item["sdPonto"]),
                "perfil": item["tipoPerfil"],
            })
    except (KeyError, TypeError, ValueError):
        raise ErroApi("Os usuários vieram da API em formato inesperado.")

    return lista


def listar_comunidades_api() -> list[dict]:
    """
    GET /comunidades: lista as comunidades da plataforma.
    Entrada: não recebe parâmetros.
    Saida: lista de dicts com id, nome e descricao.
    Erro: ErroApi se a consulta falhar.
    """
    dados = buscar_json("/comunidades")
    lista = []

    try:
        # Converte os campos da API para os nomes usados no sistema
        for item in dados:
            lista.append({
                "id": item["id"],
                "nome": item["nmComunidade"],
                "descricao": item["descricao"],
            })
    except (KeyError, TypeError):
        raise ErroApi("As comunidades vieram da API em formato inesperado.")

    return lista


def listar_postagens_api() -> list[dict]:
    """
    GET /postagens: lista as postagens (ações registradas) de todos os
    usuários, no mesmo formato de banco.montar_postagem.
    Entrada: não recebe parâmetros.
    Saida: lista de dicts com id, acao, url, status, pontos, id_usuario e
           id_comunidade.
    Erro: ErroApi se a consulta falhar.
    """
    dados = buscar_json("/postagens")
    lista = []

    try:
        # Converte os campos da API para os nomes usados no sistema
        for item in dados:
            lista.append({
                "id": item["id"],
                "acao": item["ctTexto"],
                "url": item["ctUrl"],
                "status": item["stValidacao"],
                "pontos": float(item["ptGerado"]),
                "id_usuario": item["idUsuario"],
                "id_comunidade": item["idComunidade"],
            })
    except (KeyError, TypeError, ValueError):
        raise ErroApi("As postagens vieram da API em formato inesperado.")

    return lista
