import unittest
from ravel.core import Outcome, evaluate, wilson_upper

class TestPolicy(unittest.TestCase):
    def setUp(self):
        self.seed = Outcome('seed',70,100,0,100,1500,1200,True)
    def test_security(self):
        c=Outcome('unsafe',90,100,0,100,1500,1200,False)
        self.assertEqual(evaluate(self.seed,c)[1],'security_gate')
    def test_cost(self):
        c=Outcome('costly',90,100,0,100,5000,1200,True)
        self.assertEqual(evaluate(self.seed,c)[1],'token_budget')
    def test_regressions(self):
        c=Outcome('regressive',90,100,12,100,2000,1500,True)
        self.assertEqual(evaluate(self.seed,c)[1],'regression_confidence_gate')
    def test_accept(self):
        c=Outcome('balanced',78,100,0,100,2200,1750,True)
        self.assertTrue(evaluate(self.seed,c)[0])
    def test_zero_trials(self):
        self.assertEqual(wilson_upper(0,0),1.0)

if __name__=='__main__': unittest.main()
