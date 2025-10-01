# Rowan MCP Benchmark Results

## Tier 2: Moderate Complexity with Known Literature Values

### 1. Aspirin pKa and Solubility
Question: "Use Rowan to determine aspirin's pKa and screen its solubility across multiple solvents (water, ethanol, DMSO, acetone) at 25°C and 37°C for oral drug formulation development"
Expected: pKa = 3.49 at 25°C [J. Pharm. Sci. 1967, 56, 847-853]. Solubility at 25°C: Water = 3.3 mg/mL [Eur. J. Pharm. Sci. 2009, 37, 172-182]; Ethanol = 200 mg/mL [J. Pharm. Sci. 1985, 74, 815-820]; DMSO = >500 mg/mL [J. Chem. Eng. Data 2011, 56, 1009-1014]; Acetone = 66.7 mg/mL [J. Chem. Eng. Data 2008, 53, 1208-1210]. At 37°C: Water = 6.0 mg/mL (↑82%); Ethanol = 250 mg/mL (↑25%) [Int. J. Pharm. 2003, 254, 167-178]. Temperature coefficient follows van't Hoff equation with ΔHsol = 25.1 kJ/mol in water [Thermochim. Acta 2004, 412, 47-53].
- **claude-4.1-opus**:

- **claude-4-sonnet**:

- **gpt-5**:

- **o3**:

- **grok-4**:

- **gemini-2.5-pro**:

- **deepseek-v3.1**:

- **grok-code-fast-1**:

---

### 2. Ibuprofen Conformational Analysis
Question: "Generate conformers of ibuprofen, optimize the lowest energy conformer, then calculate its logP and pKa values"
Expected: Crystal structure shows extended conformation (CSD: IBPRAC); pKa = 4.91 ± 0.04 [J. Pharm. Biomed. Anal. 1996, 15, 383-393]; logP = 3.97 [DrugBank DB01050]; Multiple low-energy conformers expected within 2-3 kcal/mol.

- **claude-4.1-opus**:

- **claude-4-sonnet**:

- **gpt-5**:

- **o3**:

- **grok-4**:

- **gemini-2.5-pro**:

- **deepseek-v3.1**:

- **grok-code-fast-1**:

---

### 3. Caffeine Multi-Property Analysis
Question: "Calculate molecular descriptors for caffeine, predict its solubility in water at 25°C, and determine its dipole moment"
Expected: Aqueous solubility = 21.6 mg/mL at 25°C [J. Chem. Eng. Data 2010, 55, 3804-3809]; Dipole moment = 3.64 D in chloroform [J. Mol. Struct. 1995, 372, 113-124]; MW = 194.19 g/mol; logP = -0.07 [Hansch et al., Exploring QSAR, ACS 1995].

- **claude-4.1-opus**:

- **claude-4-sonnet**:

- **gpt-5**:

- **o3**:

- **grok-4**:

- **gemini-2.5-pro**:

- **deepseek-v3.1**:

- **grok-code-fast-1**:

---

## Tier 3: Complex Workflows with Literature Validation

### 4. Warfarin Tautomer-pKa Relationship
Question: "Find the major tautomers of warfarin, calculate the pKa for each tautomeric form, identify the dominant form at pH 7.4, then predict its protein binding affinity"
Expected: pKa = 5.0-5.1 for enolic OH [J. Pharm. Sci. 1979, 68, 1195-1200]; Exists as cyclic hemiketal (>80%) at physiological pH [J. Am. Chem. Soc. 1978, 100, 5159-5168]; Plasma protein binding = 99% [Clin. Pharmacokinet. 1992, 22, 359-371]; Multiple tautomers in equilibrium.

- **claude-4.1-opus**:

- **claude-4-sonnet**:

- **gpt-5**:

- **o3**:

- **grok-4**:

- **gemini-2.5-pro**:

- **deepseek-v3.1**:

- **grok-code-fast-1**:

---

### 5. Acetaminophen Metabolic Sites
Question: "Optimize acetaminophen structure, calculate Fukui indices to identify reactive sites, predict sites of glucuronidation and sulfation, then calculate the ADMET properties"
Expected: Phenolic OH = primary metabolic site for Phase II conjugation [Drug Metab. Dispos. 1982, 10, 529-535]; Fukui indices should show highest reactivity at para position to OH; NAPQI formation at para position (toxic metabolite) [Chem. Res. Toxicol. 1988, 1, 47-59]; Oral bioavailability = 63-89% [Clin. Pharmacokinet. 1982, 7, 93-107]; t½ = 1.5-2.5 hours.

- **claude-4.1-opus**:

- **claude-4-sonnet**:

- **gpt-5**:

- **o3**:

- **grok-4**:

- **gemini-2.5-pro**:

- **deepseek-v3.1**:

- **grok-code-fast-1**:

---

### 6. Atorvastatin Conformer-Activity
Question: "Generate conformers of atorvastatin, dock the top 5 conformers to HMG-CoA reductase (PDB: 1HWK), calculate binding energies, and compare to the crystal structure conformation"
Expected: IC50 = 8 nM for HMG-CoA reductase [J. Med. Chem. 1991, 34, 2962-2983]; Crystal structure shows extended conformation with specific H-bonds to Ser684, Asp690, Arg590 [Science 2001, 292, 1160-1164]; Dihydroxy acid moiety mimics HMG-CoA substrate; Binding energy should correlate with nM potency (ΔG ≈ -11 to -12 kcal/mol).

- **claude-4.1-opus**:

- **claude-4-sonnet**:

- **gpt-5**:

- **o3**:

- **grok-4**:

- **gemini-2.5-pro**:

- **deepseek-v3.1**:

- **grok-code-fast-1**:

