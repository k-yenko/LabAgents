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

## Tier 2: Moderate Complexity + Tool Chaining
Biologically relevant molecules with 2-3 tool combinations.

13. **PROTAC Degrader Analysis**: "Find conformers of ARV-110 (PROTAC), calculate solubility in blood plasma conditions, then dock to both androgen receptor and cereblon E3 ligase"
14. **GLP-1 Agonist Optimization**: "Optimize semaglutide structure, calculate pKa values for all ionizable groups, predict solubility at stomach pH (1.5) vs intestinal pH (7)"
15. **mRNA Cap Analog**: "Generate tautomers of m7GpppG cap structure, calculate electronic properties for each, identify sites susceptible to enzymatic hydrolysis via Fukui indices"

## Tier 3: High Complexity + Multi-Tool Workflows
Advanced pharmaceutical systems with 4+ tool integrations.

16. **ADC Payload Release**: "Scan the disulfide bond in a mertansine-linker conjugate, find the transition state for glutathione-mediated cleavage, run IRC to confirm the release mechanism, calculate the freed payload's membrane permeability"
17. **KRAS G12C Inhibitor**: "Generate conformers of sotorasib, dock each to both GDP-bound and GTP-bound KRAS G12C, calculate covalent warhead reactivity via Fukui analysis, predict metabolic stability"
18. **CAR-T Target Validation**: "Calculate electronic properties of CD19 epitope region, dock therapeutic antibody fragment, run MD simulation of the complex, analyze hydrogen bonding patterns over time"
19. **Psychedelic Therapeutic**: "Find tautomers of psilocybin, calculate pKa to determine protonation at physiological pH, generate conformers of dominant species, dock to 5-HT2A receptor, compare binding to endogenous serotonin"
20. **COVID Protease Inhibitor**: "Optimize nirmatrelvir geometry, scan the critical C-N bond that forms with Cys145, calculate transition state for covalent inhibition, predict resistance mutations via protein-ligand MD"
