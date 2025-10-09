# Rowan MCP Benchmark Queries

## How to Run Eval Sessions

Copy-paste the commands below to run eval sessions. Each command starts the session, then you ask the question, and finally end the session with your answer.

### Usage Pattern:
1. Copy-paste the start command and **change [MODEL]** to match what you're testing
2. Available models: `claude-4.1-opus`, `claude-4-sonnet`, `gpt-5`, `o3`, `grok-4`, `gemini-2.5-pro`, `deepseek-v3.1`, `sonic`
3. Let the model work on the question
4. **At the end, copy-paste this logging prompt:**
   ```
   Log all Rowan tools you used with log_rowan_tool_call, then use end_eval_session with your complete answer.
   ```

---

## Tier 1: Single Tool Calls
Every tool tested with simplest possible invocation.

1. **Basic Calculation**: "Optimize the geometry of water" ✅
2. **Conformer Search**: "Find the conformers of diethyl ether" ✅
3. **pKa**: "Calculate the pKa of phenol" ✅
4. **Redox Potential**: "Calculate the oxidation potential of benzene" ✅
5. **Solubility**: "Predict the solubility of aspirin in water" ✅
6. **Descriptors**: "Calculate molecular descriptors for ibuprofen" ✅
7. **Tautomers**: "Find the tautomers of 2-hydroxypyridine"  ✅
8. **Scan**: What's the energy barrier for rotating the O-O bond in hydrogen peroxide? Why does it prefer the skewed conformation? ✅
9. **IRC**: "Run an IRC calculation for HNCO + H2O transition state ✅
10. **Fukui**: "Calculate Fukui indices for aniline" ✅
11. **Docking**: "Dock aspirin to CDK2 kinase" ✅
12. **Protein Cofolding**: "Fold CDK2 with a small molecule ligand" ✅

---

## Tier 2: Moderate Complexity with Known Literature Values

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

---

### 2. Caffeine Multi-Property Analysis [tier2_003]

**Copy-paste to start eval (replace [MODEL] with your target model):**
```
Use the start_eval_session tool with question_id="tier2_003", model="[MODEL]", question="Calculate molecular descriptors for caffeine, predict its solubility in water at 25°C, and determine its dipole moment"
```

**Expected Tool Use**:
- `molecule_lookup` - convert "caffeine" to SMILES
- `submit_descriptors_workflow` - calculates molecular descriptors
- `submit_solubility_workflow` - predicts water solubility at 25°C
- `submit_basic_calculation_workflow` - computes dipole moment with electronic properties task

**Expected**: Molecular descriptors include molecular weight 194.19 g/mol, TPSA 58.44 Å², 0 rotatable bonds, 0 H-bond donors, and 6 H-bond acceptors. Water solubility at 25°C is 2.2 mg/mL (standard experimental value). The dipole moment is 3.70 ± 0.05 D experimentally in benzene and 3.90 D via B3LYP/6-311++G** vacuum calculation.

---

### 3. Morphine Tautomer Analysis [tier2_004]

**Copy-paste to start eval (replace [MODEL] with your target model):**
```
Use the start_eval_session tool with question_id="tier2_004", model="[MODEL]", question="Find all tautomers of morphine and calculate the pKa of each tautomeric form to determine which is dominant at physiological pH"
```

**Expected Tool Use**:
- `molecule_lookup` - convert "morphine" to SMILES
- `submit_tautomer_search_workflow` - finds tautomeric forms
- `submit_macropka_workflow` - calculates pKa values and determines dominant form at pH 7.4

**Expected**: Morphine exists primarily in a single tautomeric form due to its rigid pentacyclic structure. The pKa values are 8.0 for the tertiary amine (computational M06-2X) and 9.9 for the phenolic OH (experimental). At physiological pH 7.4, the dominant form is the monocationic species with protonated tertiary amine (~80% protonated) and neutral phenolic OH.

---

### 4. Paracetamol Electronic Structure [tier2_005]

**Copy-paste to start eval (replace [MODEL] with your target model):**
```
Use the start_eval_session tool with question_id="tier2_005", model="[MODEL]", question="Optimize paracetamol geometry, calculate its electronic properties including HOMO/LUMO energies and dipole moment"
```

**Expected Tool Use**:
- `molecule_lookup` - convert "paracetamol" to SMILES
- `submit_basic_calculation_workflow` - with tasks=["optimize", "electronic_properties"] to get optimized geometry, HOMO/LUMO energies, and dipole moment

**Expected**: B3LYP/6-31G+(d,p) optimization reveals two stable conformations (PAM1 and PAM2), with PAM2 more stable (H atoms of -NH and -OH pointing same side). HOMO/LUMO energies were calculated via B3LYP/6-31G+(d,p) for reactivity predictions. The dipole moment is 2.28 Debye (DFT B3LYP/6-31G+(d,p)).

---

### 5. Benzene Redox Potential [tier2_006]

**Copy-paste to start eval (replace [MODEL] with your target model):**
```
Use the start_eval_session tool with question_id="tier2_006", model="[MODEL]", question="Calculate the oxidation and reduction potentials of benzene versus SCE in acetonitrile. Log all Rowan tools you used with log_rowan_tool_call, then use end_eval_session with your complete answer."
```

