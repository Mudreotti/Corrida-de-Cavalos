# Autores: Murilo Andreotti Borges (RA 25163806-2) e Matheus Marçal Martinelli (RA 25076306-2)
# Sistemas Operacionais - Trabalho 02: jogo com troca de mensagens e gerenciamento de memória
# Prof. Maurilio Campano Jr - Corrida de Cavalos: Duelo 1x1 em rede
"""
app.py - laço principal que o servidor e o cliente têm em COMUM.

Cada processo abre a sua janela, lê o teclado do seu jogador e desenha o estado que está na memória
compartilhada. O que muda entre servidor e cliente (o que fazer com uma tecla, como mudar de fase)
fica nas subclasses: JogoServidor (servidor.py) e JogoCliente (cliente.py).

Teclado (igual nos dois processos, cada jogador usa o PRÓPRIO teclado):
    personalização : W/S ou setas cima/baixo = escolher linha | A/D ou setas esq./dir. = mudar opção
                     F ou ENTER = ficar pronto
    corrida (QTE)  : W A S D  (ou as setas, que valem como W=cima A=esq. S=baixo D=dir.)
    resultado      : ESPAÇO = revanche
"""
import random
import sys
import time

import pygame

import estado as E
import grafico as G
import protocolo as P
import telas as T

TECLAS_QTE = {pygame.K_w: "W", pygame.K_a: "A", pygame.K_s: "S", pygame.K_d: "D",
              pygame.K_UP: "W", pygame.K_LEFT: "A", pygame.K_DOWN: "S", pygame.K_RIGHT: "D"}


