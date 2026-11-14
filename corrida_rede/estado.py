# Autores: Murilo Andreotti Borges (RA 25163806-2) e Matheus Marçal Martinelli (RA 25076306-2)
# Sistemas Operacionais - Trabalho 02: jogo com troca de mensagens e gerenciamento de memória
# Prof. Maurilio Campano Jr - Corrida de Cavalos: Duelo 1x1 em rede
"""
estado.py - MEMÓRIA COMPARTILHADA do jogo.

O estado da partida (fase, posições, QTEs, placar, visual dos dois jogadores...) NÃO fica em
variáveis soltas: vive num bloco de memória de tamanho fixo, alocado uma única vez
(multiprocessing.shared_memory) com layout binário definido por `struct`.

Quem acessa esse bloco (várias THREADS do mesmo processo):
    servidor:  thread principal (simulação + desenho), thread de recepção, thread de envio
    cliente :  thread principal (desenho + teclado) e thread de recepção

Como evitamos corrida de dados (EXCLUSÃO MÚTUA):
  1. `self.lock` (threading.Lock = mutex): toda leitura e toda escrita do bloco acontece dentro de
     `with self.lock:`. Só uma thread por vez entra na região crítica.
  2. Contador de versão `seq` no começo do bloco (seqlock): vale +1 ANTES de escrever (ímpar =
     escrita em andamento) e +1 DEPOIS (par = bloco consistente). Outro PROCESSO que atacha o
     bloco pelo nome (monitor.py) não consegue usar o mutex da nossa thread, então lê só quando
     seq é par e igual antes/depois da cópia; senão repete.

Gerenciamento de memória:
  - bloco com tamanho fixo (TAMANHO bytes), criado uma vez e liberado em fechar() (close + unlink);
  - nada cresce durante o jogo: a fila de entradas tem tamanho máximo.
"""
import struct
import threading
import time
from collections import deque
from multiprocessing import shared_memory

import protocolo as P

# ---- layout binário (little-endian, sem alinhamento) ----
CABECALHO = struct.Struct("<I7Biii")
# seq | fase conectado comprimento10 n_qtes vencedor placar1 placar2 | frame t1_ms t2_ms
JOGADOR = struct.Struct("<iBbB16BBBhBBBBi")
# x(centi-px) terminou ajuste pronto | 16 índices de visual | qte_ativo qte_tecla qte_tempo
# qte_acertos qte_feitos feedback feedback_tempo | tempo_final_ms
TAMANHO = CABECALHO.size + 2 * JOGADOR.size

CAMPOS_CAB = ("fase", "conectado", "comprimento10", "n_qtes", "vencedor", "placar1", "placar2",
              "frame", "t1_ms", "t2_ms")
CAMPOS_QTE = ("qte_ativo", "qte_tecla", "qte_tempo", "qte_acertos", "qte_feitos", "fb", "fb_t")


def estado_inicial():
    return {
        "seq": 0, "fase": P.FASE_PERSONALIZACAO, "conectado": 0, "comprimento10": 35, "n_qtes": 12,
        "vencedor": 0, "placar1": 0, "placar2": 0, "frame": 0, "t1_ms": 0, "t2_ms": 0,
        "j": [{"x": 0, "terminou": 0, "ajuste": 0, "pronto": 0, "indices": [0] * 16,
               "qte_ativo": 0, "qte_tecla": 0, "qte_tempo": 0, "qte_acertos": 0, "qte_feitos": 0,
               "fb": 0, "fb_t": 0, "tempo_ms": 0} for _ in range(2)],
    }


def desempacotar(dados):
    """bytes -> dict (função pura: também é usada pelo monitor, em outro processo)."""
    c = CABECALHO.unpack_from(dados, 0)
    d = {"seq": c[0]}
    d.update(dict(zip(CAMPOS_CAB, c[1:])))
    d["j"] = []
    for i in range(2):
        v = JOGADOR.unpack_from(dados, CABECALHO.size + i * JOGADOR.size)
        d["j"].append({"x": v[0], "terminou": v[1], "ajuste": v[2], "pronto": v[3],
                       "indices": list(v[4:20]),
                       **dict(zip(CAMPOS_QTE, v[20:27])), "tempo_ms": v[27]})
    return d


