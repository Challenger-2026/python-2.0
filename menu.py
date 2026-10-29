"""
Camada de interface (menus, mensagens e entrada de dados) do
Sistema de Pontos Ambientais Lobo-guará Tech.

Este modulo cuida de tudo o que aparece na tela e de tudo o que e
digitado pelo usuario. O calculo e a validação ficam em dados.py e o
acesso ao banco fica em banco.py; aqui so chamamos essas funções e
mostramos o resultado. Cada função tem uma única responsabilidade:
as funções "pede_*" fazem uma pergunta, as "mostra_*" imprimem algo e
as "*_interativo" juntam essas peças em uma tela completa.
"""

import textwrap

import api
import banco
import dados
import exportar

# Resultado de decide_proximo_passo: o que fazer depois de registrar um dia.
PASSO_SEGUIR: str = "seguir"
PASSO_PARAR: str = "parar"
PASSO_CONCLUIDO: str = "concluido"



# PERGUNTAS REUTILIZÁVEIS


def pausar() -> None:
    """
    Pausa a execução até o usuário apertar ENTER, pra dar tempo de ver as
    informações antes da tela mudar.
    Entrada: não recebe parâmetros.
    Saida: não retorna valor.
    """
    input("\nPressione ENTER para continuar...")


def pergunta_sim_nao(pergunta: str) -> bool:
    """
    Faz uma pergunta de sim ou não e repete até receber s ou n.
    Entrada: pergunta (str), sem o "(s/n)" no final.
    Saida: True se a resposta foi s, False se foi n.
    """
    resposta = input(f"\n{pergunta} (s/n): ").strip().lower()

    while resposta not in ("s", "n"):
        print("Resposta inválida, digite s ou n.")
        resposta = input(f"{pergunta} (s/n): ").strip().lower()

    return resposta == "s"


def pede_numero_da_lista(pergunta: str, quantidade: int) -> int:
    """
    Pede a posição de um item numa lista mostrada na tela (1, 2, 3...) e
    repete até receber um número dentro da lista.
    Entrada: pergunta (str); quantidade (int), total de itens da lista.
    Saida: posição escolhida (int), entre 1 e quantidade.
    """
    escolha = input(f"\n{pergunta} (número): ").strip()

    # Repete até receber um inteiro dentro da lista
    while not dados.inteiro_valido(escolha) or not (1 <= int(escolha) <= quantidade):
        print("Número inválido.")
        escolha = input(f"{pergunta} (número): ").strip()

    return int(escolha)


# ---------------------------------------------------------------------------
# IDENTIFICAÇÃO DO USUÁRIO
# ---------------------------------------------------------------------------

def pede_cpf_valido() -> str:
    """
    Pede o CPF até receber um válido, ou 0 para desistir.
    Entrada: CPF informado pelo teclado.
    Saida: CPF (str) com 11 números, ou string vazia se o usuário digitou 0.
    """
    cpf = input("\nCPF (só números, ou 0 para voltar): ").strip()

    while cpf != "0" and not dados.cpf_formato_valido(cpf):
        print("CPF inválido, digite os 11 números do CPF.")
        cpf = input("CPF (só números, ou 0 para voltar): ").strip()

    # String vazia indica que o usuário desistiu
    if cpf == "0":
        return ""

    return cpf


def pede_usuario_cadastrado(conexao) -> dict | None:
    """
    Pede o CPF até encontrar um usuário cadastrado no banco.
    Entrada: conexao (conexão aberta); CPF pelo teclado.
    Saida: dict com id e nome do usuário, ou None se ele desistiu (digitou 0).
    """
    while True:
        cpf = pede_cpf_valido()

        if not cpf:
            return None

        usuario = banco.buscar_usuario_por_cpf(conexao, cpf)

        if usuario is not None:
            return usuario

        print("CPF não cadastrado. Cadastre-se pelo site e tente de novo.")


def escolhe_comunidade(comunidades: list[dict]) -> int:
    """
    Mostra as comunidades do usuário e pede em qual ele quer registrar.
    Entrada: comunidades (list[dict]) com id e nome, não vazia.
    Saida: id (int) da comunidade escolhida.
    """
    print("\nSuas comunidades:")

    for numero, comunidade in enumerate(comunidades, start=1):
        print(f"{numero}. {comunidade['nome']}")

    numero_escolhido = pede_numero_da_lista("Em qual comunidade registrar?", len(comunidades))

    return comunidades[numero_escolhido - 1]["id"]


def identificar_usuario(conexao) -> tuple[dict | None, int | None]:
    """
    Identifica o usuário pelo CPF e, se ele participar de comunidades, pede
    em qual quer registrar as ações. Só é chamada quando o usuário escolhe
    no menu uma opção que precisa de identificação.
    Entrada: conexao (conexão aberta); CPF e comunidade pelo teclado.
    Saida: tupla (usuario, id_comunidade). usuario é dict com id e nome (ou
           None se desistiu); id_comunidade é None se ele não tem comunidade.
    """
    print("\n=== IDENTIFICAÇÃO ===")

    usuario = pede_usuario_cadastrado(conexao)

    if usuario is None:
        return None, None

    print(f"\nOlá, {usuario['nome']}!")

    comunidades = banco.listar_comunidades_do_usuario(conexao, usuario["id"])

    if not comunidades:
        print("Você ainda não participa de nenhuma comunidade; entre em uma pelo site para registrar ações.")
        return usuario, None

    return usuario, escolhe_comunidade(comunidades)



