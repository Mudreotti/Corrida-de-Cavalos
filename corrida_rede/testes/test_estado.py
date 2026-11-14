# Autores: Murilo Andreotti Borges (RA 25163806-2) e Matheus Marçal Martinelli (RA 25076306-2)
# Sistemas Operacionais - Trabalho 02: jogo com troca de mensagens e gerenciamento de memória
# Prof. Maurilio Campano Jr - Corrida de Cavalos: Duelo 1x1 em rede
import os, subprocess, sys, threading, time, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import estado as E


class TestEstado(unittest.TestCase):
    def setUp(self):
        self.est = E.EstadoCompartilhado("teste_estado_%d" % os.getpid())

    def tearDown(self):
        self.est.fechar()

    def test_layout_tamanho_fixo(self):
        self.assertEqual(E.TAMANHO, E.CABECALHO.size + 2 * E.JOGADOR.size)
        self.assertEqual(self.est.shm.size >= E.TAMANHO, True)

    def test_ida_e_volta(self):
        self.est.set(fase=2, frame=-90, placar1=3)
        self.est.set_jogador(1, x=123456, pronto=1, indices=list(range(16)), qte_tecla=4, qte_tempo=-7)
        d = self.est.ler()
        self.assertEqual((d["fase"], d["frame"], d["placar1"]), (2, -90, 3))
        self.assertEqual(d["j"][1]["x"], 123456)
        self.assertEqual(d["j"][1]["indices"], list(range(16)))
        self.assertEqual(d["j"][1]["qte_tempo"], -7)
        self.assertEqual(d["seq"] % 2, 0)

    def test_exclusao_mutua_duas_threads(self):
        """4 threads fazem 2000 incrementos cada na MESMA posição de memória: sem a trava, perderia contagem."""
        N = 2000

        def trabalhador():
            for _ in range(N):
                self.est.modificar(lambda d: d.__setitem__("t1_ms", d["t1_ms"] + 1))
        ts = [threading.Thread(target=trabalhador) for _ in range(4)]
        [t.start() for t in ts]
        [t.join() for t in ts]
        self.assertEqual(self.est.ler()["t1_ms"], 4 * N)

    def test_leitura_externa_consistente(self):
        """Outro PROCESSO lê enquanto uma thread escreve; invariante: x1 == x2 sempre."""
        parar = threading.Event()

        def escritor():
            v = 0
            while not parar.is_set():
                v += 1
                def f(d, v=v):
                    d["j"][0]["x"] = v
                    d["j"][1]["x"] = v
                self.est.modificar(f)
        t = threading.Thread(target=escritor); t.start()
        codigo = (
            "import sys; sys.path.insert(0, %r); import estado as E\n"
            "ruins = 0\n"
            "for _ in range(300):\n"
            "    d = E.ler_externo(%r)\n"
            "    ruins += d['j'][0]['x'] != d['j'][1]['x']\n"
            "print(ruins)\n" % (os.path.join(os.path.dirname(__file__), ".."), self.est.nome))
        saida = subprocess.run([sys.executable, "-c", codigo], capture_output=True, text=True, timeout=60)
        parar.set(); t.join()
        self.assertEqual(saida.stdout.strip().splitlines()[-1], "0", saida.stderr)

    def test_fila_de_entradas_limitada(self):
        for i in range(500):
            self.est.empilhar_entrada(2, "W")
        self.assertEqual(len(self.est.retirar_entradas()), E.EstadoCompartilhado.MAX_ENTRADAS)
        self.assertEqual(self.est.retirar_entradas(), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
