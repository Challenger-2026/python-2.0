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


def pede_opcao(validas: tuple) -> str:
    """
    Pede a opção de um menu e repete até receber uma das válidas.
    Entrada: validas (tuple) com as opções aceitas, como ("0", "1", "2").
    Saida: opção (str) válida.
    """
    opcao = input("\nOpção: ").strip()

    while opcao not in validas:
        print("Opção inválida.")
        opcao = input("Opção: ").strip()

    return opcao


def pede_valor_valido(pergunta: str, valida, mensagem_erro: str) -> str:
    """
    Faz uma pergunta e repete até a resposta passar na função de validação.
    Serve para qualquer texto (nome, link, busca...): quem chama diz qual
    validação usar.
    Entrada: pergunta (str), sem os dois-pontos; valida (função) que recebe o
             texto e devolve True ou False, como dados.nome_valido;
             mensagem_erro (str) mostrada quando a resposta é recusada.
    Saida: resposta (str), sem espaços nas pontas.
    """
    resposta = input(f"\n{pergunta}: ").strip()

    while not valida(resposta):
        print(mensagem_erro)
        resposta = input(f"{pergunta}: ").strip()

    return resposta


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
# CPF
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


def escolhe_comunidade(lista: list[dict], titulo: str, pergunta: str) -> int:
    """
    Mostra comunidades numeradas e pede uma delas. Serve para qualquer lista
    de comunidades (do usuário, da API, as que faltam entrar...).
    Entrada: lista (list[dict]) com id e nome, não vazia; titulo (str)
             mostrado acima da lista; pergunta (str) feita ao usuário.
    Saida: id (int) da comunidade escolhida.
    """
    print(f"\n{titulo}")

    for numero, item in enumerate(lista, start=1):
        print(f"{numero}. {item['nome']}")

    escolha = pede_numero_da_lista(pergunta, len(lista))

    return lista[escolha - 1]["id"]


def escolhe_comunidade_ou_aviso(lista: list[dict], titulo: str, pergunta: str, aviso: str) -> int | None:
    """
    Pede uma comunidade da lista ou, se ela estiver vazia, mostra um aviso.
    Entrada: lista (list[dict]); titulo, pergunta e aviso (str).
    Saida: id (int) da comunidade escolhida, ou None se a lista está vazia.
    """
    if not lista:
        print(f"\n{aviso}")
        return None

    return escolhe_comunidade(lista, titulo, pergunta)


def escolhe_comunidade_do_usuario(conexao, usuario: dict) -> int | None:
    """
    Pede em qual das comunidades do usuário ele quer registrar as ações.
    Entrada: conexao (conexão aberta); usuario (dict com id); resposta pelo
             teclado.
    Saida: id (int) da comunidade, ou None se ele não participa de nenhuma
           (ou se a consulta falhou).
    """
    try:
        lista = banco.listar_comunidades_do_usuario(conexao, usuario["id"])
    except banco.ErroBanco as erro:
        print(f"\nErro: {erro}")
        return None

    if not lista:
        return None

    return escolhe_comunidade(lista, "Suas comunidades:", "Em qual comunidade registrar?")


# CADASTRO DE USUÁRIO

def pede_cpf_novo(conexao) -> str:
    """
    Pede o CPF até receber um válido que ainda não esteja cadastrado.
    Entrada: conexao (conexão aberta); CPF pelo teclado (0 para desistir).
    Saida: CPF (str) com 11 números, ou string vazia se o usuário desistiu.
    Erro: banco.ErroBanco se a consulta falhar.
    """
    while True:
        cpf = pede_cpf_valido()

        if not cpf:
            return ""

        if not banco.campo_ja_cadastrado(conexao, "cpf", cpf):
            return cpf

        print("Esse CPF já está cadastrado. Use outra opção do menu para entrar.")


def pede_nome_completo() -> str:
    """
    Pede o nome completo até receber nome e sobrenome.
    Entrada: nome pelo teclado.
    Saida: nome completo (str).
    """
    return pede_valor_valido(
        "Nome completo", dados.nome_completo_valido, "Digite nome e sobrenome (até 150 letras).",
    )


def pede_email_novo(conexao, id_usuario: int = 0) -> str:
    """
    Pede o e-mail até receber um válido que ainda não esteja cadastrado.
    Entrada: conexao (conexão aberta); id_usuario (int), usuário que pode
             manter o próprio e-mail (0 no cadastro novo); e-mail pelo
             teclado.
    Saida: e-mail (str).
    Erro: banco.ErroBanco se a consulta falhar.
    """
    while True:
        email = input("\nE-mail: ").strip()

        if not dados.email_valido(email):
            print("E-mail inválido. Exemplo: nome@dominio.com")
        elif banco.campo_ja_cadastrado(conexao, "email", email, id_usuario):
            print("Esse e-mail já está cadastrado.")
        else:
            return email


def pede_username_novo(conexao, id_usuario: int = 0) -> str:
    """
    Pede o username até receber um válido que ainda não esteja cadastrado.
    Entrada: conexao (conexão aberta); id_usuario (int), usuário que pode
             manter o próprio username (0 no cadastro novo); username pelo
             teclado.
    Saida: username (str).
    Erro: banco.ErroBanco se a consulta falhar.
    """
    while True:
        username = input("\nUsername: ").strip()

        if not dados.username_valido(username):
            print("Username inválido: use de 3 a 50 letras, números ou _ (sem espaços).")
        elif banco.campo_ja_cadastrado(conexao, "username", username, id_usuario):
            print("Esse username já está cadastrado.")
        else:
            return username


