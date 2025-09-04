#!/usr/bin/env python3
"""
Upload evaluation questions dataset to Arize using their Python SDK
"""

from arize.experimental.datasets import ArizeDatasetsClient
import pandas as pd
import json
import os
from typing import List, Dict

# Arize configuration
ARIZE_API_KEY = "ak-c1f7e212-1a95-42f4-9293-f7fcbd52dd93-hvoru4msS6j4XUVX_JWATlrB7b8wiPUc"  # Replace with your actual API key
SPACE_ID = "U3BhY2U6MjcxMDE6WE5RNg=="
DATASET_ID = "RGF0YXNldDozMDQxMTE6U2RZcg=="

def load_questions_from_v2_queries() -> List[Dict]:
    """Load questions from v2_queries.md file"""
    questions = []
    
    # Define the questions based on v2_queries.md structure
    tier2_questions = [
        {
            "question_id": "tier2_002",
            "tier": "Tier 2",
            "category": "Conformational Analysis",
            "question": "Generate conformers of ibuprofen, optimize the lowest energy conformer, then calculate its logP and pKa values",
            "expected_result": "pKa = 4.91; logP = 3.97; Multiple conformers within 2-3 kcal/mol",
            "complexity": "Moderate",
            "primary_tools": ["rowan_conformers", "rowan_descriptors", "rowan_pka"],
            "molecule": "ibuprofen"
        },
        {
            "question_id": "tier2_003", 
            "tier": "Tier 2",
            "category": "Multi-Property Analysis",
            "question": "Calculate molecular descriptors for caffeine, predict its solubility in water at 25°C, and determine its dipole moment",
            "expected_result": "Solubility = 21.6 mg/mL at 25°C; Dipole moment = 3.64 D",
            "complexity": "Moderate",
            "primary_tools": ["rowan_descriptors", "rowan_solubility", "rowan_electronic_properties"],
            "molecule": "caffeine"
        },
        {
            "question_id": "tier2_004",
            "tier": "Tier 2", 
            "category": "Tautomer Analysis",
            "question": "Find all tautomers of morphine and calculate the pKa of each tautomeric form to determine which is dominant at physiological pH",
            "expected_result": "Primary pKa around 8.0 for tertiary amine; phenolic OH pKa around 9.9",
            "complexity": "Moderate",
            "primary_tools": ["rowan_tautomers", "rowan_pka"],
            "molecule": "morphine"
        },
        {
            "question_id": "tier2_005",
            "tier": "Tier 2",
            "category": "Electronic Structure",
            "question": "Optimize paracetamol geometry, calculate its electronic properties including HOMO/LUMO energies and dipole moment", 
            "expected_result": "HOMO-LUMO gap ~4-5 eV; significant dipole moment due to polar groups",
            "complexity": "Moderate",
            "primary_tools": ["rowan_multistage_opt", "rowan_electronic_properties"],
            "molecule": "paracetamol"
        },
        {
            "question_id": "tier2_006",
            "tier": "Tier 2",
            "category": "Redox Potential",
            "question": "Calculate the oxidation and reduction potentials of benzene versus SCE in acetonitrile",
            "expected_result": "High oxidation potential (~2.5 V vs SCE); benzene is electron-rich aromatic",
            "complexity": "Moderate", 
            "primary_tools": ["rowan_redox_potential"],
            "molecule": "benzene"
        },
        {
            "question_id": "tier2_007",
            "tier": "Tier 2",
            "category": "Temperature Solubility",
            "question": "Predict the solubility of caffeine in water at 25°C, 37°C, and 50°C to determine the temperature dependence",
            "expected_result": "Increasing solubility with temperature; ~21 mg/mL at 25°C",
            "complexity": "Moderate",
            "primary_tools": ["rowan_solubility"],
            "molecule": "caffeine"
        }
    ]
    
    tier3_questions = [
        {
            "question_id": "tier3_001",
            "tier": "Tier 3",
            "category": "Tautomer-pKa Relationship", 
            "question": "Find the major tautomers of warfarin, calculate the pKa for each tautomeric form, identify the dominant form at pH 7.4, then predict its protein binding affinity",
            "expected_result": "pKa = 5.0-5.1 for enolic OH; 99% protein binding",
            "complexity": "Complex",
            "primary_tools": ["rowan_tautomers", "rowan_pka", "rowan_docking"],
            "molecule": "warfarin"
        },
        {
            "question_id": "tier3_002",
            "tier": "Tier 3",
            "category": "Metabolic Sites",
            "question": "Optimize acetaminophen structure, calculate Fukui indices to identify reactive sites, predict sites of glucuronidation and sulfation, then calculate the ADMET properties",
            "expected_result": "Phenolic OH = primary metabolic site; Bioavailability = 63-89%",
            "complexity": "Complex",
            "primary_tools": ["rowan_multistage_opt", "rowan_fukui", "rowan_admet"],
            "molecule": "acetaminophen"
        },
        {
            "question_id": "tier3_003",
            "tier": "Tier 3", 
            "category": "Conformer-Activity",
            "question": "Generate conformers of atorvastatin, dock the top 5 conformers to HMG-CoA reductase (PDB: 1HWK), calculate binding energies, and compare to the crystal structure conformation",
            "expected_result": "IC50 = 8 nM; Binding energy ≈ -11 to -12 kcal/mol",
            "complexity": "Complex",
            "primary_tools": ["rowan_conformers", "rowan_docking"],
            "molecule": "atorvastatin"
        },
        {
            "question_id": "tier3_004",
            "tier": "Tier 3",
            "category": "Reaction Pathway",
            "question": "Run a dihedral scan on serotonin's ethylamine chain, identify the energy minimum, then calculate Fukui indices to predict the most reactive sites for electrophilic attack",
            "expected_result": "Multiple conformational minima; highest f(-) indices at aromatic positions ortho to OH",
            "complexity": "Complex",
            "primary_tools": ["rowan_scan", "rowan_fukui"],
            "molecule": "serotonin"
        },
        {
            "question_id": "tier3_005",
            "tier": "Tier 3",
            "category": "Conformer-ADMET Analysis",
            "question": "Generate conformers of paclitaxel (taxol), select the lowest energy conformer, then predict its ADMET properties focusing on blood-brain barrier permeability",
            "expected_result": "Complex conformational landscape; poor BBB permeability due to size and polarity",
            "complexity": "Complex",
            "primary_tools": ["rowan_conformers", "rowan_admet"],
            "molecule": "paclitaxel"
        },
        {
            "question_id": "tier3_006",
            "tier": "Tier 3",
            "category": "Comprehensive Study", 
            "question": "Optimize penicillin G geometry, calculate molecular descriptors, predict solubility at multiple temperatures, then dock to a β-lactamase enzyme to understand resistance mechanisms",
            "expected_result": "β-lactam ring strain; moderate solubility; competitive binding to β-lactamase active site",
            "complexity": "Complex",
            "primary_tools": ["rowan_multistage_opt", "rowan_descriptors", "rowan_solubility", "rowan_docking"],
            "molecule": "penicillin G"
        }
    ]
    
    questions.extend(tier2_questions)
    questions.extend(tier3_questions)
    
    return questions

