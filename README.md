# Corrida de Cavalos

Projeto acadêmico desenvolvido em **Python** para a disciplina de **Sistemas Operacionais**. O jogo propõe uma corrida multiplayer entre dois jogadores, com comunicação por rede e simulação controlada pelo servidor.

## Tecnologias e conceitos

- Python 3.13
- Pygame
- Sockets TCP para comunicação cliente-servidor
- Threads para operações concorrentes
- Memória compartilhada com `multiprocessing.shared_memory`
- Sincronização com locks e mecanismo seqlock
- Protocolo próprio para troca de mensagens

## Como funciona

O servidor controla a partida e a simulação. O cliente se conecta ao servidor, envia comandos do jogador e recebe atualizações do estado da corrida. A comunicação utiliza TCP e um protocolo próprio que trata mensagens recebidas de forma fragmentada ou agrupada.

Durante a partida, os jogadores participam de desafios de comandos (QTE) para influenciar o desempenho dos cavalos. O projeto também inclui telas de preparação, contagem regressiva, resultado e possibilidade de revanche.

## Estrutura do projeto

Os módulos estão separados por responsabilidade: interface e telas, comunicação em rede, protocolo, estado da partida, simulação, gráficos e monitoramento. A pasta `testes/` reúne testes automatizados para estado, integração, protocolo e simulação.

## Como executar

> As instruções abaixo pressupõem que os arquivos-fonte do projeto estejam presentes neste repositório.

1. Instale o Python 3.13.
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Inicie o servidor pelo script `jogar_servidor.bat`.
4. Inicie o cliente pelo script `jogar_cliente.bat`.

Para executar os dois jogadores em computadores diferentes, ambos precisam conseguir alcançar o computador que está hospedando o servidor. A configuração de rede e do firewall deve ser feita antes da partida.

## Testes

Os testes automatizados estão na pasta `testes/`. Com as dependências instaladas, podem ser executados com:

```bash
python -m unittest discover -s testes -v
```

## Integrantes

- Murilo Andreotti Borges
- Matheus Marçal Martinelli

## Observações

Este projeto está em desenvolvimento. A versão atual documenta uma partida com um cliente conectado ao servidor. Não há criptografia nem reconexão automática durante uma corrida.