def pede_data_nascimento():
    """
    Pede a data de nascimento até receber uma data real.
    Entrada: data pelo teclado, no formato dd/mm/aaaa.
    Saida: datetime da data informada.
    """
    texto = input("\nData de nascimento (dd/mm/aaaa): ")
    data = dados.converte_data_nascimento(texto)

    while data is None:
        print("Data inválida. Exemplo: 25/12/2005")
        texto = input("Data de nascimento (dd/mm/aaaa): ")
        data = dados.converte_data_nascimento(texto)

    return data


def pede_senha_nova() -> str:
    """
    Pede a senha duas vezes até as duas coincidirem.
    Entrada: senha pelo teclado.
    Saida: senha (str).
    """
    while True:
        senha = input("\nSenha (mínimo 6 caracteres, sem espaços): ")

        if not dados.senha_valida(senha):
            print("Senha inválida.")
        elif senha != input("Repita a senha: "):
            print("As senhas não conferem.")
        else:
            return senha


def pede_dados_do_cadastro(conexao) -> dict | None:
    """
    Pergunta, um por vez, todos os dados do novo usuário.
    Entrada: conexao (conexão aberta); respostas pelo teclado.
    Saida: dict com cpf, nome, email, username, nascimento e senha; ou None
           se o usuário desistiu no CPF.
    Erro: banco.ErroBanco se uma consulta falhar.
    """
    cpf = pede_cpf_novo(conexao)

    if not cpf:
        return None

    nome = pede_nome_completo()
    email = pede_email_novo(conexao)
    username = pede_username_novo(conexao)
    nascimento = pede_data_nascimento()
    senha = pede_senha_nova()

    return {
        "cpf": cpf,
        "nome": nome,
        "email": email,
        "username": username,
        "nascimento": nascimento,
        "senha": senha,
    }


def mostra_resumo_do_cadastro(cadastro: dict) -> None:
    """
    Mostra os dados digitados para o usuário conferir. O CPF e a senha não
    aparecem na tela.
    Entrada: cadastro (dict) de pede_dados_do_cadastro.
    Saida: não retorna valor; imprime o resumo.
    """
    print("\n" + "-" * 50)
    print(f"Nome.......: {cadastro['nome']}")
    print(f"E-mail.....: {cadastro['email']}")
    print(f"Username...: {cadastro['username']}")
    print(f"Nascimento.: {cadastro['nascimento'].strftime('%d/%m/%Y')}")
    print("-" * 50)


def grava_cadastro(conexao, cadastro: dict) -> None:
    """
    Grava o cadastro no banco (CPF com pontos e traço, senha preparada).
    Entrada: conexao (conexão aberta); cadastro (dict).
    Saida: não retorna valor.
    Erro: banco.ErroBanco se o banco recusar.
    """
    banco.inserir_usuario(
        conexao,
        cadastro["nome"],
        dados.formata_cpf(cadastro["cpf"]),
        cadastro["email"],
        cadastro["username"],
        dados.preparar_senha(cadastro["senha"]),
        cadastro["nascimento"],
    )


def cadastrar_usuario_interativo(conexao) -> bool:
    """
    Tela de cadastro: pergunta os dados, mostra o resumo, pede confirmação e
    grava o novo usuário (perfil COMUM, nível 1, saldo 0).
    Entrada: conexao (conexão aberta); dados pelo teclado.
    Saida: True se cadastrou; False se desistiu, cancelou ou houve erro.
    """
    print("\n=== CADASTRO DE USUÁRIO ===")

    sucesso = False
    confirmou = False

    try:
        cadastro = pede_dados_do_cadastro(conexao)

        if cadastro is not None:
            mostra_resumo_do_cadastro(cadastro)
            confirmou = pergunta_sim_nao("Confirma o cadastro?")

        if confirmou:
            grava_cadastro(conexao, cadastro)

    except banco.ErroBanco as erro:
        print(f"\nErro: {erro}")

    else:
        if confirmou:
            print("\nCadastro realizado! Escolha \"Entrar\" no menu para acessar sua conta.")
            sucesso = True
        else:
            print("\nCadastro cancelado.")

    pausar()
    return sucesso



# LOGIN E CONTA DO USUÁRIO (CRUD DO CADASTRO)

# Campo do perfil escolhido em "Alterar dados" -> chave do dict do perfil
CAMPOS_DO_PERFIL: dict = {"1": "nome", "2": "username"}

TENTATIVAS_DE_LOGIN: int = 3


def entrar_interativo(conexao) -> dict | None:
    """
    Tela de login: pede username (ou e-mail) e senha, com até 3 tentativas.
    Entrada: conexao (conexão aberta); login e senha pelo teclado (0 no login
             volta ao menu).
    Saida: dict com id e nome do usuário, ou None se ele desistiu, errou as
           3 vezes ou houve erro no banco.
    """
    print("\n=== ENTRAR ===")

    for tentativa in range(1, TENTATIVAS_DE_LOGIN + 1):
        login = input("\nUsername ou e-mail (0 para voltar): ").strip()

        if login == "0":
            return None

        senha = input("Senha: ")

        try:
            usuario = banco.buscar_usuario_por_login(conexao, login, dados.preparar_senha(senha))
        except banco.ErroBanco as erro:
            print(f"\nErro: {erro}")
            return None

        if usuario is not None:
            print(f"\nOlá, {usuario['nome']}!")
            return usuario

        print(f"Username/e-mail ou senha incorretos (tentativa {tentativa} de {TENTATIVAS_DE_LOGIN}).")

    return None


