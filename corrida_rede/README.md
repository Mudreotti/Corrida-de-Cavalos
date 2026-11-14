# Corrida de Cavalos — Duelo 1x1 em rede

**Trabalho 02 – Sistemas Operacionais (Prof. Maurilio Campano Jr)** — jogo com troca de mensagens e gerenciamento de memória.

| | |
|---|---|
| Alunos | Murilo Andreotti Borges (RA 25163806-2) · Matheus Marçal Martinelli (RA 25076306-2) |
| Linguagem | Python 3.13 (+ `pygame` só para a interface) |
| Comunicação | `socket` TCP (porta **51171**, a mesma dos exemplos do professor) |
| Concorrência | `threading` (equivalente ao `pthreads.h` dos exemplos) |
| Memória | `multiprocessing.shared_memory` + `struct` (bloco fixo de 93 bytes) |

## 1. O jogo

Dois jogadores, **cada um no seu computador (ou na sua janela)**, disputam uma corrida de cavalos de pista longa (~15 s).
Os dois cavalos têm **exatamente os mesmos atributos**; quem ganha é quem acerta mais **QTEs**: de tempos em tempos aparece uma
tecla (W, A, S ou D) para cada jogador. Acertar dá velocidade extra; errar ou demorar faz o cavalo perder o ritmo.
Antes de cada corrida cada jogador personaliza o **seu** cavalo e o **seu** corredor, e vê o do adversário mudando ao vivo.

## 2. Como executar

```
py -3.13 -m pip install pygame
py -3.13 servidor.py          (Jogador 1 – abre a porta 51171 e espera)
py -3.13 cliente.py           (Jogador 2 – pede o IP; 127.0.0.1 se for no mesmo PC)
py -3.13 monitor.py           (opcional – terceiro processo lendo a memória compartilhada)
```
Também há `jogar_servidor.bat`, `jogar_cliente.bat` e `monitor.bat`. Em outro computador da mesma rede, o cliente digita o IP que o servidor mostra
na tela de espera (o firewall do Windows pode perguntar se libera o Python: permita em rede privada).

**Teclas** (cada jogador usa o próprio teclado): `W/S` ou setas ↑↓ escolhem a linha · `A/D` ou setas ←→ mudam a opção · `F` ou `ENTER` = pronto ·
na corrida, `W A S D` (ou setas) respondem o QTE · `ESPAÇO` = revanche · `ESC` = sair.

**Modo de teste/demonstração:** `--bot` faz o jogador jogar sozinho (`py servidor.py --bot --rodadas 2`).

## 3. Arquitetura

```
        PROCESSO 1 – SERVIDOR (Jogador 1)                       PROCESSO 2 – CLIENTE (Jogador 2)
 ┌───────────────────────────────────────────┐            ┌─────────────────────────────────────┐
 │ thread principal: teclado + SIMULAÇÃO     │            │ thread principal: teclado + desenho │
 │                   + desenho               │  mensagens │                                     │
 │ thread telemetria: manda T (30x/s)  ──────┼──── TCP ───┼──► thread recepção: grava T, S, G, W│
 │ thread recepção:  ◄─ Q, V, R, N ──────────┼─ porta ────┼──  (a thread principal manda Q,V,R) │
 │ thread aceitar:   accept()                │   51171    │                                     │
 │        │                                  │            │            │                        │
 │   [ MEMÓRIA COMPARTILHADA + MUTEX ]       │            │   [ MEMÓRIA COMPARTILHADA + MUTEX ] │
 └───────────────────────────────────────────┘            └─────────────────────────────────────┘
        ▲ lida também por monitor.py (3º processo, via seqlock)
```

O **servidor é a autoridade**: simula a corrida, decide se cada QTE foi acertado e quem venceu. O cliente só manda "apertei a tecla X" e recebe o estado.
Isso evita que os dois processos discordem do que aconteceu. (Nos exemplos do professor o servidor também é jogador e cada processo guarda a sua cópia do estado,
que só muda por mensagens — a mesma ideia.)

| Arquivo | Papel |
|---|---|
| `protocolo.py` | **notação das mensagens** (codificar, decodificar, validar, remontar o fluxo TCP) |
| `estado.py` | **memória compartilhada** + mutex + seqlock |
| `rede.py` | sockets (`bind/listen/accept/connect/send/recv`), thread de recepção, trava de envio, log |
| `simulacao.py` | regras da corrida e dos QTEs (só no servidor) |
| `app.py` | laço principal comum (teclado, desenho, bot) |
| `servidor.py` / `cliente.py` | cada papel: o que fazer com cada mensagem e cada tecla |
| `telas.py`, `grafico.py` | desenho (pixel art), sem lógica de jogo nem de rede |
| `monitor.py` | 3º processo lendo a memória compartilhada (bônus) |
| `testes/` | testes unitários e de integração |

