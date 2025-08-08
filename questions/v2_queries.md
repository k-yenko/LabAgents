# Rowan MCP Benchmark Queries

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

## Tier 2: Moderate Complexity with Known Literature Values

### 1. Aspirin pKa and Solubility
**Query**: "Calculate the pKa of aspirin (acetylsalicylic acid), then predict its solubility in water at pH 1.2 (stomach) and pH 7.4 (blood)"

**Literature Values**:
- pKa: 3.5 (carboxylic acid group) [J. Pharm. Sci. 1967, 56, 847]
- Solubility at 25°C: 3.3 mg/mL in water [Merck Index]
- pH-dependent solubility well characterized

---

### 2. Ibuprofen Conformational Analysis
**Query**: "Generate conformers of ibuprofen, optimize the lowest energy conformer, then calculate its logP and pKa values"

**Literature Values**:
- pKa: 4.91 [J. Pharm. Biomed. Anal. 1996, 15, 383]
- logP: 3.97 [Drug Bank]
- Crystal structure available (CSD: IBPRAC)

---

### 3. Caffeine Multi-Property Analysis
**Query**: "Calculate molecular descriptors for caffeine, predict its solubility in water at 25°C, and determine its dipole moment"

**Literature Values**:
- Solubility: 21.6 mg/mL at 25°C [J. Chem. Eng. Data 2010, 55, 3804]
- Dipole moment: 3.64 D [J. Mol. Struct. 1995, 372, 113]
- MW: 194.19 g/mol, logP: -0.07

---

## Tier 3: Complex Workflows with Literature Validation

### 4. Warfarin Tautomer-pKa Relationship
**Query**: "Find the major tautomers of warfarin, calculate the pKa for each tautomeric form, identify the dominant form at pH 7.4, then predict its protein binding affinity"

**Literature Values**:
- pKa: 5.0-5.1 (enolic OH) [J. Pharm. Sci. 1979, 68, 1195]
- Exists primarily in cyclic hemiketal form at physiological pH
- 99% plasma protein bound [Clinical Pharmacokinetics 1992, 22, 359]
- Multiple tautomers characterized by NMR

---

### 5. Acetaminophen Metabolic Sites
**Query**: "Optimize acetaminophen structure, calculate Fukui indices to identify reactive sites, predict sites of glucuronidation and sulfation, then calculate the ADMET properties"

**Literature Values**:
- Primary metabolic sites: phenolic OH (glucuronidation/sulfation)
- Reactive metabolite: N-acetyl-p-benzoquinone imine (NAPQI)
- Hepatotoxicity well characterized
- Bioavailability: 63-89% [Clin. Pharmacokinet. 1982, 7, 93]

---

### 6. Atorvastatin Conformer-Activity
**Query**: "Generate conformers of atorvastatin, dock the top 5 conformers to HMG-CoA reductase (PDB: 1HWK), calculate binding energies, and compare to the crystal structure conformation"

**Literature Values**:
- IC50: 8 nM for HMG-CoA reductase [Nature 1985, 318, 324]
- Crystal structure with enzyme available (PDB: 1HWK)
- Known bioactive conformation
- Specific hydrogen bonding pattern documented