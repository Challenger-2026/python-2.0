"""
Camada de dados e regras de negócio do Sistema de Pontos Ambientais Lobo-guará Tech.

Este modulo concentra: as estruturas de dados (períodos, níveis de impacto,
registros), as validações de entrada, os cálculos de pontuação e as
operações de CRUD sobre a lista de registros. Quem cuida da interação com
o usuário é o módulo menu.py.
"""


# ---------------------------------------------------------------------------
# DADOS DO SISTEMA
# ---------------------------------------------------------------------------

# Cada período é uma tupla: (id, faixa_dias, pontos_por_dia_texto, total_texto, limite_dias)
periodos: list[tuple] = [
    (1, "1 a 7 dias", "1 ponto por dia", "7 pontos", 7),
    (2, "8 a 15 dias", "2 pontos por dia", "16 pontos", 15),
    (3, "16 a 30 dias", "3 pontos por dia", "45 pontos", 30),
]

# Cada nível de impacto é uma tupla: (id, nome, peso). É a escala fixa que
# define quanto uma ação realizada vale; não existe nível "Nenhuma" aqui,
# porque não fazer nada não é um nível de impacto, é a ausência de um.
niveis_impacto: list[tuple] = [
    (1, "Alto", 1.06),
    (2, "Médio", 0.66),
    (3, "Baixo", 0.16),
]

# Cada registro é um dicionário: {"dia", "periodo", "acao", "nivel", "peso",
# "nome", "cpf", "pontos"}. É criado inteiramente durante "Registrar pontos"
# (a pessoa digita o que fez) e é sobre ele que o CRUD de "Gerenciar ações"
# atua (listar/buscar/atualizar/excluir) - não existe um catálogo separado.
registros: list[dict] = []

# Progresso do ciclo de "Registrar pontos" em andamento, pra permitir
# continuar de onde parou em vez de recomeçar do zero. "ativo" fica False
# quando ainda não há nada pra continuar (nunca começou, ou o ciclo
# anterior já foi concluído - limite de pontos atingido ou 30 dias
# completos).
progresso: dict = {
    "ativo": False,
    "periodo": 1,
    "dia": 1,
    "pts_dias": 0.0,
    "pts_acoes": 0.0,
    "periodos_usados": [],
    "dias_registrados": 0,
}

LIMITE_TOTAL: float = 100.0
LIMITE_DIAS: float = 68.0
LIMITE_ACOES: float = 31.80


# ---------------------------------------------------------------------------
# VALIDAÇÃO
# ---------------------------------------------------------------------------

def nome_valido(nome: str) -> bool:
    """
    Verifica se o nome nÃo esta vazio.
    Entrada: nome (str).
    Saida: True se valido ou False se invalido.
    """
    return bool(nome.strip())


def cpf_valido(cpf: str) -> bool:
    """
    Valida o formato e os digitos verificadores do CPF.
    Entrada: cpf (str), contendo somente os 11 numeros.
    Saida: True se valido ou False se invalido.
    """
    cpf = cpf.strip()

    if len(cpf) != 11 or not cpf.isascii() or not cpf.isdigit():
        return False

    if cpf == cpf[0] * 11:
        return False

    for tamanho in (9, 10):
        soma = 0

        for i in range(tamanho):
            soma += int(cpf[i]) * (tamanho + 1 - i)

        digito = (soma * 10) % 11

        if digito == 10:
            digito = 0

        if int(cpf[tamanho]) != digito:
            return False

    return True


def inteiro_valido(texto: str) -> bool:
    """
    Verifica se o texto pode ser convertido para inteiro.
    Entrada: texto (str).
    Saida: True se a conversão for possivel ou False caso contrário.
    """
    try:
        int(texto)
        return True
    except ValueError:
        return False


def periodo_valido(p: int) -> bool:
    """
    Verifica se o período existe.
    Entrada: p (int), número do período.
    Saida: True para 1, 2 ou 3; False para os demais valores.
    """
    return p in (1, 2, 3)


def nivel_impacto_valido(niveis_impacto: list[tuple], nivel: int) -> bool:
    """
    Verifica se o nível de impacto existe.
    Entrada: niveis_impacto (list[tuple]); nivel (int).
    Saida: True se existir ou False caso contrario.
    """
    for n in niveis_impacto:
        if n[0] == nivel:
            return True

    return False


# ---------------------------------------------------------------------------
# CÁLCULO DE PONTOS
# ---------------------------------------------------------------------------

def base_diaria(dia: int) -> float:
    """
    Calcula os pontos básicos do dia.
    Entrada: dia (int), entre 1 e 30.
    Saida: pontuação base (float).
    """
    if dia <= 7:
        return 1.0
    elif dia <= 15:
        return 2.0
    else:
        return 3.0


def peso_do_nivel(niveis_impacto: list[tuple], nivel: int) -> float:
    """
    Busca o peso associado a um nível de impacto.
    Entrada: niveis_impacto (list[tuple]); nivel (int) existente.
    Saida: peso (float) ou 0.0 se o nivel nao existir.
    """
    for n in niveis_impacto:
        if n[0] == nivel:
            return n[2]

    return 0.0