## 4. Notação das mensagens

Toda mensagem é uma linha ASCII: **`<origem><tipo><carga>\n`** (como o `2Cc3` do enunciado: quem enviou + o que aconteceu + parâmetros).
`origem`: `1` = servidor, `2` = cliente.

| Tipo | Exemplo | Significado |
|---|---|---|
| `H` | `2H1` / `1H1` | handshake (carga = versão do protocolo) |
| `V` | `2V4401100011070100` | visual: 16 dígitos hexadecimais, um por linha da personalização (cavalo + corredor) |
| `R` | `2R1` | jogador ficou pronto (`1`) ou desfez (`0`) |
| `S` | `1S35;12` | **start**: pista 3,5× e 12 QTEs → `fase := CONTAGEM` |
| `G` | `1G` | **go**: fim da contagem → `fase := CORRIDA` |
| `Q` | `2QW` | **ação do jogo**: o jogador 2 apertou W (ou A, S, D) |
| `T` | `1T412;81234;80990;00;10;1,2,40,5,6,0,0;0,0,0,4,5,1,60` | telemetria: frame; x1; x2; chegou(2); ajuste(2); QTE do J1; QTE do J2 |
| `W` | `1W1;15719;16453;11;9;12` | **winner**: vencedor; tempos em ms; acertos de cada um; total de QTEs → `fase := RESULTADO` |
| `N` | `2N` / `1N` | pede / confirma revanche → `fase := PERSONALIZAÇÃO` |
| `X` | `2X` | saindo |

Detalhe do `T`: cada QTE vai como `ativo,tecla(1=W 2=A 3=S 4=D),tempo restante,acertos,feitos,feedback,tempo do feedback`.
Mensagens malformadas são descartadas (`ErroProtocolo`), e o `Leitor` remonta o fluxo TCP (um `recv()` pode trazer meia mensagem ou várias juntas).

**Variável de controle (a "vez" do enunciado):** `fase` existe nos **dois** processos — `0 PERSONALIZAÇÃO → 1 CONTAGEM → 2 CORRIDA → 3 RESULTADO → (N) → 0` —
e **só muda quando chega mensagem do servidor** (`S`, `G`, `W`, `N`).

**Exemplo real de uma partida (log do servidor):**
```
[  1.029] SERVIDOR RECEBIDO 2H1            cliente se apresenta
[  1.029] SERVIDOR ENVIADO  1H1            servidor responde
[  1.032] SERVIDOR ENVIADO  1R1            servidor já está pronto
[  1.537] SERVIDOR RECEBIDO 2R1            cliente ficou pronto
[  1.546] SERVIDOR ENVIADO  1S35;12        largada: fase 0 -> 1 (nos dois)
[  4.450] SERVIDOR ENVIADO  1G             fim da contagem: fase 1 -> 2
[  6.329] SERVIDOR RECEBIDO 2QD            jogador 2 acertou/apertou D
[ 20.408] SERVIDOR ENVIADO  1W1;15719;16453;11;9;12    jogador 1 venceu: fase 2 -> 3
```

## 5. Memória compartilhada

O estado da partida **não fica em variáveis soltas**: vive num bloco de **93 bytes** alocado uma vez (`SharedMemory(create=True, size=TAMANHO)`) com
layout binário fixo (`struct`): cabeçalho de 23 bytes (contador `seq`, `fase`, conexão, tamanho da pista, nº de QTEs, vencedor, placar, frame, tempos)
+ 35 bytes por jogador (posição, chegou, ajuste de velocidade, pronto, 16 índices de visual, estado do QTE, tempo final).
Todas as threads do processo leem/escrevem esse bloco: a simulação **publica** nele, a thread de telemetria **lê** para montar o `T`,
a thread de recepção do cliente **grava** o `T` recebido e a thread principal **lê** para desenhar.

## 6. Exclusão mútua

1. **Mutex** (`threading.Lock`) em `EstadoCompartilhado`: toda leitura e escrita do bloco acontece dentro de `with self.lock:` (região crítica). O método
   `modificar()` faz ler → alterar → gravar numa única região crítica (sem "perder" atualização). *Teste:* 4 threads fazem 2000 incrementos cada na mesma posição → resultado exato (8000).
