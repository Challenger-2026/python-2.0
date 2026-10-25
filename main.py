"""
Ponto de entrada do Sistema de Pontos Ambientais - Lobo-guará Tech.

O sistema abre direto no menu principal. O usuário só é identificado (por
CPF, no banco) na primeira vez que escolhe uma opção que precisa dele.
Este módulo só organiza o fluxo entre os menus: o cálculo e a validação
ficam em dados.py, o acesso ao banco fica em banco.py e a interação com o
usuário fica em menu.py. A sessão (usuário e comunidade em uso) é um dict
com as chaves "usuario" e "id_comunidade".
"""

import os

import banco
import dados
import menu


def garante_identificacao(conexao, sessao: dict) -> bool:
    """
    Identifica o usuário se ainda não houver ninguém identificado na sessão.
    Entrada: conexao (conexão aberta); sessao (dict) que é atualizado.
    Saida: True se há um usuário identificado; False se ele desistiu.
    """
    if sessao["usuario"] is None:
        sessao["usuario"], sessao["id_comunidade"] = menu.identificar_usuario(conexao)

    return sessao["usuario"] is not None


def executa_menu_crud(conexao, id_usuario: int) -> None:
    """
    Mostra o submenu "Gerenciar ações" até o usuário voltar.
    Entrada: conexao (conexão aberta); id_usuario (int).
    Saida: não retorna valor.
    """
    while True:
        opcao = menu.menu_crud()

        match opcao:
            case "1":
                menu.listar_registros_interativo(conexao, id_usuario)
            case "2":
                menu.buscar_registro_interativo(conexao, id_usuario)
            case "3":
                menu.atualizar_registro_interativo(conexao, id_usuario)
            case "4":
                menu.excluir_registro_interativo(conexao, id_usuario)
            case "5":
                return


def executa_menu_relatorios(conexao, id_usuario: int) -> None:
    """
    Mostra o submenu "Relatórios" até o usuário voltar.
    Entrada: conexao (conexão aberta); id_usuario (int).
    Saida: não retorna valor.
    """
    while True:
        opcao = menu.menu_relatorios()

        match opcao:
            case "1":
                menu.listar_registros_interativo(conexao, id_usuario)
            case "2":
                menu.relatorio_por_status_interativo(conexao, id_usuario)
            case "3":
                menu.relatorio_por_pontos_interativo(conexao, id_usuario)
            case "4":
                return


def executa_opcao_do_usuario(conexao, sessao: dict, opcao: str) -> None:
    """
    Executa uma opção do menu principal que precisa de usuário identificado.
    Entrada: conexao (conexão aberta); sessao (dict) com usuario e
             id_comunidade; opcao (str): "1" registrar, "2" gerenciar ou
             "3" relatórios.
    Saida: não retorna valor.
    """
    usuario = sessao["usuario"]

    match opcao:
        case "1":
            menu.registrar_pontos(
                conexao,
                usuario,
                sessao["id_comunidade"],
                dados.periodos,
                dados.niveis_impacto,
                dados.progresso,
                dados.LIMITE_TOTAL,
                dados.LIMITE_DIAS,
                dados.LIMITE_ACOES,
            )
        case "2":
            executa_menu_crud(conexao, usuario["id"])
        case "3":
            executa_menu_relatorios(conexao, usuario["id"])


def executa_menu_principal(conexao) -> None:
    """
    Mostra o menu principal até o usuário sair.
    Entrada: conexao (conexão aberta).
    Saida: não retorna valor.
    """
    sessao = {"usuario": None, "id_comunidade": None}

    while True:
        nome_usuario = sessao["usuario"]["nome"] if sessao["usuario"] else None
        opcao = menu.menu_principal(nome_usuario)

        if opcao == "0":
            print("Encerrando o sistema...")
            return

        if opcao == "4":
            sessao = {"usuario": None, "id_comunidade": None}
            dados.progresso["ativo"] = False
            continue

        if garante_identificacao(conexao, sessao):
            executa_opcao_do_usuario(conexao, sessao, opcao)


def main() -> None:
    """
    Abre a conexão com o banco, executa o sistema e fecha a conexão no fim.
    Entrada: não recebe parametros; utiliza os menus interativos.
    Saida: não retorna valor.
    """
    os.system("cls" if os.name == "nt" else "clear")

    try:
        conexao = banco.conectar()
    except banco.ErroBanco as erro:
        print(f"Erro: {erro}")
        return

    try:
        executa_menu_principal(conexao)
    except banco.ErroBanco as erro:
        print(f"\nErro: {erro}")
    finally:
        conexao.close()


if __name__ == "__main__":
    main()
