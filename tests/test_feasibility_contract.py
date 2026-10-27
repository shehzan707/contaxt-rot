"""Synthetic token accounting tests, not GPU or native-tokenizer validation."""
import unittest,types,sys
from unittest.mock import patch
from src.core import place_evidence
from src.infer import generate
class ContractTests(unittest.TestCase):
 def test_4k_16k_layout(self):
  for target in [4096,16384]:
   size=target//128;donors=[' '.join([f'd{i}']*size) for i in range(127)];e=' '.join(['evidence']*size)
   for position,goal in [('middle',.5),('end',.9)]:
    r=place_evidence(donors,e,target,position,lambda s:len(s.split()))
    self.assertEqual(r['tokens'],target);self.assertLessEqual(abs(r['midpoint']-goal),.03);self.assertIn(e,r['text'])
 def test_native_count_overflow_gate(self):
  class Tokenizer:
   def apply_chat_template(self,*a,**kw):return 'formatted prompt'
   def __call__(self,*a,**kw):return {'input_ids':types.SimpleNamespace(shape=(1,4096))}
  model=types.SimpleNamespace(config=types.SimpleNamespace(max_position_embeddings=4096))
  with patch.dict(sys.modules,{'torch':types.SimpleNamespace()}):
   self.assertRaises(ValueError,generate,model,Tokenizer(),{'id':'google/gemma-3-4b-it'},'x',128)