class Jogo:
    papel = 0                    # 1 = servidor (Jogador 1) | 2 = cliente (Jogador 2)
    titulo = ""

    def __init__(self, nome_memoria, bot=False, rodadas=0, acerto=0.9, log=None):
        self.estado = E.EstadoCompartilhado(nome_memoria)
        self.vis = T.Visual()
        self.sel = 0
        self.rodando = True
        self.bot, self.rodadas, self.acerto = bot, rodadas, acerto
        self.log = log
        self.frame_local = 0
        self.ultima_fase = -1
        self._bot_t0 = 0
        self._bot_visto = None
        self._bot_reage_em = 0
        self._bot_tecla = None
        self.resumo = []          # resultados das corridas (para os testes)
        pygame.display.set_caption(self.titulo)

    # ------------------------------------------------ ganchos (cada papel implementa)
    def ao_mudar_visual(self): ...
    def ao_alternar_pronto(self): ...
    def ao_tecla_qte(self, tecla): ...
    def ao_revanche(self): ...
    def logica_por_frame(self): ...
    def aviso_lobby(self, d): return None
    def encerrar_rede(self): ...

    # ------------------------------------------------ edição do próprio visual
    @property
    def meu(self):
        return self.papel - 1

    def mudar_opcao(self, delta):
        d = self.estado.ler()
        if d["fase"] != P.FASE_PERSONALIZACAO or d["j"][self.meu]["pronto"]:
            return
        n = len(G.LINHAS_PERS[self.sel][3])
        novo = (d["j"][self.meu]["indices"][self.sel] + delta) % n

        def f(dd):
            dd["j"][self.meu]["indices"][self.sel] = novo
        self.estado.modificar(f)
        self.ao_mudar_visual()

    def mover_selecao(self, delta):
        self.sel = (self.sel + delta) % len(G.LINHAS_PERS)

    # ------------------------------------------------ teclado
    def tratar_tecla(self, tecla):
        d = self.estado.ler()
        fase = d["fase"]
        if tecla == pygame.K_ESCAPE:
            self.rodando = False
        elif fase == P.FASE_PERSONALIZACAO:
            if tecla in (pygame.K_w, pygame.K_UP):
                self.mover_selecao(-1)
            elif tecla in (pygame.K_s, pygame.K_DOWN):
                self.mover_selecao(1)
            elif tecla in (pygame.K_a, pygame.K_LEFT):
                self.mudar_opcao(-1)
            elif tecla in (pygame.K_d, pygame.K_RIGHT):
                self.mudar_opcao(1)
            elif tecla in (pygame.K_f, pygame.K_RETURN, pygame.K_KP_ENTER):
                self.ao_alternar_pronto()
        elif fase == P.FASE_CORRIDA:
            if tecla in TECLAS_QTE:
                self.ao_tecla_qte(TECLAS_QTE[tecla])
        elif fase == P.FASE_RESULTADO:
            if tecla == pygame.K_SPACE:
                self.ao_revanche()

    # ------------------------------------------------ bot (para testes e demonstrações)
    def bot_passo(self, d):
        fase, j = d["fase"], d["j"][self.meu]
        if fase != self.ultima_fase:
            self.ultima_fase, self._bot_t0 = fase, self.frame_local
            if fase == P.FASE_PERSONALIZACAO and self.frame_local < 5:
                for k, (_g, _r, _c, op) in enumerate(G.LINHAS_PERS):     # visual aleatório
                    self.sel = k
                    self.mudar_opcao(random.randrange(len(op)))
            if fase == P.FASE_RESULTADO:
                self.resumo.append((d["vencedor"], d["t1_ms"], d["t2_ms"],
                                    d["j"][0]["qte_acertos"], d["j"][1]["qte_acertos"],
                                    d["placar1"], d["placar2"]))
        espera = self.frame_local - self._bot_t0
        if fase == P.FASE_PERSONALIZACAO and not j["pronto"] and espera > 30 and self.conectado(d):
            self.ao_alternar_pronto()
        elif fase == P.FASE_CORRIDA and j["qte_ativo"]:
            chave = (j["qte_feitos"], j["qte_tecla"])
            if chave != self._bot_visto:                     # novo QTE: decide como reagir
                self._bot_visto = chave
                self._bot_reage_em = self.frame_local + random.randint(8, 30)
                certa = P.CODIGO_TECLA.get(j["qte_tecla"], "W")
                if random.random() < self.acerto:
                    self._bot_tecla = certa
                else:
                    self._bot_tecla = random.choice([t for t in "WASD" if t != certa]) if random.random() < 0.5 else None
            if self._bot_tecla and self.frame_local >= self._bot_reage_em:
                self.ao_tecla_qte(self._bot_tecla)
                self._bot_tecla = None
        elif fase == P.FASE_RESULTADO and espera > 90:
            if self.rodadas > 1:
                # Em partidas automatizadas, somente o servidor coordena a revanche.
                # O cliente aguarda a mensagem N enviada pelo servidor; assim os dois
                # processos não disputam a transição para a próxima rodada.
                self.rodadas -= 1
                if self.papel == 1:
                    self.ao_revanche()
                # Impede que este resultado seja processado novamente enquanto
                # aguardamos a próxima rodada (especialmente no cliente).
                self._bot_t0 = self.frame_local + 10**6
            elif self.rodadas == 1 and espera > 150:
                # A última rodada já terminou e seu resultado foi recebido.
                self.rodando = False

    def conectado(self, d):
        return bool(d["conectado"])

    # ------------------------------------------------ desenho
    def desenhar(self, d):
        self.vis.sincronizar(d)
        fase = d["fase"]
        if fase == P.FASE_PERSONALIZACAO:
            T.desenhar_lobby(d, self.papel, self.sel, self.vis, self.aviso_lobby(d))
        elif fase in (P.FASE_CONTAGEM, P.FASE_CORRIDA):
            T.desenhar_corrida(d, self.papel, self.vis)
        else:
            if not self.vis.confete:
                self.vis.criar_confete()
            self.vis.atualizar_confete()
            T.desenhar_resultado(d, self.papel, self.vis, self.papel == 1)
        if fase != P.FASE_RESULTADO:
            self.vis.confete = []

    def loop(self):
        try:
            while self.rodando:
                for ev in pygame.event.get():
                    if ev.type == pygame.QUIT:
                        self.rodando = False
                    elif ev.type == pygame.KEYDOWN:
                        self.tratar_tecla(ev.key)
                self.logica_por_frame()
                d = self.estado.ler()
                if self.bot:
                    self.bot_passo(d)
                self.desenhar(d)
                pygame.transform.scale(G.tela, G.janela.get_size(), G.janela)
                pygame.display.flip()
                G.relogio.tick(G.FPS)
                self.frame_local += 1
        finally:
            self.encerrar_rede()
            self.estado.fechar()
            pygame.quit()
