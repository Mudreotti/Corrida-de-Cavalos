# Autores: Murilo Andreotti Borges (RA 25163806-2) e Matheus Marçal Martinelli (RA 25076306-2)
# Sistemas Operacionais - Trabalho 02: jogo com troca de mensagens e gerenciamento de memória
# Prof. Maurilio Campano Jr - Corrida de Cavalos: Duelo 1x1 em rede
"""
cliente.py - JOGADOR 2 (CLIENTE).

    python cliente.py                 pergunta o IP do servidor na janela
    python cliente.py --host 127.0.0.1    conecta direto (mesmo computador)

Threads deste processo:
    principal : teclado (manda a mensagem Q ao servidor) e desenho do estado
    recepcao  : fica em recv() esperando as mensagens do servidor e grava o resultado na memória
                compartilhada (criada em rede.Conexao)
O cliente NÃO simula nada: a corrida inteira é calculada no servidor e chega aqui por mensagens.
A variável `fase` do cliente só muda quando chega uma mensagem S, G, W ou N do servidor.
"""
import argparse
import sys

import pygame

import app
import estado as E
import grafico as G
import protocolo as P
import rede as R
import telas as T


class JogoCliente(app.Jogo):
    papel = 2
    titulo = "Corrida de Cavalos - JOGADOR 2 (CLIENTE)"

    def __init__(self, host, porta, silencioso=False, **kw):
        log = R.Log(not silencioso, "CLIENTE ")
        super().__init__("corrida_estado_cliente", log=log, **kw)
        self.caiu = False
        padrao = G.Cavalo("x").indices()
        self.estado.set_jogador(0, indices=padrao)
        self.estado.set_jogador(1, indices=padrao)
        try:
            self.conexao = R.conectar(host, porta, self.receber, self.ao_cair, log, tentativas=3)
        except OSError:
            self.estado.fechar()
            raise
        self.estado.set(conectado=1)
        self.conexao.enviar(P.msg_hello(P.CLIENTE))
        self.conexao.enviar(P.msg_visual(P.CLIENTE, padrao))
        self.conexao.enviar(P.msg_pronto(P.CLIENTE, False))

    # ------------------------------------------------------------ mensagens que CHEGAM (thread de recepção)
    def ao_cair(self):
        self.caiu = True
        self.estado.set(conectado=0)
        # Nos testes/demonstrações automatizados, o servidor encerra após a
        # última rodada. Sem janela/teclado, o bot ficaria preso no lobby.
        if self.bot:
            self.rodando = False

    def receber(self, msg, valor):
        if msg.origem != P.SERVIDOR:
            return
        t = msg.tipo
        if t == "V":
            self.estado.set_jogador(0, indices=valor)
        elif t == "R":
            self.estado.set_jogador(0, pronto=1 if valor else 0)
        elif t == "S":                                   # fase := CONTAGEM
            comprimento, n_qtes = valor

            def f(d):
                d.update(fase=P.FASE_CONTAGEM, comprimento10=int(round(comprimento * 10)), n_qtes=n_qtes,
                         frame=-180, vencedor=0, t1_ms=0, t2_ms=0)
                for j in d["j"]:
                    j.update(x=G.LINHA_LARGADA * 100, terminou=0, ajuste=0, qte_ativo=0, qte_tecla=0,
                             qte_tempo=0, qte_acertos=0, qte_feitos=0, fb=0, fb_t=0, tempo_ms=0)
            self.estado.modificar(f)
        elif t == "G":                                   # fase := CORRIDA
            self.estado.set(fase=P.FASE_CORRIDA)
        elif t == "T":                                   # estado da corrida calculado pelo servidor
            def f(d):
                d["frame"] = valor.frame
                for i in (0, 1):
                    j = d["j"][i]
                    j["x"], j["terminou"], j["ajuste"] = valor.x[i], int(valor.terminou[i]), valor.ajuste[i]
                    (j["qte_ativo"], j["qte_tecla"], j["qte_tempo"], j["qte_acertos"],
                     j["qte_feitos"], j["fb"], j["fb_t"]) = valor.qte[i]
            self.estado.modificar(f)
        elif t == "W":                                   # fase := RESULTADO
            def f(d):
                d["fase"] = P.FASE_RESULTADO
                d["vencedor"] = valor.vencedor
                d["t1_ms"], d["t2_ms"] = valor.tempos_ms
                d["n_qtes"] = valor.total
                d["placar%d" % valor.vencedor] += 1
                for i in (0, 1):
                    d["j"][i]["qte_acertos"] = valor.acertos[i]
                    d["j"][i]["tempo_ms"] = valor.tempos_ms[i]
                    d["j"][i]["terminou"] = 1
            self.estado.modificar(f)
        elif t == "N":                                   # fase := PERSONALIZAÇÃO
            def f(d):
                d.update(fase=P.FASE_PERSONALIZACAO, frame=0, vencedor=0)
                for j in d["j"]:
                    j.update(pronto=0, terminou=0, ajuste=0, x=G.LINHA_LARGADA * 100, qte_ativo=0, qte_tecla=0,
                             qte_tempo=0, qte_feitos=0, fb=0, fb_t=0)
            self.estado.modificar(f)
        elif t == "X":
            self.ao_cair()

    # ------------------------------------------------------------ ações do jogador local
    def ao_mudar_visual(self):
        d = self.estado.ler()
        self.conexao.enviar(P.msg_visual(P.CLIENTE, d["j"][1]["indices"]))

    def ao_alternar_pronto(self):
        novo = 0 if self.estado.ler()["j"][1]["pronto"] else 1
        self.estado.set_jogador(1, pronto=novo)
        self.conexao.enviar(P.msg_pronto(P.CLIENTE, novo))

    def ao_tecla_qte(self, tecla):
        self.conexao.enviar(P.msg_qte(tecla))

    def ao_revanche(self):
        self.conexao.enviar(P.msg_nova(P.CLIENTE))      # o servidor responde com 1N

    def aviso_lobby(self, d):
        if self.caiu:
            return ["CONEXÃO PERDIDA", "O SERVIDOR FECHOU.", "APERTE ESC PARA SAIR"]
        return None

    def encerrar_rede(self):
        if not self.caiu:
            self.conexao.enviar(P.msg_saida(P.CLIENTE))
        self.conexao.fechar()


