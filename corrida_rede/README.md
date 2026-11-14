# 🏇 Corrida de Cavalos — Duelo 1x1 em Rede

Jogo de corrida para dois participantes, desenvolvido em Python como projeto acadêmico da disciplina **Sistemas Operacionais**. Os jogadores personalizam seus cavalos e disputam uma corrida em tempo real: durante a prova, precisam responder a comandos rápidos (QTEs) para ganhar velocidade.

> **Trabalho 02 — Sistemas Operacionais**  
> Professor: Maurilio Campano Jr.  
> **Desenvolvedores:** Murilo Andreotti Borges e Matheus Marçal Martinelli

---

## 🎮 Sobre o jogo

- **Dois jogadores simultâneos:** um atua como servidor e o outro como cliente.
- **Partida em rede:** comunicação entre processos por sockets TCP.
- **Personalização:** cada participante escolhe a aparência do próprio cavalo e corredor.
- **Desafios QTE:** durante a corrida, teclas são solicitadas para cada jogador. Acertos influenciam o ritmo do cavalo.
- **Acompanhamento em tempo real:** a posição dos cavalos e os eventos da partida são sincronizados entre os jogadores.
- **Revanche:** ao final da corrida, os participantes podem iniciar uma nova disputa.

Os dois cavalos começam com os mesmos atributos. O desempenho nos QTEs influencia o resultado da corrida.

## 🖥️ Tecnologias e conceitos

| Tecnologia / recurso | Utilização |
|---|---|
| **Python 3.13** | Linguagem principal |
| **Pygame** | Interface gráfica e entrada do teclado |
| **Socket TCP** | Comunicação entre servidor e cliente |
| **Threading** | Execução concorrente de tarefas |
| **Shared Memory** | Compartilhamento do estado entre threads/processos |
| **Struct** | Organização do estado em memória binária |
| **Mutex (threading.Lock)** | Proteção de regiões críticas |
| **Seqlock** | Leitura consistente da memória pelo processo monitor |

## ⚙️ Como executar

### 1. Pré-requisitos

- Windows (os arquivos auxiliares .bat foram preparados para esse ambiente).
- Python **3.13** instalado e disponível pelo comando py.
- Conexão de rede entre os computadores, caso os jogadores estejam em máquinas diferentes.

### 2. Instalar a dependência

Abra o terminal dentro da pasta corrida_rede e execute:

    py -3.13 -m pip install -r requirements.txt

### 3. Iniciar a partida

**No computador do Jogador 1 — servidor:**

    py -3.13 servidor.py

O servidor abre o jogo e aguarda a conexão do segundo participante. Ele informa o IP que o cliente deverá utilizar.

**No computador do Jogador 2 — cliente:**

    py -3.13 cliente.py

Na tela de conexão, informe o IP exibido pelo servidor.

Se os dois jogadores estiverem no mesmo computador, utilize **127.0.0.1**.

> **Atenção:** em computadores diferentes, ambos precisam estar na mesma rede ou ter conectividade entre si. O firewall do Windows pode solicitar autorização para o Python; permita o acesso em redes privadas. A porta padrão utilizada pelo jogo é **51171**.

### Atalhos no Windows

Também é possível iniciar os participantes pelos arquivos:

- **jogar_servidor.bat** — inicia o servidor.
- **jogar_cliente.bat** — inicia o cliente.
- **monitor.bat** — inicia o monitor de memória compartilhada.

## 🕹️ Controles

| Tecla | Ação |
|---|---|
| W / S ou setas ↑ / ↓ | Navegar pelas opções de personalização |
| A / D ou setas ← / → | Alterar a opção selecionada |
| F ou ENTER | Confirmar / ficar pronto |
| W, A, S, D ou setas | Responder aos QTEs durante a corrida |
| ESPAÇO | Solicitar revanche |
| ESC | Sair |

## 🧩 Arquitetura do projeto

A aplicação é dividida em dois processos independentes:

- **Servidor:** aceita a conexão, coordena a partida, executa a simulação e determina o vencedor.
- **Cliente:** envia as ações do segundo jogador e recebe as atualizações da partida.

O servidor é a autoridade da simulação. Dessa forma, os dois participantes recebem o mesmo resultado, evitando que cada computador calcule uma corrida diferente.

### Fluxo simplificado

    JOGADOR 1                         JOGADOR 2
     SERVIDOR                          CLIENTE
        |                                 |
        | <------ conexão TCP ----------> |
        |                                 |
        | <---- personalização/pronto --> |
        |                                 |
        | -------- início da corrida ---->|
        |                                 |
        | <------- teclas QTE ------------|
        |                                 |
        | ------ estado/telemetria ------>|
        |                                 |
        | -------- resultado ------------>|
        |                                 |
        | <--------- revanche ----------->|

### Organização dos arquivos

| Arquivo / pasta | Responsabilidade |
|---|---|
| **servidor.py** | Inicialização e regras do processo servidor |
| **cliente.py** | Inicialização e comportamento do processo cliente |
| **app.py** | Laço principal do jogo, entrada e atualização da interface |
| **rede.py** | Sockets TCP, envio e recepção de mensagens |
| **protocolo.py** | Formatação, validação e interpretação das mensagens |
| **estado.py** | Estado compartilhado, mutex e leitura consistente |
| **simulacao.py** | Regras da corrida e funcionamento dos QTEs |
| **telas.py** e **grafico.py** | Elementos visuais e renderização |
| **monitor.py** | Processo auxiliar para observar a memória compartilhada |
| **testes/** | Testes unitários e de integração |

## 🧵 Concorrência e gerenciamento de memória

O projeto aplica conceitos estudados em Sistemas Operacionais:

1. **Threads:** tarefas de recepção de mensagens, telemetria e execução principal funcionam concorrentemente.
2. **Exclusão mútua:** um mutex protege as operações de leitura e escrita do estado compartilhado, evitando condições de corrida.
3. **Sincronização de envio:** uma trava por conexão evita que mensagens enviadas por threads diferentes se misturem.
4. **Memória compartilhada:** cada processo utiliza um bloco de tamanho fixo de **93 bytes** para armazenar o estado da partida.
5. **Seqlock:** permite que o processo monitor consulte o estado compartilhado e verifique se a leitura ocorreu durante uma atualização.
6. **Limites de memória:** buffers, filas e caches possuem limites definidos para evitar crescimento descontrolado.

O bloco de memória é fechado e liberado ao encerrar o processo.

## 🧪 Executar os testes

Na pasta corrida_rede, execute:

    py -3.13 -m unittest discover -s testes -v

A suíte cobre os módulos de estado, protocolo e simulação, além de um teste de integração que executa servidor e cliente como processos separados e verifica o resultado de duas corridas.

## 📁 Estrutura resumida

    corrida_rede/
    ├── app.py
    ├── cliente.py
    ├── servidor.py
    ├── estado.py
    ├── rede.py
    ├── protocolo.py
    ├── simulacao.py
    ├── grafico.py
    ├── telas.py
    ├── monitor.py
    ├── requirements.txt
    ├── jogar_cliente.bat
    ├── jogar_servidor.bat
    ├── monitor.bat
    └── testes/
        ├── test_estado.py
        ├── test_integracao.py
        ├── test_protocolo.py
        └── test_simulacao.py

## ⚠️ Limitações conhecidas

- A aplicação foi projetada para uma partida com **um servidor e um cliente**.
- A comunicação não utiliza criptografia.
- Não há reconexão automática para retomar uma corrida interrompida por queda de conexão.

---

**Projeto acadêmico desenvolvido para praticar comunicação em rede, programação concorrente, sincronização e gerenciamento de memória com Python.**
