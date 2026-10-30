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


def monta_exportacao_crud(usuario: dict, registros: list[dict]) -> dict:
    """
    Monta o conteúdo do JSON com as ações do usuário que estão no banco.
    Entrada: usuario (dict com id e nome); registros (list[dict]) no formato
             de banco.montar_postagem.
    Saida: dict pronto para virar JSON, com o usuário, a data da exportação,
           o total de registros, o total de pontos e a lista de registros.
    """
    total = 0

    for item in registros:
        total += item["pontos"]

    return {
        "usuario": {"id": usuario["id"], "nome": usuario["nome"]},
        "exportado_em": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "total_registros": len(registros),
        "total_pontos": round(total, 2),
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
    dias = 0
    total = 0

    for item in respostas:
        total += item["pontos"]

        # Conta só os dias em que houve ação
        if item["fez_acao"]:
            dias += 1

    return {
        "usuario": {"id": usuario["id"], "nome": usuario["nome"]},
        "id_comunidade": id_comunidade,
        "exportado_em": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "resumo": {
            "dias_registrados": len(respostas),
            "dias_com_acao": dias,
            "total_pontos": round(total, 2),
        },
        "respostas": respostas,
    }


def salvar_json(nome: str, conteudo: dict) -> str:
    """
    Grava o conteúdo em um arquivo JSON na pasta "exportacoes" do projeto,
    criando a pasta se não existir. Se o arquivo já existir, é substituído.
    Entrada: nome (str), por exemplo "crud_usuario_1.json";
             conteudo (dict) com tipos que o JSON aceita.
    Saida: caminho completo (str) do arquivo gravado.
    Erro: RuntimeError se não for possível gravar.
    """
    # Grava sempre na pasta "exportacoes", ao lado deste arquivo
    pasta = os.path.dirname(os.path.abspath(__file__))
    destino = os.path.join(pasta, PASTA_EXPORTACAO)
    caminho = os.path.join(destino, nome)

    try:
        # exist_ok evita erro se a pasta já existir
        os.makedirs(destino, exist_ok=True)

        with open(caminho, "w", encoding="utf-8") as arquivo:
            # ensure_ascii=False mantém os acentos; indent deixa o arquivo legível
            json.dump(conteudo, arquivo, ensure_ascii=False, indent=4)
    except (OSError, TypeError) as erro:
        raise RuntimeError(f"Não foi possível gravar o arquivo {nome}: {erro}")

    return caminho