def empacotar(d, destino, seq):
    CABECALHO.pack_into(destino, 0, seq, *(d[k] for k in CAMPOS_CAB))
    for i, j in enumerate(d["j"]):
        JOGADOR.pack_into(destino, CABECALHO.size + i * JOGADOR.size,
                          j["x"], j["terminou"], j["ajuste"], j["pronto"], *j["indices"],
                          *(j[k] for k in CAMPOS_QTE), j["tempo_ms"])


def anexar(nome):
    """Abre um bloco que OUTRO processo criou. Quem só anexa não pode apagar o bloco ao sair,
    por isso desligamos o rastreamento (Python 3.13+: track=False; antes: unregister manual)."""
    try:
        return shared_memory.SharedMemory(name=nome, track=False)
    except TypeError:
        shm = shared_memory.SharedMemory(name=nome)
        try:
            from multiprocessing import resource_tracker
            resource_tracker.unregister(shm._name, "shared_memory")
        except Exception:
            pass
        return shm


def ler_externo(nome, tentativas=20000):
    """Leitura consistente feita por OUTRO PROCESSO (sem o mutex): protocolo do seqlock."""
    shm = anexar(nome)
    try:
        for k in range(tentativas):
            antes = struct.unpack_from("<I", shm.buf, 0)[0]
            if antes % 2:                      # escrita em andamento: tenta de novo
                time.sleep(0)
                continue
            copia = bytes(shm.buf[:TAMANHO])
            depois = struct.unpack_from("<I", shm.buf, 0)[0]
            if antes == depois:                # ninguém escreveu durante a cópia
                return desempacotar(copia)
            time.sleep(0)
        raise RuntimeError("não foi possível obter uma leitura consistente")
    finally:
        shm.close()


class EstadoCompartilhado:
    MAX_ENTRADAS = 64

    def __init__(self, nome):
        self.nome = nome
        self.lock = threading.Lock()
        try:
            self.shm = shared_memory.SharedMemory(name=nome, create=True, size=TAMANHO)
        except FileExistsError:               # sobrou de uma execução anterior: reaproveita
            self.shm = shared_memory.SharedMemory(name=nome)
        self._seq = 0
        self.entradas = deque(maxlen=self.MAX_ENTRADAS)   # teclas do jogador remoto (só o servidor usa)
        with self.lock:
            self._gravar(estado_inicial())

    # ----- região crítica: só chamar com self.lock já adquirido -----
    def _gravar(self, d):
        self._seq += 1                         # ímpar: escrevendo
        struct.pack_into("<I", self.shm.buf, 0, self._seq)
        empacotar(d, self.shm.buf, self._seq)
        self._seq += 1                         # par: consistente
        struct.pack_into("<I", self.shm.buf, 0, self._seq)

    def _ler_bruto(self):
        return desempacotar(self.shm.buf)

    # ----- API usada pelas threads -----
    def ler(self):
        """Cópia consistente do estado (a thread não mexe na memória compartilhada fora da trava)."""
        with self.lock:
            return self._ler_bruto()

    def modificar(self, funcao):
        """Lê, aplica `funcao(dict)` e grava de volta - tudo dentro de UMA região crítica."""
        with self.lock:
            d = self._ler_bruto()
            r = funcao(d)
            self._gravar(d)
            return r

    def set(self, **campos):
        def f(d):
            d.update(campos)
        self.modificar(f)

    def set_jogador(self, i, **campos):
        def f(d):
            d["j"][i].update(campos)
        self.modificar(f)

    def empilhar_entrada(self, jogador, tecla):
        with self.lock:
            self.entradas.append((jogador, tecla))

    def retirar_entradas(self):
        with self.lock:
            itens = list(self.entradas)
            self.entradas.clear()
            return itens

    def fechar(self):
        """Libera a memória: close() solta o mapeamento neste processo; unlink() apaga o bloco."""
        try:
            self.shm.close()
            self.shm.unlink()
        except (FileNotFoundError, OSError):
            pass
