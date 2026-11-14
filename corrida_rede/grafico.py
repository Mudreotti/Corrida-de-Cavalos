# Autores: Murilo Andreotti Borges (RA 25163806-2) e Matheus Marçal Martinelli (RA 25076306-2)
# Sistemas Operacionais - Trabalho 02: jogo com troca de mensagens e gerenciamento de memória
# Prof. Maurilio Campano Jr - Corrida de Cavalos: Duelo 1x1 em rede
"""
grafico.py - camada gráfica do jogo (reaproveitada do jogo "Corrida de Cavalos").

Contém só o que é desenhado: fonte em pixels, sprites do cavalo e do corredor,
pista, torcida e a classe Cavalo (aparência + posição).
NÃO tem nada de rede: quem decide o que acontece na corrida é o servidor
(simulacao.py) e quem transporta as informações é a rede (rede.py).

O jogo é desenhado num canvas pequeno (500x320) e ampliado 2x sem suavização
(é isso que dá o visual de pixel art).
"""
import math
import random
import sys

import pygame

pygame.init()

LARGURA, ALTURA = 500, 320

ESCALA = 2

FPS = 60

janela = pygame.display.set_mode((LARGURA * ESCALA, ALTURA * ESCALA))

tela = pygame.Surface((LARGURA, ALTURA))

relogio = pygame.time.Clock()

TOPO_PISTA = 48

AREA_PISTA = 192

LINHA_LARGADA = 40

LINHA_CHEGADA = LARGURA - 40

VEL_ESCALA = 0.5

OURO = (255, 208, 72)

OURO_ESC = (196, 128, 36)

BRANCO = (246, 242, 232)

PRETO = (16, 12, 24)

CINZA = (150, 150, 172)

CINZA_ESC = (84, 84, 108)

VERDE = (120, 226, 126)

VERMELHO = (244, 96, 86)

AZUL_CLARO = (130, 188, 255)

ROXO_ESC = (28, 24, 54)

ROXO_MED = (52, 44, 92)

ROXO_BORDA = (126, 108, 184)

_FONTE_SPEC = """
A
.###.
#...#
#...#
#####
#...#
#...#
#...#

B
####.
#...#
#...#
####.
#...#
#...#
####.

C
.###.
#...#
#....
#....
#....
#...#
.###.

D
####.
#...#
#...#
#...#
#...#
#...#
####.

E
#####
#....
#....
####.
#....
#....
#####

F
#####
#....
#....
####.
#....
#....
#....

G
.###.
#...#
#....
#.###
#...#
#...#
.###.

H
#...#
#...#
#...#
#####
#...#
#...#
#...#

I
.###.
..#..
..#..
..#..
..#..
..#..
.###.

J
..###
...#.
...#.
...#.
...#.
#..#.
.##..

K
#...#
#..#.
#.#..
##...
#.#..
#..#.
#...#

L
#....
#....
#....
#....
#....
#....
#####

M
#...#
##.##
#.#.#
#.#.#
#...#
#...#
#...#

N
#...#
##..#
#.#.#
#..##
#...#
#...#
#...#

O
.###.
#...#
#...#
#...#
#...#
#...#
.###.

P
####.
#...#
#...#
####.
#....
#....
#....

Q
.###.
#...#
#...#
#...#
#.#.#
#..#.
.##.#

R
####.
#...#
#...#
####.
#.#..
#..#.
#...#

S
.####
#....
#....
.###.
....#
....#
####.

T
#####
..#..
..#..
..#..
..#..
..#..
..#..

U
#...#
#...#
#...#
#...#
#...#
#...#
.###.

V
#...#
#...#
#...#
#...#
#...#
.#.#.
..#..

W
#...#
#...#
#...#
#.#.#
#.#.#
##.##
#...#

X
#...#
#...#
.#.#.
..#..
.#.#.
#...#
#...#

Y
#...#
#...#
.#.#.
..#..
..#..
..#..
..#..

Z
#####
....#
...#.
..#..
.#...
#....
#####

0
.###.
#...#
#..##
#.#.#
##..#
#...#
.###.

1
..#..
.##..
..#..
..#..
..#..
..#..
.###.

2
.###.
#...#
....#
...#.
..#..
.#...
#####

3
.###.
#...#
....#
..##.
....#
#...#
.###.

4
...#.
..##.
.#.#.
#..#.
#####
...#.
...#.

5
#####
#....
####.
....#
....#
#...#
.###.

6
.###.
#....
#....
####.
#...#
#...#
.###.

7
#####
....#
...#.
..#..
.#...
.#...
.#...

8
.###.
#...#
#...#
.###.
#...#
#...#
.###.

9
.###.
#...#
#...#
.####
....#
....#
.###.

SP
...
...
...
...
...
...
...

.
.
.
.
.
.
.
#

,
..
..
..
..
..
.#
#.

:
.
.
#
.
.
#
.

;
..
..
.#
..
..
.#
#.

!
#
#
#
#
#
.
#

?
.###.
#...#
....#
..##.
..#..
.....
..#..

-
....
....
....
####
....
....
....

+
.....
..#..
..#..
#####
..#..
..#..
.....

/
....#
....#
...#.
..#..
.#...
#....
#....

%
##..#
##..#
...#.
..#..
.#...
#..##
#..##

(
..#
.#.
#..
#..
#..
.#.
..#

)
#..
.#.
..#
..#
..#
.#.
#..

'
#
#
.
.
.
.
.

"
#.#
#.#
...
...
...
...
...

>
#...
.#..
..#.
...#
..#.
.#..
#...

<
...#
..#.
.#..
#...
.#..
..#.
...#

=
.....
.....
#####
.....
#####
.....
.....

*
.....
#.#.#
.###.
#####
.###.
#.#.#
.....

|
#
#
#
#
#
#
#

_
.....
.....
.....
.....
.....
.....
#####

$
..#..
.####
#.#..
.###.
..#.#
####.
..#..

º
.#.
#.#
.#.
...
...
...
...
"""

_GLIFOS = {}

for _bloco in _FONTE_SPEC.strip("\n").split("\n\n"):
    _linhas = _bloco.split("\n")
    _chave = " " if _linhas[0] == "SP" else _linhas[0]
    _rows = _linhas[1:]
    assert len(_rows) == 7, (_chave, _rows)
    _pix = [(c, r + 2) for r, row in enumerate(_rows) for c, ch in enumerate(row) if ch == "#"]
    _GLIFOS[_chave] = (_pix, len(_rows[0]))

