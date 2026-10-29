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
    # Só pergunta o CPF se ninguém foi identificado ainda
    if sessao["usuario"] is None:
        sessao["usuario"], sessao["id_comunidade"] = menu.identificar_usuario(conexao)

    return sessao["usuario"] is not None


def registra_pontos_da_sessao(conexao, sessao: dict) -> None:
    """
    Abre o fluxo "Registrar pontos" para o usuário da sessão. É o INSERT do
    sistema: cada ação registrada vira uma postagem no banco. Usada pelo menu
    principal e pelo submenu "Gerenciar ações".
    Entrada: conexao (conexão aberta); sessao (dict) com usuario e
             id_comunidade.
    Saida: não retorna valor.
    """
    menu.registrar_pontos(
        conexao,
        sessao["usuario"],
        sessao["id_comunidade"],
        dados.periodos,
        dados.niveis_impacto,
        dados.progresso,
        dados.LIMITE_TOTAL,
        dados.LIMITE_DIAS,
        dados.LIMITE_ACOES,
    )


def executa_menu_crud(conexao, sessao: dict) -> None:
    """
    Mostra o submenu "Gerenciar ações" (o CRUD) até o usuário voltar.
    Entrada: conexao (conexão aberta); sessao (dict) com usuario e
             id_comunidade.
    Saida: não retorna valor.
    """
    id_usuario = sessao["usuario"]["id"]

    while True:
        opcao = menu.menu_crud()

        match opcao:
            case "1":
                registra_pontos_da_sessao(conexao, sessao)
            case "2":
                menu.listar_registros_interativo(conexao, id_usuario)
            case "3":
                menu.buscar_registro_interativo(conexao, id_usuario)
            case "4":
                menu.atualizar_registro_interativo(conexao, id_usuario)
            case "5":
                menu.excluir_registro_interativo(conexao, id_usuario)
            case "6":
                return


def executa_menu_relatorios(conexao, usuario: dict, id_comunidade: int | None) -> None:
    """
    Mostra o submenu "Relatórios" até o usuário voltar.
    Entrada: conexao (conexão aberta); usuario (dict com id e nome);
             id_comunidade (int, ou None).
    Saida: não retorna valor.
    """
    while True:
        opcao = menu.menu_relatorios()

        match opcao:
            case "1":
                menu.listar_registros_interativo(conexao, usuario["id"])
            case "2":
                menu.relatorio_por_status_interativo(conexao, usuario["id"])
            case "3":
                menu.relatorio_por_pontos_interativo(conexao, usuario["id"])
            case "4":
                menu.exportar_registros_interativo(conexao, usuario)
            case "5":
                menu.exportar_respostas_interativo(usuario, id_comunidade)
            case "6":
                return


def executa_menu_api() -> None:
    """
    Mostra o submenu "Consultar API pública" até o usuário voltar. Não
    precisa de usuário identificado, pois consulta dados de toda a plataforma.
    Entrada: não recebe parâmetros.
    Saida: não retorna valor.
    """
    while True:
        opcao = menu.menu_api()

        match opcao:
            case "1":
                menu.ranking_api_interativo()
            case "2":
                menu.postagens_da_comunidade_api_interativo()
            case "3":
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
            registra_pontos_da_sessao(conexao, sessao)
        case "2":
            executa_menu_crud(conexao, sessao)
        case "3":
            executa_menu_relatorios(conexao, usuario, sessao["id_comunidade"])


def executa_menu_principal(conexao) -> None:
    """
    Mostra o menu principal até o usuário sair.
    Entrada: conexao (conexão aberta).
    Saida: não retorna valor.
    """
    sessao = {"usuario": None, "id_comunidade": None}

    while True:
        nome_usuario = None

        if sessao["usuario"] is not None:
            nome_usuario = sessao["usuario"]["nome"]

        opcao = menu.menu_principal(nome_usuario)

        if opcao == "0":
            print("Encerrando o sistema...")
            return

        # Trocar de usuário: zera a sessão, o progresso e as respostas guardadas
        if opcao == "4":
            sessao = {"usuario": None, "id_comunidade": None}
            dados.progresso["ativo"] = False
            dados.respostas_usuario.clear()
            continue

        # A consulta à API não precisa de usuário identificado
        if opcao == "5":
            executa_menu_api()
            continue

        # Opções 1, 2 e 3 só rodam com usuário identificado
        if garante_identificacao(conexao, sessao):
            executa_opcao_do_usuario(conexao, sessao, opcao)


def main() -> None:
    """
    Abre a conexão com o banco, executa o sistema e fecha a conexão no fim.
    Entrada: não recebe parametros; utiliza os menus interativos.
    Saida: não retorna valor.
    """
    # Limpa o terminal (cls no Windows, clear nos outros sistemas)
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")

    try:
        conexao = banco.conectar()
    except banco.ErroBanco as erro:
        print(f"Erro: {erro}")
        return

    try:
        executa_menu_principal(conexao)
    except banco.ErroBanco as erro:
        print(f"\nErro: {erro}")
    except (KeyboardInterrupt, EOFError):
        # Ctrl+C ou Ctrl+D encerram o sistema sem mostrar o erro do Python
        print("\nSistema encerrado.")
    finally:
        # Fecha a conexão com o banco mesmo se ocorrer erro
        conexao.close()


if __name__ == "__main__":
    main()