def create_arize_dataset_format(questions: List[Dict]) -> pd.DataFrame:
    """Convert questions to DataFrame format suitable for Arize"""
    
    # Create rows for the DataFrame
    rows = []
    for q in questions:
        row = {
            'question_id': q['question_id'],
            'tier': q['tier'],
            'category': q['category'],
            'question_text': q['question'],
            'expected_result': q['expected_result'],
            'complexity_level': q['complexity'],
            'target_molecule': q['molecule'],
            'primary_tools_required': ', '.join(q['primary_tools']),
            'num_tools_required': len(q['primary_tools']),
            'evaluation_type': 'computational_chemistry',
            'domain': 'drug_discovery',
            'requires_literature_validation': 'yes' if 'Tier 3' in q['tier'] else 'no'
        }
        rows.append(row)
    
    df = pd.DataFrame(rows)
    return df

def upload_to_arize(df: pd.DataFrame) -> None:
    """Upload DataFrame to Arize dataset"""
    
    # Initialize Arize client
    client = ArizeDatasetsClient(api_key=ARIZE_API_KEY)
    
    print(f"📊 Uploading {len(df)} questions to Arize dataset...")
    print(f"Dataset columns: {list(df.columns)}")
    
    try:
        # Update the dataset
        response = client.update_dataset(
            space_id=SPACE_ID, 
            dataset_id=DATASET_ID, 
            data=df
        )
        
        print("✅ Successfully uploaded dataset to Arize!")
        print(f"Response: {response}")
        
    except Exception as e:
        print(f"❌ Error uploading to Arize: {e}")
        print("Please check:")
        print("1. API key is correct")
        print("2. Space ID and Dataset ID are valid") 
        print("3. Dataset schema matches expected format")

def save_local_backup(df: pd.DataFrame) -> None:
    """Save local backup of the dataset"""
    backup_file = "arize_questions_dataset.csv"
    df.to_csv(backup_file, index=False)
    print(f"💾 Saved local backup to {backup_file}")

def main():
    """Main function to load questions and upload to Arize"""
    
    print("🧪 Rowan MCP Benchmark Dataset Upload to Arize")
    print("=" * 50)
    
    # Load questions
    print("📚 Loading questions from evaluation dataset...")
    questions = load_questions_from_v2_queries()
    print(f"Loaded {len(questions)} questions")
    
    # Convert to Arize format
    print("🔄 Converting to Arize dataset format...")
    df = create_arize_dataset_format(questions)
    
    # Display preview
    print("\n📋 Dataset Preview:")
    print(df[['question_id', 'tier', 'category', 'target_molecule']].to_string())
    
    # Save local backup
    save_local_backup(df)
    
    # Check if API key is set
    if ARIZE_API_KEY == "YOUR_API_KEY":
        print("\n⚠️  Please set your actual Arize API key in the ARIZE_API_KEY variable")
        print("Dataset prepared but not uploaded. Update API key and run again.")
        return
    
    # Upload to Arize
    upload_to_arize(df)

if __name__ == "__main__":
    main()