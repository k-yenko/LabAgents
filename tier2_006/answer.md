### 5. Benzene Redox Potential [tier2_006]

**Copy-paste to start eval (replace [MODEL] with your target model):**
```
Use the start_eval_session tool with question_id="tier2_006", model="[MODEL]", question="Calculate the oxidation and reduction potentials of benzene versus SCE in acetonitrile"
```

**Expected Tool Use**:
- `molecule_lookup` - convert "benzene" to SMILES
- `submit_redox_potential_workflow` - with reduction=True and oxidation=True

**Expected**: The oxidation potential versus SCE in acetonitrile is +2.48 ± 0.03 V (electron-transfer equilibria method) and the reduction potential versus SCE in acetonitrile is -3.42 ± 0.05 V (cyclic voltammetry at -60°C).