# TABELAS NA TELA


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
    Exibe os dados de um único registro, com os rótulos alinhados.
    Entrada: registro (dict) com acao, url, status e pontos.
    Saida: não retorna valor; imprime os dados.
    """
    print("-" * 50)
    print(f"Ação.......: {registro['acao']}")
    print(f"Evidência..: {registro['url']}")
    print(f"Status.....: {registro['status']}")
    print(f"Pontos.....: {registro['pontos']:.2f}")
    print("-" * 50)


def mostra_registros_numerados(lista_registros: list[dict]) -> None:
    """
    Exibe uma tabela com os registros, numerados pela posição (1, 2, 3...)
    para permitir escolher um deles. Ação longa quebra em mais linhas dentro
    da mesma borda, por palavra inteira (igual ao "Wrap Text" do Excel).
    Entrada: lista_registros (list[dict]).
    Saida: não retorna valor; imprime a tabela numerada.
    """
    largura_acao = 30

    borda = "+" + "-" * 5 + "+" + "-" * 32 + "+" + "-" * 12 + "+" + "-" * 8 + "+"

    print("\n" + borda)
    print(f"| {'Nº':>3} | {'Ação':<30} | {'Status':<10} | {'Pontos':>6} |")
    print(borda)

    for posicao, registro in enumerate(lista_registros, start=1):
        # Quebra ações longas em várias linhas sem estourar a borda da tabela
        texto_da_acao = registro["acao"]

        if texto_da_acao is None:
            texto_da_acao = ""

        linhas_da_acao = textwrap.wrap(texto_da_acao, largura_acao)

        if not linhas_da_acao:
            linhas_da_acao = [""]

        for indice, linha_da_acao in enumerate(linhas_da_acao):
            # Só a primeira linha mostra status e pontos
            if indice == 0:
                print(
                    f"| {posicao:>3} | {linha_da_acao:<{largura_acao}} | "
                    f"{registro['status']:<10} | {registro['pontos']:>6.2f} |"
                )
            else:
                print(f"| {'':>3} | {linha_da_acao:<{largura_acao}} | {'':<10} | {'':>6} |")

        print(borda)



# REGISTRO DE PONTOS: ciclo (período inicial, retomada e progresso)
#
# O "ciclo" é um dict com o andamento do registro (periodo, dia, pontos...),
# no mesmo formato do dict "progresso" de dados.py, usado para retomar.


def limite_de_dias(lista_periodos: list[tuple], periodo: int) -> int:
    """
    Busca o último dia de um período.
    Entrada: lista_periodos (list[tuple]); periodo (int), de 1 a 3.
    Saida: último dia do período (int).
    """
    # A posição 4 da tupla é o último dia do período
    return lista_periodos[periodo - 1][4]


def pede_periodo_inicial(lista_periodos: list[tuple]) -> int:
    """
    Mostra os períodos e pede em qual começar.
    Entrada: lista_periodos (list[tuple]); período pelo teclado.
    Saida: número do período escolhido (int), de 1 a 3.
    """
    mostra_periodos(lista_periodos)

    entrada = input("\nPeríodo inicial (1, 2 ou 3): ").strip()

    while not dados.inteiro_valido(entrada) or not dados.periodo_valido(int(entrada)):
        print("Período inválido.")
        entrada = input("Período inicial (1, 2 ou 3): ").strip()

    return int(entrada)


def inicia_novo_ciclo(lista_periodos: list[tuple]) -> dict:
    """
    Cria um ciclo do zero, no período e dia 1 escolhidos pelo usuário.
    Entrada: lista_periodos (list[tuple]).
    Saida: ciclo (dict) novo, sem pontos e sem dias registrados.
    """
    periodo = pede_periodo_inicial(lista_periodos)

    return {
        "periodo": periodo,
        "dia": 1,
        "pts_dias": 0.0,
        "pts_acoes": 0.0,
        "periodos_usados": [periodo],
        "dias_registrados": 0,
    }


def retoma_ciclo(progresso: dict) -> dict:
    """
    Cria um ciclo a partir do progresso salvo, para continuar de onde parou.
    Entrada: progresso (dict) com ativo=True.
    Saida: ciclo (dict) com uma cópia dos dados do progresso.
    """
    return {
        "periodo": progresso["periodo"],
        "dia": progresso["dia"],
        "pts_dias": progresso["pts_dias"],
        "pts_acoes": progresso["pts_acoes"],
        # list() copia a lista para não alterar o progresso salvo
        "periodos_usados": list(progresso["periodos_usados"]),
        "dias_registrados": progresso["dias_registrados"],
    }


def salva_progresso(progresso: dict, ciclo: dict) -> None:
    """
    Guarda o ciclo em andamento no progresso, para continuar depois.
    Entrada: progresso (dict) que será atualizado; ciclo (dict).
    Saida: não retorna valor.
    """
    progresso["ativo"] = True
    progresso["periodo"] = ciclo["periodo"]
    progresso["dia"] = ciclo["dia"]
    progresso["pts_dias"] = ciclo["pts_dias"]
    progresso["pts_acoes"] = ciclo["pts_acoes"]
    progresso["periodos_usados"] = ciclo["periodos_usados"]
    progresso["dias_registrados"] = ciclo["dias_registrados"]


def pergunta_continuar_ou_recomecar(progresso: dict) -> bool:
    """
    Mostra o progresso salvo e pergunta se continua ou recomeça do zero.
    Entrada: progresso (dict) com ativo=True; resposta pelo teclado.
    Saida: True se o usuário quer continuar (c), False se quer recomeçar (r).
    """
    acumulado = progresso["pts_dias"] + progresso["pts_acoes"]

    print(
        f"\nVocê tem um progresso salvo: Dia {progresso['dia']} | "
        f"Período {progresso['periodo']} | {acumulado:.2f} pts acumulados"
    )
    resposta = input("\nContinuar de onde parou ou recomeçar do zero? (c/r): ").strip().lower()

    while resposta not in ("c", "r"):
        print("Resposta inválida, digite c ou r.")
        resposta = input("Continuar de onde parou ou recomeçar do zero? (c/r): ").strip().lower()

    return resposta == "c"


# REGISTRO DE PONTOS: perguntas sobre a ação do dia

def pede_nivel_impacto(niveis_impacto: list[tuple]) -> int:
    """
    Pede o nível de impacto da ação até receber um que exista.
    Entrada: niveis_impacto (list[tuple]); nível pelo teclado.
    Saida: id do nível escolhido (int).
    """
    entrada = input("\nNível de impacto da ação (1, 2 ou 3): ").strip()

    while not dados.inteiro_valido(entrada) or not dados.nivel_impacto_valido(niveis_impacto, int(entrada)):
        print("Nível de impacto inválido.")
        entrada = input("Nível de impacto da ação (1, 2 ou 3): ").strip()

    return int(entrada)


def pede_nome_da_acao() -> str:
    """
    Pede o nome da ação realizada até receber um texto não vazio.
    Entrada: nome pelo teclado.
    Saida: nome da ação (str).
    """
    acao = input("\nAção realizada no dia: ").strip()

    while not dados.nome_valido(acao):
        print("Ação inválida.")
        acao = input("Ação realizada no dia: ").strip()

    return acao


def pede_link_evidencia() -> str:
    """
    Pede o link da evidência da ação até receber um link válido.
    Entrada: link pelo teclado.
    Saida: link (str) começando com http:// ou https://.
    """
    url = input("\nLink da evidência (começa com http): ").strip()

    while not dados.url_valida(url):
        print("Link inválido.")
        url = input("Link da evidência (começa com http): ").strip()

    return url


def pede_dados_da_acao(niveis_impacto: list[tuple]) -> dict:
    """
    Mostra os níveis e exemplos e pergunta tudo sobre a ação do dia: nível
    de impacto, nome e link da evidência.
    Entrada: niveis_impacto (list[tuple]); respostas pelo teclado.
    Saida: dict com nivel (nome), peso, acao e url.
    """
    mostra_exemplos_acoes(niveis_impacto)

    nivel = pede_nivel_impacto(niveis_impacto)
    acao = pede_nome_da_acao()
    url = pede_link_evidencia()

    return {
        "nivel": dados.nome_do_nivel(niveis_impacto, nivel),
        "peso": dados.peso_do_nivel(niveis_impacto, nivel),
        "acao": acao,
        "url": url,
    }


# REGISTRO DE PONTOS: um dia

def mostra_cabecalho_do_dia(ciclo: dict) -> None:
    """
    Mostra o título do dia que vai ser registrado.
    Entrada: ciclo (dict) com dia e periodo.
    Saida: não retorna valor; imprime o cabeçalho.
    """
    print(f"\n{'=' * 50}")
    print(f"DIA {ciclo['dia']} | Período {ciclo['periodo']} | base {dados.base_diaria(ciclo['dia']):.2f} pts")
    print(f"{'=' * 50}")


def mostra_resultado_do_dia(resultado: dict, ciclo: dict, limite_total: float) -> None:
    """
    Mostra o que foi registrado no dia e o acumulado do ciclo.
    Entrada: resultado (dict) com acao, nivel, peso e pontos; ciclo (dict);
             limite_total (float).
    Saida: não retorna valor; imprime o resultado.
    """
    print("\n" + "=" * 50)
    print(f"REGISTRO DO DIA {ciclo['dia']}")
    print("=" * 50)
    print(f"Ação......: {resultado['acao']}")
    print(f"Nível.....: {resultado['nivel']}")
    print(f"Peso......: {resultado['peso']:.2f}")
    print(f"Pontos dia: {resultado['pontos']:.2f}")
    print(f"Acumulado.: {ciclo['pts_dias'] + ciclo['pts_acoes']:.2f} / {limite_total:.2f}")
    print("=" * 50)


def registra_dia_com_acao(
    conexao,
    usuario: dict,
    id_comunidade: int,
    ciclo: dict,
    niveis_impacto: list[tuple],
    limites: tuple[float, float, float],
) -> dict | None:
    """
    Registra um dia em que o usuário fez uma ação: pergunta os dados, calcula
    os pontos e grava a ação no banco. Se o banco recusar, desfaz o cálculo
    dos pontos do dia.
    Entrada: conexao (conexão aberta); usuario (dict); id_comunidade (int);
             ciclo (dict) que é atualizado com os pontos; niveis_impacto
             (list[tuple]); limites (tuple) com limite_total, limite_pts_dias
             e limite_pts_acoes.
    Saida: resultado (dict com acao, nivel, peso e pontos), ou None se o
           banco recusou o registro.
    """
    limite_total, limite_pts_dias, limite_pts_acoes = limites

    dados_da_acao = pede_dados_da_acao(niveis_impacto)

    # Guarda os acumulados para desfazer se o banco recusar o registro
    pts_dias_antes = ciclo["pts_dias"]
    pts_acoes_antes = ciclo["pts_acoes"]

    pontos_do_dia, ciclo["pts_dias"], ciclo["pts_acoes"] = dados.calcula_pontos_dia(
        ciclo["dia"], dados_da_acao["peso"], pts_dias_antes, pts_acoes_antes,
        limite_total, limite_pts_dias, limite_pts_acoes,
    )

    try:
        banco.inserir_postagem(
            conexao, dados_da_acao["acao"], dados_da_acao["url"],
            pontos_do_dia, usuario["id"], id_comunidade,
        )
    except banco.ErroBanco as erro:
        print(f"\nErro: {erro}")
        # Restaura os pontos de antes do dia
        ciclo["pts_dias"] = pts_dias_antes
        ciclo["pts_acoes"] = pts_acoes_antes
        return None

    return {
        "acao": dados_da_acao["acao"],
        "url": dados_da_acao["url"],
        "nivel": dados_da_acao["nivel"],
        "peso": dados_da_acao["peso"],
        "pontos": pontos_do_dia,
    }


def registra_dia(
    conexao,
    usuario: dict,
    id_comunidade: int,
    ciclo: dict,
    niveis_impacto: list[tuple],
    limites: tuple[float, float, float],
) -> bool:
    """
    Registra um dia do ciclo: pergunta se houve ação e, se houve, grava no
    banco. Dias sem ação valem 0 pontos e não são gravados no banco.
    Entrada: mesmos parâmetros de registra_dia_com_acao.
    Saida: True se o dia foi registrado; False se o banco recusou.
    """
    mostra_cabecalho_do_dia(ciclo)

    fez_acao = pergunta_sim_nao("Fez alguma ação ambiental nesse dia?")

    if fez_acao:
        resultado = registra_dia_com_acao(conexao, usuario, id_comunidade, ciclo, niveis_impacto, limites)

        if resultado is None:
            return False
    else:
        # Dia sem ação: vale 0 pontos e não vai para o banco
        resultado = {"acao": "Nenhuma ação", "url": "", "nivel": "Nenhuma", "peso": 0.0, "pontos": 0.0}

    # Guarda a resposta do dia para a exportação em JSON
    dados.respostas_usuario.append({
        "periodo": ciclo["periodo"],
        "dia": ciclo["dia"],
        "fez_acao": fez_acao,
        "acao": resultado["acao"],
        "nivel": resultado["nivel"],
        "peso": resultado["peso"],
        "url": resultado["url"],
        "pontos": round(resultado["pontos"], 2),
    })

    ciclo["dias_registrados"] += 1
    mostra_resultado_do_dia(resultado, ciclo, limites[0])

    return True


# REGISTRO DE PONTOS: o que fazer depois de cada dia

def decide_proximo_dia(ciclo: dict) -> str:
    """
    Pergunta se o usuário quer registrar o próximo dia e avança o dia do
    ciclo (também quando ele decide parar, pra retomar do dia seguinte).
    Entrada: ciclo (dict) que é atualizado; resposta pelo teclado.
    Saida: PASSO_SEGUIR se quer continuar, PASSO_PARAR se não.
    """
    quer_continuar = pergunta_sim_nao("Registrar próximo dia?")

    # Avança o dia mesmo se parar, para retomar do dia seguinte
    ciclo["dia"] += 1

    if quer_continuar:
        return PASSO_SEGUIR

    return PASSO_PARAR


def decide_fim_do_periodo(ciclo: dict, lista_periodos: list[tuple]) -> str:
    """
    Trata o último dia de um período: conclui o ciclo se era o período 3, ou
    pergunta se o usuário quer ir para o período seguinte.
    Entrada: ciclo (dict) que é atualizado; lista_periodos (list[tuple]);
             resposta pelo teclado.
    Saida: PASSO_CONCLUIDO, PASSO_SEGUIR (foi para o próximo período) ou
           PASSO_PARAR (preferiu parar).
    """
    if ciclo["periodo"] == 3:
        print("\nCompletou o período 3.")
        return PASSO_CONCLUIDO

    proximo_periodo = ciclo["periodo"] + 1

    print(f"\nCompletou o período {ciclo['periodo']} ({limite_de_dias(lista_periodos, ciclo['periodo'])} dias).")

    if not pergunta_sim_nao(f"Ir para o período {proximo_periodo}?"):
        return PASSO_PARAR

    # Passa para o período seguinte e já avança o dia
    ciclo["periodo"] = proximo_periodo
    ciclo["periodos_usados"].append(proximo_periodo)
    ciclo["dia"] += 1

    return PASSO_SEGUIR


def decide_proximo_passo(ciclo: dict, lista_periodos: list[tuple], limite_total: float) -> str:
    """
    Decide o que fazer depois de registrar um dia: concluir se atingiu o
    limite de pontos, tratar o fim do período, ou perguntar pelo próximo dia.
    Entrada: ciclo (dict); lista_periodos (list[tuple]); limite_total (float).
    Saida: PASSO_SEGUIR, PASSO_PARAR ou PASSO_CONCLUIDO.
    """
    # Ordem: limite de pontos, fim do período e, por último, próximo dia
    if ciclo["pts_dias"] + ciclo["pts_acoes"] >= limite_total:
        print("\nLimite de 100 pontos atingido!")
        return PASSO_CONCLUIDO

    if ciclo["dia"] >= limite_de_dias(lista_periodos, ciclo["periodo"]):
        return decide_fim_do_periodo(ciclo, lista_periodos)

    return decide_proximo_dia(ciclo)


def executa_ciclo(
    conexao,
    usuario: dict,
    id_comunidade: int,
    ciclo: dict,
    lista_periodos: list[tuple],
    niveis_impacto: list[tuple],
    limites: tuple[float, float, float],
) -> bool:
    """
    Registra dia após dia até o ciclo terminar ou o usuário parar.
    Entrada: conexao (conexão aberta); usuario (dict); id_comunidade (int);
             ciclo (dict) que é atualizado; lista_periodos e niveis_impacto
             (list[tuple]); limites (tuple) com limite_total, limite_pts_dias
             e limite_pts_acoes.
    Saida: True se o ciclo foi concluído (limite de pontos ou 30 dias);
           False se o usuário parou no meio ou o banco recusou um registro.
    """
    while True:
        if not registra_dia(conexao, usuario, id_comunidade, ciclo, niveis_impacto, limites):
            return False

        passo = decide_proximo_passo(ciclo, lista_periodos, limites[0])

        if passo == PASSO_CONCLUIDO:
            return True

        if passo == PASSO_PARAR:
            return False


def mostra_resumo_final(usuario: dict, ciclo: dict, limites: tuple[float, float, float]) -> None:
    """
    Mostra o resumo do ciclo: períodos usados, dias e pontos por categoria.
    Entrada: usuario (dict); ciclo (dict); limites (tuple) com limite_total,
             limite_pts_dias e limite_pts_acoes.
    Saida: não retorna valor; imprime o resumo.
    """
    limite_total, limite_pts_dias, limite_pts_acoes = limites
    periodos_usados = ""

    for p in ciclo["periodos_usados"]:
        if periodos_usados:
            periodos_usados += ", "

        periodos_usados += str(p)

    print("\n" + "=" * 50)
    print("RESUMO FINAL")
    print("=" * 50)
    print(f"Usuário.......: {usuario['nome']}")
    print(f"Períodos......: {periodos_usados}")
    print(f"Dias..........: {ciclo['dias_registrados']}")
    print(f"Pontos dias...: {ciclo['pts_dias']:.2f} (limite {limite_pts_dias:.2f})")
    print(f"Pontos ações..: {ciclo['pts_acoes']:.2f} (limite {limite_pts_acoes:.2f})")
    print(f"TOTAL.........: {ciclo['pts_dias'] + ciclo['pts_acoes']:.2f} (limite {limite_total:.2f})")
    print("=" * 50)


def registrar_pontos(
    conexao,
    usuario: dict,
    id_comunidade: int | None,
    lista_periodos: list[tuple],
    niveis_impacto: list[tuple],
    progresso: dict,
    limite_total: float,
    limite_pts_dias: float,
    limite_pts_acoes: float,
) -> None:
    """
    Conduz o registro de pontos ambientais: escolhe se continua o progresso
    salvo ou começa um ciclo novo, registra os dias, mostra o resumo e, se o
    ciclo terminou de verdade, oferece começar outro na hora. As ações feitas
    são gravadas no banco como postagens PENDENTES.
    Entrada: conexao (conexão aberta com o banco); usuario (dict com id e
             nome); id_comunidade (int, ou None se o usuário não tiver
             comunidade); lista_periodos, niveis_impacto e progresso
             (listas/dict de dados); limite_total, limite_pts_dias e
             limite_pts_acoes (float), os tetos do sistema.
    Saida: não retorna valor; grava as ações no banco e atualiza progresso.
    """
    print("\n=== REGISTRO DE PONTOS AMBIENTAIS ===")

    if id_comunidade is None:
        print("\nVocê precisa participar de uma comunidade para registrar ações.")
        pausar()
        return

    limites = (limite_total, limite_pts_dias, limite_pts_acoes)
    # Só pergunta se continua quando há progresso salvo
    continuar_de_onde_parou = False

    if progresso["ativo"]:
        continuar_de_onde_parou = pergunta_continuar_ou_recomecar(progresso)

    while True:
        if continuar_de_onde_parou:
            ciclo = retoma_ciclo(progresso)
        else:
            ciclo = inicia_novo_ciclo(lista_periodos)
            dados.respostas_usuario.clear()

        # Nas próximas voltas do loop, os ciclos começam do zero
        continuar_de_onde_parou = False

        concluido = executa_ciclo(conexao, usuario, id_comunidade, ciclo, lista_periodos, niveis_impacto, limites)

        mostra_resumo_final(usuario, ciclo, limites)
        pausar()

        # Parou no meio: guarda o progresso para retomar depois
        if not concluido:
            salva_progresso(progresso, ciclo)
            return

        progresso["ativo"] = False

        if not pergunta_sim_nao("Deseja iniciar um novo registro do zero agora?"):
            return


# GERENCIAR AÇÕES (CRUD no banco + tratamento de erros)

def pede_nome_para_busca() -> str:
    """
    Pede o nome exato da ação a buscar, até receber um texto não vazio.
    Entrada: nome pelo teclado.
    Saida: nome (str).
    """
    nome_da_acao = input("\nBuscar ação (nome exato): ").strip()

    while not dados.nome_valido(nome_da_acao):
        print("Digite um nome para buscar.")
        nome_da_acao = input("Buscar ação (nome exato): ").strip()

    return nome_da_acao


def pede_novo_nome() -> str:
    """
    Pede o novo nome de uma ação até receber um texto não vazio.
    Entrada: nome pelo teclado.
    Saida: novo nome (str).
    """
    novo_nome = input("\nNovo nome da ação: ").strip()

    while not dados.nome_valido(novo_nome):
        print("Nome inválido.")
        novo_nome = input("Novo nome da ação: ").strip()

    return novo_nome


def escolhe_registro(conexao, id_usuario: int, verbo: str) -> dict:
    """
    Mostra os registros do usuário numerados e pede qual ele quer usar.
    Entrada: conexao (conexão aberta); id_usuario (int); verbo (str) que
             completa a pergunta, como "atualizar" ou "excluir".
    Saida: registro escolhido (dict).
    Erro: ValueError se o usuário não tem nenhum registro;
          banco.ErroBanco se o banco falhar.
    """
    registros = banco.listar_postagens(conexao, id_usuario)

    if not registros:
        raise ValueError("Nenhum registro cadastrado ainda.")

    mostra_registros_numerados(registros)

    numero = pede_numero_da_lista(f"Qual desses você quer {verbo}?", len(registros))

    return registros[numero - 1]


def listar_registros_interativo(conexao, id_usuario: int) -> None:
    """
    Lista todos os registros do usuário gravados no banco.
    Entrada: conexao (conexão aberta); id_usuario (int).
    Saida: não retorna valor; exibe os registros.
    """
    try:
        registros = banco.listar_postagens(conexao, id_usuario)
    except banco.ErroBanco as erro:
        print(f"\nErro: {erro}")
    else:
        if registros:
            mostra_registros_numerados(registros)
        else:
            print("\nNenhum registro ainda.")

    pausar()


def buscar_registro_interativo(conexao, id_usuario: int) -> None:
    """
    Pergunta o nome de uma ação e mostra os registros do usuário com esse nome.
    Entrada: conexao (conexão aberta); id_usuario (int); nome pelo teclado.
    Saida: não retorna valor; imprime os registros encontrados.
    """
    nome_da_acao = pede_nome_para_busca()

    try:
        encontrados = banco.buscar_postagens(conexao, id_usuario, nome_da_acao)
    except banco.ErroBanco as erro:
        print(f"\nErro: {erro}")
    else:
        if encontrados:
            mostra_registros_numerados(encontrados)
        else:
            print("Nada encontrado.")

    pausar()


def atualizar_registro_interativo(conexao, id_usuario: int) -> bool:
    """
    Deixa escolher um registro pela posição na lista e atualiza o nome da
    ação no banco. Só registros PENDENTES podem ser alterados.
    Entrada: conexao (conexão aberta); id_usuario (int); posição e novo nome
             pelo teclado.
    Saida: True se atualizou; False se houve erro ou nada foi alterado.
    """
    sucesso = False

    # except trata erros esperados, else mostra o resultado e finally sempre roda
    try:
        registro = escolhe_registro(conexao, id_usuario, "atualizar")

        mostra_registro(registro)

        novo_nome = pede_novo_nome()
        foi_atualizado = banco.atualizar_postagem(conexao, registro["id"], id_usuario, novo_nome)

    except (ValueError, banco.ErroBanco) as erro:
        print(f"\nErro: {erro}")

    else:
        if foi_atualizado:
            print("Registro atualizado!")
            sucesso = True
        else:
            print("Não foi possível atualizar: só registros PENDENTES podem ser alterados.")

    finally:
        print("Fim da tentativa de atualização.")

    pausar()
    return sucesso


def excluir_registro_interativo(conexao, id_usuario: int) -> bool:
    """
    Deixa escolher um registro pela posição na lista, pede confirmação e
    exclui no banco. Só registros PENDENTES podem ser excluídos.
    Entrada: conexao (conexão aberta); id_usuario (int); posição e confirmação
             pelo teclado.
    Saida: True se excluiu; False se houve erro, cancelamento ou nada foi
           excluído.
    """
    sucesso = False
    confirmou = False

    # Mesmo esquema de try/except/else/finally do atualizar
    try:
        registro = escolhe_registro(conexao, id_usuario, "excluir")

        mostra_registro(registro)

        confirmou = pergunta_sim_nao("Confirma exclusão?")
        # Só exclui no banco se o usuário confirmou
        foi_excluido = False

        if confirmou:
            foi_excluido = banco.excluir_postagem(conexao, registro["id"], id_usuario)

    except (ValueError, banco.ErroBanco) as erro:
        print(f"\nErro: {erro}")

    else:
        if not confirmou:
            print("Exclusão cancelada.")
        elif foi_excluido:
            print("Registro excluído!")
            sucesso = True
        else:
            print("Não foi possível excluir: só registros PENDENTES podem ser excluídos.")

    finally:
        print("Fim da tentativa de exclusão.")

    pausar()
    return sucesso


# RELATÓRIOS


def pede_status() -> str:
    """
    Pede o status a filtrar até receber um válido.
    Entrada: status pelo teclado.
    Saida: status (str) em maiúsculas: PENDENTE, APROVADO ou REJEITADO.
    """
    status = input("\nStatus (PENDENTE, APROVADO ou REJEITADO): ").strip().upper()

    while status not in ("PENDENTE", "APROVADO", "REJEITADO"):
        print("Status inválido.")
        status = input("Status (PENDENTE, APROVADO ou REJEITADO): ").strip().upper()

    return status


def relatorio_por_status_interativo(conexao, id_usuario: int) -> None:
    """
    Pergunta um status e mostra só os registros do usuário com esse status.
    Entrada: conexao (conexão aberta); id_usuario (int); status pelo teclado.
    Saida: não retorna valor; exibe os registros.
    """
    status = pede_status()

    try:
        registros = banco.listar_postagens(conexao, id_usuario)
    except banco.ErroBanco as erro:
        print(f"\nErro: {erro}")
    else:
        filtrados = dados.filtrar_por_status(registros, status)

        if filtrados:
            mostra_registros_numerados(filtrados)
        else:
            print("Nenhum registro com esse status.")

    pausar()


def relatorio_por_pontos_interativo(conexao, id_usuario: int) -> None:
    """
    Mostra os registros do usuário do maior para o menor número de pontos.
    Entrada: conexao (conexão aberta); id_usuario (int).
    Saida: não retorna valor; exibe os registros.
    """
    try:
        registros = banco.listar_postagens(conexao, id_usuario)
    except banco.ErroBanco as erro:
        print(f"\nErro: {erro}")
    else:
        if registros:
            mostra_registros_numerados(dados.registros_por_pontos(registros))
        else:
            print("\nNenhum registro ainda.")

    pausar()


# EXPORTAÇÃO PARA JSON

def exportar_registros_interativo(conexao, usuario: dict) -> None:
    """
    Exporta para JSON as ações do usuário que estão no banco (dados do CRUD).
    Entrada: conexao (conexão aberta); usuario (dict com id e nome).
    Saida: não retorna valor; mostra onde o arquivo foi gravado.
    """
    try:
        registros = banco.listar_postagens(conexao, usuario["id"])

        if not registros:
            print("\nNenhum registro para exportar.")
        else:
            conteudo = exportar.monta_exportacao_crud(usuario, registros)
            caminho = exportar.salvar_json(f"crud_usuario_{usuario['id']}.json", conteudo)
            print(f"\n{len(registros)} registro(s) exportado(s) para:\n{caminho}")
    except (banco.ErroBanco, exportar.ErroExportacao) as erro:
        print(f"\nErro: {erro}")

    pausar()


def exportar_respostas_interativo(usuario: dict, id_comunidade: int | None) -> None:
    """
    Exporta para JSON o que o usuário respondeu em "Registrar pontos".
    Entrada: usuario (dict com id e nome); id_comunidade (int, ou None).
    Saida: não retorna valor; mostra onde o arquivo foi gravado.
    """
    if not dados.respostas_usuario:
        print("\nVocê ainda não registrou nenhum dia em \"Registrar pontos\".")
        pausar()
        return

    try:
        conteudo = exportar.monta_exportacao_respostas(usuario, id_comunidade, dados.respostas_usuario)
        caminho = exportar.salvar_json(f"respostas_usuario_{usuario['id']}.json", conteudo)
    except exportar.ErroExportacao as erro:
        print(f"\nErro: {erro}")
    else:
        print(f"\n{len(dados.respostas_usuario)} dia(s) exportado(s) para:\n{caminho}")

    pausar()


# CONSULTAS NA API PÚBLICA


def ranking_api_interativo() -> None:
    """
    Busca os usuários na API e mostra o ranking por pontos.
    Entrada: não recebe parâmetros.
    Saida: não retorna valor; exibe o ranking.
    """
    print("\nConsultando a API (pode demorar na primeira vez)...")

    try:
        usuarios = api.listar_usuarios_api()
    except api.ErroApi as erro:
        print(f"\nErro: {erro}")
    else:
        ranking = dados.ranking_de_usuarios(usuarios)
        borda = "+" + "-" * 5 + "+" + "-" * 27 + "+" + "-" * 12 + "+" + "-" * 10 + "+"

        print("\n" + borda)
        print(f"| {'Pos':>3} | {'Nome':<25} | {'Perfil':<10} | {'Pontos':>8} |")
        print(borda)

        for posicao, usuario in enumerate(ranking, start=1):
            print(
                f"| {posicao:>3} | {usuario['nome'][:25]:<25} | "
                f"{usuario['perfil']:<10} | {usuario['pontos']:>8.1f} |"
            )

        print(borda)

    pausar()


def escolhe_comunidade_api(comunidades: list[dict]) -> int:
    """
    Mostra as comunidades da API numeradas e pede uma delas.
    Entrada: comunidades (list[dict]) com id e nome, não vazia.
    Saida: id (int) da comunidade escolhida.
    """
    print("\nComunidades:")

    for posicao, comunidade in enumerate(comunidades, start=1):
        print(f"{posicao}. {comunidade['nome']}")

    escolha = pede_numero_da_lista("Escolha a comunidade", len(comunidades))

    return comunidades[escolha - 1]["id"]


def postagens_da_comunidade_api_interativo() -> None:
    """
    Busca as comunidades e as postagens na API e mostra as postagens da
    comunidade escolhida pelo usuário.
    Entrada: não recebe parâmetros; comunidade pelo teclado.
    Saida: não retorna valor; exibe as postagens.
    """
    print("\nConsultando a API (pode demorar na primeira vez)...")

    try:
        comunidades = api.listar_comunidades_api()
        postagens = api.listar_postagens_api()
    except api.ErroApi as erro:
        print(f"\nErro: {erro}")
        pausar()
        return

    if not comunidades:
        print("\nA API não tem comunidades cadastradas.")
        pausar()
        return

    id_comunidade = escolhe_comunidade_api(comunidades)
    postagens_filtradas = dados.filtrar_por_comunidade(postagens, id_comunidade)

    if postagens_filtradas:
        mostra_registros_numerados(postagens_filtradas)
    else:
        print("\nNenhuma postagem nessa comunidade.")

    pausar()


# MENUS

def menu_principal(nome_usuario: str | None) -> str:
    """
    Exibe e valida as opções do menu principal. É a primeira tela do sistema;
    as opções 1, 2 e 3 pedem a identificação do usuário na primeira vez.
    Entrada: nome_usuario (str, ou None se ninguém se identificou ainda);
             opção informada pelo usuário no teclado.
    Saida: opção valida (str).
    """
    print("\n" + "=" * 50)
    print("SISTEMA DE PONTOS AMBIENTAIS LOBO-GUARÁ TECH")
    print("=" * 50)
    if nome_usuario is None:
        nome_usuario = "não identificado"

    print(f"Usuário: {nome_usuario}")
    print("-" * 50)
    print("0. Sair")
    print("1. Registrar pontos")
    print("2. Gerenciar ações")
    print("3. Relatórios")
    print("4. Trocar de usuário")
    print("5. Consultar API pública")

    op = input("\nOpção: ").strip()

    # Repete até digitar uma opção existente
    while op not in ("0", "1", "2", "3", "4", "5"):
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
    print("1. Inserir (registrar ação)")
    print("2. Listar")
    print("3. Buscar")
    print("4. Atualizar")
    print("5. Excluir")
    print("6. Voltar")

    op = input("\nOpção: ").strip()

    while op not in ("1", "2", "3", "4", "5", "6"):
        print("Opção inválida.")
        op = input("Opção: ").strip()

    return op


def menu_api() -> str:
    """
    Exibe e valida as opções de consulta à API pública.
    Entrada: opção informada pelo usuário no teclado.
    Saida: opção valida (str).
    """
    print("\n" + "=" * 50)
    print("CONSULTAR API PÚBLICA")
    print("=" * 50)
    print("1. Ranking de usuários")
    print("2. Postagens de uma comunidade")
    print("3. Voltar")

    op = input("\nOpção: ").strip()

    while op not in ("1", "2", "3"):
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
    print("2. Filtrar por status")
    print("3. Ações por pontos")
    print("4. Exportar ações do banco (JSON)")
    print("5. Exportar minhas respostas (JSON)")
    print("6. Voltar")

    op = input("\nOpção: ").strip()

    while op not in ("1", "2", "3", "4", "5", "6"):
        print("Opção inválida.")
        op = input("Opção: ").strip()

    return op
