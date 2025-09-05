### 2. Acetaminophen Metabolic Sites [tier3_002]

**Copy-paste to start eval (replace [MODEL] with your target model):**
```
Use the start_eval_session tool with question_id="tier3_002", model="[MODEL]", question="Optimize acetaminophen structure, calculate Fukui indices to identify reactive sites, predict sites of glucuronidation and sulfation, then calculate the ADMET properties"
```

**Expected Tool Use**:
- `molecule_lookup` - convert "acetaminophen" to SMILES
- `submit_basic_calculation_workflow` - optimizes structure
- `submit_fukui_workflow` - calculates Fukui indices for reactive site prediction
- `submit_descriptors_workflow` - generates ADMET properties

**Expected**: Acetaminophen undergoes glucuronidation (50-70% via UGT1A1, UGT1A6 at phenolic hydroxyl), sulfation (25-35% via SULT1A1, SULT1A3 at phenolic hydroxyl), and oxidation (5-15% via CYP2E1 forming hepatotoxic NAPQI). Fukui indices calculate f(+) for nucleophilic attack, f(-) for electrophilic attack, and f(0) for radical reactions. ADMET properties predict good oral bioavailability, positive blood-brain barrier permeability models, and primarily renal elimination of conjugates.
