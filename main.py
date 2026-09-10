"""
Ponto de entrada do Sistema de Pontos Ambientais - Lobo-guará Tech.

Organiza o fluxo entre os menus definidos em menu.py. Toda a lógica
de calculo/validação esta em dados.py, e toda a interação com o usuario
esta em menu.py. Este é o único módulo que referencia as variaveis de
dados.py (registros, periodos, niveis_impacto, progresso, LIMITE_*)
pelo nome - as demais funções recebem tudo por parametro.
"""

import os

import dados
import menu


def main() -> None:
    """
    Executa o sistema e direciona as escolhas dos menus.
    Entrada: não recebe parametros; utiliza os menus interativos.
    Saida: não retorna valor.
    """
    os.system("cls" if os.name == "nt" else "clear")

    nome, cpf = menu.identificar_usuario()

    while True:
        op = menu.menu_principal()

        match op:
            case "0":
                print("Encerrando o sistema...")
                break
            case "1":
                menu.registrar_pontos(
                    nome,
                    cpf,
                    dados.periodos,
                    dados.registros,
                    dados.niveis_impacto,
                    dados.progresso,
                    dados.LIMITE_TOTAL,
                    dados.LIMITE_DIAS,
                    dados.LIMITE_ACOES,
                )

            case "2":
                while True:
                    sub = menu.menu_crud()

                    match sub:
                        case "1":
                            menu.listar_registros_interativo(dados.registros)

                        case "2":
                            termo = input("\nBuscar ação (nome exato): ").strip()

                            while not dados.nome_valido(termo):
                                print("Digite um nome para buscar.")
                                termo = input("Buscar ação (nome exato): ").strip()

                            menu.buscar_registro_interativo(dados.registros, termo)

                        case "3":
                            menu.atualizar_registro_interativo(dados.registros)

                        case "4":
                            menu.excluir_registro_interativo(dados.registros)

                        case "5":
                            break

            case "3":
                while True:
                    sub = menu.menu_relatorios()

                    match sub:
                        case "1":
                            menu.listar_registros_interativo(dados.registros)

                        case "2":
                            p = input("\nPeríodo (1, 2 ou 3): ").strip()

                            if dados.inteiro_valido(p) and dados.periodo_valido(int(p)):
                                filtrados = dados.filtrar_por_periodo(dados.periodos, dados.registros, int(p))

                                if filtrados:
                                    menu.mostra_registros_numerados(filtrados)
                                else:
                                    print("Sem informações desse período.")

                                menu.pausar()
                            else:
                                print("Período inválido.")

                        case "3":
                            ordenados = dados.registros_por_peso(dados.registros)

                            if ordenados:
                                menu.mostra_registros_numerados(ordenados)
                            else:
                                print("Nenhum registro ainda.")

                            menu.pausar()

                        case "4":
                            break


if __name__ == "__main__":
    main()
