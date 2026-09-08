"""
Camada de interface (menus, mensagens e entrada de dados) do
Sistema de Pontos Ambientais Lobo-guará Tech.

Este modulo cuida de tudo o que aparece na tela e de tudo o que e
digitado pelo usuario. O calculo e a validação ficam em dados.py; aqui
so chamamos essas funções e mostramos o resultado.
"""

import dados


# ---------------------------------------------------------------------------
# TELA
# ---------------------------------------------------------------------------

def pausar() -> None:
    """
    Pausa a execução até o usuário apertar ENTER, pra dar tempo de ver as
    informações antes da tela mudar.
    Entrada: não recebe parâmetros.
    Saida: não retorna valor.
    """
    input("\nPressione ENTER para continuar...")


def identificar_usuario() -> tuple[str, str]:
    """
    Pede o nome e o CPF do usuário logo na entrada do sistema, como um
    login - só é pedido uma vez, não a cada "Registrar pontos".
    Entrada: nome e CPF informados pelo teclado.
    Saida: tupla (nome, cpf), já validados.
    """
    print("\n" + "=" * 50)
    print("SISTEMA DE PONTOS AMBIENTAIS LOBO-GUARÁ TECH")
    print("=" * 50)

    nome = input("\nNome do usuário: ").strip()

    while not dados.nome_valido(nome):
        print("Nome inválido, digite de novo.")
        nome = input("Nome do usuário: ").strip()

    cpf = input("CPF (só números): ").strip()

    while not dados.cpf_valido(cpf):
        print("CPF inválido, digite os 11 números de um CPF válido.")
        cpf = input("CPF (só números): ").strip()

    print(f"\nOlá, {nome}!")

    return nome, cpf


# ---------------------------------------------------------------------------
# TABELAS NA TELA
# ---------------------------------------------------------------------------

def mostra_periodos(lista_periodos: list[tuple]) -> None:
    """
    Exibe a tabela de períodos.
    Entrada: lista_periodos (list[tuple]).
    Saida: não retorna valor; imprime a tabela.
    """
    borda = "+" + "-" * 4 + "+" + "-" * 14 + "+" + "-" * 18 + "+" + "-" * 11 + "+"

    print("\n" + borda)
    print(f"| {'ID':>2} | {'Dias':<12} | {'Pontos/dia':<16} | {'Total':<9} |")
    print(borda)

    for p in lista_periodos:
        print(f"| {p[0]:>2} | {p[1]:<12} | {p[2]:<16} | {p[3]:<9} |")

    print(borda)


def mostra_niveis_impacto(niveis_impacto: list[tuple]) -> None:
    """
    Exibe a tabela de níveis de impacto.
    Entrada: niveis_impacto (list[tuple]).
    Saida: não retorna valor; imprime a tabela.
    """
    borda = "+" + "-" * 4 + "+" + "-" * 7 + "+" + "-" * 6 + "+"

    print("\n" + borda)
    print(f"| {'ID':>2} | {'Nível':<5} | {'Peso':>4} |")
    print(borda)

    for n in niveis_impacto:
        print(f"| {n[0]:>2} | {n[1]:<5} | {n[2]:>4.2f} |")

    print(borda)


def mostra_exemplos_acoes(niveis_impacto: list[tuple]) -> None:
    """
    Mostra a tabela de níveis de impacto e sugestões de ações ambientais
    agrupadas por nível, pra ilustrar o que pode ser informado no dia.
    Entrada: niveis_impacto (list[tuple]).
    Saida: não retorna valor; imprime a tabela e as sugestões, que são
           só ilustrativas.
    """
    mostra_niveis_impacto(niveis_impacto)

    print("\nExemplos de ações por nível:")
    print("-" * 50)
    print("Alto..: Plantar uma árvore, Voluntariado ambiental")
    print("Médio.: Reduzir uso de plásticos, Economizar água no banho")
    print("Baixo.: Reciclar papel e vidro, Usar transporte público,")
    print("        Fazer compostagem em casa")
    print("-" * 50)


