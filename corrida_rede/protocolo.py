# Autores: Murilo Andreotti Borges (RA 25163806-2) e Matheus Marçal Martinelli (RA 25076306-2)
# Sistemas Operacionais - Trabalho 02: jogo com troca de mensagens e gerenciamento de memória
# Prof. Maurilio Campano Jr - Corrida de Cavalos: Duelo 1x1 em rede
"""
protocolo.py - NOTAÇÃO DAS MENSAGENS trocadas entre servidor (Jogador 1) e cliente (Jogador 2).

Toda mensagem é uma linha de texto ASCII terminada em '\\n':

        <origem><tipo><carga>\\n

    origem : '1' = veio do servidor (Jogador 1)   |   '2' = veio do cliente (Jogador 2)
    tipo   : UMA letra maiúscula que diz qual é a ação (tabela abaixo)
    carga  : parâmetros da ação (pode ser vazia)

Assim como no exemplo "2Cc3" do enunciado (2 = vez do jogador 2, C = cavalo, c3 = casa),
o primeiro caractere diz quem enviou e o segundo diz o que aconteceu.

TABELA DE TIPOS
  H  handshake           2H1                  cliente se apresenta (carga = versão do protocolo)
                         1H1                  servidor responde
  V  visual              1V00A1..             16 dígitos hexadecimais = índice escolhido em cada
                                              linha da personalização (cavalo + corredor)
  R  pronto              2R1  /  2R0          jogador ficou pronto / desfez
  S  start (largada)     1S35;12              <comprimento da pista x10>;<nº de QTEs>
                                              => fase := CONTAGEM
  G  go                  1G                   fim da contagem => fase := CORRIDA
  Q  QTE (ação do jogo)  2QW                  jogador 2 apertou a tecla W/A/S/D
  T  telemetria          1T412;81234;80990;00;10;1,2,40,5,6,0,0;0,0,0,4,5,1,60
                                              estado da corrida (veja Telemetria)
  W  winner (fim)        1W1;14962;14947;11;11;12
                                              <vencedor>;<t1 ms>;<t2 ms>;<acertos1>;<acertos2>;<total>
                                              => fase := RESULTADO
  N  nova rodada         2N  /  1N            pede/confirma revanche => fase := PERSONALIZAÇÃO
  X  saída               2X  /  1X            avisa que está saindo

FASES DO JOGO (variável `fase`, existe nos DOIS processos e só muda por mensagem do servidor;
é o equivalente à variável "vez" do enunciado)
  0 PERSONALIZAÇÃO -> 1 CONTAGEM -> 2 CORRIDA -> 3 RESULTADO -> (N) -> 0 ...
"""
from collections import namedtuple

VERSAO = 1
PORTA = 51171                 # mesma porta usada nos exemplos do professor
MAX_LINHA = 512               # tamanho máximo de uma mensagem (buffer de tamanho fixo)

SERVIDOR, CLIENTE = 1, 2

FASE_PERSONALIZACAO, FASE_CONTAGEM, FASE_CORRIDA, FASE_RESULTADO = 0, 1, 2, 3
NOMES_FASE = ["PERSONALIZACAO", "CONTAGEM", "CORRIDA", "RESULTADO"]

TECLA_CODIGO = {"W": 1, "A": 2, "S": 3, "D": 4}
CODIGO_TECLA = {v: k for k, v in TECLA_CODIGO.items()}

TIPOS = "HVRSGQTWNX"

# Feedback de QTE que trafega na telemetria
FB_NENHUM, FB_PERFEITO, FB_ERRO, FB_LENTO = 0, 1, 2, 3

Mensagem = namedtuple("Mensagem", "origem tipo carga")
Telemetria = namedtuple("Telemetria", "frame x terminou ajuste qte")
# qte = (ativo, tecla, tempo, acertos, feitos, feedback, feedback_tempo)
Resultado = namedtuple("Resultado", "vencedor tempos_ms acertos total")


class ErroProtocolo(ValueError):
    """Mensagem fora da notação."""


# ------------------------------------------------------------------ codificar
def codificar(origem, tipo, carga=""):
    """Monta a linha de bytes pronta para enviar pelo socket."""
    if origem not in (SERVIDOR, CLIENTE) or tipo not in TIPOS:
        raise ErroProtocolo(f"origem/tipo inválidos: {origem!r} {tipo!r}")
    linha = f"{origem}{tipo}{carga}\n"
    if len(linha) > MAX_LINHA:
        raise ErroProtocolo("mensagem grande demais")
    return linha.encode("ascii")


def msg_hello(origem):
    return codificar(origem, "H", str(VERSAO))


