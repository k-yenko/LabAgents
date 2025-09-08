### 4. Serotonin Conformational Energy [tier3_004]

**Question**: Run a dihedral scan on serotonin's ethylamine chain, identify the energy minimum, then calculate Fukui indices to predict the most reactive sites for electrophilic attack

**Expected Tool Use**:
- `submit_scan_workflow` - with scan_settings for dihedral scan of ethylamine chain
- `submit_fukui_workflow` - predicts reactive sites for electrophilic attack

**Expected**: Ethylamine chain dihedral scan (B3LYP/6-311+G(d,p)) identifies six conformational energy minima, with the most stable being extended anti-conformation at 0 kcal/mol and energy barriers of 2-4 kcal/mol between minima. Fukui indices show nucleophilic attack favored at C2 position (f⁻ = 0.089) and electrophilic attack at C5 position (f⁺ = 0.093), making C5 of the indole ring the primary site for electrophilic attack with C6 and C7 as secondary sites.