**Expected Tool Use**:
- `molecule_lookup` - convert "benzene" to SMILES
- `submit_redox_potential_workflow` - with reduction=True and oxidation=True

**Expected**: The oxidation potential versus SCE in acetonitrile is +2.48 ± 0.03 V (electron-transfer equilibria method) and the reduction potential versus SCE in acetonitrile is -3.42 ± 0.05 V (cyclic voltammetry at -60°C).

---

### 6. Caffeine Temperature Solubility [tier2_007]

**Copy-paste to start eval (replace [MODEL] with your target model):**
```
Use the start_eval_session tool with question_id="tier2_007", model="[MODEL]", question="Predict the solubility of caffeine in water at 25°C, 37°C, and 50°C to determine the temperature dependence. Log all Rowan tools you used with log_rowan_tool_call, then use end_eval_session with your complete answer"
```

**Expected Tool Use**:
- `molecule_lookup` - convert "caffeine" to SMILES
- `submit_solubility_workflow` - with temperatures='[298.15, 310.15, 323.15]' for 25°C, 37°C, and 50°C

**Expected**: Caffeine solubility in water shows strong temperature dependence: 2.2 mg/mL at 25°C, ~4-5 mg/mL at 37°C (estimated), ~15-20 mg/mL at 50°C (extrapolated), 180 mg/mL at 80°C, and 670 mg/mL at 100°C.

---

## Tier 3: Complex Workflows with Literature Validation

### 1. Warfarin Tautomer-pKa Relationship [tier3_001]

**Copy-paste to start eval (replace [MODEL] with your target model):**
```
Use the start_eval_session tool with question_id="tier3_001", model="[MODEL]", question="Find the major tautomers of warfarin, calculate the pKa for each tautomeric form, identify the dominant form at pH 7.4, then predict its protein binding affinity. Log all Rowan tools you used with log_rowan_tool_call, then use end_eval_session with your complete answer"
```

**Expected Tool Use**:
- `molecule_lookup` - convert "warfarin" to SMILES
- `submit_tautomer_search_workflow` - identifies major tautomers
- `submit_macropka_workflow` - calculates pKa values and dominant form at pH 7.4
- `create_protein_from_pdb_id` - fetch human serum albumin structure
- `submit_docking_workflow` - determines protein binding affinity

**Expected**: Warfarin exhibits 40 distinct tautomeric forms via prototropic and ring-chain tautomerism, with T4S (open-chain) most stable in gas phase at 0.0 kcal/mol and T10S_R (cyclic hemiketal) most stable in aqueous solution. The pKa of the coumarin 4-hydroxyl group is 5.05-5.2, making the deprotonated anionic form dominant at pH 7.4. Protein binding to human serum albumin is 99% at Sudlow Site I in subdomain IIA, with crystal structure available at 2.5 Å resolution.

---

### 2. Acetaminophen Metabolic Sites [tier3_002]

**Copy-paste to start eval (replace [MODEL] with your target model):**
```
Use the start_eval_session tool with question_id="tier3_002", model="[MODEL]", question="Optimize acetaminophen structure, calculate Fukui indices to identify reactive sites, predict sites of glucuronidation and sulfation, then calculate the ADMET properties. Log all Rowan tools you used with log_rowan_tool_call, then use end_eval_session with your complete answer"
```

**Expected Tool Use**:
- `molecule_lookup` - convert "acetaminophen" to SMILES
- `submit_basic_calculation_workflow` - optimizes structure
- `submit_fukui_workflow` - calculates Fukui indices for reactive site prediction
- `submit_descriptors_workflow` - generates ADMET properties

**Expected**: Acetaminophen undergoes glucuronidation (50-70% via UGT1A1, UGT1A6 at phenolic hydroxyl), sulfation (25-35% via SULT1A1, SULT1A3 at phenolic hydroxyl), and oxidation (5-15% via CYP2E1 forming hepatotoxic NAPQI). Fukui indices calculate f(+) for nucleophilic attack, f(-) for electrophilic attack, and f(0) for radical reactions. ADMET properties predict good oral bioavailability, positive blood-brain barrier permeability models, and primarily renal elimination of conjugates.

---

### 3. Atorvastatin Conformer-Activity [tier3_003]

**Copy-paste to start eval (replace [MODEL] with your target model):**
```
Use the start_eval_session tool with question_id="tier3_003", model="[MODEL]", question="Generate conformers of atorvastatin, dock the top 5 conformers to HMG-CoA reductase (PDB: 1HWK), calculate binding energies, and compare to the crystal structure conformation. Log all Rowan tools you used with log_rowan_tool_call, then use end_eval_session with your complete answer"
```

**Expected Tool Use**:
- `molecule_lookup` - convert "atorvastatin" to SMILES
- `submit_conformer_search_workflow` - generates conformers
- `create_protein_from_pdb_id` - with code="1HWK" for HMG-CoA reductase
- `submit_docking_workflow` - dock top 5 conformers individually

