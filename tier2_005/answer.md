### 4. Paracetamol Electronic Structure [tier2_005]

**Question**: Optimize paracetamol geometry, calculate its electronic properties including HOMO/LUMO energies and dipole moment

**Expected Tool Use**:
- `submit_basic_calculation_workflow` - with tasks=["optimize", "electronic_properties"] to get optimized geometry, HOMO/LUMO energies, and dipole moment

**Expected**: B3LYP/6-31G+(d,p) optimization reveals two stable conformations (PAM1 and PAM2), with PAM2 more stable (H atoms of -NH and -OH pointing same side). HOMO/LUMO energies were calculated via B3LYP/6-31G+(d,p) for reactivity predictions. The dipole moment is 2.28 Debye (DFT B3LYP/6-31G+(d,p)).