def mostra_perfil(perfil: dict) -> None:
    """
    Mostra os dados do perfil. O CPF e a senha não aparecem na tela.
    Entrada: perfil (dict) de banco.buscar_perfil.
    Saida: não retorna valor; imprime o perfil.
    """
    print("\n" + "-" * 50)
    print(f"Nome.......: {perfil['nome']}")
    print(f"E-mail.....: {perfil['email']}")
    print(f"Username...: {perfil['username']}")
    print(f"Nascimento.: {perfil['nascimento'].strftime('%d/%m/%Y')}")
    print(f"Perfil.....: {perfil['perfil']}")
    print(f"Nível......: {perfil['nivel']}")
    print(f"Pontos.....: {perfil['pontos']:.2f}")
    print("-" * 50)


def ver_perfil_interativo(conexao, id_usuario: int) -> None:
    """
    READ: mostra o perfil do usuário que está na conta.
    Entrada: conexao (conexão aberta); id_usuario (int).
    Saida: não retorna valor; exibe o perfil.
    """
    try:
        perfil = banco.buscar_perfil(conexao, id_usuario)
    except banco.ErroBanco as erro:
        print(f"\nErro: {erro}")
    else:
        if perfil is None:
            print("\nPerfil não encontrado.")
        else:
            mostra_perfil(perfil)

    pausar()


def pede_novo_valor(conexao, opcao: str, id_usuario: int) -> str:
    """
    Pergunta o novo valor do dado escolhido em "Alterar dados".
    Entrada: conexao (conexão aberta); opcao (str), 1 (nome) ou 2
             (username); id_usuario (int).
    Saida: novo valor (str).
    Erro: banco.ErroBanco se uma consulta falhar.
    """
    match opcao:
        case "1":
            return pede_nome_completo()
        case _:
            return pede_username_novo(conexao, id_usuario)


def alterar_dados_interativo(conexao, usuario: dict) -> bool:
    """
    UPDATE: deixa escolher um dado do perfil (nome ou username), pergunta o novo valor e grava no banco.
    Entrada: conexao (conexão aberta); usuario (dict com id e nome) que tem o
             nome atualizado se o nome mudar; respostas pelo teclado.
    Saida: True se atualizou; False se desistiu ou houve erro.
    """
    opcao = menu_alterar_dados()

    if opcao == "3":
        return False

    sucesso = False

    try:
        perfil = banco.buscar_perfil(conexao, usuario["id"])

        if perfil is not None:
            perfil[CAMPOS_DO_PERFIL[opcao]] = pede_novo_valor(conexao, opcao, usuario["id"])

            sucesso = banco.atualizar_usuario(
                conexao, usuario["id"], perfil["nome"], perfil["username"],
            )

    except banco.ErroBanco as erro:
        print(f"\nErro: {erro}")

    else:
        if sucesso:
            # Mantém o nome mostrado no menu igual ao do banco
            usuario["nome"] = perfil["nome"]
            print("\nDados atualizados!")
        else:
            print("\nNão foi possível atualizar: perfil não encontrado.")

    pausar()
    return sucesso


def alterar_senha_interativo(conexao, id_usuario: int) -> bool:
    """
    UPDATE: troca a senha, exigindo a senha atual.
    Entrada: conexao (conexão aberta); id_usuario (int); senhas pelo teclado.
    Saida: True se trocou; False se a senha atual estava errada ou houve erro.
    """
    senha_atual = input("\nSenha atual: ")
    senha_nova = pede_senha_nova()
    trocou = False

    try:
        trocou = banco.atualizar_senha(
            conexao, id_usuario, dados.preparar_senha(senha_atual), dados.preparar_senha(senha_nova),
        )
    except banco.ErroBanco as erro:
        print(f"\nErro: {erro}")
    else:
        if trocou:
            print("\nSenha alterada!")
        else:
            print("\nSenha atual incorreta.")

    pausar()
    return trocou


def excluir_conta_interativo(conexao, usuario: dict) -> bool:
    """
    DELETE: exclui a conta do usuário, depois de uma confirmação e da senha.
    Entrada: conexao (conexão aberta); usuario (dict com id); confirmação e
             senha pelo teclado.
    Saida: True se a conta foi excluída; False se cancelou, errou a senha ou
           o banco recusou (conta com vínculos).
    """
    print("\nATENÇÃO: excluir a conta apaga o seu perfil e não pode ser desfeito.")

    excluida = False

    if pergunta_sim_nao("Deseja mesmo excluir a sua conta?"):
        senha = input("Digite a sua senha para confirmar: ")

        try:
            excluida = banco.excluir_usuario(conexao, usuario["id"], dados.preparar_senha(senha))
        except banco.ErroBanco as erro:
            print(f"\nErro: {erro}")
        else:
            if excluida:
                print("\nConta excluída. Até logo!")
            else:
                print("\nSenha incorreta. A conta não foi excluída.")
    else:
        print("\nExclusão cancelada.")

    pausar()
    return excluida


def listar_minhas_comunidades_interativo(conexao, id_usuario: int) -> None:
    """
    READ: mostra as comunidades de que o usuário participa.
    Entrada: conexao (conexão aberta); id_usuario (int).
    Saida: não retorna valor; imprime a lista.
    """
    try:
        lista = banco.listar_comunidades_do_usuario(conexao, id_usuario)
    except banco.ErroBanco as erro:
        print(f"\nErro: {erro}")
    else:
        if not lista:
            print("\nVocê ainda não participa de nenhuma comunidade.")
        else:
            print("\nSuas comunidades:")

            for item in lista:
                print(f"- {item['nome']}")

    pausar()


