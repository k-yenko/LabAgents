# Tier 1 Questions - Basic tool selection
TIER1_QUESTIONS = {
    "tier1_001": "What is the predicted aqueous solubility of remdesivir at physiological temperature?",
    "tier1_002": "Calculate the pKa of the carboxyl group in gabapentin to understand its ionization at stomach pH",
    "tier1_003": "Determine the major tautomeric forms of hydroxychloroquine in aqueous solution",
    "tier1_004": "What are the key molecular descriptors for psilocybin that would be relevant for CNS drug development?",
    "tier1_005": "Calculate the reduction potential of vitamin C (ascorbic acid) to understand its antioxidant capacity",
    "tier1_006": "What is the solubility of ketamine in ethanol at room temperature for pharmaceutical formulation?",
    "tier1_007": "Determine the pKa of the amine group in semaglutide's structure",
    "tier1_008": "Find the oxidation potential of melatonin to assess its stability in biological systems",
    "tier1_009": "Find all possible tautomers of α-chlorotetrahydropyran",
    "tier1_010": "Find all tautomers of 4-hydroxypyrimidine and identify which one has the lowest energy",
}

# Tier 2 Questions - Intermediate complexity
TIER2_QUESTIONS = {
    "tier2_001": "Generate conformers of ibuprofen, optimize the lowest energy conformer, then calculate its logP and pKa values",
    "tier2_002": "Calculate molecular descriptors for caffeine, predict its solubility in water at 25°C, and determine its dipole moment",
    "tier2_003": "Find all tautomers of morphine and calculate the pKa of each tautomeric form to determine which is dominant at physiological pH",
    "tier2_004": "Optimize paracetamol geometry, calculate its electronic properties including HOMO/LUMO energies and dipole moment",
    "tier2_005": "Calculate the oxidation and reduction potentials of benzene versus SCE in acetonitrile",
    "tier2_006": "Predict the solubility of caffeine in water at 25°C, 37°C, and 50°C to determine the temperature dependence",
}

# Tier 3 Questions - Advanced complexity
TIER3_QUESTIONS = {
    "tier3_001": "Find the major tautomers of warfarin, calculate the pKa for each tautomeric form, identify the dominant form at pH 7.4, then predict its protein binding affinity",
    "tier3_002": "Optimize acetaminophen structure, calculate Fukui indices to identify reactive sites, predict sites of glucuronidation and sulfation, then calculate the ADMET properties",
    "tier3_003": "Generate conformers of atorvastatin, dock the top 5 conformers to HMG-CoA reductase (PDB: 1HWK), calculate binding energies, and compare to the crystal structure conformation",
    "tier3_004": "Run a dihedral scan on serotonin's ethylamine chain, identify the energy minimum, then calculate Fukui indices to predict the most reactive sites for electrophilic attack",
    "tier3_005": "Generate conformers of paclitaxel (taxol), select the lowest energy conformer, then predict its ADMET properties focusing on blood-brain barrier permeability",
    "tier3_006": "Optimize penicillin G geometry, calculate molecular descriptors, predict solubility at multiple temperatures, then dock to a β-lactamase enzyme to understand resistance mechanisms",
}

# Combined dictionary for easy access
ALL_QUESTIONS = {**TIER1_QUESTIONS, **TIER2_QUESTIONS, **TIER3_QUESTIONS}

def get_questions_by_tier(tier: int) -> dict:
    """Get questions for a specific tier"""
    if tier == 1:
        return TIER1_QUESTIONS
    elif tier == 2:
        return TIER2_QUESTIONS
    elif tier == 3:
        return TIER3_QUESTIONS
    else:
        raise ValueError(f"Tier {tier} not supported. Use tier 1, 2, or 3.")