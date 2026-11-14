# Autores: Murilo Andreotti Borges (RA 25163806-2) e Matheus Marçal Martinelli (RA 25076306-2)
# Sistemas Operacionais - Trabalho 02: jogo com troca de mensagens e gerenciamento de memória
# Prof. Maurilio Campano Jr - Corrida de Cavalos: Duelo 1x1 em rede
"""
servidor.py - JOGADOR 1 (SERVIDOR).

    python servidor.py              abre a janela e espera o Jogador 2 na porta 51171

Threads deste processo (todas compartilham o MESMO bloco de memória, protegido por trava):
    principal   : teclado, simulação da corrida (autoridade do jogo) e desenho
    recepcao    : fica em recv() esperando mensagens do cliente (criada em rede.Conexao)
    aceitar     : fica em accept() esperando o cliente conectar (criada em rede.ServidorTCP)
    telemetria  : 30x por segundo lê a memória compartilhada e manda o estado (mensagem T) ao cliente
"""
import argparse
import sys
import threading

import app
import estado as E
import grafico as G
import protocolo as P
import rede as R
import simulacao as S


class JogoServidor(app.Jogo):
    papel = 1
    titulo = "Corrida de Cavalos - JOGADOR 1 (SERVIDOR)"

    def __init__(self, porta, silencioso=False, **kw):
        log = R.Log(not silencioso, "SERVIDOR")
        super().__init__("corrida_estado_servidor", log=log, **kw)
        self.corrida = S.Corrida()
        self.ip = R.ip_local()
        self.porta = porta
        padrao = G.Cavalo("x").indices()
        self.estado.set_jogador(0, indices=padrao)
        self.estado.set_jogador(1, indices=padrao)
        try:
            self.rede = R.ServidorTCP(porta, self.receber, self.ao_conectar, self.ao_cair, log)
        except OSError as e:
            self.estado.fechar()
            raise SystemExit(f"Não foi possível abrir a porta {porta}: {e}")
        self.parar_tx = threading.Event()
        threading.Thread(target=self._enviar_telemetria, daemon=True, name="telemetria").start()
        log.info(f"escutando na porta {porta} (IP desta máquina: {self.ip})")

    # ------------------------------------------------------------ mensagens que CHEGAM (thread de recepção)
    def ao_conectar(self):
        self.estado.set(conectado=1)

    def ao_cair(self):
        """O jogador 2 saiu: volta ao início e espera outro."""
        self.voltar_ao_lobby()
        self.estado.set(conectado=0, placar1=0, placar2=0)
        self.estado.set_jogador(1, indices=G.Cavalo("x").indices())

    def receber(self, msg, valor):
        fase = self.estado.ler()["fase"]
        if msg.origem != P.CLIENTE:
            return
        if msg.tipo == "H":                       # cliente se apresentou: responde e manda o que já temos
            self.rede.enviar(P.msg_hello(P.SERVIDOR))
            d = self.estado.ler()
            self.rede.enviar(P.msg_visual(P.SERVIDOR, d["j"][0]["indices"]))
            self.rede.enviar(P.msg_pronto(P.SERVIDOR, d["j"][0]["pronto"]))
        elif msg.tipo == "V" and fase == P.FASE_PERSONALIZACAO:
            self.estado.set_jogador(1, indices=valor)
        elif msg.tipo == "R" and fase == P.FASE_PERSONALIZACAO:
            self.estado.set_jogador(1, pronto=1 if valor else 0)
        elif msg.tipo == "Q" and fase == P.FASE_CORRIDA:
            self.estado.empilhar_entrada(2, valor)     # a simulação consome na próxima frame
        elif msg.tipo == "N" and fase == P.FASE_RESULTADO:
            self.voltar_ao_lobby()
            self.rede.enviar(P.msg_nova(P.SERVIDOR))

    # ------------------------------------------------------------ ações do jogador local
    def ao_mudar_visual(self):
        d = self.estado.ler()
        self.rede.enviar(P.msg_visual(P.SERVIDOR, d["j"][0]["indices"]))

    def ao_alternar_pronto(self):
        novo = 0 if self.estado.ler()["j"][0]["pronto"] else 1
        self.estado.set_jogador(0, pronto=novo)
        self.rede.enviar(P.msg_pronto(P.SERVIDOR, novo))

    def ao_tecla_qte(self, tecla):
        self.estado.empilhar_entrada(1, tecla)

    def ao_revanche(self):
        if self.estado.ler()["fase"] == P.FASE_RESULTADO:
            self.voltar_ao_lobby()
            self.rede.enviar(P.msg_nova(P.SERVIDOR))

    def aviso_lobby(self, d):
        if not d["conectado"]:
            return ["AGUARDANDO O JOGADOR 2", f"PORTA {self.porta}   IP {self.ip}",
                    "NO OUTRO PC: python cliente.py"]
        return None

    # ------------------------------------------------------------ regras do jogo (thread principal)
    def logica_por_frame(self):
        d = self.estado.ler()
        fase = d["fase"]
        if fase == P.FASE_PERSONALIZACAO:
            if d["conectado"] and d["j"][0]["pronto"] and d["j"][1]["pronto"]:
                self.iniciar_corrida()
        elif fase in (P.FASE_CONTAGEM, P.FASE_CORRIDA):
            for jogador, tecla in self.estado.retirar_entradas():
                self.corrida.registrar_tecla(jogador - 1, tecla)
            evento = self.corrida.tick()

            def f(dd):                              # UMA região crítica: estado + mudança de fase
                self.corrida.publicar_em(dd)
                if evento == "go":
                    dd["fase"] = P.FASE_CORRIDA
                elif evento == "fim":
                    dd["fase"] = P.FASE_RESULTADO
                    dd["placar%d" % self.corrida.vencedor] += 1
            self.estado.modificar(f)
            if evento == "go":
                self.rede.enviar(P.msg_go())
            elif evento == "fim":
                d = self.estado.ler()
                self.rede.enviar(P.msg_winner(d["vencedor"], [d["t1_ms"], d["t2_ms"]],
                                              [d["j"][0]["qte_acertos"], d["j"][1]["qte_acertos"]], d["n_qtes"]))

    def iniciar_corrida(self):
        self.corrida.iniciar()
        self.estado.retirar_entradas()              # descarta teclas antigas

        def f(dd):
            dd.update(fase=P.FASE_CONTAGEM, comprimento10=int(round(S.COMPRIMENTO * 10)),
                      n_qtes=S.N_QTES, vencedor=0)
            self.corrida.publicar_em(dd)
        self.estado.modificar(f)
        self.rede.enviar(P.msg_start(S.COMPRIMENTO, S.N_QTES))

    def voltar_ao_lobby(self):
        def f(dd):
            dd.update(fase=P.FASE_PERSONALIZACAO, frame=0, vencedor=0, t1_ms=0, t2_ms=0)
            for j in dd["j"]:
                j.update(pronto=0, terminou=0, ajuste=0, x=G.LINHA_LARGADA * 100, qte_ativo=0, qte_tecla=0,
                         qte_tempo=0, qte_acertos=0, qte_feitos=0, fb=0, fb_t=0, tempo_ms=0)
        self.estado.modificar(f)

    # ------------------------------------------------------------ thread de telemetria
    def _enviar_telemetria(self):
        while not self.parar_tx.wait(1 / 30):
            d = self.estado.ler()
            if d["conectado"] and d["fase"] in (P.FASE_CONTAGEM, P.FASE_CORRIDA):
                j = d["j"]
                self.rede.enviar(P.msg_telemetria(
                    d["frame"], [j[0]["x"], j[1]["x"]], [j[0]["terminou"], j[1]["terminou"]],
                    [j[0]["ajuste"], j[1]["ajuste"]], [tuple(x[k] for k in E.CAMPOS_QTE) for x in j]))

    def encerrar_rede(self):
        self.parar_tx.set()
        if self.estado.ler()["conectado"]:
            self.rede.enviar(P.msg_saida(P.SERVIDOR))
        self.rede.fechar()


def main():
    ap = argparse.ArgumentParser(description="Jogador 1 (servidor) do duelo de corrida em rede")
    ap.add_argument("--porta", type=int, default=P.PORTA)
    ap.add_argument("--bot", action="store_true", help="joga sozinho (para testes e demonstração)")
    ap.add_argument("--rodadas", type=int, default=0, help="com --bot: quantas corridas jogar antes de sair")
    ap.add_argument("--acerto", type=float, default=0.9, help="com --bot: chance de acertar cada QTE")
    ap.add_argument("--silencioso", action="store_true", help="não mostra o log de mensagens")
    a = ap.parse_args()
    jogo = JogoServidor(a.porta, a.silencioso, bot=a.bot, rodadas=a.rodadas, acerto=a.acerto)
    jogo.loop()
    for r in jogo.resumo:
        print("RESULTADO servidor:", r, flush=True)


if __name__ == "__main__":
    main()