def mostra_registro(registro: dict) -> None:
    """
    Exibe os dados de um único registro, com os rótulos alinhados. O CPF
    não é exibido (dado sensível) - fica guardado só internamente.
    Entrada: registro (dict), com dia, periodo, acao, nivel, peso, nome,
             cpf e pontos.
    Saida: não retorna valor; imprime os dados.
    """
    print("-" * 50)
    print(f"Dia........: {registro['dia']}")
    print(f"Período....: {registro['periodo']}")
    print(f"Ação.......: {registro['acao']}")
    print(f"Nível......: {registro['nivel']}")
    print(f"Peso.......: {registro['peso']:.2f}")
    print(f"Pontos.....: {registro['pontos']:.2f}")
    print(f"Nome.......: {registro['nome']}")
    print("-" * 50)


def mostra_registros_numerados(lista_registros: list[dict]) -> None:
    """
    Exibe uma tabela com os registros, numerados pela posição (1, 2,
    3...) dentro dessa lista, pra permitir escolher um deles sem usar
    nenhum ID fixo. O CPF não é exibido (dado sensível) - fica guardado
    só internamente.
    Entrada: lista_registros (list[dict]).
    Saida: não retorna valor; imprime a tabela numerada.
    """
    borda = (
        "+" + "-" * 5 + "+" + "-" * 5 + "+" + "-" * 5 + "+" + "-" * 22
        + "+" + "-" * 9 + "+" + "-" * 7 + "+" + "-" * 8 + "+" + "-" * 14 + "+"
    )

    print("\n" + borda)
    print(
        f"| {'Nº':>3} | {'Dia':>3} | {'Per':>3} | {'Ação':<20} | "
        f"{'Nível':<7} | {'Peso':>5} | {'Pontos':>6} | {'Nome':<12} |"
    )
    print(borda)

    for posicao, r in enumerate(lista_registros, start=1):
        print(
            f"| {posicao:>3} | {r['dia']:>3} | {r['periodo']:>3} | "
            f"{r['acao']:<20} | {r['nivel']:<7} | {r['peso']:>5.2f} | "
            f"{r['pontos']:>6.2f} | {r['nome']:<12} |"
        )

    print(borda)


# ---------------------------------------------------------------------------
# REGISTRO DE PONTOS (a "ação" principal do sistema)
# ---------------------------------------------------------------------------