def msg_visual(origem, indices):
    return codificar(origem, "V", "".join("%X" % (i & 15) for i in indices))


def msg_pronto(origem, pronto):
    return codificar(origem, "R", "1" if pronto else "0")


def msg_start(comprimento, n_qtes):
    return codificar(SERVIDOR, "S", f"{int(round(comprimento * 10))};{n_qtes}")


def msg_go():
    return codificar(SERVIDOR, "G")


def msg_qte(tecla):
    return codificar(CLIENTE, "Q", tecla)


def msg_telemetria(frame, x, terminou, ajuste, qte):
    """x: [x1, x2] em centésimos de pixel | terminou: [bool, bool] | ajuste: [-1/0/1, ...] | qte: 2 tuplas"""
    aj = "".join(str({-1: 2, 0: 0, 1: 1}[a]) for a in ajuste)
    term = "".join("1" if t else "0" for t in terminou)
    q = ";".join(",".join(str(int(v)) for v in qq) for qq in qte)
    return codificar(SERVIDOR, "T", f"{frame};{x[0]};{x[1]};{term};{aj};{q}")


def msg_winner(vencedor, tempos_ms, acertos, total):
    return codificar(SERVIDOR, "W", f"{vencedor};{tempos_ms[0]};{tempos_ms[1]};{acertos[0]};{acertos[1]};{total}")


def msg_nova(origem):
    return codificar(origem, "N")


def msg_saida(origem):
    return codificar(origem, "X")


# ------------------------------------------------------------------ decodificar
def decodificar(linha):
    """Lê uma linha (str, sem o '\\n') e devolve (Mensagem, dados).
    `dados` já vem interpretado conforme o tipo. Levanta ErroProtocolo se estiver fora da notação."""
    if len(linha) < 2 or len(linha) > MAX_LINHA:
        raise ErroProtocolo(f"tamanho inválido: {linha[:20]!r}")
    if linha[0] not in "12":
        raise ErroProtocolo(f"origem inválida: {linha[:20]!r}")
    origem, tipo, carga = int(linha[0]), linha[1], linha[2:]
    if tipo not in TIPOS:
        raise ErroProtocolo(f"tipo desconhecido: {tipo!r}")
    msg = Mensagem(origem, tipo, carga)
    try:
        return msg, _interpretar(msg)
    except (ValueError, IndexError, KeyError) as e:
        raise ErroProtocolo(f"carga inválida em {linha[:40]!r}: {e}")


def _interpretar(m):
    t, c = m.tipo, m.carga
    if t == "H":
        return int(c)
    if t == "V":
        if len(c) != 16:
            raise ValueError("V precisa de 16 dígitos")
        return [int(ch, 16) for ch in c]
    if t == "R":
        if c not in ("0", "1"):
            raise ValueError("R precisa de 0 ou 1")
        return c == "1"
    if t == "S":
        comp, n = c.split(";")
        return int(comp) / 10.0, int(n)
    if t == "Q":
        if c not in TECLA_CODIGO:
            raise ValueError("tecla inválida")
        return c
    if t == "T":
        campos = c.split(";")
        if len(campos) != 7:
            raise ValueError("T precisa de 7 campos")
        frame, x1, x2, term, aj, q1, q2 = campos
        ajuste = [{"0": 0, "1": 1, "2": -1}[ch] for ch in aj]
        qte = []
        for q in (q1, q2):
            v = tuple(int(n) for n in q.split(","))
            if len(v) != 7:
                raise ValueError("qte precisa de 7 valores")
            qte.append(v)
        return Telemetria(int(frame), [int(x1), int(x2)], [ch == "1" for ch in term], ajuste, qte)
    if t == "W":
        v, t1, t2, a1, a2, total = (int(n) for n in c.split(";"))
        return Resultado(v, [t1, t2], [a1, a2], total)
    return None   # G, N, X não têm carga


# ------------------------------------------------------------------ leitura do fluxo TCP
class Leitor:
    """O TCP é um FLUXO de bytes: uma chamada recv() pode trazer meia mensagem ou várias juntas.
    O Leitor guarda os bytes recebidos num buffer de tamanho limitado e devolve só linhas completas."""

    def __init__(self):
        self.buf = bytearray()

    def alimentar(self, dados):
        self.buf += dados
        linhas = []
        while True:
            i = self.buf.find(b"\n")
            if i < 0:
                break
            linhas.append(bytes(self.buf[:i]).decode("ascii", errors="replace"))
            del self.buf[:i + 1]
        if len(self.buf) > MAX_LINHA:      # lixo sem '\n': descarta para não crescer sem limite
            self.buf.clear()
        return linhas
