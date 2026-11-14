
# Autores: Murilo Andreotti Borges (RA 25163806-2) e Matheus Marçal Martinelli (RA 25076306-2)
# Sistemas Operacionais - Trabalho 02: jogo com troca de mensagens e gerenciamento de memória
# Prof. Maurilio Campano Jr - Corrida de Cavalos: Duelo 1x1 em rede

"""Teste de integração: executa servidor e cliente como processos separados.

Em caso de timeout, encerra os processos e preserva/imprime os logs capturados,
para que a falha de comunicação possa ser diagnosticada sem perder a saída.
"""

import ast
import os
import subprocess
import sys
import time
import unittest
from concurrent.futures import ThreadPoolExecutor

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENV = dict(
    os.environ,
    SDL_VIDEODRIVER="dummy",
    SDL_AUDIODRIVER="dummy",
    PYTHONUNBUFFERED="1",
)
PORTA = "52311"
TEMPO_LIMITE = 240


def rodar(args):
    return subprocess.Popen(
        [sys.executable] + args,
        cwd=RAIZ,
        env=ENV,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )


def coletar_saida(processo):
    """Aguarda o processo; em timeout, mata-o e ainda coleta o log restante."""
    try:
        saida, _ = processo.communicate(timeout=TEMPO_LIMITE)
        return saida, False
    except subprocess.TimeoutExpired:
        processo.kill()
        saida, _ = processo.communicate()
        return saida, True


def resultados(saida, prefixo):
    encontrados = []
    for linha in saida.splitlines():
        if linha.startswith(prefixo):
            try:
                encontrados.append(ast.literal_eval(linha.split(":", 1)[1].strip()))
            except (ValueError, SyntaxError):
                pass
    return encontrados


class TestIntegracao(unittest.TestCase):
    def test_duas_corridas_completas(self):
        srv = rodar([
            "servidor.py", "--porta", PORTA, "--bot",
            "--rodadas", "2", "--acerto", "0.9"
        ])
        cli = None
        so = co = ""
        timeout_srv = timeout_cli = False

        try:
            time.sleep(1.0)
            cli = rodar([
                "cliente.py", "--host", "127.0.0.1",
                "--porta", PORTA, "--bot",
                "--rodadas", "2", "--acerto", "0.9"
            ])

            # Os dois pipes são drenados simultaneamente para evitar bloqueio.
            with ThreadPoolExecutor(max_workers=2) as executor:
                futuro_srv = executor.submit(coletar_saida, srv)
                futuro_cli = executor.submit(coletar_saida, cli)
                so, timeout_srv = futuro_srv.result(timeout=TEMPO_LIMITE + 10)
                co, timeout_cli = futuro_cli.result(timeout=TEMPO_LIMITE + 10)

        finally:
            for processo in (srv, cli):
                if processo is not None and processo.poll() is None:
                    processo.kill()
                    processo.wait()

        r_srv = resultados(so, "RESULTADO servidor")
        r_cli = resultados(co, "RESULTADO cliente")

        print("\n========== LOG COMPLETO FINAL DO SERVIDOR ==========")
        print(so[-12000:])
        print("\n========== LOG COMPLETO FINAL DO CLIENTE ==========")
        print(co[-12000:])
        print("\n========== INFORMAÇÕES DOS PROCESSOS ==========")
        print("Timeout do servidor:", timeout_srv)
        print("Timeout do cliente:", timeout_cli)
        print("Código de saída do servidor:", srv.returncode)
        print("Código de saída do cliente:", cli.returncode if cli else "não iniciado")
        print("Resultados do servidor:", r_srv)
        print("Resultados do cliente:", r_cli)

        self.assertFalse(
            timeout_srv or timeout_cli,
            "Um dos processos excedeu o limite de tempo. Consulte os logs completos acima."
        )
        self.assertEqual(
            len(r_srv), 2,
            f"Esperados 2 resultados no servidor; encontrados {len(r_srv)}.\n{so[-12000:]}"
        )
        self.assertEqual(
            len(r_cli), 2,
            f"Esperados 2 resultados no cliente; encontrados {len(r_cli)}.\n{co[-12000:]}"
        )

        for numero, (resultado_srv, resultado_cli) in enumerate(
            zip(r_srv, r_cli), start=1
        ):
            self.assertEqual(
                resultado_srv,
                resultado_cli,
                f"Resultado da corrida {numero} divergiu entre servidor e cliente."
            )

        self.assertEqual(srv.returncode, 0, so[-1500:])
        self.assertEqual(cli.returncode, 0, co[-1500:])
        self.assertIn("1G", so)
        self.assertIn("1W", so)
        self.assertGreaterEqual(so.count("ENVIADO  1N"), 1, so[-4000:])
        self.assertGreaterEqual(so.count("ENVIADO  1S35;12"), 2, so[-4000:])
        self.assertGreaterEqual(co.count("RECEBIDO 1W"), 2, co[-4000:])
        self.assertRegex(
            so,
            r"RECEBIDO 2QW|RECEBIDO 2QA|RECEBIDO 2QS|RECEBIDO 2QD"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
