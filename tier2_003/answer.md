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
