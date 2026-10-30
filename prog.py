"""
Programa principal do Sistema de Pontos Ambientais - Lobo-guará Tech.

Abre a conexão com o banco e repete o menu de entrada (ninguém na conta)
ou o menu principal (usuário na conta) até o usuário sair. Cada opção é
tratada num match/case que chama as funções de fluxo.py e menu.py.
Para rodar o sistema: python prog.py
"""

import banco
import fluxo
import menu

fluxo.limpa_tela()

sessao = {"usuario": None, "id_comunidade": None}
continuar = True
conexao = None

try:
    conexao = banco.conectar()

    while continuar:
        if sessao["usuario"] is None:
            # Ninguém na conta: menu de entrada
            match menu.menu_inicial():
                case "0":
                    continuar = False
                case "1":
                    fluxo.entra_na_conta(conexao, sessao)
                case "2":
                    menu.cadastrar_usuario_interativo(conexao)
                case "3":
                    fluxo.executa_menu_api()
        else:
            # Usuário na conta: menu principal
            match menu.menu_principal(sessao["usuario"]["nome"]):
                case "0":
                    continuar = False
                case "1":
                    fluxo.registra_pontos_da_sessao(conexao, sessao)
                case "2":
                    fluxo.executa_menu_crud(conexao, sessao)
                case "3":
                    fluxo.executa_menu_relatorios(conexao, sessao["usuario"], sessao["id_comunidade"])
                case "4":
                    fluxo.executa_menu_conta(conexao, sessao)
                case "5":
                    fluxo.executa_menu_api()
                case "6":
                    fluxo.reinicia_sessao(sessao)

    print("Encerrando o sistema...")
except RuntimeError as erro:
    print(f"\nErro: {erro}")
except (KeyboardInterrupt, EOFError):
    # Ctrl+C ou Ctrl+D encerram o sistema sem mostrar o erro do Python
    print("\nSistema encerrado.")
finally:
    # Fecha a conexão com o banco mesmo se ocorrer erro
    if conexao is not None:
        conexao.close()