2. **Trava de envio** (`send_lock`) em cada socket: o laço do jogo manda `G`/`W` enquanto a thread de telemetria manda `T`; sem a trava os bytes das mensagens se misturariam.
   *Teste:* 3 threads mandaram 900 mensagens ao mesmo tempo e todas chegaram íntegras.
3. **Seqlock** para outro **processo** (`monitor.py`), que não pode usar o mutex das nossas threads: `seq` é incrementado antes (ímpar = escrevendo) e depois (par = consistente)
   de cada escrita; o leitor só aceita a cópia se `seq` era par e não mudou. *Teste:* um processo lê 300 vezes enquanto uma thread escreve e a invariante `x1 == x2` nunca quebra.

Além disso, o servidor é a **única autoridade** sobre a corrida: as teclas do jogador 2 entram numa fila protegida pelo mutex e são consumidas pela simulação, na ordem.

## 7. Gerenciamento de memória

- Bloco compartilhado de **tamanho fixo** (93 bytes), criado uma vez e **liberado** ao sair (`close()` + `unlink()`); o `monitor.py` mostra o bloco sumindo quando o jogo fecha.
- Buffer de recepção fixo (`RECV_BUF = 1024`), `Leitor` com limite de 512 bytes (lixo sem `\n` é descartado), fila de entradas com tamanho máximo (`deque(maxlen=64)`).
- Caches de sprites e de textos com **limite** (são esvaziados ao passar do limite); nada cresce sem controle durante a partida.
- Mensagens pequenas, de tamanho máximo conhecido (`MAX_LINHA = 512`).

## 8. Respostas prontas para o formulário

- **Nome do jogo:** Corrida de Cavalos — Duelo 1x1 em rede.
- **Explicação:** corrida de cavalos de pista longa para dois jogadores em processos separados; cada um personaliza o seu cavalo e o seu corredor, e durante a prova responde QTEs (W/A/S/D) que dão ou tiram velocidade.
  Os cavalos têm atributos iguais, então vence quem acerta mais QTEs. O servidor simula a corrida e o cliente recebe o estado.
- **Linguagem:** Python 3.13 (`socket`, `threading`, `multiprocessing.shared_memory`, `struct`) com `pygame` para a interface.
- **Como e quais informações são trocadas:** por socket TCP (porta 51171), mensagens de texto `<origem><tipo><carga>\n`: apresentação (`H`), aparência escolhida (`V`), pronto (`R`),
  largada (`S`) e fim da contagem (`G`) enviados pelo servidor, tecla do QTE do jogador 2 (`Q`), telemetria com posições e QTEs a 30 Hz (`T`), resultado (`W`) e revanche/saída (`N`, `X`).
  A variável `fase` existe nos dois processos e só muda por mensagens do servidor. O estado fica num bloco de memória compartilhada de 93 bytes em cada processo.
- **Exclusão mútua:** mutex (`threading.Lock`) em toda leitura/escrita do bloco compartilhado (leitura-modificação-gravação numa região crítica única), trava de envio por socket, seqlock para leitura por outro processo,
  e servidor como única autoridade sobre a simulação (as teclas do jogador 2 entram numa fila protegida e são consumidas pela simulação).

## 9. Roteiro sugerido para o vídeo (1 min)

1. (0–10 s) Três janelas lado a lado: servidor, cliente e o terminal do `monitor.py`. Mostrar o log de mensagens no terminal do servidor.
2. (10–20 s) Cada jogador personaliza e o outro vê mudar ao vivo (`V`); os dois ficam prontos (`R`) → `S`, contagem, `G`.
3. (20–45 s) Corrida: cada jogador no seu teclado; apontar o log (`Q`, `T`) e o monitor mostrando `seq` subindo e as posições.
4. (45–60 s) Resultado (`W`), placar, revanche (`N`), e dizer em uma frase onde está o mutex.

## 10. Executáveis e testes

- **Sem executável:** zipar esta pasta (sem `__pycache__`). **Com executável:** rodar `gerar_exe.bat` no Windows (usa PyInstaller) e zipar junto a pasta `dist/`.
- Testes: `py -3.13 testes/test_protocolo.py`, `testes/test_estado.py`, `testes/test_simulacao.py` e `testes/test_integracao.py`
  (sobe servidor e cliente como processos separados, jogam 2 corridas e conferem que os dois chegam ao **mesmo resultado**).

## 11. Limitações

Um cliente por vez; sem criptografia; sem reconexão no meio da corrida (se alguém cair, o servidor volta ao início e espera outro jogador).