_MARCAS = {
    "agudo": [(3, 0), (2, 1)],
    "grave": [(1, 0), (2, 1)],
    "circ": [(2, 0), (1, 1), (3, 1)],
    "til": [(1, 0), (2, 0), (4, 0), (0, 1), (3, 1)],
    "trema": [(1, 1), (3, 1)],
    "cedilha": [(2, 9)],
}

_ACENTOS = {
    "Á": ("A", "agudo"), "À": ("A", "grave"), "Â": ("A", "circ"), "Ã": ("A", "til"),
    "É": ("E", "agudo"), "Ê": ("E", "circ"), "Í": ("I", "agudo"),
    "Ó": ("O", "agudo"), "Ô": ("O", "circ"), "Õ": ("O", "til"),
    "Ú": ("U", "agudo"), "Ü": ("U", "trema"), "Ç": ("C", "cedilha"),
}

CELULA_H = 10

def _glifo(ch):
    if ch in _GLIFOS:
        return _GLIFOS[ch]
    if ch in _ACENTOS:
        base, marca = _ACENTOS[ch]
        pix, larg = _GLIFOS[base]
        return pix + _MARCAS[marca], larg
    return _GLIFOS["?"]

_cache_texto = {}

def _superficie_texto(msg, cor, esc, contorno):
    chave = (msg, cor, esc, contorno)
    surf = _cache_texto.get(chave)
    if surf is not None:
        return surf
    if len(_cache_texto) > 900:
        _cache_texto.clear()
    pixels = []
    x = 0
    for ch in msg.upper():
        pix, larg = _glifo(ch)
        pixels += [(x + px, py) for px, py in pix]
        x += larg + 1
    larg_total = max(1, x - 1)
    pad = 1 if contorno else 0
    surf = pygame.Surface(((larg_total + 2 * pad) * esc, (CELULA_H + 2 * pad) * esc), pygame.SRCALPHA)
    if contorno:
        for px, py in pixels:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx or dy:
                        surf.fill(contorno, ((px + dx + pad) * esc, (py + dy + pad) * esc, esc, esc))
    for px, py in pixels:
        surf.fill(cor, ((px + pad) * esc, (py + pad) * esc, esc, esc))
    _cache_texto[chave] = surf
    return surf

def larg_texto(msg, esc=1):
    return sum(_glifo(ch)[1] + 1 for ch in msg.upper()) * esc - esc

def texto(msg, x, y, cor=BRANCO, esc=1, ancora="esq", contorno=None, sombra=None, alvo=None):
    """Desenha texto em pixels. (x, y) = meio vertical da letra. ancora: esq | centro | dir"""
    alvo = alvo or tela
    msg = str(msg)
    pad = esc if contorno else 0
    w = larg_texto(msg, esc)
    if ancora == "centro":
        x0 = x - w // 2
    elif ancora == "dir":
        x0 = x - w
    else:
        x0 = x
    topo = int(y - 5.5 * esc)
    if sombra:
        alvo.blit(_superficie_texto(msg, sombra, esc, None), (x0 + esc, topo + esc))
    alvo.blit(_superficie_texto(msg, cor, esc, contorno), (x0 - pad, topo - pad))
    return pygame.Rect(x0, topo + 2 * esc, w, 7 * esc)

_DIG3 = {
    "0": ("###", "#.#", "#.#", "#.#", "###"), "1": (".#.", "##.", ".#.", ".#.", "###"),
    "2": ("###", "..#", "###", "#..", "###"), "3": ("###", "..#", "###", "..#", "###"),
    "4": ("#.#", "#.#", "###", "..#", "..#"), "5": ("###", "#..", "###", "..#", "###"),
    "6": ("###", "#..", "###", "#.#", "###"), "7": ("###", "..#", ".#.", ".#.", ".#."),
    "8": ("###", "#.#", "###", "#.#", "###"), "9": ("###", "#.#", "###", "..#", "###"),
}

def digito3(alvo, ch, x, y, cor):
    for r, row in enumerate(_DIG3[ch]):
        for c, p in enumerate(row):
            if p == "#":
                alvo.set_at((x + c, y + r), cor)

def escurecer(cor, f=0.65):
    return tuple(int(v * f) for v in cor[:3])

def clarear(cor, f=0.35):
    return tuple(int(v + (255 - v) * f) for v in cor[:3])

def lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]

def fmt_tempo(t):
    if t is None:
        return "-:--.--"
    return f"{int(t // 60)}:{t % 60:05.2f}"

def retang(cor, x, y, w, h, alvo=None):
    (alvo or tela).fill(cor, (int(x), int(y), int(w), int(h)))

def caixa(x, y, w, h, fundo=ROXO_ESC, borda=ROXO_BORDA, sombra=True, brilho=True):
    """Painel de pixel art: cantos cortados, borda de 1px, sombra dura e brilho no topo."""
    if sombra:
        tela.fill((0, 0, 0), (x + 2, y + 3, w, h))
    tela.fill(borda, (x + 1, y, w - 2, h))
    tela.fill(borda, (x, y + 1, w, h - 2))
    tela.fill(fundo, (x + 1, y + 1, w - 2, h - 2))
    if brilho and h > 8:
        tela.fill(clarear(fundo, 0.14), (x + 2, y + 1, w - 4, 1))
        tela.fill(escurecer(fundo, 0.7), (x + 2, y + h - 2, w - 4, 1))

