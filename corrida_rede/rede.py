# Autores: Murilo Andreotti Borges (RA 25163806-2) e Matheus Marçal Martinelli (RA 25076306-2)
# Sistemas Operacionais - Trabalho 02: jogo com troca de mensagens e gerenciamento de memória
# Prof. Maurilio Campano Jr - Corrida de Cavalos: Duelo 1x1 em rede
"""
rede.py - COMUNICAÇÃO POR SOCKET TCP entre os dois processos (equivalente ao winsock2 + pthreads
dos exemplos em C do professor).

    Servidor  : socket() -> bind() -> listen() -> accept()      (porta 51171, como nos exemplos)
    Cliente   : socket() -> connect()
    Depois    : send()/recv() de mensagens de texto na notação de protocolo.py

Cada conexão tem uma THREAD de recepção (fica bloqueada em recv() e chama `ao_receber` para cada
mensagem completa) e uma TRAVA de envio (send_lock): duas threads diferentes mandam mensagens
pelo mesmo socket (ex.: o laço do jogo manda 'G' e a thread de telemetria manda 'T'); sem a
trava os bytes das duas mensagens poderiam se misturar no fluxo.
"""
import socket
import sys
import threading
import time

import protocolo as P

RECV_BUF = 1024            # buffer de recepção de tamanho fixo (como o `char buffer[...]` do C)


class Log:
    """Mostra no terminal as mensagens trocadas. A telemetria (T) é muito frequente, então é resumida."""

    def __init__(self, ativo=True, nome=""):
        self.ativo = ativo
        self.nome = nome
        self.t0 = time.time()
        self.cont_t = {"ENVIADO": 0, "RECEBIDO": 0}
        self.ult_t = time.time()
        self.lock = threading.Lock()

    def msg(self, sentido, linha):
        if not self.ativo:
            return
        with self.lock:
            if linha[1:2] == "T":
                self.cont_t[sentido] += 1
                if time.time() - self.ult_t > 2.0:
                    print(f"[{self._hora()}] {self.nome} {sentido:8s} T x{self.cont_t[sentido]} (telemetria resumida) "
                          f"ex.: {linha[:60]}", flush=True)
                    self.cont_t[sentido] = 0
                    self.ult_t = time.time()
                return
            print(f"[{self._hora()}] {self.nome} {sentido:8s} {linha}", flush=True)

    def info(self, texto):
        if self.ativo:
            with self.lock:
                print(f"[{self._hora()}] {self.nome} ---- {texto}", flush=True)

    def _hora(self):
        return "%7.3f" % (time.time() - self.t0)


class Conexao:
    """Um socket TCP já conectado + thread de recepção + envio protegido por trava."""

    def __init__(self, sock, ao_receber, ao_cair, log):
        self.sock = sock
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)   # não agrupar mensagens pequenas
        self.ao_receber = ao_receber
        self.ao_cair = ao_cair
        self.log = log
        self.send_lock = threading.Lock()
        self.viva = True
        self.leitor = P.Leitor()
        self.thread = threading.Thread(target=self._receber, daemon=True, name="recepcao")
        self.thread.start()

    def enviar(self, dados):
        """Envia uma mensagem (bytes). Retorna False se a conexão caiu."""
        if not self.viva:
            return False
        try:
            with self.send_lock:
                self.sock.sendall(dados)
            self.log.msg("ENVIADO", dados.decode("ascii").rstrip("\n"))
            return True
        except OSError:
            self._cair()
            return False

    def _receber(self):
        while self.viva:
            try:
                dados = self.sock.recv(RECV_BUF)
            except OSError:
                break
            if not dados:                      # o outro lado fechou
                break
            for linha in self.leitor.alimentar(dados):
                self.log.msg("RECEBIDO", linha)
                try:
                    msg, valor = P.decodificar(linha)
                except P.ErroProtocolo as e:
                    self.log.info(f"mensagem inválida ignorada: {e}")
                    continue
                self.ao_receber(msg, valor)
        self._cair()

    def _cair(self):
        if self.viva:
            self.viva = False
            try:
                self.sock.close()
            except OSError:
                pass
            self.ao_cair()

    def fechar(self):
        self._cair()


class ServidorTCP:
    """Fica escutando na porta; aceita UM cliente por vez (o jogo é de dois jogadores)."""

    def __init__(self, porta, ao_receber, ao_conectar, ao_cair, log):
        self.porta = porta
        self.ao_receber = ao_receber
        self.ao_conectar = ao_conectar
        self.ao_cair = ao_cair
        self.log = log
        self.conexao = None
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if sys.platform == "win32":
            # no Windows, SO_REUSEADDR deixaria DOIS servidores abrirem a mesma porta sem erro
            self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        else:
            self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind(("", porta))
        self.listener.listen(1)
        self.ativo = True
        threading.Thread(target=self._aceitar, daemon=True, name="aceitar").start()

    def _aceitar(self):
        while self.ativo:
            try:
                sock, addr = self.listener.accept()
            except OSError:
                break
            if self.conexao is not None and self.conexao.viva:
                try:                           # já tem jogador 2: recusa
                    sock.sendall(P.msg_saida(P.SERVIDOR))
                    sock.close()
                except OSError:
                    pass
                continue
            self.log.info(f"cliente conectado: {addr[0]}:{addr[1]}")
            self.conexao = Conexao(sock, self.ao_receber, self._caiu, self.log)
            self.ao_conectar()

    def _caiu(self):
        self.log.info("cliente desconectou")
        self.ao_cair()

    def enviar(self, dados):
        c = self.conexao
        return c.enviar(dados) if c is not None else False

    def fechar(self):
        self.ativo = False
        try:
            self.listener.close()
        except OSError:
            pass
        if self.conexao is not None:
            self.conexao.fechar()


def conectar(host, porta, ao_receber, ao_cair, log, tentativas=1):
    """Lado do cliente: connect() e devolve a Conexao (ou levanta OSError)."""
    ultimo = None
    for _ in range(tentativas):
        try:
            sock = socket.create_connection((host, porta), timeout=5)
            sock.settimeout(None)
            return Conexao(sock, ao_receber, ao_cair, log)
        except OSError as e:
            ultimo = e
            time.sleep(0.3)
    raise ultimo


def ip_local():
    """IP da máquina na rede local (para o outro jogador digitar)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"