**Expected**: Multiple conformers are identified with >60% not binding in local minimum, showing clear correlation between strain energy and ligand flexibility. HMG-CoA reductase binding shows Ki values in the 2-250 nM range, binding enthalpy 0 to -9.3 kcal/mol at 25°C (ITC), and 10,000× higher affinity than natural substrate. Crystal structure data (PDB: 1HWK for human HMG-CoA reductase complex) reveals buried surface area of 1060 Å² with Type II statin showing additional fluorophenyl binding.

---

### 4. Serotonin Reaction Pathway [tier3_004]

**Copy-paste to start eval (replace [MODEL] with your target model):**
```
Use the start_eval_session tool with question_id="tier3_004", model="[MODEL]", question="Run a dihedral scan on serotonin's ethylamine chain, identify the energy minimum, then calculate Fukui indices to predict the most reactive sites for electrophilic attack. Log all Rowan tools you used with log_rowan_tool_call, then use end_eval_session with your complete answer
```

**Expected Tool Use**:
- `molecule_lookup` - convert "serotonin" to SMILES
- `submit_scan_workflow` - with scan_settings for dihedral scan of ethylamine chain
- `submit_fukui_workflow` - predicts reactive sites for electrophilic attack

**Expected**: Ethylamine chain dihedral scan (B3LYP/6-311+G(d,p)) identifies six conformational energy minima, with the most stable being extended anti-conformation at 0 kcal/mol and energy barriers of 2-4 kcal/mol between minima. Fukui indices show nucleophilic attack favored at C2 position (f⁻ = 0.089) and electrophilic attack at C5 position (f⁺ = 0.093), making C5 of the indole ring the primary site for electrophilic attack with C6 and C7 as secondary sites.

---

### 5. Taxol Conformer-ADMET Analysis [tier3_005]

**Copy-paste to start eval (replace [MODEL] with your target model):**
```
Use the start_eval_session tool with question_id="tier3_005", model="[MODEL]", question="Generate conformers of paclitaxel (taxol), select the lowest energy conformer, then predict its ADMET properties focusing on blood-brain barrier permeability. Log all Rowan tools you used with log_rowan_tool_call, then use end_eval_session with your complete answer
```

**Expected Tool Use**:
- `molecule_lookup` - convert "paclitaxel" or "taxol" to SMILES
- `submit_conformer_search_workflow` - generates conformers and identifies lowest energy
- `submit_descriptors_workflow` - calculates ADMET properties including BBB permeability

**Expected**: Seven major conformations identified via NMR/NAMFIS in CDCl₃ show population distributions of 4-35% with ΔG range 0.0-1.3 kcal/mol. The lowest energy conformer is method-dependent with T-Taxol butterfly conformation often favored. ADMET properties include LogP ~3.96, molecular weight 853.92 g/mol, and poor water solubility requiring special formulation. Blood-brain barrier permeability is very poor due to P-glycoprotein efflux, with P-gp inhibition increasing brain levels by >1000-fold.

---

### 6. Penicillin G Comprehensive Study [tier3_006]

**Copy-paste to start eval (replace [MODEL] with your target model):**
```
Use the start_eval_session tool with question_id="tier3_006", model="[MODEL]", question="Optimize penicillin G geometry, calculate molecular descriptors, predict solubility at multiple temperatures, then dock to a β-lactamase enzyme to understand resistance mechanisms. Log all Rowan tools you used with log_rowan_tool_call, then use end_eval_session with your complete answer"
```

**Expected Tool Use**:
- `molecule_lookup` - convert "penicillin G" to SMILES
- `submit_basic_calculation_workflow` - optimizes geometry
- `submit_descriptors_workflow` - calculates molecular descriptors
- `submit_solubility_workflow` - predicts solubility at multiple temperatures
- `create_protein_from_pdb_id` - fetch β-lactamase structure
- `submit_docking_workflow` - dock to β-lactamase for resistance mechanism analysis

**Expected**: B3LYP/6-31G(d) optimization reveals highly strained β-lactam ring with critical N4-C7 bond order decreasing with substituents. Molecular descriptors include molecular weight 334.39 g/mol, LogP 1.8-2.1, 2 H-bond donors, 5-6 H-bond acceptors, and TPSA ~120-130 Å². Temperature-dependent solubility data is limited but sodium/potassium salts improve solubility with general classification as moderately water-soluble as salt. β-lactamase binding data (PBP2x) shows Kd = 0.9 mM, acylation rate k₂ = 180 s⁻¹, and overall binding efficiency = 200,000 M⁻¹s⁻¹.


**Key computational methods:**
Benchmark values were primarily obtained using DFT functionals (B3LYP, M06-2X, CAM-B3LYP), basis sets (6-31G(d), 6-311+G(d,p), aug-cc-pVDZ), solvation models (PCM, SMD), software (Gaussian 09/16, various computational chemistry packages), and experimental validation (X-ray crystallography, NMR, ITC, cyclic voltammetry), representing current methods in computational chemistry benchmarking for pharmaceutical compounds.