def pedir_ip(padrao, erro=""):
    """Tela simples para digitar o IP do servidor."""
    ip = padrao
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                return None
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and ip:
                    return ip
                if ev.key == pygame.K_BACKSPACE:
                    ip = ip[:-1]
                elif ev.unicode and ev.unicode in "0123456789." and len(ip) < 15:
                    ip += ev.unicode
        T.desenhar_espera(["IP DO SERVIDOR", ip + "_", "ENTER PARA CONECTAR", erro])
        pygame.transform.scale(G.tela, G.janela.get_size(), G.janela)
        pygame.display.flip()
        G.relogio.tick(30)


def main():
    ap = argparse.ArgumentParser(description="Jogador 2 (cliente) do duelo de corrida em rede")
    ap.add_argument("--host", default=None, help="IP do servidor (se omitido, pergunta na janela)")
    ap.add_argument("--porta", type=int, default=P.PORTA)
    ap.add_argument("--bot", action="store_true", help="joga sozinho (para testes e demonstração)")
    ap.add_argument("--rodadas", type=int, default=0)
    ap.add_argument("--acerto", type=float, default=0.9)
    ap.add_argument("--silencioso", action="store_true")
    a = ap.parse_args()
    host, erro = a.host, ""
    while True:
        if host is None:
            host = pedir_ip("127.0.0.1", erro)
            if host is None:
                return
        try:
            jogo = JogoCliente(host, a.porta, a.silencioso, bot=a.bot, rodadas=a.rodadas, acerto=a.acerto)
            break
        except OSError as e:
            if a.host is not None:
                raise SystemExit(f"Não foi possível conectar em {host}:{a.porta} ({e})")
            erro, host = "NAO FOI POSSIVEL CONECTAR", None
    jogo.loop()
    for r in jogo.resumo:
        print("RESULTADO cliente :", r, flush=True)


if __name__ == "__main__":
    main()
