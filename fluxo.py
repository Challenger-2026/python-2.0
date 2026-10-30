"""
Funções de apoio do programa principal (prog.py) do Sistema de Pontos Ambientais - Lobo-guará Tech.

O sistema abre direto no menu de entrada (Entrar, Cadastrar-se ou consultar
a API pública), como uma rede social. Depois do login, o usuário vê o menu
principal. Cada menu é uma estrutura match/case que chama a função
correspondente a cada opção.
Este módulo só organiza o fluxo entre os menus: o cálculo e a validação
ficam em dados.py, o acesso ao banco fica em banco.py e a interação com o
usuário fica em menu.py. A sessão (usuário e comunidade em uso) é um dict
com as chaves "usuario" e "id_comunidade".
"""

import os
import dados
import menu


def reinicia_sessao(sessao: dict) -> None:
    """
    Zera a sessão (ao sair da conta ou excluí-la): esquece o usuário e a
    comunidade, o progresso salvo e as respostas guardadas.
    Entrada: sessao (dict) que é atualizado.
    Saida: não retorna valor.
    """
    sessao["usuario"] = None
    sessao["id_comunidade"] = None
    dados.progresso["ativo"] = False
    dados.respostas_usuario.clear()


def entra_na_conta(conexao, sessao: dict) -> None:
    """
    Faz o login e, se der certo, guarda o usuário na sessão.
    Entrada: conexao (conexão aberta); sessao (dict) que é atualizado.
    Saida: não retorna valor.
    """
    usuario = menu.entrar_interativo(conexao)

    if usuario is not None:
        # Começa limpo, sem o progresso de quem entrou antes
        reinicia_sessao(sessao)
        sessao["usuario"] = usuario


def registra_pontos_da_sessao(conexao, sessao: dict) -> None:
    """
    Abre o fluxo "Registrar pontos" para o usuário da sessão. É o INSERT de
    postagens: cada ação registrada vira uma postagem no banco. Usada pelo
    menu principal e pelo submenu "Gerenciar ações". Se ainda não houver
    comunidade escolhida, pergunta qual usar.
    Entrada: conexao (conexão aberta); sessao (dict) com usuario e
             id_comunidade.
    Saida: não retorna valor.
    """
    if sessao["id_comunidade"] is None:
        sessao["id_comunidade"] = menu.escolhe_comunidade_do_usuario(conexao, sessao["usuario"])

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


def executa_menu_comunidades(conexao, sessao: dict) -> None:
    """
    Mostra o submenu "Minhas comunidades" até o usuário voltar. Ao sair, a
    comunidade da sessão é esquecida, porque as comunidades do usuário podem
    ter mudado (será perguntada de novo em "Registrar pontos").
    Entrada: conexao (conexão aberta); sessao (dict) que é atualizado.
    Saida: não retorna valor.
    """
    id_usuario = sessao["usuario"]["id"]

    while True:
        opcao = menu.menu_comunidades()

        match opcao:
            case "1":
                menu.listar_minhas_comunidades_interativo(conexao, id_usuario)
            case "2":
                menu.entrar_comunidade_interativo(conexao, id_usuario)
            case "3":
                menu.sair_comunidade_interativo(conexao, id_usuario)
            case "4":
                sessao["id_comunidade"] = None
                return


def executa_menu_conta(conexao, sessao: dict) -> None:
    """
    Mostra o submenu "Minha conta" (o CRUD do cadastro) até o usuário voltar
    ou excluir a conta.
    Entrada: conexao (conexão aberta); sessao (dict) que é atualizado se a
             conta for excluída.
    Saida: não retorna valor.
    """
    usuario = sessao["usuario"]

    while True:
        opcao = menu.menu_conta()

        match opcao:
            case "1":
                menu.ver_perfil_interativo(conexao, usuario["id"])
            case "2":
                menu.alterar_dados_interativo(conexao, usuario)
            case "3":
                menu.alterar_senha_interativo(conexao, usuario["id"])
            case "4":
                executa_menu_comunidades(conexao, sessao)
            case "5":
                # Conta excluída: não há mais usuário na sessão
                if menu.excluir_conta_interativo(conexao, usuario):
                    reinicia_sessao(sessao)
                    return
            case "6":
                return


def executa_menu_api() -> None:
    """
    Mostra o submenu "Consultar API pública" até o usuário voltar. Não
    precisa de usuário na conta, pois consulta dados de toda a plataforma.
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


def limpa_tela() -> None:
    """
    Limpa o terminal (cls no Windows, clear nos outros sistemas).
    Entrada: não recebe parâmetros.
    Saida: não retorna valor.
    """
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")