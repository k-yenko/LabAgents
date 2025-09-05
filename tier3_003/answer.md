### 3. Atorvastatin Conformer-Activity [tier3_003]

**Copy-paste to start eval (replace [MODEL] with your target model):**
```
Use the start_eval_session tool with question_id="tier3_003", model="[MODEL]", question="Generate conformers of atorvastatin, dock the top 5 conformers to HMG-CoA reductase (PDB: 1HWK), calculate binding energies, and compare to the crystal structure conformation"
```

**Expected Tool Use**:
- `molecule_lookup` - convert "atorvastatin" to SMILES
- `submit_conformer_search_workflow` - generates conformers
- `create_protein_from_pdb_id` - with code="1HWK" for HMG-CoA reductase
- `submit_docking_workflow` - dock top 5 conformers individually

**Expected**: Multiple conformers are identified with >60% not binding in local minimum, showing clear correlation between strain energy and ligand flexibility. HMG-CoA reductase binding shows Ki values in the 2-250 nM range, binding enthalpy 0 to -9.3 kcal/mol at 25°C (ITC), and 10,000× higher affinity than natural substrate. Crystal structure data (PDB: 1HWK for human HMG-CoA reductase complex) reveals buried surface area of 1060 Å² with Type II statin showing additional fluorophenyl binding.
