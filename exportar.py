"""
Exportação de dados do Sistema de Pontos Ambientais para arquivos JSON.

Gera dois arquivos na pasta "exportacoes" do projeto:
    crud_usuario_<id>.json      -> as ações do usuário que estão no banco
    respostas_usuario_<id>.json -> o que o usuário respondeu em "Registrar
                                   pontos" (dia a dia)
Nenhuma função aqui usa print() ou input().
"""

import json
import os
from datetime import datetime

PASTA_EXPORTACAO: str = "exportacoes"


class ErroExportacao(Exception):
    """Erro ao gravar o arquivo, com mensagem amigável para o usuário."""


def monta_exportacao_crud(usuario: dict, registros: list[dict]) -> dict:
    """
    Monta o conteúdo do JSON com as ações do usuário que estão no banco.
    Entrada: usuario (dict com id e nome); registros (list[dict]) no formato
             de banco.montar_postagem.
    Saida: dict pronto para virar JSON, com o usuário, a data da exportação,
           o total de registros, o total de pontos e a lista de registros.
    """
    total_pontos = 0

    for registro in registros:
        total_pontos += registro["pontos"]

    return {
        "usuario": {"id": usuario["id"], "nome": usuario["nome"]},
        "exportado_em": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "total_registros": len(registros),
        "total_pontos": round(total_pontos, 2),
        "registros": registros,
    }


def monta_exportacao_respostas(usuario: dict, id_comunidade: int | None, respostas: list[dict]) -> dict:
    """
    Monta o conteúdo do JSON com as respostas dadas em "Registrar pontos".
    Entrada: usuario (dict com id e nome); id_comunidade (int, ou None);
             respostas (list[dict]), uma por dia registrado.
    Saida: dict pronto para virar JSON, com o usuário, a comunidade, um
           resumo (dias, dias com ação e pontos) e a lista de respostas.
    """
    dias_com_acao = 0
    total_pontos = 0

    for resposta in respostas:
        total_pontos += resposta["pontos"]

        # Conta só os dias em que houve ação
        if resposta["fez_acao"]:
            dias_com_acao += 1

    return {
        "usuario": {"id": usuario["id"], "nome": usuario["nome"]},
        "id_comunidade": id_comunidade,
        "exportado_em": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "resumo": {
            "dias_registrados": len(respostas),
            "dias_com_acao": dias_com_acao,
            "total_pontos": round(total_pontos, 2),
        },
        "respostas": respostas,
    }


def salvar_json(nome_arquivo: str, conteudo: dict) -> str:
    """
    Grava o conteúdo em um arquivo JSON na pasta "exportacoes" do projeto,
    criando a pasta se não existir. Se o arquivo já existir, é substituído.
    Entrada: nome_arquivo (str), por exemplo "crud_usuario_1.json";
             conteudo (dict) com tipos que o JSON aceita.
    Saida: caminho completo (str) do arquivo gravado.
    Erro: ErroExportacao se não for possível gravar.
    """
    # Grava sempre na pasta "exportacoes", ao lado deste arquivo
    pasta_do_projeto = os.path.dirname(os.path.abspath(__file__))
    pasta_destino = os.path.join(pasta_do_projeto, PASTA_EXPORTACAO)
    caminho_arquivo = os.path.join(pasta_destino, nome_arquivo)

    try:
        # exist_ok evita erro se a pasta já existir
        os.makedirs(pasta_destino, exist_ok=True)

        with open(caminho_arquivo, "w", encoding="utf-8") as arquivo_json:
            # ensure_ascii=False mantém os acentos; indent deixa o arquivo legível
            json.dump(conteudo, arquivo_json, ensure_ascii=False, indent=4)
    except (OSError, TypeError) as erro:
        raise ErroExportacao(f"Não foi possível gravar o arquivo {nome_arquivo}: {erro}")

    return caminho_arquivo
