"""
Camada de dados e regras de negócio do Sistema de Pontos Ambientais Lobo-guará Tech.

Este modulo concentra: as estruturas de dados (períodos e níveis de impacto),
as validações de entrada, os cálculos de pontuação e os filtros e ordenações
dos registros. A interação com o usuário fica em menu.py e o acesso ao banco
fica em banco.py.
"""



# DADOS DO SISTEMA

# Cada período é uma tupla: (id, faixa_dias, pontos_por_dia_texto, total_texto, limite_dias)
periodos: list[tuple] = [
    (1, "1 a 7 dias", "1 ponto por dia", "7 pontos", 7),
    (2, "8 a 15 dias", "2 pontos por dia", "16 pontos", 15),
    (3, "16 a 30 dias", "3 pontos por dia", "45 pontos", 30),
]

# Cada nível de impacto é uma tupla: (id, nome, peso).
niveis_impacto: list[tuple] = [
    (1, "Alto", 1.06),
    (2, "Médio", 0.66),
    (3, "Baixo", 0.16),
]

# Respostas dadas em "Registrar pontos", uma por dia registrado (usadas na
# exportação JSON). Guarda o ciclo em andamento e é limpa a cada ciclo novo.
respostas_usuario: list[dict] = []

# Ciclo de "Registrar pontos" em andamento, para continuar de onde parou.
# "ativo" é False quando não há nada para continuar.
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

# VALIDAÇÃO

def nome_valido(nome: str) -> bool:
    """
    Verifica se o nome não está vazio.
    Entrada: nome (str).
    Saida: True se valido ou False se invalido.
    """
    return bool(nome.strip())


def cpf_formato_valido(cpf: str) -> bool:
    """
    Valida só o formato do CPF: 11 números, não todos iguais. Os dígitos
    verificadores não são conferidos porque o CPF é procurado no banco logo
    em seguida, e os CPFs cadastrados ali são fictícios.
    Entrada: cpf (str), contendo somente os 11 numeros.
    Saida: True se valido ou False se invalido.
    """
    cpf = cpf.strip()

    # 11 dígitos e não pode ser sequência repetida (ex.: 11111111111)
    return len(cpf) == 11 and cpf.isascii() and cpf.isdigit() and cpf != cpf[0] * 11


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

# CÁLCULO DE PONTOS

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
    # Quanto ainda cabe no limite total
    restante_total = max(0.0, limite_total - pts_dias - pts_acoes)

    # Pontos dos dias: base diária limitada pelo teto dos dias e pelo restante
    pontos_dias = min(
        base_diaria(dia),
        max(0.0, limite_pts_dias - pts_dias),
        restante_total,
    )

    # Desconta os pontos dos dias do que ainda cabe
    restante_total = max(0.0, restante_total - pontos_dias)

    # Pontos da ação: peso do nível limitado pelo teto das ações e pelo restante
    pontos_acoes = min(
        peso,
        max(0.0, limite_pts_acoes - pts_acoes),
        restante_total,
    )

    # Atualiza os acumulados, arredondando para 2 casas
    novo_pts_dias = round(pts_dias + pontos_dias, 2)
    novo_pts_acoes = round(pts_acoes + pontos_acoes, 2)
    pts_do_dia = round(pontos_dias + pontos_acoes, 2)

    return pts_do_dia, novo_pts_dias, novo_pts_acoes


# REGISTROS VINDOS DO BANCO (link, status e pontos)

def url_valida(url: str) -> bool:
    """
    Verifica se o link da evidência começa com http:// ou https:// e não
    tem espaços.
    Entrada: url (str).
    Saida: True se valido ou False se invalido.
    """
    url = url.strip()

    return url.startswith(("http://", "https://")) and " " not in url and len(url) > 10


def filtrar_por_status(lista_registros: list[dict], status: str) -> list[dict]:
    """
    Seleciona os registros com o status informado (PENDENTE, APROVADO ou
    REJEITADO).
    Entrada: lista_registros (list[dict]); status (str).
    Saida: nova lista, podendo estar vazia.
    """
    registros_filtrados = []

    for registro in lista_registros:
        # Compara em maiúsculas para ignorar diferença de caixa
        if registro["status"].upper() == status.upper():
            registros_filtrados.append(registro)

    return registros_filtrados


def pega_pontos_registro(registro: dict) -> float:
    """
    Obtém os pontos de um registro para ordenar a lista.
    Entrada: registro (dict).
    Saida: pontos (float).
    """
    return registro["pontos"]


def registros_por_pontos(lista_registros: list[dict]) -> list[dict]:
    """
    Ordena os registros do maior para o menor número de pontos.
    Entrada: lista_registros (list[dict]).
    Saida: nova lista ordenada, preservando a original.
    """
    return sorted(lista_registros, key=pega_pontos_registro, reverse=True)


def pega_pontos_usuario(usuario: dict) -> float:
    """
    Obtém os pontos de um usuário para ordenar o ranking.
    Entrada: usuario (dict) com a chave "pontos".
    Saida: pontos (float).
    """
    return usuario["pontos"]


def ranking_de_usuarios(lista_usuarios: list[dict]) -> list[dict]:
    """
    Ordena os usuários do maior para o menor saldo de pontos.
    Entrada: lista_usuarios (list[dict]).
    Saida: nova lista ordenada, preservando a original.
    """
    return sorted(lista_usuarios, key=pega_pontos_usuario, reverse=True)


def filtrar_por_comunidade(lista_registros: list[dict], id_comunidade: int) -> list[dict]:
    """
    Seleciona as postagens de uma comunidade.
    Entrada: lista_registros (list[dict]) com a chave "id_comunidade";
             id_comunidade (int).
    Saida: nova lista, podendo estar vazia.
    """
    registros_filtrados = []

    for registro in lista_registros:
        if registro["id_comunidade"] == id_comunidade:
            registros_filtrados.append(registro)

    return registros_filtrados
