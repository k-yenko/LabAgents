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
