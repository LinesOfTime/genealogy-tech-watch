from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from correct_openrefine import correction


class OpenRefineTests(unittest.TestCase):
    def test_narrow_preserving_idempotent_correction(self):
        old='Очистка, кластеризация и согласование таблиц | Часть 51: незакрытые поля: первоисточник'
        c=[dict(name='OpenRefine/OpenRefine',description='Программа',use_case='',limitations=old,priority='P2')]
        r={'openrefine/openrefine':dict(project_type='Программа',audit_notes=old,editorial_use_case='',guide_excerpt='Назначение: Программа')}
        new_c,new_r=correction(c,r)
        self.assertEqual(c[0]['use_case'],'')
        self.assertEqual(new_r['openrefine/openrefine']['project_type'],'Программа')
        self.assertEqual(new_r['openrefine/openrefine']['audit_notes'],old)
        self.assertEqual(new_r['openrefine/openrefine']['guide_excerpt'],'Назначение: Программа')
        self.assertEqual(new_c[0]['editorial_corrections'][0]['previous_catalog']['limitations'],old)
        self.assertEqual(new_c[0]['priority'],'P2')
        self.assertIn('независимо не испытывался',new_c[0]['use_case'])
        self.assertEqual((new_c,new_r),correction(new_c,new_r))


if __name__=='__main__':unittest.main()
