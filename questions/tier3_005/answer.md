### 5. Paclitaxel Conformer-ADMET [tier3_005]

**Question**: Generate conformers of paclitaxel (taxol), select the lowest energy conformer, then predict its ADMET properties focusing on blood-brain barrier permeability

**Expected Tool Use**:
- `submit_conformer_search_workflow` - generates conformers and identifies lowest energy
- `submit_descriptors_workflow` - calculates ADMET properties including BBB permeability

**Expected**: Seven major conformations identified via NMR/NAMFIS in CDCl₃ show population distributions of 4-35% with ΔG range 0.0-1.3 kcal/mol. The lowest energy conformer is method-dependent with T-Taxol butterfly conformation often favored. ADMET properties include LogP ~3.96, molecular weight 853.92 g/mol, and poor water solubility requiring special formulation. Blood-brain barrier permeability is very poor due to P-glycoprotein efflux, with P-gp inhibition increasing brain levels by >1000-fold.