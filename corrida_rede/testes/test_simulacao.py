# Autores: Murilo Andreotti Borges (RA 25163806-2) e Matheus Marçal Martinelli (RA 25076306-2)
# Sistemas Operacionais - Trabalho 02: jogo com troca de mensagens e gerenciamento de memória
# Prof. Maurilio Campano Jr - Corrida de Cavalos: Duelo 1x1 em rede
import os, random, sys, unittest
os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import simulacao as S, estado as E


def jogar(taxa=(0.9, 0.9), semente=None):
    if semente is not None:
        random.seed(semente)
    c = S.Corrida(); c.iniciar()
    ultimo = [None, None]; guarda = 0
    while not c.terminou and guarda < 30000:
        c.tick(); guarda += 1
        for i in (0, 1):
            q = c.qte[i]
            if q["ativo"] and ultimo[i] != q["proximo"]:
                ultimo[i] = q["proximo"]
                if random.random() < taxa[i]:
                    c.registrar_tecla(i, q["tecla"])
    return c


class TestSimulacao(unittest.TestCase):
    def test_corrida_termina_e_define_vencedor(self):
        c = jogar(semente=1)
        self.assertTrue(c.terminou)
        self.assertIn(c.vencedor, (1, 2))
        self.assertGreater(min(x.tempo_final for x in c.cavs), 8.0)       # prova longa

    def test_atributos_iguais(self):
        c = S.Corrida()
        a, b = c.cavs
        self.assertEqual((a.velocidade, a.resistencia, a.sorte), (b.velocidade, b.resistencia, b.sorte))

    def test_equilibrio(self):
        vit = [0, 0]
        for n in range(60):
            vit[jogar(semente=100 + n).vencedor - 1] += 1
        self.assertGreater(min(vit), 15, vit)        # com o mesmo desempenho, ninguém domina

    def test_quem_acerta_mais_ganha(self):
        vit = [0, 0]
        for n in range(30):
            vit[jogar((1.0, 0.4), semente=300 + n).vencedor - 1] += 1
        self.assertGreater(vit[0], vit[1] * 3, vit)

    def test_tecla_errada_e_ignorada_sem_qte(self):
        c = S.Corrida(); c.iniciar()
        for _ in range(200): c.tick()
        c.registrar_tecla(0, "W")                    # sem QTE ativo: nada acontece
        self.assertEqual(c.qte[0]["feitos"], 0)

    def test_publicacao_na_memoria_compartilhada(self):
        est = E.EstadoCompartilhado("teste_sim_%d" % os.getpid())
        try:
            c = jogar(semente=5)
            est.modificar(c.publicar_em)
            d = est.ler()
            self.assertEqual(d["vencedor"], c.vencedor)
            self.assertEqual(d["j"][0]["x"], int(round(c.cavs[0].x * 100)))
            self.assertEqual(d["j"][0]["qte_acertos"] + d["j"][1]["qte_acertos"],
                             c.qte[0]["acertos"] + c.qte[1]["acertos"])
        finally:
            est.fechar()


if __name__ == "__main__":
    unittest.main(verbosity=2)