def registrar_pontos(
    nome: str,
    cpf: str,
    lista_periodos: list[tuple],
    lista_registros: list[dict],
    niveis_impacto: list[tuple],
    progresso: dict,
    limite_total: float,
    limite_pts_dias: float,
    limite_pts_acoes: float,
) -> None:
    """
    Conduz o registro de pontos ambientais e apresenta o resumo. Nome e
    CPF já vêm identificados de antes (pedidos uma única vez na entrada
    do sistema). A cada dia, pergunta se a pessoa fez alguma ação; se
    sim, pede o nível de impacto dela (Alto/Médio/Baixo) e o nome do que
    foi feito - é esse registro que "cadastra" a ação no sistema, não
    existe um catálogo separado.

    Se já existir um progresso salvo (de uma chamada anterior em que a
    pessoa parou no meio), pergunta se quer continuar de onde parou ou
    recomeçar do zero. Ao terminar um ciclo (atingir o limite de pontos
    ou completar os 30 dias), avisa e pergunta se quer iniciar um novo
    registro na hora, sem precisar voltar pro menu.
    Entrada: nome e cpf (str), já identificados; lista_periodos,
             lista_registros, niveis_impacto e progresso (listas/dict de
             dados); limite_total, limite_pts_dias e limite_pts_acoes
             (float), os tetos do sistema; além dos dados informados
             pelo usuário no teclado.
    Saida: não retorna valor; adiciona registros em lista_registros e
           atualiza progresso.
    """
    print("\n=== REGISTRO DE PONTOS AMBIENTAIS ===")

    continuar_de_onde_parou = False

    if progresso["ativo"]:
        acumulado = progresso["pts_dias"] + progresso["pts_acoes"]
        print(
            f"\nVocê tem um progresso salvo: Dia {progresso['dia']} | "
            f"Período {progresso['periodo']} | {acumulado:.2f} pts acumulados"
        )
        resp = input("\nContinuar de onde parou ou recomeçar do zero? (c/r): ").strip().lower()

        while resp not in ("c", "r"):
            print("Resposta inválida, digite c ou r.")
            resp = input("Continuar de onde parou ou recomeçar do zero? (c/r): ").strip().lower()

        continuar_de_onde_parou = resp == "c"

    while True:
        if continuar_de_onde_parou:
            periodo = progresso["periodo"]
            dia = progresso["dia"]
            limite_dias = lista_periodos[periodo - 1][4]
            periodos_usados = progresso["periodos_usados"]
            dias_registrados = progresso["dias_registrados"]
            pts_dias = progresso["pts_dias"]
            pts_acoes = progresso["pts_acoes"]

        else:
            mostra_periodos(lista_periodos)

            entrada = input("\nPeríodo inicial (1, 2 ou 3): ").strip()

            while not dados.inteiro_valido(entrada) or not dados.periodo_valido(int(entrada)):
                print("Período inválido.")
                entrada = input("Período inicial (1, 2 ou 3): ").strip()

            periodo = int(entrada)
            limite_dias = lista_periodos[periodo - 1][4]
            periodos_usados = [periodo]

            if periodo == 1:
                dia = 1
            else:
                dia = lista_periodos[periodo - 2][4] + 1

            dias_registrados = 0
            pts_dias = 0.0
            pts_acoes = 0.0

        continuar_de_onde_parou = False
        concluido = False

        while True:
            print(f"\n{'=' * 50}")
            print(f"DIA {dia} | Período {periodo} | base {dados.base_diaria(dia):.2f} pts")
            print(f"{'=' * 50}")

            fez_acao = input("Fez alguma ação ambiental nesse dia? (s/n): ").strip().lower()

            while fez_acao not in ("s", "n"):
                print("Resposta inválida, digite s ou n.")
                fez_acao = input("Fez alguma ação ambiental nesse dia? (s/n): ").strip().lower()

            if fez_acao == "n":
                acao = "Nenhuma ação"
                nivel_nome = "Nenhuma"
                peso = 0.0
                pts = 0.0

            else:
                mostra_exemplos_acoes(niveis_impacto)

                entrada = input("\nNível de impacto da ação (1, 2 ou 3): ").strip()

                while not dados.inteiro_valido(entrada) or not dados.nivel_impacto_valido(niveis_impacto, int(entrada)):
                    print("Nível de impacto inválido.")
                    entrada = input("Nível de impacto da ação (1, 2 ou 3): ").strip()

                nivel = int(entrada)
                peso = dados.peso_do_nivel(niveis_impacto, nivel)
                nivel_nome = dados.nome_do_nivel(niveis_impacto, nivel)

                acao = input("\nAção realizada no dia: ").strip()

                while not dados.nome_valido(acao):
                    print("Ação inválida.")
                    acao = input("Ação realizada no dia: ").strip()

                pts, pts_dias, pts_acoes = dados.calcula_pontos_dia(
                    dia, peso, pts_dias, pts_acoes,
                    limite_total, limite_pts_dias, limite_pts_acoes,
                )

            lista_registros.append({
                "dia": dia,
                "periodo": periodo,
                "acao": acao,
                "nivel": nivel_nome,
                "peso": peso,
                "nome": nome,
                "cpf": cpf,
                "pontos": pts,
            })

            dias_registrados += 1

            print("\n" + "=" * 50)
            print(f"REGISTRO DO DIA {dia}")
            print("=" * 50)
            print(f"Ação......: {acao}")
            print(f"Nível.....: {nivel_nome}")
            print(f"Peso......: {peso:.2f}")
            print(f"Pontos dia: {pts:.2f}")
            print(f"Acumulado.: {pts_dias + pts_acoes:.2f} / {limite_total:.2f}")
            print("=" * 50)

            if pts_dias + pts_acoes >= limite_total:
                print("\nLimite de 100 pontos atingido!")
                concluido = True
                break

            if dia >= limite_dias:
                if periodo == 3:
                    print("\nCompletou o período 3.")
                    concluido = True
                    break

                prox = periodo + 1

                print(f"\nCompletou o período {periodo} ({limite_dias} dias).")

                resp = input(f"\nIr para o período {prox}? (s/n): ").strip().lower()

                while resp not in ("s", "n"):
                    print("Resposta inválida, digite s ou n.")
                    resp = input(f"Ir para o período {prox}? (s/n): ").strip().lower()

                if resp != "s":
                    break

                periodo = prox
                limite_dias = lista_periodos[periodo - 1][4]
                periodos_usados.append(periodo)
                dia += 1
                continue

            resp = input("\nRegistrar próximo dia? (s/n): ").strip().lower()

            while resp not in ("s", "n"):
                print("Resposta inválida, digite s ou n.")
                resp = input("\nRegistrar próximo dia? (s/n): ").strip().lower()

            dia += 1

            if resp != "s":
                break

        print("\n" + "=" * 50)
        print("RESUMO FINAL")
        print("=" * 50)
        print(f"Usuário.......: {nome}")
        print(f"Períodos......: {', '.join(str(p) for p in periodos_usados)}")
        print(f"Dias..........: {dias_registrados}")
        print(f"Pontos dias...: {pts_dias:.2f} (limite {limite_pts_dias:.2f})")
        print(f"Pontos ações..: {pts_acoes:.2f} (limite {limite_pts_acoes:.2f})")
        print(f"TOTAL.........: {pts_dias + pts_acoes:.2f} (limite {limite_total:.2f})")
        print("=" * 50)

        pausar()

        if concluido:
            resp_novo = input("\nDeseja iniciar um novo registro do zero agora? (s/n): ").strip().lower()

            while resp_novo not in ("s", "n"):
                print("Resposta inválida, digite s ou n.")
                resp_novo = input("Deseja iniciar um novo registro do zero agora? (s/n): ").strip().lower()

            progresso["ativo"] = False

            if resp_novo == "s":
                continue

            break

        progresso["ativo"] = True
        progresso["periodo"] = periodo
        progresso["dia"] = dia
        progresso["pts_dias"] = pts_dias
        progresso["pts_acoes"] = pts_acoes
        progresso["periodos_usados"] = periodos_usados
        progresso["dias_registrados"] = dias_registrados
        break


