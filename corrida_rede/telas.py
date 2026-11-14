# Autores: Murilo Andreotti Borges (RA 25163806-2) e Matheus Marçal Martinelli (RA 25076306-2)
# Sistemas Operacionais - Trabalho 02: jogo com troca de mensagens e gerenciamento de memória
# Prof. Maurilio Campano Jr - Corrida de Cavalos: Duelo 1x1 em rede
"""
telas.py - DESENHO das telas. Nenhuma função aqui mexe no jogo: todas recebem uma CÓPIA do estado
(dict lido da memória compartilhada) e só desenham. Por isso o servidor e o cliente usam
exatamente as mesmas telas.
"""
import math
import random

import pygame

from grafico import *            # tela, texto(), caixa(), desenhar_cavalo(), cores...
import protocolo as P

PVP_CORES = [(110, 180, 255), (255, 120, 96)]
NOMES = ["JOGADOR 1", "JOGADOR 2"]
FEEDBACK = {P.FB_PERFEITO: ("PERFEITO!", VERDE), P.FB_ERRO: ("TECLA ERRADA!", VERMELHO),
            P.FB_LENTO: ("MUITO LENTO!", VERMELHO)}


class Visual:
    """Cavalos usados só para DESENHAR (posição e aparência vêm da memória compartilhada)."""

    def __init__(self):
        self.cavs = [Cavalo("Jogador 1"), Cavalo("Jogador 2")]
        self.confete = []

    def sincronizar(self, d):
        alt = AREA_PISTA // 2
        fim = LINHA_LARGADA + (LINHA_CHEGADA - LINHA_LARGADA) * d["comprimento10"] / 10.0
        for i in (0, 1):
            c, j = self.cavs[i], d["j"][i]
            c.aplicar_indices(j["indices"])
            c.numero = i + 1
            c.x = j["x"] / 100.0 if d["fase"] != P.FASE_PERSONALIZACAO else LINHA_LARGADA
            c.y = TOPO_PISTA + i * alt + alt - 3
            c.terminou = bool(j["terminou"])
            c.fim = fim

    def criar_confete(self):
        self.confete = [[random.uniform(0, LARGURA), random.uniform(-ALTURA, 0), random.uniform(0.8, 1.8),
                         random.uniform(0, 6.28), random.choice(CORES_CONFETE), random.choice([2, 2, 3])]
                        for _ in range(110)]

    def atualizar_confete(self):
        for p in self.confete:
            p[1] += p[2]
            p[3] += 0.08
            p[0] += math.sin(p[3]) * 0.7
            if p[1] > ALTURA:
                p[1] = -4


def quadro_galope(c):
    return int(c.x / 5.0) % 8


