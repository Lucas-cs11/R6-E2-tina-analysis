"""Regression checks for TINA 4.0.0 reachability evidence."""
import unittest

from tina_batch import classify


def output(label, counts='', completed=True):
    return ('Tina version 4.0.0 -- 07/04/26 -- LAAS/CNRS\n\nmode -R\n\n'
            'REACHABILITY ANALYSIS -------- \n\n' + label + '\n' + counts +
            '\nLIVENESS ANALYSIS -------- \n' +
            ('\nANALYSIS COMPLETED -------- \n' if completed else ''))


class VerdictTest(unittest.TestCase):
    def test_bounded(self):
        self.assertEqual(classify(0, output('bounded', '2 marking(s), 1 transition(s)\n'), ''), 'BOUNDED')

    def test_unbounded_is_not_bounded(self):
        self.assertEqual(classify(0, output('net unbounded'), ''), 'UNBOUNDED')

    def test_incomplete(self):
        self.assertEqual(classify(0, output('bounded', completed=False), ''), 'INDETERMINATE')

    def test_conflicting(self):
        self.assertEqual(classify(0, output('bounded\nnet unbounded'), ''), 'INDETERMINATE')

    def test_nonzero_and_stderr(self):
        for rc, stderr in [(1, ''), (0, 'parser error')]:
            with self.subTest(rc=rc, stderr=stderr):
                self.assertEqual(classify(rc, output('net unbounded'), stderr), 'TOOL_ERROR')

    def test_bare_word(self):
        self.assertEqual(classify(0, 'bounded', ''), 'INDETERMINATE')


if __name__ == '__main__':
    unittest.main()
