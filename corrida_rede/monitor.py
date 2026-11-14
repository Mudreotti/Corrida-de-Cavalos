# Autores: Murilo Andreotti Borges (RA 25163806-2) e Matheus Marçal Martinelli (RA 25076306-2)
# Sistemas Operacionais - Trabalho 02: jogo com troca de mensagens e gerenciamento de memória
# Prof. Maurilio Campano Jr - Corrida de Cavalos: Duelo 1x1 em rede
"""
monitor.py - BÔNUS para a demonstração: um TERCEIRO PROCESSO que lê a memória compartilhada do
servidor enquanto o jogo acontece.

    python monitor.py                              lê o bloco "corrida_estado_servidor"
    python monitor.py corrida_estado_cliente       lê o bloco do cliente (mesmo computador)

Como ele não pode usar o mutex das threads do servidor, usa o contador de versão (seqlock):
só aceita a cópia do bloco se o contador era par e não mudou durante a leitura.
"""
import sys
import time

import estado as E
import protocolo as P


def main():
    nome = sys.argv[1] if len(sys.argv) > 1 else "corrida_estado_servidor"
    print(f"monitor lendo a memória compartilhada '{nome}' ({E.TAMANHO} bytes). Ctrl+C para sair.")
    while True:
        try:
            d = E.ler_externo(nome)
        except FileNotFoundError:
            print("  (aguardando o jogo iniciar...)", flush=True)
            time.sleep(1.0)
            continue
        j1, j2 = d["j"]
        print(f"seq={d['seq']:6d} fase={P.NOMES_FASE[d['fase']]:15s} frame={d['frame']:5d} "
              f"x1={j1['x'] / 100:7.1f} x2={j2['x'] / 100:7.1f} "
              f"QTE acertos J1={j1['qte_acertos']:2d}/{j1['qte_feitos']:2d} J2={j2['qte_acertos']:2d}/{j2['qte_feitos']:2d} "
              f"placar={d['placar1']}x{d['placar2']} conectado={d['conectado']}", flush=True)
        time.sleep(0.5)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