def entrar_comunidade_interativo(conexao, id_usuario: int) -> bool:
    """
    CREATE: mostra as comunidades em que o usuário ainda não está e o coloca
    na escolhida. Só quem participa de uma comunidade pode registrar pontos.
    Entrada: conexao (conexão aberta); id_usuario (int); escolha pelo teclado.
    Saida: True se entrou; False se não havia o que escolher ou houve erro.
    """
    entrou = False

    try:
        todas = banco.listar_comunidades(conexao)
        minhas = banco.listar_comunidades_do_usuario(conexao, id_usuario)

        id_comunidade = escolhe_comunidade_ou_aviso(
            dados.itens_que_faltam(todas, minhas),
            "Comunidades disponíveis:", "Em qual comunidade entrar?",
            "Você já participa de todas as comunidades.",
        )

        if id_comunidade is not None:
            banco.entrar_na_comunidade(conexao, id_usuario, id_comunidade)
            entrou = True

    except banco.ErroBanco as erro:
        print(f"\nErro: {erro}")

    else:
        if entrou:
            print("\nVocê entrou na comunidade!")

    pausar()
    return entrou


def sair_comunidade_interativo(conexao, id_usuario: int) -> bool:
    """
    DELETE: mostra as comunidades do usuário e o tira da escolhida.
    Entrada: conexao (conexão aberta); id_usuario (int); escolha pelo teclado.
    Saida: True se saiu; False se não havia o que escolher ou houve erro.
    """
    saiu = False

    try:
        id_comunidade = escolhe_comunidade_ou_aviso(
            banco.listar_comunidades_do_usuario(conexao, id_usuario),
            "Suas comunidades:", "De qual comunidade sair?",
            "Você ainda não participa de nenhuma comunidade.",
        )

        if id_comunidade is not None:
            saiu = banco.sair_da_comunidade(conexao, id_usuario, id_comunidade)

    except banco.ErroBanco as erro:
        print(f"\nErro: {erro}")

    else:
        if saiu:
            print("\nVocê saiu da comunidade.")

    pausar()
    return saiu



# TABELAS NA TELA


def mostra_periodos(periodos: list[tuple]) -> None:
    """
    Exibe a tabela de períodos.
    Entrada: periodos (list[tuple]).
    Saida: não retorna valor; imprime a tabela.
    """
    borda = "+" + "-" * 4 + "+" + "-" * 14 + "+" + "-" * 18 + "+" + "-" * 11 + "+"

    print("\n" + borda)
    print(f"| {'ID':>2} | {'Dias':<12} | {'Pontos/dia':<16} | {'Total':<9} |")
    print(borda)

    for item in periodos:
        print(f"| {item[0]:>2} | {item[1]:<12} | {item[2]:<16} | {item[3]:<9} |")

    print(borda)


def mostra_niveis_impacto(niveis: list[tuple]) -> None:
    """
    Exibe a tabela de níveis de impacto.
    Entrada: niveis (list[tuple]).
    Saida: não retorna valor; imprime a tabela.
    """
    borda = "+" + "-" * 4 + "+" + "-" * 7 + "+" + "-" * 6 + "+"

    borda = "+" + "-" * 4 + "+" + "-" * 12 + "+" + "-" * 8 + "+"

    print("\n" + borda)
    print(f"| {'ID':>2} | {'Nível':<10} | {'Pontos':>6} |")
    print(borda)

    for item in niveis:
        print(f"| {item[0]:>2} | {item[1]:<10} | {item[2]:>6.2f} |")

    print(borda)


def mostra_exemplos_acoes(niveis: list[tuple]) -> None:
    """
    Mostra a tabela de níveis de impacto e sugestões de ações ambientais
    agrupadas por nível, pra ilustrar o que pode ser informado no dia.
    Entrada: niveis (list[tuple]).
    Saida: não retorna valor; imprime a tabela e as sugestões, que são
           só ilustrativas.
    """
    mostra_niveis_impacto(niveis)

    print("\nExemplos de ações por nível:")
    print("-" * 50)
    print("Crítico....: Mutirões, recuperação de nascentes,")
    print("             descarte de resíduos perigosos")
    print("Estrutural.: Compostagem, energia limpa,")
    print("             substituição de itens descartáveis")
    print("Rotina.....: Transporte ativo, economia de água,")
    print("             consumo consciente")
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


def quebra_texto(texto: str | None, largura: int) -> list[str]:
    """
    Quebra um texto em linhas de até "largura" letras, por palavra inteira
    (igual ao "Wrap Text" do Excel).
    Entrada: texto (str, ou None); largura (int).
    Saida: lista com pelo menos uma linha (vazia se o texto for vazio).
    """
    if texto is None:
        texto = ""

    linhas = textwrap.wrap(texto, largura)

    if not linhas:
        linhas = [""]

    return linhas


def mostra_linhas_do_registro(posicao: int, registro: dict, largura: int) -> None:
    """
    Imprime um registro dentro da tabela numerada. Ação longa ocupa mais de
    uma linha; só a primeira mostra o número, o status e os pontos.
    Entrada: posicao (int); registro (dict); largura (int) da coluna Ação.
    Saida: não retorna valor; imprime as linhas.
    """
    linhas = quebra_texto(registro["acao"], largura)

    for indice, linha in enumerate(linhas):
        if indice == 0:
            print(
                f"| {posicao:>3} | {linha:<{largura}} | "
                f"{registro['status']:<10} | {registro['pontos']:>6.2f} |"
            )
        else:
            print(f"| {'':>3} | {linha:<{largura}} | {'':<10} | {'':>6} |")