# =============================================================== personalização
def desenhar_lobby(d, papel, sel, vis, aviso=None):
    tela.blit(FUNDO_LOJA, (0, 0))
    tela.fill((12, 10, 26), (0, 0, LARGURA, 18))
    tela.fill(OURO, (0, 18, LARGURA, 1))
    texto(f"VOCÊ É O JOGADOR {papel}", 6, 9, PVP_CORES[papel - 1])
    texto("DUELO 1X1 EM REDE", 250, 9, OURO, 1, "centro")
    texto(f"PLACAR {d['placar1']} X {d['placar2']}", LARGURA - 6, 9, BRANCO, 1, "dir")
    minha = papel - 1

    for i in (0, 1):
        x0 = 4 + i * 248
        cor, j = PVP_CORES[i], d["j"][i]
        pronto, editavel = bool(j["pronto"]), (i == minha)
        caixa(x0, 22, 244, 280, (20, 18, 44), VERDE if pronto else cor)
        texto(NOMES[i] + ("  (VOCÊ)" if editavel else ""), x0 + 8, 32, cor, 1, contorno=PRETO)
        texto("VEL 8 RES 8 SOR 8", x0 + 236, 32, (214, 212, 232), 1, "dir")
        tela.fill((34, 30, 70), (x0 + 8, 40, 228, 58))
        tela.fill((54, 48, 106), (x0 + 8, 84, 228, 14))
        desenhar_cavalo(x0 + 122, 92, vis.cavs[i], 0, False, None, 1)

        cont = {"cavalo": 0, "competidor": 0}
        for idx, (grupo, rotulo, chave, opcoes) in enumerate(LINHAS_PERS):
            k = cont[grupo]
            cont[grupo] += 1
            cy = (120 if grupo == "cavalo" else 214) + k * 10
            marcada = editavel and idx == sel and not pronto
            if marcada:
                tela.fill(cor, (x0 + 4, cy - 5, 236, 10))
                tela.fill(ROXO_MED, (x0 + 5, cy - 4, 234, 8))
            nome_op, cor_op = opcoes[j["indices"][idx] % len(opcoes)]
            texto(rotulo, x0 + 10, cy, BRANCO if marcada else (196, 194, 218))
            if cor_op:
                tela.fill((0, 0, 0), (x0 + 99, cy - 4, 9, 9))
                tela.fill(cor_op, (x0 + 100, cy - 3, 7, 7))
            if editavel:
                cs = cor if marcada else (104, 102, 144)
                seta_pixel(x0 + 118, cy, -1, cs)
                seta_pixel(x0 + 228, cy, 1, cs)
            texto(nome_op, x0 + 173, cy, (255, 238, 176) if marcada else (226, 224, 238), 1, "centro")
        texto("CAVALO", x0 + 8, 108, OURO)
        tela.fill(OURO_ESC, (x0 + 8, 114, 228, 1))
        texto("CORREDOR", x0 + 8, 202, OURO)
        tela.fill(OURO_ESC, (x0 + 8, 208, 228, 1))

        if pronto:
            texto("PRONTO!", x0 + 122, 293, VERDE, 1, "centro")
        elif editavel:
            texto("F OU ENTER = PRONTO", x0 + 122, 293, (170, 168, 204), 1, "centro")
        else:
            texto("ESCOLHENDO...", x0 + 122, 293, (140, 138, 170), 1, "centro")

    if aviso:
        cobrir_tela(9)
        caixa(100, 120, 300, 70, (20, 16, 40), OURO)
        for k, linha in enumerate(aviso):
            texto(linha, 250, 140 + k * 16, OURO if k == 0 else BRANCO, 1, "centro")
    barra_dicas("W/S OU SETAS ESCOLHEM  |  A/D OU SETAS MUDAM  |  F OU ENTER = PRONTO  |  ESC SAI")


# =============================================================== corrida
def _camera(d):
    xa, xb = d["j"][0]["x"] / 100.0, d["j"][1]["x"] / 100.0
    fim = LINHA_LARGADA + (LINHA_CHEGADA - LINHA_LARGADA) * d["comprimento10"] / 10.0
    lider, ultimo = max(xa, xb), min(xa, xb)
    alvo = (xa + xb) / 2 - 250
    alvo = max(alvo, lider - 440)
    alvo = min(alvo, ultimo - 60)
    return int(max(0, min(alvo, fim + 40 - LARGURA)))