# ---------------------------------------------------------------------------
# GERENCIAR AÇÕES (CRUD sobre os registros + tratamento de erros)
# ---------------------------------------------------------------------------

def listar_registros_interativo(lista_registros: list[dict]) -> None:
    """
    Lista todos os registros de ações feitas até agora.
    Entrada: lista_registros (list[dict]).
    Saida: não retorna valor; exibe os registros.
    """
    if not lista_registros:
        print("\nNenhum registro ainda.")
    else:
        mostra_registros_numerados(lista_registros)

    pausar()


def buscar_registro_interativo(lista_registros: list[dict], termo: str) -> None:
    """
    Busca registros pelo nome da ação e exibe o resultado.
    Entrada: lista_registros (list[dict]); termo (str).
    Saida: não retorna valor; imprime os registros encontrados.
    """
    encontrados = dados.buscar_registros(lista_registros, termo)

    if encontrados:
        mostra_registros_numerados(encontrados)
    else:
        print("Nada encontrado.")

    pausar()


def atualizar_registro_interativo(lista_registros: list[dict]) -> bool:
    """
    Mostra todos os registros numerados, deixa escolher um pela posição na
    lista (não por um ID fixo) e atualiza o nome dele. Em caso de erro de
    validação, pergunta de novo em vez de cancelar a atualização.
    Entrada: lista_registros (list[dict]); posição escolhida e novo nome
             informados pelo teclado.
    Saida: True depois de atualizar com sucesso.
    """
    while True:
        try:
            if not lista_registros:
                raise ValueError("Nenhum registro cadastrado ainda.")

            mostra_registros_numerados(lista_registros)

            entrada = input("\nQual desses você quer atualizar? (digite o número da lista acima): ").strip()

            while not dados.inteiro_valido(entrada) or not (1 <= int(entrada) <= len(lista_registros)):
                print("Número inválido.")
                entrada = input("Qual desses você quer atualizar? (digite o número da lista acima): ").strip()

            registro = lista_registros[int(entrada) - 1]

            mostra_registro(registro)

            nome = input("\nNovo nome da ação (deixe em branco para manter): ").strip()

        except ValueError as e:
            print(f"Erro: {e}")
            continue

        else:
            dados.atualizar_registro(lista_registros, registro, nome)
            print("Registro atualizado!")

        finally:
            print("Fim da tentativa de atualização.")

        pausar()
        return True


