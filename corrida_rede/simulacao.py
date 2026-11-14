# Autores: Murilo Andreotti Borges (RA 25163806-2) e Matheus Marçal Martinelli (RA 25076306-2)
# Sistemas Operacionais - Trabalho 02: jogo com troca de mensagens e gerenciamento de memória
# Prof. Maurilio Campano Jr - Corrida de Cavalos: Duelo 1x1 em rede
"""
simulacao.py - REGRAS DA CORRIDA (rodam SOMENTE no servidor).

O servidor é a autoridade: ele simula os dois cavalos, decide se cada QTE foi acertado e quem
venceu. O cliente só manda "apertei a tecla X" (mensagem Q) e recebe o resultado por telemetria (T).
Assim os dois processos nunca discordam do que aconteceu (sem trapaça e sem divergência de estado).

Ação do jogo = QTE: de tempos em tempos aparece uma tecla (W/A/S/D) para cada jogador.
Acertar dá velocidade extra por 2 s; errar a tecla ou demorar faz o cavalo perder o ritmo.
"""
import random

import grafico as g
import protocolo as P

QTE_JANELA = 70                  # frames para apertar (60 = 1 segundo)
QTE_BONUS, QTE_BONUS_DURACAO = 1.0, 120
QTE_PENALIDADE, QTE_PENALIDADE_DURACAO = -0.5, 45
FB_TEMPO = 80                    # por quantos frames o texto "Perfeito!" fica na tela
CONTAGEM_FRAMES = 180            # 3 segundos de contagem regressiva

COMPRIMENTO = 3.5                # prova longa (3,5x a pista curta)
N_QTES = 12
FADIGA = 1.3


def pontos_qte(n, ini=0.07, fim=0.93):
    """Em que fração da pista cada QTE aparece (uniforme)."""
    return [ini + (fim - ini) * i / (n - 1) for i in range(n)]


def _novo_qte():
    return {"ativo": False, "tecla": "", "tempo": 0, "proximo": 0, "acertos": 0, "feitos": 0,
            "fb": P.FB_NENHUM, "fb_t": 0}


class Corrida:
    def __init__(self):
        self.cavs = [g.Cavalo("Jogador 1"), g.Cavalo("Jogador 2")]
        self.qte = [_novo_qte(), _novo_qte()]
        self.pontos = []
        self.frame = 0
        self.vencedor = 0

    # ---------------------------------------------------------------- ciclo de vida
    def iniciar(self, comprimento=COMPRIMENTO, n_qtes=N_QTES):
        fim = int(g.LINHA_LARGADA + (g.LINHA_CHEGADA - g.LINHA_LARGADA) * comprimento)
        for i, c in enumerate(self.cavs):
            c.preparar(i, i + 1, 2, fim, FADIGA)
        self.qte = [_novo_qte(), _novo_qte()]
        self.pontos = pontos_qte(n_qtes)
        self.frame = -CONTAGEM_FRAMES
        self.vencedor = 0

    @property
    def terminou(self):
        return all(c.terminou for c in self.cavs)

    def tick(self):
        """Avança 1 frame. Retorna 'go' quando a contagem acaba, 'fim' quando a prova termina."""
        evento = None
        self.frame += 1
        if self.frame < 0:
            return None
        if self.frame == 0:
            return "go"
        for i in (0, 1):
            self._atualizar_qte(i)
            self.cavs[i].atualizar(self.frame)
        if self.terminou and self.vencedor == 0:
            a, b = self.cavs
            self.vencedor = 1 if a.tempo_final <= b.tempo_final else 2
            evento = "fim"
        return evento

    # ---------------------------------------------------------------- QTEs
    def _atualizar_qte(self, i):
        q, c = self.qte[i], self.cavs[i]
        if q["fb_t"] > 0:
            q["fb_t"] -= 1
            if q["fb_t"] == 0:
                q["fb"] = P.FB_NENHUM
        if c.terminou:
            q["ativo"] = False
            return
        if q["ativo"]:
            q["tempo"] -= 1
            if q["tempo"] <= 0:                       # demorou: penalidade
                q["ativo"] = False
                self._resolver(i, False, P.FB_LENTO)
        elif q["proximo"] < len(self.pontos) and c.progresso() >= self.pontos[q["proximo"]]:
            q["ativo"] = True
            q["tecla"] = random.choice("WASD")
            q["tempo"] = QTE_JANELA
            q["proximo"] += 1

    def _resolver(self, i, acertou, feedback):
        q, c = self.qte[i], self.cavs[i]
        q["feitos"] += 1
        q["fb"], q["fb_t"] = feedback, FB_TEMPO
        if acertou:
            q["acertos"] += 1
            c.aplicar_ajuste(QTE_BONUS, QTE_BONUS_DURACAO)
        else:
            c.aplicar_ajuste(QTE_PENALIDADE, QTE_PENALIDADE_DURACAO)

    def registrar_tecla(self, i, tecla):
        """O jogador i (0 ou 1) apertou `tecla`. Só vale se houver um QTE ativo para ele."""
        q, c = self.qte[i], self.cavs[i]
        if self.frame < 0 or not q["ativo"] or c.terminou:
            return
        q["ativo"] = False
        if tecla == q["tecla"]:
            self._resolver(i, True, P.FB_PERFEITO)
        else:
            self._resolver(i, False, P.FB_ERRO)

    # ---------------------------------------------------------------- publicação
    def publicar_em(self, d):
        """Copia o estado simulado para o dicionário que vai para a memória compartilhada."""
        d["frame"] = self.frame
        d["vencedor"] = self.vencedor
        for i in (0, 1):
            c, q, j = self.cavs[i], self.qte[i], d["j"][i]
            j["x"] = int(round(c.x * 100))
            j["terminou"] = 1 if c.terminou else 0
            j["ajuste"] = 0 if c.ajuste_frames <= 0 else (1 if c.ajuste_vel > 0 else -1)
            j["qte_ativo"] = 1 if q["ativo"] else 0
            j["qte_tecla"] = P.TECLA_CODIGO[q["tecla"]] if q["tecla"] and q["ativo"] else 0
            j["qte_tempo"] = q["tempo"]
            j["qte_acertos"] = q["acertos"]
            j["qte_feitos"] = q["feitos"]
            j["fb"], j["fb_t"] = q["fb"], q["fb_t"]
            j["tempo_ms"] = int(round(c.tempo_final * 1000)) if c.tempo_final is not None else 0
        d["t1_ms"], d["t2_ms"] = d["j"][0]["tempo_ms"], d["j"][1]["tempo_ms"]
