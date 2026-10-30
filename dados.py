"""
Camada de dados e regras de negócio do Sistema de Pontos Ambientais Lobo-guará Tech.

Este modulo concentra: as estruturas de dados (períodos e níveis de impacto),
as validações de entrada, os cálculos de pontuação e os filtros e ordenações
dos registros. A interação com o usuário fica em menu.py e o acesso ao banco
fica em banco.py.
"""

from datetime import datetime


# DADOS DO SISTEMA

# Cada período é uma tupla: (id, faixa_dias, pontos_por_dia_texto, total_texto, limite_dias)
periodos: list[tuple] = [
    (1, "1 a 7 dias", "10 pts por dia", "70 pts", 7),
    (2, "8 a 15 dias", "20 pts por dia", "160 pts", 15),
    (3, "16 a 30 dias", "30 pts por dia", "450 pts", 30),
]

# Cada nível de impacto é uma tupla: (id, nome, peso).
niveis_impacto: list[tuple] = [
    (1, "Crítico", 10.6),
    (2, "Estrutural", 6.6),
    (3, "Rotina", 1.6),
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

LIMITE_TOTAL: float = 1000.0
LIMITE_DIAS: float = 680.0
LIMITE_ACOES: float = 318.0

# VALIDAÇÃO

def nome_valido(texto: str) -> bool:
    """
    Verifica se o nome não está vazio.
    Entrada: texto (str).
    Saida: True se valido ou False se invalido.
    """
    return bool(texto.strip())


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


def formata_cpf(cpf: str) -> str:
    """
    Coloca pontos e traço no CPF, como ele é guardado no banco.
    Entrada: cpf (str) com 11 números.
    Saida: CPF formatado (str), por exemplo 123.456.789-01.
    """
    return f"{cpf[0:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:11]}"


def nome_completo_valido(texto: str) -> bool:
    """
    Verifica se o texto tem nome e sobrenome e cabe no banco (150 letras).
    Entrada: texto (str).
    Saida: True se válido ou False se inválido.
    """
    texto = texto.strip()

    return len(texto.split()) >= 2 and len(texto) <= 150


def email_valido(texto: str) -> bool:
    """
    Verifica o formato básico do e-mail: um só @, texto antes dele e um
    domínio com ponto, sem espaços.
    Entrada: texto (str).
    Saida: True se válido ou False se inválido.
    """
    texto = texto.strip()

    if " " in texto or len(texto) > 150 or texto.count("@") != 1:
        return False

    antes, dominio = texto.split("@")

    return len(antes) > 0 and "." in dominio and not dominio.startswith(".") and not dominio.endswith(".")


def username_valido(texto: str) -> bool:
    """
    Verifica se o username tem de 3 a 50 caracteres, só com letras, números
    e _ (sem espaços).
    Entrada: texto (str).
    Saida: True se válido ou False se inválido.
    """
    texto = texto.strip()

    return 3 <= len(texto) <= 50 and texto.isascii() and texto.replace("_", "").isalnum()


def senha_valida(texto: str) -> bool:
    """
    Verifica se a senha tem de 6 a 150 caracteres e não tem espaços.
    Entrada: texto (str).
    Saida: True se válida ou False se inválida.
    """
    return 6 <= len(texto) <= 150 and " " not in texto


def preparar_senha(senha: str) -> str:
    """
    Prepara a senha para ser gravada no banco. Hoje devolve o texto como foi
    digitado, igual ao que o grupo assumiu da API Java; se a API usar hash,
    é só trocar este ponto.
    Entrada: senha (str).
    Saida: senha (str) pronta para gravar.
    """
    return senha


def converte_data_nascimento(texto: str) -> datetime | None:
    """
    Converte uma data no formato dd/mm/aaaa. Não aceita datas inválidas,
    futuras ou antes de 1900.
    Entrada: texto (str), por exemplo "25/12/2005".
    Saida: datetime da data, ou None se for inválida.
    """
    try:
        data = datetime.strptime(texto.strip(), "%d/%m/%Y")
    except ValueError:
        return None

    if data > datetime.now() or data.year < 1900:
        return None

    return data


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


def periodo_valido(numero: int) -> bool:
    """
    Verifica se o período existe.
    Entrada: numero (int), número do período.
    Saida: True para 1, 2 ou 3; False para os demais valores.
    """
    return numero in (1, 2, 3)


def buscar_item(lista: list[tuple], numero: int) -> tuple | None:
    """
    Procura numa lista de tuplas a que tem o número no início (posição 0).
    Entrada: lista (list[tuple]); numero (int).
    Saida: a tupla encontrada, ou None se não existir.
    """
    for item in lista:
        if item[0] == numero:
            return item

    return None


def nivel_impacto_valido(lista: list[tuple], numero: int) -> bool:
    """
    Verifica se o nível de impacto existe.
    Entrada: lista (list[tuple]); numero (int).
    Saida: True se existir ou False caso contrario.
    """
    return buscar_item(lista, numero) is not None


# CÁLCULO DE PONTOS

def base_diaria(dia: int) -> float:
    """
    Calcula os pontos básicos do dia.
    Entrada: dia (int), entre 1 e 30.
    Saida: pontuação base (float).
    """
    if dia <= 7:
        return 10.0
    elif dia <= 15:
        return 20.0
    else:
        return 30.0


def peso_do_nivel(lista: list[tuple], numero: int) -> float:
    """
    Busca o peso associado a um nível de impacto.
    Entrada: lista (list[tuple]); numero (int) existente.
    Saida: peso (float) ou 0.0 se o nível não existir.
    """
    item = buscar_item(lista, numero)

    if item is None:
        return 0.0

    return item[2]


def nome_do_nivel(lista: list[tuple], numero: int) -> str:
    """
    Busca o nome associado a um nível de impacto.
    Entrada: lista (list[tuple]); numero (int) existente.
    Saida: nome do nível (str), ou string vazia se o nível não existir.
    """
    item = buscar_item(lista, numero)

    if item is None:
        return ""

    return item[1]


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
    Saida: tupla (pontos, novo_dias, novo_acoes).
    """
    # Quanto ainda cabe no limite total
    restante = max(0.0, limite_total - pts_dias - pts_acoes)

    # Pontos dos dias: base diária limitada pelo teto dos dias e pelo restante
    base = min(
        base_diaria(dia),
        max(0.0, limite_pts_dias - pts_dias),
        restante,
    )

    # Desconta os pontos dos dias do que ainda cabe
    restante = max(0.0, restante - base)

    # Pontos da ação: peso do nível limitado pelo teto das ações e pelo restante
    extra = min(
        peso,
        max(0.0, limite_pts_acoes - pts_acoes),
        restante,
    )

    # Atualiza os acumulados, arredondando para 2 casas
    novo_dias = round(pts_dias + base, 2)
    novo_acoes = round(pts_acoes + extra, 2)
    pontos = round(base + extra, 2)

    return pontos, novo_dias, novo_acoes


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


def filtrar_por_campo(lista: list[dict], campo: str, valor) -> list[dict]:
    """
    Seleciona os itens em que o campo tem o valor informado. Serve para
    qualquer lista de dicts (por status, por comunidade...); textos são
    comparados sem diferenciar maiúsculas de minúsculas.
    Entrada: lista (list[dict]); campo (str), chave do dict, como "status";
             valor, o que procurar.
    Saida: nova lista, podendo estar vazia.
    """
    resultado = []

    for item in lista:
        if str(item[campo]).upper() == str(valor).upper():
            resultado.append(item)

    return resultado


def pega_pontos(item: dict) -> float:
    """
    Obtém os pontos de um item (registro ou usuário) para ordenar a lista.
    Entrada: item (dict) com a chave "pontos".
    Saida: pontos (float).
    """
    return item["pontos"]


def ordenar_por_pontos(lista: list[dict]) -> list[dict]:
    """
    Ordena do maior para o menor número de pontos. Serve para registros e
    para usuários (ranking).
    Entrada: lista (list[dict]) com a chave "pontos".
    Saida: nova lista ordenada, preservando a original.
    """
    return sorted(lista, key=pega_pontos, reverse=True)


def itens_que_faltam(lista: list[dict], outra: list[dict]) -> list[dict]:
    """
    Seleciona os itens de uma lista que não aparecem em outra (comparando
    pelo "id").
    Entrada: lista (list[dict]) e outra (list[dict]), ambas com a chave "id".
    Saida: nova lista, podendo estar vazia.
    """
    resultado = []

    for item in lista:
        if buscar_item_por_id(outra, item["id"]) is None:
            resultado.append(item)

    return resultado


def buscar_item_por_id(lista: list[dict], numero: int) -> dict | None:
    """
    Procura numa lista de dicts o que tem o "id" informado.
    Entrada: lista (list[dict]); numero (int).
    Saida: o dict encontrado, ou None.
    """
    for item in lista:
        if item["id"] == numero:
            return item

    return None