def nome_do_nivel(niveis_impacto: list[tuple], nivel: int) -> str:
    """
    Busca o nome associado a um nível de impacto.
    Entrada: niveis_impacto (list[tuple]); nivel (int) existente.
    Saida: nome do nível (str), ou string vazia se o nível não existir.
    """
    for n in niveis_impacto:
        if n[0] == nivel:
            return n[1]

    return ""


def calcula_pontos_dia(
    dia: int,
    peso: float,
    pts_dias: float,
    pts_acoes: float,
    limite_total: float,
    limite_pts_dias: float,
    limite_pts_acoes: float,
) -> tuple[float, float, float]:
    """
    Calcula os pontos de um dia em que uma ação foi realizada, respeitando
    os limites acumulados. Quem chama decide não chamar esta função quando
    nenhuma ação foi feita no dia (nesse caso os pontos do dia são 0).
    Entrada: dia (int) entre 1 e 30; peso (float) da ação realizada, já
             resolvido a partir do nível de impacto escolhido; pts_dias e
             pts_acoes (float), totais acumulados até aqui; limite_total,
             limite_pts_dias e limite_pts_acoes (float), os tetos do
             sistema.
    Saida: tupla (pontos_do_dia, novo_pts_dias, novo_pts_acoes).
    """
    restante_total = max(0.0, limite_total - pts_dias - pts_acoes)

    pontos_dias = min(
        base_diaria(dia),
        max(0.0, limite_pts_dias - pts_dias),
        restante_total,
    )

    restante_total = max(0.0, restante_total - pontos_dias)

    pontos_acoes = min(
        peso,
        max(0.0, limite_pts_acoes - pts_acoes),
        restante_total,
    )

    novo_pts_dias = round(pts_dias + pontos_dias, 2)
    novo_pts_acoes = round(pts_acoes + pontos_acoes, 2)
    pts_do_dia = round(pontos_dias + pontos_acoes, 2)

    return pts_do_dia, novo_pts_dias, novo_pts_acoes


# ---------------------------------------------------------------------------
# CRUD DE REGISTROS
# ---------------------------------------------------------------------------

def buscar_registros(lista_registros: list[dict], termo: str) -> list[dict]:
    """
    Busca registros cuja ação tenha exatamente o nome informado (sem
    diferenciar maiúsculas/minúsculas).
    Entrada: lista_registros (list[dict]); termo (str).
    Saida: lista com os mesmos dicionários encontrados (não são cópias),
           podendo estar vazia.
    """
    encontrados = []

    for r in lista_registros:
        if termo.lower() == r["acao"].lower():
            encontrados.append(r)

    return encontrados


def atualizar_registro(lista_registros: list[dict], registro: dict, nome: str = "") -> bool:
    """
    Atualiza o nome da ação de um registro existente; nome vazio mantem o
    valor atual. Nível, peso e pontos não são editáveis aqui de propósito:
    eles definem quanto aquele dia valeu e já foram calculados no momento
    do registro - se precisam mudar, o registro deve ser excluido e um
    novo criado em "Registrar pontos".
    Entrada: lista_registros (list[dict]); registro (dict) que deve ser um
             dos elementos de lista_registros; nome (texto, pode vir
             vazio), já validado por quem chama a função.
    Saida: True se o registro pertencia a lista_registros e foi atualizado,
           False caso contrario.
    """
    if registro not in lista_registros:
        return False

    if nome:
        registro["acao"] = nome

    return True


def excluir_registro(lista_registros: list[dict], registro: dict) -> bool:
    """
    Exclui um registro existente.
    Entrada: lista_registros (list[dict]); registro (dict) que deve ser um
             dos elementos de lista_registros.
    Saida: True se o registro foi encontrado e excluido, False caso
           contrário.
    """
    if registro not in lista_registros:
        return False

    lista_registros.remove(registro)
    return True


# ---------------------------------------------------------------------------
# RELATÓRIOS E FILTROS
# ---------------------------------------------------------------------------

def filtrar_por_periodo(lista_registros: list[dict], p: int) -> list[dict]:
    """
    Seleciona os registros de um periodo.
    Entrada: lista_registros (list[dict]); p (int), número do período.
    Saida: lista de dicionários encontrados, podendo estar vazia.
    """
    filtrados = []

    for r in lista_registros:
        if r["periodo"] == p:
            filtrados.append(r)

    return filtrados


def pega_peso_registro(registro: dict) -> float:
    """
    Obtem o peso de um registro para ordenar a lista.
    Entrada: registro (dict), com dia, periodo, acao, nivel, peso, nome,
             cpf e pontos.
    Saida: peso da ação realizada nesse registro (float).
    """
    return registro["peso"]


def registros_por_peso(lista_registros: list[dict]) -> list[dict]:
    """
    Ordena os registros do maior peso de ação para o menor.
    Entrada: lista_registros (list[dict]).
    Saida: nova lista ordenada, preservando a lista original.
    """
    return sorted(lista_registros, key=pega_peso_registro, reverse=True)
