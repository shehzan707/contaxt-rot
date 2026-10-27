"""Synthetic software fixtures only. No model weights, GPU or research results."""
import unittest,json,tempfile,hashlib,sys,types
from pathlib import Path
from unittest.mock import patch
from src.validation import plan,read_log,no_gold,digest
from src.kaggle_model import validate_spec
from src.data import allocate,load_hotpot
from src.methods import retrieve,compress,prompt
from src.core import place_evidence
from src.run import append
class Part1Tests(unittest.TestCase):
 def setUp(self):
  self.cfg=json.loads(Path('configs/protocol.json').read_text());self.spec=self.cfg['models'][0]
  self.row={'question_id':'q','question':'Where?','split':'pilot','condition_id':'C1','review_status':'approved','chunks':[{'id':'a','text':'context','source_ids':['a:0','a:1']}],'context_hash':hashlib.sha256(b'context').hexdigest()}
 def jobs(self,rows=None,split='pilot',conditions=None):return plan(rows or [self.row],self.cfg,self.spec,'full',split,conditions or ['C1'])
 def test_kaggle(self):validate_spec(self.spec);self.assertEqual(len(self.cfg['models']),1)
 def test_unversioned(self):self.assertRaises(ValueError,validate_spec,dict(self.spec,handle=self.spec['handle'].rsplit('/',1)[0]))
 def test_wrong_variant(self):self.assertRaises(ValueError,validate_spec,dict(self.spec,id='gemma3n'))
 def test_precision(self):self.assertRaises(ValueError,validate_spec,dict(self.spec,dtype='float16'))
 def test_nested_gold(self):self.assertRaises(ValueError,no_gold,{'chunks':[{'supporting_facts':[]} ]})
 def test_review(self):self.row['review_status']='pending';self.assertRaises(ValueError,self.jobs)
 def test_context_hash(self):self.row['chunks'][0]['text']='changed';self.assertRaises(ValueError,self.jobs)
 def test_duplicate_run(self):self.assertRaises(ValueError,self.jobs,[self.row,self.row])
 def test_incomplete_grid(self):self.assertRaises(ValueError,self.jobs,conditions=['C1','C4'])
 def test_heldout(self):self.assertRaises(ValueError,self.jobs,split='development',conditions=['C2'])
 def test_expected_identity(self):self.assertEqual(self.jobs()[0][1]['run_id'],self.jobs()[0][1]['run_id'])
 def test_resume(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'r.jsonl';b=self.jobs()[0][1];append(f,dict(b,status='ok'));self.assertEqual(len(read_log(f,digest(self.cfg))),1)
 def test_corrupt_tail(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'r.jsonl';f.write_text('{');self.assertRaises(ValueError,read_log,f,digest(self.cfg))
 def test_duplicate_log(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'r.jsonl';b=self.jobs()[0][1];append(f,b);append(f,b);self.assertRaises(ValueError,read_log,f,digest(self.cfg))
 def test_zero_quota(self):self.assertEqual(allocate([],{'pilot':{'bridge':0}})[0],{'pilot':[]})
 def test_negative_quota(self):self.assertRaises(ValueError,allocate,[],{'pilot':{'bridge':-1}})
 def test_grouped_provenance(self):
  chunks=[{'id':'a','text':'capital city','source_ids':['a:0','a:1']},{'id':'b','text':'ocean'},{'id':'c','text':'snow'}]
  self.assertEqual(retrieve('capital',chunks,2,lambda s:len(s.split()))[0]['source_ids'],['a:0','a:1'])
 def test_context_reconstruction(self):
  ds=['x']*98;v=place_evidence(ds,'e e',100,'middle',lambda s:len(s.split()));ds.insert(v['insertion_index'],'e e');self.assertEqual('\n'.join(ds),v['text'])
 def test_full_prompt(self):self.assertIn('Context:\ncontext\n\nQuestion:',prompt('q','context','full'))
 def test_compression_contract(self):
  calls={}
  class Fake:
   def __init__(self,**kw):calls.update(kw)
   def compress_prompt(self,*args,**kw):calls.update(kw);return {'compressed_prompt':'short'}
  with patch.dict(sys.modules,{'llmlingua':types.SimpleNamespace(PromptCompressor=Fake)}):
   text,out=compress('q',['a'],'local',10,len)
  self.assertEqual(text,'short');self.assertEqual(calls['rank_method'],'longllmlingua');self.assertTrue(calls['condition_compare'])
if __name__=='__main__':unittest.main()
