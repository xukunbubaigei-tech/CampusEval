import json
import unittest
from pathlib import Path
from CampusEval.scripts.curation.training.repair_training import curate, conic_answer

ROOT=Path(__file__).resolve().parents[2]


class TrainingCurationTests(unittest.TestCase):

    def test_pm_is_not_printed_as_infix_addition(self):
        self.assertEqual(conic_answer('(3, pm*2*sqrt(3))'),r'$(3, \pm 2 \sqrt{3})$')
        self.assertIn(r'\pm ',conic_answer('y=pm*(4/3)*x'))
        self.assertNotIn('PM',conic_answer('y=pm*x'))

    def test_parser_rejects_executable_calls(self):
        with self.assertRaises(ValueError):conic_answer('__import__("os")')

    def test_curation_preserves_full_solutions_when_repeated(self):
        changes=json.loads((ROOT/'scripts/curation/training/overrides.json').read_text(encoding='utf-8'))
        rows=[json.loads(l) for l in (ROOT/'datasets/main/training.jsonl').read_text(encoding='utf-8').splitlines()]
        self.assertTrue(rows)
        for row in rows:
            first=curate(row,changes)
            self.assertEqual(curate(first,changes),first,row['id'])

    def test_worked_answer_is_retained_as_solution(self):
        record={'id':'example','source':'gaokao','question':{'text':'题目','images':[],'options':[]},
                'answer':{'final_answer':'完整推导，故答案为$2$。','solution':'解题思路'},
                'metadata':{'question_type':'解答题','paper_name':'示例'}}
        result=curate(record,{'example':{'answer.final_answer':'$2$'}})
        self.assertEqual(result['answer']['solution'],record['answer']['final_answer'])
        self.assertEqual(result['answer']['final_answer'],'$2$')


if __name__=='__main__':unittest.main()
