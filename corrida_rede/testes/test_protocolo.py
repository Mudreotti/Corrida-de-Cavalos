# Autores: Murilo Andreotti Borges (RA 25163806-2) e Matheus Marçal Martinelli (RA 25076306-2)
# Sistemas Operacionais - Trabalho 02: jogo com troca de mensagens e gerenciamento de memória
# Prof. Maurilio Campano Jr - Corrida de Cavalos: Duelo 1x1 em rede
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import protocolo as p


class TestProtocolo(unittest.TestCase):
    def ida_e_volta(self, dados):
        msg, val = p.decodificar(dados.decode().rstrip("\n"))
        return msg, val

    def test_hello(self):
        m, v = self.ida_e_volta(p.msg_hello(p.CLIENTE))
        self.assertEqual((m.origem, m.tipo, v), (2, "H", p.VERSAO))

    def test_visual(self):
        idx = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 0, 1, 2, 3, 4]
        m, v = self.ida_e_volta(p.msg_visual(p.SERVIDOR, idx))
        self.assertEqual(v, idx)

    def test_pronto_start_go(self):
        self.assertTrue(self.ida_e_volta(p.msg_pronto(2, True))[1])
        self.assertFalse(self.ida_e_volta(p.msg_pronto(2, False))[1])
        self.assertEqual(self.ida_e_volta(p.msg_start(3.5, 12))[1], (3.5, 12))
        self.assertEqual(self.ida_e_volta(p.msg_go())[0].tipo, "G")

    def test_qte(self):
        for t in "WASD":
            self.assertEqual(self.ida_e_volta(p.msg_qte(t))[1], t)
        with self.assertRaises(p.ErroProtocolo):
            p.decodificar("2QZ")

    def test_telemetria(self):
        q = [(1, 2, 40, 5, 6, 0, 0), (0, 0, 0, 4, 5, 1, 60)]
        dados = p.msg_telemetria(412, [81234, 80990], [False, True], [1, -1], q)
        m, v = self.ida_e_volta(dados)
        self.assertEqual(v.frame, 412)
        self.assertEqual(v.x, [81234, 80990])
        self.assertEqual(v.terminou, [False, True])
        self.assertEqual(v.ajuste, [1, -1])
        self.assertEqual(v.qte, q)

    def test_winner(self):
        m, v = self.ida_e_volta(p.msg_winner(1, [14962, 14947], [11, 11], 12))
        self.assertEqual(v, p.Resultado(1, [14962, 14947], [11, 11], 12))

    def test_mensagens_invalidas(self):
        for lixo in ["", "3H1", "1Z", "2V12", "1T1;2", "1S35", "2R9", "1Wabc", "x"]:
            with self.assertRaises(p.ErroProtocolo, msg=lixo):
                p.decodificar(lixo)

    def test_leitor_fragmentos_e_juntos(self):
        l = p.Leitor()
        self.assertEqual(l.alimentar(b"2R"), [])            # meia mensagem
        self.assertEqual(l.alimentar(b"1\n2QW\n1"), ["2R1", "2QW"])   # fim da 1ª + 2ª inteira + começo da 3ª
        self.assertEqual(l.alimentar(b"G\n"), ["1G"])

    def test_leitor_descarta_lixo_sem_quebra(self):
        l = p.Leitor()
        l.alimentar(b"x" * (p.MAX_LINHA + 10))
        self.assertEqual(len(l.buf), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
