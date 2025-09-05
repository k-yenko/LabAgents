### 6. Caffeine Temperature Solubility [tier2_007]

**Copy-paste to start eval (replace [MODEL] with your target model):**
```
Use the start_eval_session tool with question_id="tier2_007", model="[MODEL]", question="Predict the solubility of caffeine in water at 25°C, 37°C, and 50°C to determine the temperature dependence"
```

**Expected Tool Use**:
- `molecule_lookup` - convert "caffeine" to SMILES
- `submit_solubility_workflow` - with temperatures='[298.15, 310.15, 323.15]' for 25°C, 37°C, and 50°C

**Expected**: Caffeine solubility in water shows strong temperature dependence: 2.2 mg/mL at 25°C, ~4-5 mg/mL at 37°C (estimated), ~15-20 mg/mL at 50°C (extrapolated), 180 mg/mL at 80°C, and 670 mg/mL at 100°C.