def selo(x, y, w, h, msg, fundo=OURO, cor_texto=(48, 30, 8)):
    tela.fill(escurecer(fundo, 0.55), (x + 1, y, w - 2, h))
    tela.fill(escurecer(fundo, 0.55), (x, y + 1, w, h - 2))
    tela.fill(fundo, (x + 1, y + 1, w - 2, h - 2))
    texto(msg, x + w // 2, y + h // 2 + 0, cor_texto, ancora="centro")

def barra_dicas(msg):
    tela.fill((10, 8, 20), (0, ALTURA - 14, LARGURA, 14))
    tela.fill(OURO_ESC, (0, ALTURA - 14, LARGURA, 1))
    texto(msg, LARGURA // 2, ALTURA - 7, (220, 216, 230), ancora="centro")

def seta_pixel(cx, cy, direcao, cor):
    """Setinha de 4 pixels de largura (direcao: -1 esquerda, 1 direita)."""
    for i in range(4):
        h = 3 - i if direcao > 0 else i
        x = cx - 2 + i
        tela.fill(cor, (x, cy - h, 1, h * 2 + 1))

_BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]

def _criar_dither():
    chave = (255, 0, 255)
    niveis = []
    for nivel in range(17):
        tile = pygame.Surface((4, 4))
        tile.fill(chave)
        for yy in range(4):
            for xx in range(4):
                if _BAYER[yy][xx] < nivel:
                    tile.set_at((xx, yy), (0, 0, 0))
        faixa = pygame.Surface((LARGURA, 4))
        faixa.fill(chave)
        for xx in range(0, LARGURA, 4):
            faixa.blit(tile, (xx, 0))
        grande = pygame.Surface((LARGURA, ALTURA))
        grande.fill(chave)
        for yy in range(0, ALTURA, 4):
            grande.blit(faixa, (0, yy))
        grande.set_colorkey(chave)
        niveis.append(grande)
    return niveis

DITHER = _criar_dither()

def cobrir_tela(nivel=8):
    tela.blit(DITHER[nivel], (0, 0))

PELAGENS = [
    ("Alazão",   (186, 98, 48),   (104, 52, 26)),
    ("Castanho", (128, 74, 42),   (44, 28, 20)),
    ("Baio",     (212, 164, 96),  (64, 44, 30)),
    ("Palomino", (234, 194, 108), (248, 244, 232)),
    ("Tordilho", (184, 186, 196), (108, 110, 120)),
    ("Preto",    (56, 52, 62),    (22, 20, 28)),
    ("Ruão",     (160, 104, 92),  (74, 52, 48)),
]

RACAS = {
    "poney": {"nome": "Pônei", "mod": (-1, 0, 1), "corpo": -1, "perna": 8, "peludo": False,
              "preco": 0.8, "peso": 1, "pelagens": [0, 1, 2, 3, 5], "marcas": ["nenhuma", "estrela"],
              "desc": "Pequeno e simpático. Sorte de principiante."},
    "puro_sangue": {"nome": "Puro-sangue", "mod": (2, -1, 0), "corpo": -1, "perna": 12,
                    "peludo": False, "preco": 1.4, "peso": 2, "pelagens": [0, 1, 5, 2],
                    "marcas": ["estrela", "nenhuma", "meias"],
                    "desc": "Velocíssimo, mas se cansa fácil."},
    "quarto_milha": {"nome": "Quarto de Milha", "mod": (1, 1, -1), "corpo": 1, "perna": 10,
                     "peludo": False, "preco": 1.1, "peso": 2, "pelagens": [0, 1, 2, 6],
                     "marcas": ["meias", "nenhuma", "estrela"],
                     "desc": "Musculoso e explosivo na largada."},
    "arabe": {"nome": "Árabe", "mod": (0, 2, 0), "corpo": -1, "perna": 11, "peludo": False,
              "preco": 1.3, "peso": 2, "pelagens": [4, 2, 0, 5],
              "marcas": ["estrela", "meias", "nenhuma"],
              "desc": "Resistência lendária. Nunca perde o fôlego."},
    "mangalarga": {"nome": "Mangalarga", "mod": (0, 1, 1), "corpo": 0, "perna": 11,
                   "peludo": False, "preco": 1.2, "peso": 2, "pelagens": [3, 2, 0, 1],
                   "marcas": ["estrela", "meias", "nenhuma"],
                   "desc": "Equilibrado e de boa sorte."},
    "crioulo": {"nome": "Crioulo", "mod": (-1, 2, 0), "corpo": 1, "perna": 9,
                "peludo": False, "preco": 1.0, "peso": 2, "pelagens": [2, 6, 1, 0],
                "marcas": ["nenhuma", "estrela"],
                "desc": "Rústico e muito resistente."},
    "appaloosa": {"nome": "Appaloosa", "mod": (0, 0, 2), "corpo": 0, "perna": 11,
                  "peludo": False, "preco": 1.3, "peso": 1, "pelagens": [4, 1, 0],
                  "marcas": ["manchas"],
                  "desc": "Pelagem manchada e muita sorte."},
    "frisio": {"nome": "Frísio", "mod": (-1, 1, 1), "corpo": 1, "perna": 12, "peludo": True,
               "preco": 1.5, "peso": 1, "pelagens": [5], "marcas": ["nenhuma"],
               "desc": "Imponente, todo preto, de patas peludas."},
    "pampa": {"nome": "Pampa", "mod": (1, 0, 1), "corpo": 0, "perna": 11, "peludo": False,
              "preco": 1.2, "peso": 1, "pelagens": [0, 1, 5, 2], "marcas": ["pampa"],
              "desc": "Malhado e cheio de personalidade."},
}

CORES_ROUPA = [("Vermelho", (214, 48, 52)), ("Azul", (52, 92, 212)), ("Verde", (54, 168, 84)),
               ("Amarelo", (248, 208, 46)), ("Roxo", (146, 70, 182)), ("Laranja", (244, 134, 44)),
               ("Rosa", (240, 114, 168)), ("Branco", (242, 242, 240)), ("Preto", (40, 40, 48)),
               ("Ciano", (54, 196, 206))]

PELES = [("Tom 1", (252, 224, 194)), ("Tom 2", (242, 202, 162)), ("Tom 3", (216, 166, 120)),
         ("Tom 4", (172, 116, 82)), ("Tom 5", (120, 80, 56))]

ESTAMPAS = ["Lisa", "Listras", "Faixa", "Bolinhas", "Metade", "Xadrez"]

CHAPEUS = ["Capacete", "Boné", "Chapéu cowboy", "Cartola", "Coroa"]

OCULOS = [("Nenhum", None), ("Escuros", (34, 34, 46)), ("Dourados", (236, 196, 64))]

LENCOS = [("Nenhum", None)] + CORES_ROUPA

SELAS = [("Marrom", (128, 78, 42)), ("Preta", (46, 42, 48)), ("Branca", (238, 234, 226)),
         ("Vermelha", (176, 44, 44)), ("Azul", (54, 84, 176)), ("Dourada", (218, 178, 64))]

MANTA_ESTILOS = ["Lisa", "Listras", "Bolinhas", "Estrela", "Xadrez"]

CRINAS = [("Automática", None), ("Preta", (30, 28, 34)), ("Branca", (242, 238, 230)),
          ("Ruiva", (166, 74, 32)), ("Dourada", (238, 194, 84)), ("Azul", (74, 114, 224)),
          ("Rosa", (242, 124, 174))]

PENACHOS = [("Nenhum", None), ("Vermelho", (224, 54, 54)), ("Azul", (64, 104, 224)),
            ("Dourado", (244, 204, 64)), ("Verde", (64, 184, 94))]

CANELEIRAS = [("Nenhuma", None), ("Brancas", (242, 242, 242)), ("Vermelhas", (214, 54, 54)),
              ("Azuis", (64, 104, 224)), ("Douradas", (244, 204, 64))]

TESTEIRAS = [("Nenhuma", None), ("Dourada", (244, 204, 64)), ("Prata", (204, 208, 218)),
             ("Vermelha", (204, 54, 54))]

def sem_cor(lista):
    return [(n, None) for n in lista]

LINHAS_PERS = [
    ("cavalo", "Pelagem", "pelagem", [(n, c) for n, c, _ in PELAGENS]),
    ("cavalo", "Crina e rabo", "crina", CRINAS),
    ("cavalo", "Sela", "sela", SELAS),
    ("cavalo", "Manta", "manta", CORES_ROUPA),
    ("cavalo", "Estampa manta", "manta_estilo", sem_cor(MANTA_ESTILOS)),
    ("cavalo", "Penacho", "penacho", PENACHOS),
    ("cavalo", "Caneleiras", "caneleiras", CANELEIRAS),
    ("cavalo", "Testeira", "testeira", TESTEIRAS),
    ("competidor", "Tom de pele", "pele", PELES),
    ("competidor", "Jaqueta", "jaqueta", CORES_ROUPA),
    ("competidor", "Estampa", "estampa", sem_cor(ESTAMPAS)),
    ("competidor", "Cor estampa", "cor2", CORES_ROUPA),
    ("competidor", "Chapéu", "chapeu", sem_cor(CHAPEUS)),
    ("competidor", "Cor do chapéu", "chapeu_cor", CORES_ROUPA),
    ("competidor", "Óculos", "oculos", OCULOS),
    ("competidor", "Lenço", "lenco", LENCOS),
]

CORES_CONFETE = [(255, 214, 90), (255, 100, 100), (100, 204, 255), (120, 255, 150), (232, 132, 255)]

def cor_crina(vis):
    c = CRINAS[vis["crina"]][1]
    return c if c else PELAGENS[vis["pelagem"]][2]

SPR_W, SPR_H = 64, 56

AX, AY = 30, 50

CONTORNO = (24, 14, 30)

CASCO = (44, 34, 40)

def _nova():
    return pygame.Surface((SPR_W, SPR_H), pygame.SRCALPHA)

def _mascara(s):
    return pygame.mask.from_surface(s, 1)

def _deslocada(m, dx, dy):
    n = pygame.mask.Mask((SPR_W, SPR_H))
    n.draw(m, (dx, dy))
    return n

def _m2s(m, cor):
    return m.to_surface(setcolor=cor, unsetcolor=(0, 0, 0, 0))

def contornar(s, cor=CONTORNO):
    m = _mascara(s)
    d = pygame.mask.Mask((SPR_W, SPR_H))
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        d.draw(m, (dx, dy))
    d.erase(m, (0, 0))
    out = _m2s(d, cor)
    out.blit(s, (0, 0))
    return out

def sombrear(s, claro, escuro):
    m = _mascara(s)
    topo = m.copy()
    topo.erase(_deslocada(m, 0, 1), (0, 0))
    ambos = _deslocada(m, 0, -1).overlap_mask(_deslocada(m, 0, -2), (0, 0))
    base = m.copy()
    base.erase(ambos, (0, 0))
    s.blit(_m2s(base, escuro), (0, 0))
    s.blit(_m2s(topo, claro), (0, 0))

def linha_px(s, cor, p1, p2, esp=2):
    x0, y0 = int(round(p1[0])), int(round(p1[1]))
    x1, y1 = int(round(p2[0])), int(round(p2[1]))
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    off = (esp - 1) // 2
    while True:
        s.fill(cor, (x0 - off, y0 - off, esp, esp))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy

def _lerp(p, q, t):
    return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)