def mostra_registros_numerados(lista: list[dict]) -> None:
    """
    Exibe uma tabela com os registros, numerados pela posição (1, 2, 3...)
    para permitir escolher um deles.
    Entrada: lista (list[dict]).
    Saida: não retorna valor; imprime a tabela numerada.
    """
    largura = 30

    borda = "+" + "-" * 5 + "+" + "-" * 32 + "+" + "-" * 12 + "+" + "-" * 8 + "+"

    print("\n" + borda)
    print(f"| {'Nº':>3} | {'Ação':<30} | {'Status':<10} | {'Pontos':>6} |")
    print(borda)

    for posicao, registro in enumerate(lista, start=1):
        mostra_linhas_do_registro(posicao, registro, largura)
        print(borda)


def mostra_registros_ou_aviso(lista: list[dict], aviso: str) -> None:
    """
    Mostra a tabela numerada ou, se a lista estiver vazia, uma mensagem.
    Entrada: lista (list[dict]); aviso (str) mostrado quando não há registros.
    Saida: não retorna valor.
    """
    if lista:
        mostra_registros_numerados(lista)
    else:
        print(aviso)



# REGISTRO DE PONTOS: ciclo (período inicial, retomada e progresso)
#
# O "ciclo" é um dict com o andamento do registro (periodo, dia, pontos...),
# no mesmo formato do dict "progresso" de dados.py, usado para retomar.


def limite_de_dias(periodos: list[tuple], periodo: int) -> int:
    """
    Busca o último dia de um período.
    Entrada: periodos (list[tuple]); periodo (int), de 1 a 3.
    Saida: último dia do período (int).
    """
    # A posição 4 da tupla é o último dia do período
    return periodos[periodo - 1][4]


def pede_periodo_inicial(periodos: list[tuple]) -> int:
    """
    Mostra os períodos e pede em qual começar.
    Entrada: periodos (list[tuple]); período pelo teclado.
    Saida: número do período escolhido (int), de 1 a 3.
    """
    mostra_periodos(periodos)

    entrada = input("\nPeríodo inicial (1, 2 ou 3): ").strip()

    while not dados.inteiro_valido(entrada) or not dados.periodo_valido(int(entrada)):
        print("Período inválido.")
        entrada = input("Período inicial (1, 2 ou 3): ").strip()

    return int(entrada)


def inicia_novo_ciclo(periodos: list[tuple]) -> dict:
    """
    Cria um ciclo do zero, no período e dia 1 escolhidos pelo usuário.
    Entrada: periodos (list[tuple]).
    Saida: ciclo (dict) novo, sem pontos e sem dias registrados.
    """
    periodo = pede_periodo_inicial(periodos)

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

def pede_nivel_impacto(niveis: list[tuple]) -> int:
    """
    Pede o nível de impacto da ação até receber um que exista.
    Entrada: niveis (list[tuple]); nível pelo teclado.
    Saida: id do nível escolhido (int).
    """
    entrada = input("\nNível de impacto da ação (1, 2 ou 3): ").strip()

    while not dados.inteiro_valido(entrada) or not dados.nivel_impacto_valido(niveis, int(entrada)):
        print("Nível de impacto inválido.")
        entrada = input("Nível de impacto da ação (1, 2 ou 3): ").strip()

    return int(entrada)


def pede_nome_da_acao() -> str:
    """
    Pede o nome da ação realizada até receber um texto não vazio.
    Entrada: nome pelo teclado.
    Saida: nome da ação (str).
    """
    return pede_valor_valido("Ação realizada no dia", dados.nome_valido, "Ação inválida.")


def pede_link_evidencia() -> str:
    """
    Pede o link da evidência da ação até receber um link válido.
    Entrada: link pelo teclado.
    Saida: link (str) começando com http:// ou https://.
    """
    return pede_valor_valido("Link da evidência (começa com http)", dados.url_valida, "Link inválido.")


