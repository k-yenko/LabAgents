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

**Expected**: pKa = 4.91; logP = 3.97; Multiple conformers within 2-3 kcal/mol

---

### 2. Caffeine Multi-Property Analysis [tier2_003]

**Copy-paste to start eval (replace [MODEL] with your target model):**
```
Use the start_eval_session tool with question_id="tier2_003", model="[MODEL]", question="Calculate molecular descriptors for caffeine, predict its solubility in water at 25°C, and determine its dipole moment"
```

**Expected**: Solubility = 21.6 mg/mL at 25°C; Dipole moment = 3.64 D

---

### 3. Morphine Tautomer Analysis [tier2_004]

**Copy-paste to start eval (replace [MODEL] with your target model):**
```
Use the start_eval_session tool with question_id="tier2_004", model="[MODEL]", question="Find all tautomers of morphine and calculate the pKa of each tautomeric form to determine which is dominant at physiological pH"
```

**Expected**: Primary pKa around 8.0 for tertiary amine; phenolic OH pKa around 9.9

---

### 4. Paracetamol Electronic Structure [tier2_005]

**Copy-paste to start eval (replace [MODEL] with your target model):**
```
Use the start_eval_session tool with question_id="tier2_005", model="[MODEL]", question="Optimize paracetamol geometry, calculate its electronic properties including HOMO/LUMO energies and dipole moment"
```

**Expected**: HOMO-LUMO gap ~4-5 eV; significant dipole moment due to polar groups

---

### 5. Benzene Redox Potential [tier2_006]

**Copy-paste to start eval (replace [MODEL] with your target model):**
```
Use the start_eval_session tool with question_id="tier2_006", model="[MODEL]", question="Calculate the oxidation and reduction potentials of benzene versus SCE in acetonitrile. Log all Rowan tools you used with log_rowan_tool_call, then use end_eval_session with your complete answer."
```

**Expected**: High oxidation potential (~2.5 V vs SCE); benzene is electron-rich aromatic

---

### 6. Caffeine Temperature Solubility [tier2_007]

**Copy-paste to start eval (replace [MODEL] with your target model):**
```
Use the start_eval_session tool with question_id="tier2_007", model="[MODEL]", question="Predict the solubility of caffeine in water at 25°C, 37°C, and 50°C to determine the temperature dependence"
```

**Expected**: Increasing solubility with temperature; ~21 mg/mL at 25°C

---

## Tier 3: Complex Workflows with Literature Validation

### 1. Warfarin Tautomer-pKa Relationship [tier3_001]

**Copy-paste to start eval (replace [MODEL] with your target model):**
```
Use the start_eval_session tool with question_id="tier3_001", model="[MODEL]", question="Find the major tautomers of warfarin, calculate the pKa for each tautomeric form, identify the dominant form at pH 7.4, then predict its protein binding affinity"
```

**Expected**: pKa = 5.0-5.1 for enolic OH; 99% protein binding

---

### 2. Acetaminophen Metabolic Sites [tier3_002]

**Copy-paste to start eval (replace [MODEL] with your target model):**
```
Use the start_eval_session tool with question_id="tier3_002", model="[MODEL]", question="Optimize acetaminophen structure, calculate Fukui indices to identify reactive sites, predict sites of glucuronidation and sulfation, then calculate the ADMET properties"
```

**Expected**: Phenolic OH = primary metabolic site; Bioavailability = 63-89%

---

### 3. Atorvastatin Conformer-Activity [tier3_003]

**Copy-paste to start eval (replace [MODEL] with your target model):**
```
Use the start_eval_session tool with question_id="tier3_003", model="[MODEL]", question="Generate conformers of atorvastatin, dock the top 5 conformers to HMG-CoA reductase (PDB: 1HWK), calculate binding energies, and compare to the crystal structure conformation"
```

**Expected**: IC50 = 8 nM; Binding energy ≈ -11 to -12 kcal/mol

---

### 4. Serotonin Reaction Pathway [tier3_004]

**Copy-paste to start eval (replace [MODEL] with your target model):**
```
Use the start_eval_session tool with question_id="tier3_004", model="[MODEL]", question="Run a dihedral scan on serotonin's ethylamine chain, identify the energy minimum, then calculate Fukui indices to predict the most reactive sites for electrophilic attack"
```

**Expected**: Multiple conformational minima; highest f(-) indices at aromatic positions ortho to OH

---

### 5. Taxol Conformer-ADMET Analysis [tier3_005]

**Copy-paste to start eval (replace [MODEL] with your target model):**
```
Use the start_eval_session tool with question_id="tier3_005", model="[MODEL]", question="Generate conformers of paclitaxel (taxol), select the lowest energy conformer, then predict its ADMET properties focusing on blood-brain barrier permeability"
```

**Expected**: Complex conformational landscape; poor BBB permeability due to size and polarity

---

### 6. Penicillin G Comprehensive Study [tier3_006]

**Copy-paste to start eval (replace [MODEL] with your target model):**
```
Use the start_eval_session tool with question_id="tier3_006", model="[MODEL]", question="Optimize penicillin G geometry, calculate molecular descriptors, predict solubility at multiple temperatures, then dock to a β-lactamase enzyme to understand resistance mechanisms"
```

**Expected**: β-lactam ring strain; moderate solubility; competitive binding to β-lactamase active site