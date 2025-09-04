# LabAgents Benchmark Reference

## **Available Tools**

### Chemistry Calculations
- `submit_basic_calculation_workflow` - Energy, optimization, frequencies with multiple engines (omol25, xtb, psi4)
- `submit_conformer_search_workflow` - Conformational search with multiple search modes (rapid/careful/meticulous)
- `submit_scan_workflow` - Molecular scans (dihedral, bond, angle) with wavefront propagation
- `submit_irc_workflow` - Intrinsic reaction coordinate calculations for transition states

### Molecular Properties
- `submit_pka_workflow` - Microscopic pKa calculations with customizable pH ranges and elements
- `submit_macropka_workflow` - Macroscopic pKa calculations across pH and charge ranges
- `submit_solubility_workflow` - Solubility predictions across multiple solvents and temperatures
- `submit_redox_potential_workflow` - Electrochemical reduction/oxidation potentials
- `submit_descriptors_workflow` - ML-ready molecular descriptors and features
- `submit_tautomer_search_workflow` - Tautomer enumeration with reckless/rapid/careful modes

### Reactivity Analysis  
- `submit_fukui_workflow` - Fukui indices for electrophilic/nucleophilic reactivity sites

### Protein & Drug Discovery
- `submit_docking_workflow` - Protein-ligand docking with conformer search and optimization
- `submit_protein_cofolding_workflow` - Multi-protein and protein-ligand cofolding predictions

### Molecule Management
- `molecule_lookup` - Convert molecule names, CAS numbers, IUPAC names to SMILES
- `batch_molecule_lookup` - Bulk molecule name to SMILES conversion
- `validate_smiles` - Validate and standardize SMILES strings

### Protein Management
- `create_protein_from_pdb_id` - Create protein from PDB ID (e.g., '1HCK')
- `retrieve_protein` - Get protein data by UUID
- `list_proteins` - List all available proteins
- `upload_protein` - Upload custom protein structures
- `delete_protein` - Remove protein from workspace
- `sanitize_protein` - Clean and validate protein structures

### Workflow Management
- `workflow_get_status` - Check workflow status with detailed progress information
- `workflow_stop` - Stop running workflows
- `workflow_delete` - Remove workflows from workspace
- `retrieve_workflow` - Get complete workflow data and results
- `retrieve_calculation_molecules` - Extract molecular structures from calculations
- `list_workflows` - List all workflows with filtering options
- `workflow_update` - Modify workflow parameters
- `workflow_is_finished` - Check if workflow is complete
- `workflow_delete_data` - Remove workflow data while keeping metadata
- `workflow_fetch_latest` - Get most recent workflow results

---

## **Benchmark Queries**

### Tier 2: Moderate Complexity with Known Literature Values

#### 1. Ibuprofen Conformational Analysis [tier2_002]
Generate conformers of ibuprofen, optimize the lowest energy conformer, then calculate its logP and pKa values

#### 2. Caffeine Multi-Property Analysis [tier2_003]
Calculate molecular descriptors for caffeine, predict its solubility in water at 25°C, and determine its dipole moment

#### 3. Morphine Tautomer Analysis [tier2_004]
Find all tautomers of morphine and calculate the pKa of each tautomeric form to determine which is dominant at physiological pH

#### 4. Paracetamol Electronic Structure [tier2_005]
Optimize paracetamol geometry, calculate its electronic properties including HOMO/LUMO energies and dipole moment

#### 5. Benzene Redox Potential [tier2_006]
Calculate the oxidation and reduction potentials of benzene versus SCE in acetonitrile. Log all Rowan tools you used with log_rowan_tool_call, then use end_eval_session with your complete answer.

#### 6. Caffeine Temperature Solubility [tier2_007]
Predict the solubility of caffeine in water at 25°C, 37°C, and 50°C to determine the temperature dependence

### Tier 3: Complex Workflows with Literature Validation

#### 1. Warfarin Tautomer-pKa Relationship [tier3_001]
Find the major tautomers of warfarin, calculate the pKa for each tautomeric form, identify the dominant form at pH 7.4, then predict its protein binding affinity

#### 2. Acetaminophen Metabolic Sites [tier3_002]
Optimize acetaminophen structure, calculate Fukui indices to identify reactive sites, predict sites of glucuronidation and sulfation, then calculate the ADMET properties

#### 3. Atorvastatin Conformer-Activity [tier3_003]
Generate conformers of atorvastatin, dock the top 5 conformers to HMG-CoA reductase (PDB: 1HWK), calculate binding energies, and compare to the crystal structure conformation

#### 4. Serotonin Reaction Pathway [tier3_004]
Run a dihedral scan on serotonin's ethylamine chain, identify the energy minimum, then calculate Fukui indices to predict the most reactive sites for electrophilic attack

#### 5. Taxol Conformer-ADMET Analysis [tier3_005]
Generate conformers of paclitaxel (taxol), select the lowest energy conformer, then predict its ADMET properties focusing on blood-brain barrier permeability

#### 6. Penicillin G Comprehensive Study [tier3_006]
Optimize penicillin G geometry, calculate molecular descriptors, predict solubility at multiple temperatures, then dock to a β-lactamase enzyme to understand resistance mechanisms