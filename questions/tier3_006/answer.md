### 6. Penicillin G Structure-Solubility [tier3_006]

**Question**: Optimize penicillin G geometry, calculate molecular descriptors, predict solubility at multiple temperatures, then dock to a β-lactamase enzyme to understand resistance mechanisms

**Expected Tool Use**:
- `submit_basic_calculation_workflow` - optimizes geometry
- `submit_descriptors_workflow` - calculates molecular descriptors
- `submit_solubility_workflow` - predicts solubility at multiple temperatures
- `create_protein_from_pdb_id` - fetch β-lactamase structure
- `submit_docking_workflow` - dock to β-lactamase for resistance mechanism analysis

**Expected**: B3LYP/6-31G(d) optimization reveals highly strained β-lactam ring with critical N4-C7 bond order decreasing with substituents. Molecular descriptors include molecular weight 334.39 g/mol, LogP 1.8-2.1, 2 H-bond donors, 5-6 H-bond acceptors, and TPSA ~120-130 Å². Temperature-dependent solubility data is limited but sodium/potassium salts improve solubility with general classification as moderately water-soluble as salt. β-lactamase binding data (PBP2x) shows Kd = 0.9 mM, acylation rate k₂ = 180 s⁻¹, and overall binding efficiency = 200,000 M⁻¹s⁻¹.