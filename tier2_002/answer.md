### 1. Ibuprofen Conformational Analysis [tier2_002]

**Copy-paste to start eval (replace [MODEL] with your target model):**
```
Use the start_eval_session tool with question_id="tier2_002", model="[MODEL]", question="Generate conformers of ibuprofen, optimize the lowest energy conformer, then calculate its logP and pKa values"
```

**Expected Tool Use**:
- `molecule_lookup` - convert "ibuprofen" to SMILES
- `submit_conformer_search_workflow` - generates conformers and identifies lowest energy conformer
- `submit_pka_workflow` - calculates pKa value
- `submit_descriptors_workflow` - provides logP value

**Expected**: DFT B3LYP analysis identifies 8 energy minima conformers with the lowest energy conformer showing s-cis orientation of the carboxylic group (s-trans significantly less stable), matching the single conformer observed in crystal structure. Experimental logP values are 2.48 (OECD guideline 107 shake flask method) and 3.97 (n-octanol/water technique). The pKa of the carboxylic acid group is 4.91 experimentally and 5.8 via DFT prediction in water.