def excluir_registro_interativo(lista_registros: list[dict]) -> bool:
    """
    Mostra todos os registros numerados, deixa escolher um pela posição na
    lista (não por um ID fixo), mostra os dados dele e pede confirmação
    antes de excluir de fato. Em caso de erro de validação, pergunta de
    novo em vez de cancelar a exclusão.
    Entrada: lista_registros (list[dict]); posição escolhida informada
             pelo teclado.
    Saida: True depois de concluir a tentativa (excluindo ou cancelando
           na confirmação).
    """
    while True:
        try:
            if not lista_registros:
                raise ValueError("Nenhum registro cadastrado ainda.")

            mostra_registros_numerados(lista_registros)

            entrada = input("\nQual desses você quer excluir? (digite o número da lista acima): ").strip()

            while not dados.inteiro_valido(entrada) or not (1 <= int(entrada) <= len(lista_registros)):
                print("Número inválido.")
                entrada = input("Qual desses você quer excluir? (digite o número da lista acima): ").strip()

            registro = lista_registros[int(entrada) - 1]

        except ValueError as e:
            print(f"Erro: {e}")
            continue

        else:
            mostra_registro(registro)

            confirma = input("\nConfirma exclusão? (s/n): ").strip().lower()

            while confirma not in ("s", "n"):
                print("Resposta inválida, digite s ou n.")
                confirma = input("Confirma exclusão? (s/n): ").strip().lower()

            if confirma == "s":
                dados.excluir_registro(lista_registros, registro)
                print("Registro excluído!")
            else:
                print("Exclusão cancelada.")

        finally:
            print("Fim da tentativa de exclusão.")

        pausar()
        return True


# ---------------------------------------------------------------------------
# MENUS
# ---------------------------------------------------------------------------

def menu_principal() -> str:
    """
    Exibe e valida as opções do menu principal.
    Entrada: opção informada pelo usuário no teclado.
    Saida: opção valida (str).
    """
    print("\n" + "=" * 50)
    print("SISTEMA DE PONTOS AMBIENTAIS LOBO-GUARÁ TECH")
    print("=" * 50)
    print("0. Sair")
    print("1. Registrar pontos")
    print("2. Gerenciar ações")
    print("3. Relatórios")

    op = input("\nOpção: ").strip()

    while op not in ("0", "1", "2", "3"):
        print("Opção inválida.")
        op = input("Opção: ").strip()

    return op


def menu_crud() -> str:
    """
    Exibe e valida as opções de gerenciamento de ações.
    Entrada: opção informada pelo usuário no teclado.
    Saida: opção valida (str).
    """
    print("\n" + "=" * 50)
    print("GERENCIAR AÇÕES")
    print("=" * 50)
    print("1. Listar")
    print("2. Buscar")
    print("3. Atualizar")
    print("4. Excluir")
    print("5. Voltar")

    op = input("\nOpção: ").strip()

    while op not in ("1", "2", "3", "4", "5"):
        print("Opção inválida.")
        op = input("Opção: ").strip()

    return op


def menu_relatorios() -> str:
    """
    Exibe e valida as opções de relatórios.
    Entrada: opcao informada pelo usuário no teclado.
    Saida: opção valida (str).
    """
    print("\n" + "=" * 50)
    print("RELATÓRIOS")
    print("=" * 50)
    print("1. Ver registros")
    print("2. Filtrar por período")
    print("3. Ações por peso")
    print("4. Voltar")

    op = input("\nOpção: ").strip()

    while op not in ("1", "2", "3", "4"):
        print("Opção inválida.")
        op = input("Opção: ").strip()

    return op