def _recortar(camada, mascara_base):
    """Mantém na camada só os pixels que estão dentro da máscara."""
    mk = _m2s(mascara_base, (255, 255, 255, 255))
    camada.blit(mk, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

def _perna(cor, hip, fase, frente, estilo, vis, r, cor_crina_v):
    """Desenha uma perna (camada própria, já com contorno)."""
    s = _nova()
    hx, hy = hip
    if fase is None:
        sw, lev = 0.0, 0.0
    else:
        sw = math.sin(fase) * 6.5
        lev = max(0.0, math.cos(fase)) * 4.5
    fx = hx + sw
    fy = AY - lev - 1
    comp = AY - hy
    mx = hx + sw * 0.5 + (2.0 if frente else -2.0) * (lev / 4.5)
    my = hy + comp * 0.52 - lev * 0.5
    linha_px(s, cor, (hx, hy), (mx, my), 3 if not frente else 2)
    linha_px(s, cor, (mx, my), (fx, fy), 2)
    if r["peludo"]:
        linha_px(s, cor_crina_v, _lerp((mx, my), (fx, fy), 0.45), (fx, fy + 1), 3)
    if vis["marca"] == "meias":
        linha_px(s, (244, 242, 236) if estilo == "perto" else (190, 188, 184),
                 _lerp((mx, my), (fx, fy), 0.55), (fx, fy), 2)
    cane = CANELEIRAS[vis["caneleiras"]][1]
    if cane:
        a = _lerp((mx, my), (fx, fy), 0.25)
        b = _lerp((mx, my), (fx, fy), 0.65)
        linha_px(s, cane if estilo == "perto" else escurecer(cane, 0.7), a, b, 2)
    s.fill(CASCO, (int(round(fx)) - 1, int(round(fy)) - 1, 3, 2))
    return contornar(s)

def _estampa_jaqueta(est, x, y, sx):
    if est == 1:
        return (y // 2) % 2 == 1
    if est == 2:
        return abs(x - (sx + 4)) <= 1
    if est == 3:
        return (x % 4 == 0 and y % 4 == 0) or (x % 4 == 2 and y % 4 == 2)
    if est == 4:
        return x > sx + 3
    if est == 5:
        return ((x // 2) + (y // 2)) % 2 == 0
    return False

def _cavaleiro(jk, sx, sy, fase_corpo):
    s = _nova()
    pele = PELES[jk["pele"]][1]
    jaq = CORES_ROUPA[jk["jaqueta"]][1]
    cor2 = CORES_ROUPA[jk["cor2"]][1]
    calca = (238, 238, 244)
    # perna e bota
    linha_px(s, calca, (sx - 1, sy), (sx + 4, sy + 6), 3)
    linha_px(s, (36, 28, 34), _lerp((sx - 1, sy), (sx + 4, sy + 6), 0.55), (sx + 4, sy + 7), 3)
    # tronco inclinado
    tronco = [(sx - 3, sy + 1), (sx + 2, sy + 2), (sx + 9, sy - 6), (sx + 4, sy - 10)]
    tmp = _nova()
    pygame.draw.polygon(tmp, jaq, tronco)
    mt = _mascara(tmp)
    for yy in range(sy - 11, sy + 4):
        for xx in range(sx - 4, sx + 11):
            if 0 <= xx < SPR_W and 0 <= yy < SPR_H and mt.get_at((xx, yy)):
                c = cor2 if _estampa_jaqueta(jk["estampa"], xx, yy, sx) else jaq
                tmp.set_at((xx, yy), c)
    s.blit(tmp, (0, 0))
    # braço
    linha_px(s, escurecer(jaq, 0.78), (sx + 6, sy - 7), (sx + 13, sy - 3), 2)
    s.set_at((sx + 14, sy - 3), pele)
    s.set_at((sx + 14, sy - 2), pele)
    # cabeça
    hx, hy = sx + 10, sy - 12
    pygame.draw.circle(s, pele, (hx, hy), 3)
    s.set_at((hx + 3, hy), escurecer(pele, 0.8))
    # lenço
    cor_l = LENCOS[jk["lenco"]][1]
    if cor_l:
        fl = 1 if fase_corpo else 0
        linha_px(s, cor_l, (sx + 7, sy - 8), (sx + 9, sy - 9), 2)
        linha_px(s, cor_l, (sx + 6, sy - 8), (sx + 1, sy - 8 + fl), 1)
        linha_px(s, escurecer(cor_l, 0.8), (sx + 5, sy - 7), (sx, sy - 6 + fl), 1)
    # óculos
    cor_o = OCULOS[jk["oculos"]][1]
    if cor_o:
        s.fill(cor_o, (hx + 1, hy - 1, 4, 2))
        s.set_at((hx - 2, hy - 1), cor_o)
    # chapéu
    cor_c = CORES_ROUPA[jk["chapeu_cor"]][1]
    tipo = jk["chapeu"]
    if tipo == 0:      # capacete
        pygame.draw.polygon(s, cor_c, [(hx - 4, hy - 1), (hx - 4, hy - 3), (hx - 2, hy - 5),
                                       (hx + 2, hy - 5), (hx + 4, hy - 3), (hx + 4, hy - 1)])
        s.fill(escurecer(cor_c, 0.65), (hx + 3, hy - 2, 4, 1))
        s.fill(clarear(cor_c, 0.5), (hx - 2, hy - 5, 3, 1))
    elif tipo == 1:    # boné
        pygame.draw.polygon(s, cor_c, [(hx - 4, hy - 1), (hx - 4, hy - 3), (hx - 2, hy - 5),
                                       (hx + 2, hy - 5), (hx + 4, hy - 3), (hx + 4, hy - 1)])
        s.fill(clarear(cor_c, 0.3), (hx + 3, hy - 2, 5, 1))
        s.set_at((hx, hy - 6), escurecer(cor_c, 0.6))
    elif tipo == 2:    # cowboy
        s.fill(cor_c, (hx - 3, hy - 8, 7, 4))
        s.fill(escurecer(cor_c, 0.6), (hx - 3, hy - 5, 7, 1))
        s.fill(cor_c, (hx - 7, hy - 4, 15, 2))
        s.fill(clarear(cor_c, 0.35), (hx - 2, hy - 8, 4, 1))
        s.set_at((hx - 7, hy - 5), cor_c)
        s.set_at((hx + 7, hy - 5), cor_c)
    elif tipo == 3:    # cartola
        s.fill(cor_c, (hx - 3, hy - 12, 7, 8))
        s.fill(CORES_ROUPA[jk["cor2"]][1], (hx - 3, hy - 6, 7, 2))
        s.fill(cor_c, (hx - 6, hy - 4, 13, 2))
        s.fill(clarear(cor_c, 0.4), (hx - 2, hy - 12, 2, 5))
    else:              # coroa
        ouro = (255, 214, 70)
        s.fill(ouro, (hx - 4, hy - 5, 9, 3))
        for px_ in (hx - 4, hx, hx + 4):
            s.fill(ouro, (px_, hy - 7, 1, 2))
        s.fill((255, 120, 120), (hx - 1, hy - 4, 3, 1))
        s.fill((255, 246, 190), (hx - 4, hy - 5, 9, 1))
    return contornar(s)

def construir_cavalo(cav, quadro, correndo, numero):
    r = RACAS[cav.raca]
    v = cav.visual
    pel = PELAGENS[v["pelagem"]][1]
    crina = cor_crina(v)
    hb = 11 + 2 * r["corpo"]
    Lp = r["perna"]
    cx = AX
    cy = AY - Lp - hb // 2 + 2
    T = cy - hb // 2
    fase = (2 * math.pi * quadro / 8) if correndo else None
    bob = 1 if (correndo and quadro in (1, 2, 5, 6)) else 0

    quadril_y = cy + hb // 2 - 3
    tras = (cx - 9, quadril_y)
    frente = (cx + 9, quadril_y)

    def f(off):
        return None if fase is None else fase + off

    final = _nova()

    # pernas de trás da cena (longe) ---------------------------------
    longe = escurecer(pel, 0.62)
    final.blit(_perna(longe, (tras[0] + 2, tras[1]), f(0.9), False, "longe", v, r, crina), (0, 0))
    final.blit(_perna(longe, (frente[0] - 2, frente[1]), f(0.9 + math.pi * 0.85), True, "longe", v, r, crina), (0, 0))

    # rabo -----------------------------------------------------------
    tw = 0 if fase is None else int(round(math.sin(fase * 1.0 + 1.0) * 2))
    rabo = _nova()
    pygame.draw.polygon(rabo, crina, [(cx - 12, T + 1), (cx - 18, T + 2 + tw), (cx - 22, T + 7 + tw),
                                      (cx - 23, T + 12 + tw), (cx - 19, T + 10 + tw), (cx - 15, T + 6)])
    final.blit(contornar(rabo), (0, 0))

    # corpo, pescoço e cabeça ---------------------------------------
    corpo = _nova()
    pygame.draw.ellipse(corpo, pel, (cx - 14, T, 29, hb))
    pygame.draw.polygon(corpo, pel, [(cx + 4, T + 2), (cx + 9, T - 11), (cx + 16, T - 9), (cx + 15, T + 5)])
    pygame.draw.polygon(corpo, pel, [(cx + 9, T - 12), (cx + 15, T - 14), (cx + 23, T - 8), (cx + 24, T - 4),
                                     (cx + 21, T - 2), (cx + 16, T - 4), (cx + 12, T - 7)])
    pygame.draw.polygon(corpo, pel, [(cx + 10, T - 12), (cx + 11, T - 17), (cx + 14, T - 13)])
    sombrear(corpo, clarear(pel, 0.22), escurecer(pel, 0.78))
    m_corpo = _mascara(corpo)

    # marcas ---------------------------------------------------------
    marca = v["marca"]
    if marca == "estrela":
        for (px_, py_) in ((cx + 16, T - 12), (cx + 17, T - 11), (cx + 17, T - 10), (cx + 18, T - 9)):
            corpo.set_at((px_, py_), (248, 246, 240))
    elif marca == "pampa":
        pt = _nova()
        pygame.draw.ellipse(pt, (246, 244, 238), (cx - 11, T + 1, 12, hb - 3))
        pygame.draw.ellipse(pt, (246, 244, 238), (cx + 4, T + 4, 8, 6))
        pygame.draw.ellipse(pt, (246, 244, 238), (cx + 12, T - 10, 5, 6))
        _recortar(pt, m_corpo)
        corpo.blit(pt, (0, 0))
    elif marca == "manchas":
        cor_m = clarear(pel, 0.8) if lum(pel) < 110 else escurecer(pel, 0.45)
        for dx, dy in ((-12, 3), (-9, 6), (-6, 2), (-12, 7), (-3, 5), (-7, 8), (0, 3), (-10, 0)):
            if m_corpo.get_at((cx + dx, T + dy)):
                corpo.set_at((cx + dx, T + dy), cor_m)

    # crina no pescoço
    pygame.draw.polygon(corpo, crina, [(cx + 4, T + 2), (cx + 8, T - 10), (cx + 11, T - 15), (cx + 13, T - 13),
                                       (cx + 10, T - 7), (cx + 8, T + 1)])
    # testeira
    cor_t = TESTEIRAS[v["testeira"]][1]
    if cor_t:
        for (px_, py_) in ((cx + 21, T - 7), (cx + 21, T - 6), (cx + 20, T - 5)):
            corpo.set_at((px_, py_), cor_t)
        linha_px(corpo, cor_t, (cx + 13, T - 12), (cx + 20, T - 5), 1)
    # olho e narina
    corpo.set_at((cx + 17, T - 9), (22, 16, 22))
    corpo.set_at((cx + 23, T - 5), escurecer(pel, 0.4))
    corpo = contornar(corpo)
    final.blit(corpo, (0, 0))

    # pernas da frente (perto) --------------------------------------
    final.blit(_perna(pel, (tras[0] - 2, tras[1]), f(0.0), False, "perto", v, r, crina), (0, 0))
    final.blit(_perna(pel, (frente[0] + 2, frente[1]), f(math.pi * 0.85), True, "perto", v, r, crina), (0, 0))

    # manta com número -----------------------------------------------
    cor_manta = CORES_ROUPA[v["manta"]][1]
    cor_ext = clarear(cor_manta, 0.6) if lum(cor_manta) < 140 else escurecer(cor_manta, 0.55)
    bw, bh = 10, max(hb - 4, 6)
    bx, by = cx - 12, T + 2
    manta = _nova()
    manta.fill(cor_manta, (bx, by, bw, bh))
    estilo = v["manta_estilo"]
    for rr in range(bh):
        for cc in range(bw):
            xx, yy = bx + cc, by + rr
            if estilo == 1 and cc % 3 == 0:
                manta.set_at((xx, yy), cor_ext)
            elif estilo == 2 and cc % 3 == 1 and rr % 3 == 1:
                manta.set_at((xx, yy), cor_ext)
            elif estilo == 4 and ((cc // 2) + (rr // 2)) % 2 == 0:
                manta.set_at((xx, yy), cor_ext)
    if estilo == 3:
        for (ox, oy) in ((1, 1), (7, 1), (1, bh - 3), (7, bh - 3)):
            for (ddx, ddy) in ((1, 0), (0, 1), (1, 1), (2, 1), (1, 2)):
                manta.set_at((bx + ox + ddx - 0, by + oy + ddy), cor_ext)
    if numero is not None:
        manta.fill(cor_manta, (bx + 2, by + (bh - 7) // 2, 5, 7))
    manta.fill(escurecer(cor_manta, 0.6), (bx, by + bh - 1, bw, 1))
    manta.fill(escurecer(cor_manta, 0.6), (bx, by, 1, bh))
    if numero is not None:
        cor_num = (250, 250, 250) if lum(cor_manta) < 150 else (24, 20, 30)
        digito3(manta, str(numero)[-1], bx + 3, by + (bh - 5) // 2, cor_num)
    _recortar(manta, m_corpo)
    final.blit(manta, (0, 0))

    # sela --------------------------------------------------------------
    cor_sela = SELAS[v["sela"]][1]
    sela = _nova()
    sela.fill(cor_sela, (cx - 8, T - 1, 10, 3))
    sela.fill(clarear(cor_sela, 0.35), (cx - 8, T - 1, 10, 1))
    sela.fill(escurecer(cor_sela, 0.6), (cx - 8, T + 1, 10, 1))
    final.blit(contornar(sela), (0, 0))
    # cilha
    for yy in range(T + 2, T + hb - 1):
        if m_corpo.get_at((cx + 1, yy)):
            final.set_at((cx + 1, yy), escurecer(cor_sela, 0.7))

    # penacho -----------------------------------------------------------
    cor_p = PENACHOS[v["penacho"]][1]
    if cor_p:
        pen = _nova()
        pygame.draw.polygon(pen, cor_p, [(cx + 13, T - 14), (cx + 12, T - 17), (cx + 14, T - 20),
                                         (cx + 15, T - 17), (cx + 16, T - 14)])
        pen.set_at((cx + 14, T - 18), clarear(cor_p, 0.6))
        final.blit(contornar(pen), (0, 0))

    # competidor --------------------------------------------------------
    sx, sy = cx - 3, T
    final.blit(_cavaleiro(cav.jockey, sx, sy, quadro % 2), (0, 0))

    if bob:
        out = _nova()
        out.blit(final, (0, -bob))
        return out
    return final

_cache_sprites = {}

_cache_sombras = {}

def sprite_cavalo(cav, quadro=0, correndo=False, numero=None):
    chave = (cav.raca, tuple(sorted(cav.visual.items())), tuple(sorted(cav.jockey.items())),
             quadro % 8 if correndo else 0, correndo, numero)
    spr = _cache_sprites.get(chave)
    if spr is None:
        if len(_cache_sprites) > 700:
            _cache_sprites.clear()
        spr = construir_cavalo(cav, quadro, correndo, numero)
        _cache_sprites[chave] = spr
    return spr

def desenhar_cavalo(x, y, cav, quadro=0, correndo=False, numero=None, esc=1, sombra=True, alvo=None, espelhar=False):
    """Desenha o cavalo com o chão em (x, y). esc deve ser um número inteiro."""
    alvo = alvo or tela
    spr = sprite_cavalo(cav, quadro, correndo, numero)
    if esc != 1:
        spr = pygame.transform.scale(spr, (SPR_W * esc, SPR_H * esc))
    if sombra:
        w = 34 * esc
        h = 5 * esc
        sh = _cache_sombras.get(esc)
        if sh is None:
            sh = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.ellipse(sh, (0, 0, 0, 96), (0, 0, w, h))
            _cache_sombras[esc] = sh
        alvo.blit(sh, (int(x - w // 2), int(y - h // 2 + 1)))
    if espelhar:
        spr = pygame.transform.flip(spr, True, False)
        alvo.blit(spr, (int(x - (SPR_W - AX) * esc), int(y - AY * esc)))
    else:
        alvo.blit(spr, (int(x - AX * esc), int(y - AY * esc)))

def faixas(surf, cores, y0, y1, trans=6):
    """Céu/gradiente em faixas, com pontilhado entre uma faixa e outra."""
    n = len(cores)
    h = y1 - y0
    for i, cor in enumerate(cores):
        a = y0 + h * i // n
        b = y0 + h * (i + 1) // n
        surf.fill(cor, (0, a, surf.get_width(), b - a))
        if i + 1 < n:
            prox = cores[i + 1]
            for yy in range(b - trans, b):
                for xx in range(surf.get_width()):
                    k = b - yy
                    if (xx + yy) % 2 == 0 and k <= trans // 2 + 1:
                        surf.set_at((xx, yy), prox)
                    elif k <= 2 and (xx % 2 == 0):
                        surf.set_at((xx, yy), prox)

def criar_fundo_loja():
    rng = random.Random(41)
    f = pygame.Surface((LARGURA, ALTURA))
    faixas(f, [(20, 20, 54), (30, 26, 70), (44, 30, 86), (60, 36, 100), (78, 42, 108), (96, 50, 112)], 0, ALTURA, 8)
    for _ in range(90):
        f.set_at((rng.randrange(LARGURA), rng.randrange(30, ALTURA)), rng.choice([(200, 200, 255), (255, 220, 200), (150, 150, 210)]))
    return f

def criar_fundo_resultado():
    f = pygame.Surface((LARGURA, ALTURA))
    faixas(f, [(16, 14, 44), (26, 20, 62), (40, 26, 80), (58, 32, 94), (76, 40, 104)], 0, 200, 8)
    luz = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    for cx in (70, 150, 230):
        pygame.draw.polygon(luz, (255, 236, 170, 30), [(cx, 0), (cx - 56, 196), (cx + 56, 196)])
        pygame.draw.polygon(luz, (255, 236, 170, 26), [(cx, 0), (cx - 30, 196), (cx + 30, 196)])
    f.blit(luz, (0, 0))
    f.fill((44, 30, 56), (0, 196, LARGURA, ALTURA - 196))
    for xx in range(0, LARGURA, 24):
        f.fill((58, 40, 72), (xx, 196, 1, ALTURA - 196))
    f.fill(OURO, (0, 196, LARGURA, 2))
    f.fill(OURO_ESC, (0, 198, LARGURA, 1))
    return f

FAIXA_W = 420

def criar_faixa_pista(n):
    """Trecho de pista que repete sem emendas, usado quando a câmera acompanha o cavalo."""
    rng = random.Random(300 + n)
    alt = AREA_PISTA // n
    f = pygame.Surface((FAIXA_W, ALTURA))
    for i in range(0, FAIXA_W, 21):
        f.fill((58, 140, 66) if (i // 21) % 2 == 0 else (52, 128, 60), (i, 0, 21, ALTURA))
    for _ in range(420):
        x, y = rng.randrange(FAIXA_W), rng.randrange(ALTURA)
        f.fill(rng.choice([(40, 104, 52), (76, 164, 84)]), (x, y, 1, 2))
    for k, c in enumerate([(92, 66, 92), (84, 60, 86), (76, 54, 80), (68, 48, 72)]):
        f.fill(c, (0, 22 + k * 6, FAIXA_W, 6))
        f.fill(escurecer(c, 0.7), (0, 22 + k * 6 + 5, FAIXA_W, 1))
    f.fill((44, 30, 50), (0, 46, FAIXA_W, 2))
    cores_b = [(220, 60, 60), (250, 210, 70), (70, 130, 230), (80, 190, 100)]
    for k, xx in enumerate(range(3, FAIXA_W, 21)):
        c = cores_b[k % 4]
        pygame.draw.polygon(f, c, [(xx, 23), (xx + 12, 23), (xx + 6, 31)])
        f.fill(escurecer(c, 0.7), (xx, 23, 12, 1))
    y_fim = TOPO_PISTA + n * alt
    for i in range(n):
        y = TOPO_PISTA + i * alt
        f.fill((194, 146, 98) if i % 2 == 0 else (184, 136, 90), (0, y, FAIXA_W, alt))
    for _ in range(90 * n):
        px, py = rng.randrange(FAIXA_W), rng.randrange(TOPO_PISTA, y_fim)
        f.fill(rng.choice([(160, 114, 72), (210, 164, 114), (172, 124, 80)]), (px, py, 1, 1))
    for _ in range(12 * n):
        px, py = rng.randrange(FAIXA_W - 4), rng.randrange(TOPO_PISTA, y_fim)
        f.fill((164, 118, 76), (px, py, rng.randrange(2, 4), 1))
    for i in range(1, n):
        y = TOPO_PISTA + i * alt
        for xx in range(0, FAIXA_W, 12):
            f.fill((240, 234, 218), (xx, y, 6, 1))
    for y_c in (TOPO_PISTA - 6, y_fim + 1):
        for xx in range(4, FAIXA_W, 28):
            f.fill((236, 232, 220), (xx, y_c, 3, 6))
            f.fill((170, 164, 154), (xx + 2, y_c, 1, 6))
        f.fill((248, 246, 238), (0, y_c + 1, FAIXA_W, 2))
        f.fill((180, 174, 164), (0, y_c + 3, FAIXA_W, 1))
    for _ in range(30):
        x, y = rng.randrange(3, FAIXA_W - 4), rng.randrange(y_fim + 10, 262)
        f.fill((30, 98, 50), (x - 2, y, 5, 2))
        f.fill((44, 124, 62), (x - 1, y - 1, 3, 1))
    for _ in range(18):
        x, y = rng.randrange(FAIXA_W), rng.randrange(y_fim + 10, 262)
        f.set_at((x, y), rng.choice([(255, 220, 90), (255, 120, 140), (255, 255, 255)]))
    return f

_FAIXAS = {}

def obter_faixa(n):
    if n not in _FAIXAS:
        _FAIXAS[n] = criar_faixa_pista(n)
    return _FAIXAS[n]

FUNDO_LOJA = criar_fundo_loja()

FUNDO_RESULTADO = criar_fundo_resultado()

_rng_n = random.Random(5)

_CORES_TORCIDA = [(200, 70, 70), (70, 110, 200), (230, 200, 70), (90, 180, 100),
                  (226, 226, 226), (190, 100, 190), (230, 140, 60)]

_PELES_TORCIDA = [(252, 224, 194), (242, 202, 162), (216, 166, 120), (172, 116, 82), (120, 80, 56)]

TORCIDA = []   # (x, y, cor da roupa, cor da pele, fase da animação)
for _fila in range(2):
    for _i in range(0, LARGURA, 5):
        TORCIDA.append((_i + _rng_n.randrange(0, 2) + _fila * 2, 34 + _fila * 5,
                        _rng_n.choice(_CORES_TORCIDA), _rng_n.choice(_PELES_TORCIDA), _rng_n.random() * 6.28))


# ---------------------------------------------------------------
# Cavalo: aparência + física da corrida
# ---------------------------------------------------------------
class Cavalo:
    """Um competidor. Os dois jogadores têm exatamente os mesmos atributos."""

    def __init__(self, nome, raca="mangalarga", velocidade=8, resistencia=8, sorte=8):
        self.nome = nome
        self.raca = raca
        self.velocidade = velocidade
        self.resistencia = resistencia
        self.sorte = sorte
        self.visual = {"pelagem": 0, "marca": "estrela", "crina": 0, "sela": 0, "manta": 1,
                       "manta_estilo": 1, "penacho": 0, "caneleiras": 0, "testeira": 0}
        self.jockey = {"pele": 1, "jaqueta": 1, "estampa": 0, "cor2": 7, "chapeu": 0,
                       "chapeu_cor": 1, "oculos": 0, "lenco": 0}
        self.numero = 0
        self.x = LINHA_LARGADA
        self.y = 0
        self.terminou = False
        self.tempo_final = None
        self.ajuste_vel = 0.0     # bônus/penalidade temporário dos QTEs
        self.ajuste_frames = 0
        self.fim = LINHA_CHEGADA
        self.fadiga = 1.0

    def aplicar_indices(self, indices):
        """Aplica a lista de 16 índices de personalização (a mesma que trafega na mensagem V)."""
        for k, (grupo, _rotulo, chave, opcoes) in enumerate(LINHAS_PERS):
            alvo = self.visual if grupo == "cavalo" else self.jockey
            alvo[chave] = indices[k] % len(opcoes)

    def indices(self):
        out = []
        for grupo, _rotulo, chave, _opcoes in LINHAS_PERS:
            alvo = self.visual if grupo == "cavalo" else self.jockey
            out.append(alvo[chave])
        return out

    @property
    def cor(self):
        return PELAGENS[self.visual["pelagem"]][1]

    def preparar(self, raia, numero, n_raias, fim, fadiga):
        self.numero = numero
        self.x = LINHA_LARGADA
        alt = AREA_PISTA // n_raias
        self.y = TOPO_PISTA + raia * alt + alt - 3
        self.terminou = False
        self.tempo_final = None
        self.ajuste_vel = 0.0
        self.ajuste_frames = 0
        self.fim = fim
        self.fadiga = fadiga

    def aplicar_ajuste(self, valor, frames):
        self.ajuste_vel = valor
        self.ajuste_frames = frames

    def progresso(self):
        return (self.x - LINHA_LARGADA) / (self.fim - LINHA_LARGADA)

    def atualizar(self, frame):
        """Um passo da física (só o servidor chama isto)."""
        if self.terminou:
            return
        vel, res, sorte = self.velocidade, self.resistencia, self.sorte
        base = 1.6 + vel * 0.08
        cansaco = max(0, self.progresso() - 0.5) * (1 - min(res, 12) / 12) * 0.6 * self.fadiga
        impulso = random.uniform(-0.8, 0.8 + sorte * 0.05)
        extra = 0.0
        if self.ajuste_frames > 0:
            extra = self.ajuste_vel
            self.ajuste_frames -= 1
        passo = max(0.3, base * (1 - min(cansaco, 0.8)) + impulso + extra) * VEL_ESCALA
        x_ant = self.x
        self.x += passo
        if self.x >= self.fim:
            fracao = (self.fim - x_ant) / passo
            self.tempo_final = (frame - 1 + fracao) / FPS
            self.x = self.fim
            self.terminou = True
