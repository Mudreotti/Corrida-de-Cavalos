# Autores: Murilo Andreotti Borges (RA 25163806-2) e Matheus Marçal Martinelli (RA 25076306-2)
# Sistemas Operacionais - Trabalho 02: jogo com troca de mensagens e gerenciamento de memória
# Prof. Maurilio Campano Jr - Corrida de Cavalos: Duelo 1x1 em rede
"""Teste de integração: sobe o SERVIDOR e o CLIENTE como processos separados (bots) e confere
que os dois chegam ao mesmo resultado trocando mensagens pelo socket."""
import ast, os, re, subprocess, sys, time, unittest

RAIZ = os.path.join(os.path.dirname(__file__), "..")
ENV = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", PYTHONUNBUFFERED="1")
PORTA = "52311"


def rodar(args, **kw):
    return subprocess.Popen([sys.executable] + args, cwd=RAIZ, env=ENV, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, **kw)


def resultados(saida, prefixo):
    return [ast.literal_eval(l.split(":", 1)[1].strip()) for l in saida.splitlines() if l.startswith(prefixo)]


class TestIntegracao(unittest.TestCase):
    def test_duas_corridas_completas(self):
        srv = rodar(["servidor.py", "--porta", PORTA, "--bot", "--rodadas", "2", "--acerto", "0.9"])
        time.sleep(1.0)
        cli = rodar(["cliente.py", "--host", "127.0.0.1", "--porta", PORTA, "--bot", "--rodadas", "2", "--acerto", "0.9"])
        try:
            so, _ = srv.communicate(timeout=240)
            co, _ = cli.communicate(timeout=60)
        finally:
            for p in (srv, cli):
                if p.poll() is None:
                    p.kill()
        r_srv, r_cli = resultados(so, "RESULTADO servidor"), resultados(co, "RESULTADO cliente")
        print("\n--- trecho do log do servidor ---")
        print("\n".join(l for l in so.splitlines() if "SERVIDOR" in l and " T x" not in l)[:1800])
        self.assertEqual(len(r_srv), 2, so[-1500:])
        self.assertEqual(len(r_cli), 2, co[-1500:])
        # os dois processos TÊM que ter o mesmo resultado (vencedor, tempos, QTEs, placar)
        for a, b in zip(r_srv, r_cli):
            self.assertEqual(a, b, f"servidor {a} != cliente {b}")
        self.assertEqual(srv.returncode, 0, so[-800:])
        self.assertEqual(cli.returncode, 0, co[-800:])
        for linha in ("1S35;12", "1G", "1W"):
            self.assertIn(linha, so)
        self.assertRegex(so, r"RECEBIDO 2QW|RECEBIDO 2QA|RECEBIDO 2QS|RECEBIDO 2QD")


if __name__ == "__main__":
    unittest.main(verbosity=2)