def _pista(cam, fim):
    faixa = obter_faixa(2)
    off = -(int(cam) % FAIXA_W)
    tela.blit(faixa, (off, 0))
    tela.blit(faixa, (off + FAIXA_W, 0))
    alt = AREA_PISTA // 2
    y_fim = TOPO_PISTA + 2 * alt
    xs = LINHA_LARGADA - cam
    if xs > -40:
        tela.fill((255, 255, 255), (xs, TOPO_PISTA, 2, 2 * alt))
        for i in range(2):
            cy = TOPO_PISTA + i * alt + alt // 2
            tela.fill((40, 28, 24), (20 - cam, cy - 5, 11, 11))
            tela.fill((236, 220, 190), (21 - cam, cy - 4, 9, 9))
            digito3(tela, str(i + 1), 24 - cam, cy - 2, (40, 28, 24))
    xf = fim - cam
    if xf < LARGURA + 20:
        for k in range(0, 2 * alt, 4):
            for col in range(2):
                c = (255, 255, 255) if ((k // 4) + col) % 2 == 0 else (20, 20, 24)
                tela.fill(c, (xf - 4 + col * 4, TOPO_PISTA + k, 4, min(4, 2 * alt - k)))
        for y_p in (TOPO_PISTA - 16, y_fim + 2):
            tela.fill((230, 226, 214), (xf - 1, y_p, 3, 14))
            pygame.draw.polygon(tela, (232, 52, 60), [(xf + 2, y_p), (xf + 12, y_p + 3), (xf + 2, y_p + 6)])


def _minimapa(d, vis):
    x0, x1, y = 90, 410, 253
    tela.fill((0, 0, 0), (x0 - 10, y - 7, x1 - x0 + 20, 15))
    tela.fill((40, 36, 64), (x0 - 9, y - 6, x1 - x0 + 18, 13))
    tela.fill(CINZA_ESC, (x0, y, x1 - x0, 1))
    tela.fill(BRANCO, (x0 - 1, y - 4, 2, 9))
    for k in range(4):
        tela.fill(BRANCO if k % 2 else PRETO, (x1, y - 4 + k * 2, 2, 2))
        tela.fill(PRETO if k % 2 else BRANCO, (x1 + 2, y - 4 + k * 2, 2, 2))
    for i in (0, 1):
        c = vis.cavs[i]
        px = int(x0 + max(0.0, min(1.0, c.progresso())) * (x1 - x0))
        py = y - 5 + i
        tela.fill(PRETO, (px - 4, py - 1, 9, 13))
        tela.fill(PVP_CORES[i], (px - 3, py, 7, 11))
        digito3(tela, str(i + 1), px - 1, py + 3, (20, 16, 30))


def _bloco_qte(d, i, papel):
    j, cor, esq = d["j"][i], PVP_CORES[i], (i == 0)
    anc = "esq" if esq else "dir"
    bx = 14 if esq else LARGURA - 42
    tx = 52 if esq else LARGURA - 52
    nome = NOMES[i] + (" (VOCÊ)" if i == papel - 1 else "")
    texto(f"{nome}  {j['qte_acertos']}/{d['n_qtes']}", 14 if esq else LARGURA - 14, 274, cor, 1, anc)
    if j["terminou"]:
        texto("CHEGOU!", tx, 293, cor, 2, anc, contorno=(30, 24, 40))
        return
    ativo = bool(j["qte_ativo"])
    caixa(bx, 281, 28, 28, (30, 26, 50), cor if ativo else CINZA_ESC, sombra=False)
    if ativo:
        texto(P.CODIGO_TECLA.get(j["qte_tecla"], "?"), bx + 14, 295, BRANCO, 3, "centro")
        texto("APERTE!", tx, 289, OURO, 1, anc)
        fr = max(0.0, j["qte_tempo"] / 70.0)
        xb = tx if esq else tx - 62
        tela.fill((0, 0, 0), (xb, 296, 62, 9))
        tela.fill(VERDE if fr > 0.4 else (255, 130, 70), (xb + 1, 297, int(60 * fr), 7))
    elif j["fb"] in FEEDBACK:
        msg, c = FEEDBACK[j["fb"]]
        texto(msg, tx, 293, c, 1, anc)


def desenhar_corrida(d, papel, vis):
    t = pygame.time.get_ticks() / 1000
    cam = _camera(d)
    fim = LINHA_LARGADA + (LINHA_CHEGADA - LINHA_LARGADA) * d["comprimento10"] / 10.0
    _pista(cam, fim)
    correndo_geral = d["frame"] >= 0
    for (x, y, cr, cp, fase) in TORCIDA:
        sx = (x - cam) % LARGURA
        oy = 1 if (correndo_geral and math.sin(t * 9 + fase) > 0) else 0
        tela.fill(cr, (sx, y - oy, 3, 3))
        tela.fill(cp, (sx, y - 3 - oy, 3, 3))

    for i in sorted((0, 1), key=lambda k: vis.cavs[k].y):
        c, j = vis.cavs[i], d["j"][i]
        sx = c.x - cam
        if sx < -50 or sx > LARGURA + 50:
            lado = 1 if sx > 0 else -1
            ax = LARGURA - 6 if lado > 0 else 6
            seta_pixel(ax, int(c.y) - 36, lado, PVP_CORES[i])
            continue
        correndo = correndo_geral and not c.terminou
        if j["ajuste"]:
            cor = (120, 255, 120) if j["ajuste"] > 0 else (255, 90, 90)
            pygame.draw.ellipse(tela, cor, (int(sx) - 30, int(c.y) - 6, 60, 12), 1)
        desenhar_cavalo(sx, c.y, c, quadro_galope(c) if correndo else 0, correndo, c.numero, 2)
        mx = int(sx)
        my = int(c.y) - 84 + (1 if (pygame.time.get_ticks() // 250) % 2 else 0)
        pygame.draw.polygon(tela, PRETO, [(mx - 5, my - 1), (mx + 5, my - 1), (mx, my + 6)])
        pygame.draw.polygon(tela, PVP_CORES[i], [(mx - 3, my), (mx + 3, my), (mx, my + 4)])
        texto(str(i + 1), mx, my - 8, PVP_CORES[i], 1, "centro", contorno=PRETO)

    _minimapa(d, vis)
    tela.fill((12, 10, 26), (0, 264, LARGURA, ALTURA - 264))
    tela.fill(OURO, (0, 264, LARGURA, 1))
    tela.fill(OURO_ESC, (0, 265, LARGURA, 1))
    texto("TEMPO", 250, 274, CINZA, 1, "centro")
    texto(fmt_tempo(max(0, d["frame"]) / FPS), 250, 292, OURO, 2, "centro", contorno=(60, 36, 8))
    _bloco_qte(d, 0, papel)
    _bloco_qte(d, 1, papel)
    if d["frame"] >= 0 and any(j["terminou"] for j in d["j"]):
        texto("AGUARDE O OUTRO JOGADOR CHEGAR...", 250, 311, BRANCO, 1, "centro")

    if d["frame"] < 0:
        caixa(130, 52, 240, 76, (14, 14, 32), OURO)
        texto("DUELO 1X1 - PROVA LONGA", 250, 64, OURO, 1, "centro")
        for i in (0, 1):
            yy = 84 + i * 16
            tela.fill((0, 0, 0), (146, yy - 5, 11, 11))
            tela.fill(PVP_CORES[i], (147, yy - 4, 9, 9))
            texto(NOMES[i] + ("  (VOCÊ)" if i == papel - 1 else ""), 164, yy, PVP_CORES[i])
            texto(f"RAIA {i + 1}", 354, yy, (170, 184, 204), 1, "dir")
        texto("ATRIBUTOS IGUAIS: GANHA QUEM ACERTAR MAIS QTES", 250, 116, (214, 212, 232), 1, "centro")
        texto(str((-d["frame"] - 1) // 60 + 1), 250, 184, OURO, 8, "centro", contorno=PRETO)
    elif d["frame"] < 50:
        texto("JÁ!", 250, 160, VERDE, 8, "centro", contorno=PRETO)


# =============================================================== resultado
def desenhar_resultado(d, papel, vis, ao_vivo_servidor):
    tela.blit(FUNDO_RESULTADO, (0, 0))
    v = d["vencedor"] - 1
    p = 1 - v
    tempos = [d["t1_ms"] / 1000.0, d["t2_ms"] / 1000.0]
    texto(f"{NOMES[v]} VENCEU!", 250, 32, PVP_CORES[v], 3, "centro", contorno=PRETO)
    base = 206
    for k, (i, cx, h, cor) in enumerate([(v, 170, 44, (230, 184, 56)), (p, 330, 28, (196, 202, 214))]):
        topo = base - h
        tela.fill(escurecer(cor, 0.5), (cx - 40, topo, 80, h))
        tela.fill(cor, (cx - 39, topo + 1, 78, h - 1))
        tela.fill(clarear(cor, 0.5), (cx - 39, topo + 1, 78, 2))
        texto(str(k + 1), cx, topo + h // 2 + 2, escurecer(cor, 0.4), 2, "centro")
        c = vis.cavs[i]
        c.x, c.y, c.terminou = LINHA_LARGADA, topo, True
        desenhar_cavalo(cx, topo, c, 0, False, i + 1, 1)
        texto(NOMES[i] + (" (VOCÊ)" if i == papel - 1 else ""), cx, base + 10, PVP_CORES[i], 1, "centro", contorno=PRETO)
        texto(fmt_tempo(tempos[i]), cx, base + 22, (214, 212, 232), 1, "centro", contorno=PRETO)
    caixa(60, 246, 380, 56, (18, 14, 40), OURO)
    texto(f"DIFERENÇA: {abs(tempos[0] - tempos[1]):.2f} S", 250, 258, BRANCO, 1, "centro")
    for i in (0, 1):
        texto(f"{NOMES[i]}: QTES {d['j'][i]['qte_acertos']}/{d['n_qtes']}", 80 + i * 180, 272, PVP_CORES[i])
    texto(f"PLACAR  J1 {d['placar1']}  X  {d['placar2']} J2", 250, 289, OURO, 1, "centro")
    for c in vis.confete:
        tela.fill(c[4], (int(c[0]), int(c[1]), c[5], c[5]))
    barra_dicas("ESPAÇO: REVANCHE  |  ESC: SAIR")


def desenhar_espera(texto_linhas):
    """Tela simples de status (aguardando conexão, desconectado...)."""
    tela.blit(FUNDO_LOJA, (0, 0))
    caixa(70, 90, 360, 110, (20, 16, 40), OURO)
    for k, linha in enumerate(texto_linhas):
        texto(linha, 250, 112 + k * 18, OURO if k == 0 else BRANCO, 1 if k else 2, "centro")
    barra_dicas("ESC SAI")