def pede_dados_da_acao(niveis: list[tuple]) -> dict:
    """
    Mostra os níveis e exemplos e pergunta tudo sobre a ação do dia: nível
    de impacto, nome e link da evidência.
    Entrada: niveis (list[tuple]); respostas pelo teclado.
    Saida: dict com nivel (nome), peso, acao e url.
    """
    mostra_exemplos_acoes(niveis)

    nivel = pede_nivel_impacto(niveis)
    acao = pede_nome_da_acao()
    url = pede_link_evidencia()

    return {
        "nivel": dados.nome_do_nivel(niveis, nivel),
        "peso": dados.peso_do_nivel(niveis, nivel),
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


def grava_acao(conexao, info: dict, pontos: float, usuario: dict, id_comunidade: int) -> bool:
    """
    Grava a ação no banco como postagem PENDENTE e avisa se o banco recusar.
    Entrada: conexao (conexão aberta); info (dict com acao e url); pontos
             (float); usuario (dict); id_comunidade (int).
    Saida: True se gravou; False se o banco recusou.
    """
    try:
        banco.inserir_postagem(
            conexao, info["acao"], info["url"], pontos, usuario["id"], id_comunidade,
        )
    except banco.ErroBanco as erro:
        print(f"\nErro: {erro}")
        return False

    return True


def monta_resultado(info: dict, pontos: float) -> dict:
    """
    Junta os dados da ação com os pontos do dia.
    Entrada: info (dict com acao, url, nivel e peso); pontos (float).
    Saida: resultado (dict com acao, url, nivel, peso e pontos).
    """
    return {
        "acao": info["acao"],
        "url": info["url"],
        "nivel": info["nivel"],
        "peso": info["peso"],
        "pontos": pontos,
    }


def registra_dia_com_acao(
    conexao,
    usuario: dict,
    id_comunidade: int,
    ciclo: dict,
    niveis: list[tuple],
    limites: tuple[float, float, float],
) -> dict | None:
    """
    Registra um dia em que o usuário fez uma ação: pergunta os dados, calcula
    os pontos e grava a ação no banco. Se o banco recusar, desfaz o cálculo
    dos pontos do dia.
    Entrada: conexao (conexão aberta); usuario (dict); id_comunidade (int);
             ciclo (dict) que é atualizado com os pontos; niveis
             (list[tuple]); limites (tuple) com limite_total, limite_pts_dias
             e limite_pts_acoes.
    Saida: resultado (dict com acao, nivel, peso e pontos), ou None se o
           banco recusou o registro.
    """
    limite_total, limite_pts_dias, limite_pts_acoes = limites

    info = pede_dados_da_acao(niveis)

    # Guarda os acumulados para desfazer se o banco recusar o registro
    dias_antes = ciclo["pts_dias"]
    acoes_antes = ciclo["pts_acoes"]

    pontos, ciclo["pts_dias"], ciclo["pts_acoes"] = dados.calcula_pontos_dia(
        ciclo["dia"], info["peso"], dias_antes, acoes_antes,
        limite_total, limite_pts_dias, limite_pts_acoes,
    )

    if not grava_acao(conexao, info, pontos, usuario, id_comunidade):
        # Restaura os pontos de antes do dia
        ciclo["pts_dias"] = dias_antes
        ciclo["pts_acoes"] = acoes_antes
        return None

    return monta_resultado(info, pontos)


def resultado_sem_acao() -> dict:
    """
    Cria o resultado de um dia em que não houve ação: vale 0 pontos.
    Entrada: não recebe parâmetros.
    Saida: resultado (dict com acao, url, nivel, peso e pontos).
    """
    return {"acao": "Nenhuma ação", "url": "", "nivel": "Nenhuma", "peso": 0.0, "pontos": 0.0}


def guarda_resposta(ciclo: dict, fez_acao: bool, resultado: dict) -> None:
    """
    Guarda a resposta do dia para a exportação em JSON.
    Entrada: ciclo (dict) com periodo e dia; fez_acao (bool); resultado (dict).
    Saida: não retorna valor; acrescenta em dados.respostas_usuario.
    """
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


def registra_dia(
    conexao,
    usuario: dict,
    id_comunidade: int,
    ciclo: dict,
    niveis: list[tuple],
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
        resultado = registra_dia_com_acao(conexao, usuario, id_comunidade, ciclo, niveis, limites)

        if resultado is None:
            return False
    else:
        resultado = resultado_sem_acao()

    guarda_resposta(ciclo, fez_acao, resultado)
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


def decide_fim_do_periodo(ciclo: dict, periodos: list[tuple]) -> str:
    """
    Trata o último dia de um período: conclui o ciclo se era o período 3, ou
    pergunta se o usuário quer ir para o período seguinte.
    Entrada: ciclo (dict) que é atualizado; periodos (list[tuple]);
             resposta pelo teclado.
    Saida: PASSO_CONCLUIDO, PASSO_SEGUIR (foi para o próximo período) ou
           PASSO_PARAR (preferiu parar).
    """
    if ciclo["periodo"] == 3:
        print("\nCompletou o período 3.")
        return PASSO_CONCLUIDO

    proximo_periodo = ciclo["periodo"] + 1

    print(f"\nCompletou o período {ciclo['periodo']} ({limite_de_dias(periodos, ciclo['periodo'])} dias).")

    if not pergunta_sim_nao(f"Ir para o período {proximo_periodo}?"):
        return PASSO_PARAR

    # Passa para o período seguinte e já avança o dia
    ciclo["periodo"] = proximo_periodo
    ciclo["periodos_usados"].append(proximo_periodo)
    ciclo["dia"] += 1

    return PASSO_SEGUIR


def decide_proximo_passo(ciclo: dict, periodos: list[tuple], limite_total: float) -> str:
    """
    Decide o que fazer depois de registrar um dia: concluir se atingiu o
    limite de pontos, tratar o fim do período, ou perguntar pelo próximo dia.
    Entrada: ciclo (dict); periodos (list[tuple]); limite_total (float).
    Saida: PASSO_SEGUIR, PASSO_PARAR ou PASSO_CONCLUIDO.
    """
    # Ordem: limite de pontos, fim do período e, por último, próximo dia
    if ciclo["pts_dias"] + ciclo["pts_acoes"] >= limite_total:
        print("\nLimite de 1000 pontos atingido!")
        return PASSO_CONCLUIDO

    if ciclo["dia"] >= limite_de_dias(periodos, ciclo["periodo"]):
        return decide_fim_do_periodo(ciclo, periodos)

    return decide_proximo_dia(ciclo)


def executa_ciclo(
    conexao,
    usuario: dict,
    id_comunidade: int,
    ciclo: dict,
    periodos: list[tuple],
    niveis: list[tuple],
    limites: tuple[float, float, float],
) -> bool:
    """
    Registra dia após dia até o ciclo terminar ou o usuário parar.
    Entrada: conexao (conexão aberta); usuario (dict); id_comunidade (int);
             ciclo (dict) que é atualizado; periodos e niveis
             (list[tuple]); limites (tuple) com limite_total, limite_pts_dias
             e limite_pts_acoes.
    Saida: True se o ciclo foi concluído (limite de pontos ou 30 dias);
           False se o usuário parou no meio ou o banco recusou um registro.
    """
    while True:
        if not registra_dia(conexao, usuario, id_comunidade, ciclo, niveis, limites):
            return False

        passo = decide_proximo_passo(ciclo, periodos, limites[0])

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
    texto = ""

    for item in ciclo["periodos_usados"]:
        if texto:
            texto += ", "

        texto += str(item)

    print("\n" + "=" * 50)
    print("RESUMO FINAL")
    print("=" * 50)
    print(f"Usuário.......: {usuario['nome']}")
    print(f"Períodos......: {texto}")
    print(f"Dias..........: {ciclo['dias_registrados']}")
    print(f"Pontos dias...: {ciclo['pts_dias']:.2f} (limite {limite_pts_dias:.2f})")
    print(f"Pontos ações..: {ciclo['pts_acoes']:.2f} (limite {limite_pts_acoes:.2f})")
    print(f"TOTAL.........: {ciclo['pts_dias'] + ciclo['pts_acoes']:.2f} (limite {limite_total:.2f})")
    print("=" * 50)


def escolhe_ciclo(periodos: list[tuple], progresso: dict) -> dict:
    """
    Decide com qual ciclo trabalhar: continua o progresso salvo (se existir e
    o usuário quiser) ou começa um ciclo novo, limpando as respostas antigas.
    Entrada: periodos (list[tuple]); progresso (dict); resposta pelo teclado.
    Saida: ciclo (dict) pronto para executar.
    """
    if progresso["ativo"] and pergunta_continuar_ou_recomecar(progresso):
        return retoma_ciclo(progresso)

    dados.respostas_usuario.clear()

    return inicia_novo_ciclo(periodos)


def registrar_pontos(
    conexao,
    usuario: dict,
    id_comunidade: int | None,
    periodos: list[tuple],
    niveis: list[tuple],
    progresso: dict,
    limite_total: float,
    limite_pts_dias: float,
    limite_pts_acoes: float,
) -> None:
    """
    Conduz o registro de pontos ambientais: escolhe o ciclo, registra os
    dias, mostra o resumo e, se o ciclo terminou de verdade, oferece começar
    outro na hora. As ações feitas são gravadas no banco como postagens
    PENDENTES.
    Entrada: conexao (conexão aberta com o banco); usuario (dict com id e
             nome); id_comunidade (int, ou None se o usuário não tiver
             comunidade); periodos, niveis e progresso (listas/dict de
             dados); limite_total, limite_pts_dias e limite_pts_acoes
             (float), os tetos do sistema.
    Saida: não retorna valor; grava as ações no banco e atualiza progresso.
    """
    print("\n=== REGISTRO DE PONTOS AMBIENTAIS ===")

    if id_comunidade is None:
        print("\nVocê precisa participar de uma comunidade para registrar ações.")
        print("Entre em uma em: Minha conta > Minhas comunidades.")
        pausar()
        return

    limites = (limite_total, limite_pts_dias, limite_pts_acoes)

    while True:
        ciclo = escolhe_ciclo(periodos, progresso)
        concluido = executa_ciclo(conexao, usuario, id_comunidade, ciclo, periodos, niveis, limites)

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
    return pede_valor_valido("Buscar ação (nome exato)", dados.nome_valido, "Digite um nome para buscar.")


def pede_novo_nome() -> str:
    """
    Pede o novo nome de uma ação até receber um texto não vazio.
    Entrada: nome pelo teclado.
    Saida: novo nome (str).
    """
    return pede_valor_valido("Novo nome da ação", dados.nome_valido, "Nome inválido.")


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
        mostra_registros_ou_aviso(registros, "\nNenhum registro ainda.")

    pausar()


def buscar_registro_interativo(conexao, id_usuario: int) -> None:
    """
    Pergunta o nome de uma ação e mostra os registros do usuário com esse nome.
    Entrada: conexao (conexão aberta); id_usuario (int); nome pelo teclado.
    Saida: não retorna valor; imprime os registros encontrados.
    """
    nome = pede_nome_para_busca()

    try:
        lista = banco.buscar_postagens(conexao, id_usuario, nome)
    except banco.ErroBanco as erro:
        print(f"\nErro: {erro}")
    else:
        mostra_registros_ou_aviso(lista, "Nada encontrado.")

    pausar()


def avisa_resultado_da_atualizacao(alterado: bool) -> bool:
    """
    Avisa se a atualização funcionou.
    Entrada: alterado (bool) devolvido pelo banco.
    Saida: o mesmo valor de alterado.
    """
    if alterado:
        print("Registro atualizado!")
    else:
        print("Não foi possível atualizar: só registros PENDENTES podem ser alterados.")

    return alterado


def avisa_resultado_da_exclusao(confirmou: bool, excluido: bool) -> bool:
    """
    Avisa se a exclusão funcionou, foi cancelada ou foi recusada.
    Entrada: confirmou (bool), se o usuário confirmou; excluido (bool)
             devolvido pelo banco.
    Saida: True se o registro foi excluído.
    """
    if not confirmou:
        print("Exclusão cancelada.")
    elif excluido:
        print("Registro excluído!")
    else:
        print("Não foi possível excluir: só registros PENDENTES podem ser excluídos.")

    return confirmou and excluido


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

        nome = pede_novo_nome()
        alterado = banco.atualizar_postagem(conexao, registro["id"], id_usuario, nome)

    except (ValueError, banco.ErroBanco) as erro:
        print(f"\nErro: {erro}")

    else:
        sucesso = avisa_resultado_da_atualizacao(alterado)

    finally:
        print("Fim da tentativa de atualização.")

    pausar()
    return sucesso


def confirma_e_exclui(conexao, registro: dict, id_usuario: int) -> tuple[bool, bool]:
    """
    Pede a confirmação e só exclui no banco se o usuário confirmar.
    Entrada: conexao (conexão aberta); registro (dict); id_usuario (int).
    Saida: tupla (confirmou, excluido), dois bool.
    Erro: banco.ErroBanco se o banco recusar.
    """
    confirmou = pergunta_sim_nao("Confirma exclusão?")
    excluido = False

    if confirmou:
        excluido = banco.excluir_postagem(conexao, registro["id"], id_usuario)

    return confirmou, excluido


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

    # Mesmo esquema de try/except/else/finally do atualizar
    try:
        registro = escolhe_registro(conexao, id_usuario, "excluir")

        mostra_registro(registro)

        confirmou, excluido = confirma_e_exclui(conexao, registro, id_usuario)

    except (ValueError, banco.ErroBanco) as erro:
        print(f"\nErro: {erro}")

    else:
        sucesso = avisa_resultado_da_exclusao(confirmou, excluido)

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
        lista = dados.filtrar_por_campo(registros, "status", status)
        mostra_registros_ou_aviso(lista, "Nenhum registro com esse status.")

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
        lista = dados.ordenar_por_pontos(registros)
        mostra_registros_ou_aviso(lista, "\nNenhum registro ainda.")

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


def mostra_ranking(ranking: list[dict]) -> None:
    """
    Exibe a tabela do ranking de usuários.
    Entrada: ranking (list[dict]) já ordenada, com nome, perfil e pontos.
    Saida: não retorna valor; imprime a tabela.
    """
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
        mostra_ranking(dados.ordenar_por_pontos(usuarios))

    pausar()


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

    id_comunidade = escolhe_comunidade(comunidades, "Comunidades:", "Escolha a comunidade")
    lista = dados.filtrar_por_campo(postagens, "id_comunidade", id_comunidade)

    mostra_registros_ou_aviso(lista, "\nNenhuma postagem nessa comunidade.")
    pausar()


# MENUS

def menu_inicial() -> str:
    """
    Exibe e valida as opções da tela de entrada do sistema (quem ainda não
    entrou numa conta). É a primeira tela do programa.
    Entrada: opção informada pelo usuário no teclado.
    Saida: opção válida (str).
    """
    print("\n" + "=" * 50)
    print("SISTEMA DE PONTOS AMBIENTAIS LOBO-GUARÁ TECH")
    print("=" * 50)
    print("0. Sair")
    print("1. Entrar")
    print("2. Cadastrar-se")
    print("3. Consultar API pública")

    return pede_opcao(("0", "1", "2", "3"))


def menu_principal(nome: str) -> str:
    """
    Exibe e valida as opções do menu de quem já entrou na conta.
    Entrada: nome (str) do usuário que está na conta; opção pelo teclado.
    Saida: opção válida (str).
    """
    print("\n" + "=" * 50)
    print("SISTEMA DE PONTOS AMBIENTAIS LOBO-GUARÁ TECH")
    print("=" * 50)
    print(f"Usuário: {nome}")
    print("-" * 50)
    print("0. Encerrar o sistema")
    print("1. Registrar pontos")
    print("2. Gerenciar ações")
    print("3. Relatórios")
    print("4. Minha conta")
    print("5. Consultar API pública")
    print("6. Sair da conta")

    return pede_opcao(("0", "1", "2", "3", "4", "5", "6"))


def menu_conta() -> str:
    """
    Exibe e valida as opções da conta do usuário (CRUD do cadastro).
    Entrada: opção informada pelo usuário no teclado.
    Saida: opção válida (str).
    """
    print("\n" + "=" * 50)
    print("MINHA CONTA")
    print("=" * 50)
    print("1. Ver perfil")
    print("2. Alterar dados")
    print("3. Alterar senha")
    print("4. Minhas comunidades")
    print("5. Excluir conta")
    print("6. Voltar")

    return pede_opcao(("1", "2", "3", "4", "5", "6"))


def menu_alterar_dados() -> str:
    """
    Exibe e valida a escolha do dado do perfil a alterar.
    Entrada: opção informada pelo usuário no teclado.
    Saida: opção válida (str).
    """
    print("\n" + "=" * 50)
    print("ALTERAR DADOS")
    print("=" * 50)
    print("1. Nome")
    print("2. Username")
    print("3. Voltar")

    return pede_opcao(("1", "2", "3"))


def menu_comunidades() -> str:
    """
    Exibe e valida as opções de comunidades do usuário.
    Entrada: opção informada pelo usuário no teclado.
    Saida: opção válida (str).
    """
    print("\n" + "=" * 50)
    print("MINHAS COMUNIDADES")
    print("=" * 50)
    print("1. Ver minhas comunidades")
    print("2. Entrar em uma comunidade")
    print("3. Sair de uma comunidade")
    print("4. Voltar")

    return pede_opcao(("1", "2", "3", "4"))


def menu_crud() -> str:
    """
    Exibe e valida as opções de gerenciamento de ações.
    Entrada: opção informada pelo usuário no teclado.
    Saida: opção válida (str).
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

    return pede_opcao(("1", "2", "3", "4", "5", "6"))


def menu_api() -> str:
    """
    Exibe e valida as opções de consulta à API pública.
    Entrada: opção informada pelo usuário no teclado.
    Saida: opção válida (str).
    """
    print("\n" + "=" * 50)
    print("CONSULTAR API PÚBLICA")
    print("=" * 50)
    print("1. Ranking de usuários")
    print("2. Postagens de uma comunidade")
    print("3. Voltar")

    return pede_opcao(("1", "2", "3"))


def menu_relatorios() -> str:
    """
    Exibe e valida as opções de relatórios.
    Entrada: opção informada pelo usuário no teclado.
    Saida: opção válida (str).
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

    return pede_opcao(("1", "2", "3", "4", "5", "6"))
