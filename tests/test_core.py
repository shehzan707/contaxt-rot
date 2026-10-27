import unittest,tempfile,json
from pathlib import Path
from src.core import *
from src.data import load_hotpot,allocate,donor_candidates
from src.context import construct_pair
from src.analyze import score,compare,select_policy
from src.methods import prompt
from src.infer import load
class Tests(unittest.TestCase):
 def fixture(self,i=0):return {'_id':str(i),'question':'Where?','answer':'Paris','type':'bridge','supporting_facts':[[str(i),0]],'context':[[str(i),['Paris '+str(i)]]]}
 def test_conditions(self):
  self.assertEqual(len(CONDITIONS),8);self.assertEqual([c['id'] for c in CONDITIONS if c['selection']=='development'],['C1','C4','C6','C7'])
 def test_scoring(self):
  self.assertEqual(answer_metrics('The Paris!','Paris'),(1,1.));self.assertEqual(answer_metrics('yes indeed','yes'),(0,0.));self.assertAlmostEqual(answer_metrics('red green','red blue')[1],.5)
 def test_schema(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'x.json';p.write_text(json.dumps([self.fixture()]));self.assertEqual(len(load_hotpot(p)),1)
   r=self.fixture();r['supporting_facts']=[['missing',0]];p.write_text(json.dumps([r]));self.assertRaises(ValueError,load_hotpot,p)
 def test_split(self):
  splits,_=allocate([self.fixture(i) for i in range(8)],{'dev':{'bridge':2},'test':{'bridge':3}})
  self.assertTrue(validate_splits(splits));self.assertEqual(len(splits['test']),3)
 def test_leak(self):self.assertRaises(ValueError,validate_splits,{'dev':[self.fixture()],'test':[self.fixture()]})
 def test_bm25(self):self.assertGreater(bm25('capital',['capital city','ocean waves'])[0],bm25('capital',['capital city','ocean waves'])[1])
 def test_budget(self):self.assertLessEqual(len(' '.join(x['text'] for x in pack('city',[{'text':'city one'},{'text':'city two'}],2,lambda x:len(x.split()))).split()),2)
 def test_position(self):
  r=place_evidence(['x']*98,'gold gold',100,'end',lambda x:len(x.split()));self.assertAlmostEqual(r['midpoint'],.9);self.assertIn('gold gold',r['text'])
 def test_position_failure(self):self.assertRaises(ValueError,place_evidence,['x'],'gold',100,'end',lambda x:len(x.split()))
 def test_review_gate(self):self.assertRaises(ValueError,construct_pair,'gold',[{'text':'x','id':'x','review_status':'pending'}],100,len)
 def test_donor_filter(self):
  r=donor_candidates('capital','Paris',[{'title':'A','id':'1','text':'Paris is here'},{'title':'B','id':'2','text':'ocean'}],[],'similar');self.assertEqual([x['id'] for x in r],['2'])
 def test_bootstrap(self):
  r=paired_bootstrap([('a',1),('a',1),('b',0)],repeats=1000);self.assertEqual(r['estimate'],.5);self.assertEqual(r['n_questions'],2);self.assertTrue(r['low']<=.5<=r['high'])
 def test_prompt(self):self.assertNotEqual(prompt('q','c','full'),prompt('q','c','evidence'));self.assertTrue(prompt('q','c','evidence').endswith('Answer:'))
 def test_pin_gate(self):self.assertRaises(ValueError,load,{'id':'x','revision':None})
 def test_missing_pairs(self):self.assertRaises(ValueError,compare,[{'question_id':'a','condition_id':'C2','model_id':'m','method':'full','em':1}],'m','bm25',['C2'])
 def test_duplicates(self):
  r={'question_id':'a','condition_id':'C1','model_id':'m','method':'full','status':'ok','parsed_answer':'yes'}
  self.assertRaises(ValueError,score,[r,r],{'a':{'answer':'yes'}})
 def test_policy_leak(self):self.assertRaises(ValueError,select_policy,[{'split':'test'}],{}, {})
class ExtraTests(unittest.TestCase):
 def test_production_bm25(self):
  from src.methods import retrieve
  chunks=[{'id':'a','text':'ocean waves'},{'id':'b','text':'capital city'},{'id':'c','text':'mountain snow'}]
  self.assertEqual(retrieve('capital',chunks,2,lambda s:len(s.split()))[0]['id'],'b')
 def test_holm(self):
  from src.analyze import holm
  self.assertEqual(holm([.01,.04,.03]),[.03,.06,.06])
 def test_retention(self):
  from src.analyze import retention
  self.assertEqual(retention(['a','b'],['a']),{'fact_recall':.5,'complete_retention':0})
 def test_compare(self):
  rows=[{'question_id':q,'condition_id':c,'model_id':'m','method':m,'em':v} for q in ('a','b') for c in ('C2','C3') for m,v in [('full',0),('bm25',1)]]
  self.assertEqual(compare(rows,'m','bm25',['C2','C3'])['estimate'],1.)
 def test_error_scoring(self):
  row={'question_id':'a','condition_id':'C1','model_id':'m','method':'full','status':'error'}
  self.assertEqual(score([row],{'a':{'answer':'Paris'}})[0]['em'],0)
 def test_logging(self):
  from src.run import append
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'runs.jsonl';append(path,{'run_id':'abc','status':'error'})
   self.assertEqual(json.loads(path.read_text())['run_id'],'abc')
 def test_policy(self):
  cells={c['id']:c for c in CONDITIONS}
  rows=[{'split':'development','question_id':'q','condition_id':c,'method':m,'em':v,'end_to_end_seconds':1} for c in ['C1','C4','C6','C7'] for m,v in [('full',0),('bm25',1)]]
  self.assertEqual(select_policy(rows,cells,cells['C2']),'bm25')
if __name__=='__main__':unittest.main()
