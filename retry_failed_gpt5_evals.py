#!/usr/bin/env python3
"""
Retry failed GPT-5 evaluations
"""
import subprocess
import sys

# List of failed log files from the previous run
failed_logs = [
    # JSON parsing errors
    "logs/tier2_005/anthropic_claude-sonnet-4.5/anthropic_claude-sonnet-4.5_20251003_142343.json",
    "logs/tier3_001/openai_o3/openai_o3_20250926_180832.json",
    
    # Insufficient credits (tier3_002-tier3_006)
    "logs/tier3_002/anthropic_claude-sonnet-4.5/anthropic_claude-sonnet-4.5_20251003_145419.json",
    "logs/tier3_002/anthropic_claude-opus-4.1/anthropic_claude-opus-4.1_20251004_123956.json",
    "logs/tier3_002/openai_o3/openai_o3_20250926_203318.json",
    "logs/tier3_002/x-ai_grok-code-fast-1/x-ai_grok-code-fast-1_20250926_204750.json",
    "logs/tier3_002/openai_gpt-5/openai_gpt-5_20250926_203138.json",
    "logs/tier3_002/anthropic_claude-sonnet-4/anthropic_claude-sonnet-4_20250926_202241.json",
    "logs/tier3_002/x-ai_grok-4-fast/x-ai_grok-4-fast:free_20250926_203513.json",
    
    "logs/tier3_003/google_gemini-2.5-pro/google_gemini-2.5-pro_20250926_223150.json",
    "logs/tier3_003/deepseek_deepseek-chat-v3.1/deepseek_deepseek-chat-v3.1:free_20251004_224444.json",
    "logs/tier3_003/anthropic_claude-sonnet-4.5/anthropic_claude-sonnet-4.5_20251005_225028.json",
    "logs/tier3_003/anthropic_claude-opus-4.1/anthropic_claude-opus-4.1_20251004_131218.json",
    "logs/tier3_003/openai_o3/openai_o3_20250926_222849.json",
    "logs/tier3_003/x-ai_grok-code-fast-1/x-ai_grok-code-fast-1_20251004_175233.json",
    "logs/tier3_003/openai_gpt-5/openai_gpt-5_20250926_222540.json",
    "logs/tier3_003/anthropic_claude-sonnet-4/anthropic_claude-sonnet-4_20250926_221526.json",
    "logs/tier3_003/x-ai_grok-4-fast/x-ai_grok-4-fast:free_20250926_223000.json",
    
    "logs/tier3_004/google_gemini-2.5-pro/google_gemini-2.5-pro_20250922_115721.json",
    "logs/tier3_004/deepseek_deepseek-chat-v3.1/deepseek_deepseek-chat-v3.1:free_20250922_120004.json",
    "logs/tier3_004/anthropic_claude-sonnet-4.5/anthropic_claude-sonnet-4.5_20251003_154145.json",
    "logs/tier3_004/anthropic_claude-opus-4.1/anthropic_claude-opus-4.1_20250922_112210.json",
    "logs/tier3_004/openai_o3/openai_o3_20250922_113700.json",
    "logs/tier3_004/x-ai_grok-code-fast-1/x-ai_grok-code-fast-1_20250922_121156.json",
    "logs/tier3_004/openai_gpt-5/openai_gpt-5_20250922_113532.json",
    "logs/tier3_004/anthropic_claude-sonnet-4/anthropic_claude-sonnet-4_20250922_104145.json",
    "logs/tier3_004/x-ai_grok-4-fast/x-ai_grok-4-fast:free_20250922_114517.json",
    
    "logs/tier3_005/google_gemini-2.5-pro/google_gemini-2.5-pro_20251004_162327.json",
    "logs/tier3_005/deepseek_deepseek-chat-v3.1/deepseek_deepseek-chat-v3.1:free_20251004_152622.json",
    "logs/tier3_005/anthropic_claude-sonnet-4.5/anthropic_claude-sonnet-4.5_20251003_155811.json",
    "logs/tier3_005/anthropic_claude-opus-4.1/anthropic_claude-opus-4.1_20251004_143021.json",
    "logs/tier3_005/openai_o3/openai_o3_20251004_174649.json",
    "logs/tier3_005/x-ai_grok-code-fast-1/x-ai_grok-code-fast-1_20251004_230003.json",
    "logs/tier3_005/openai_gpt-5/openai_gpt-5_20251008_194959.json",
    "logs/tier3_005/anthropic_claude-sonnet-4/anthropic_claude-sonnet-4_20251008_181522.json",
    "logs/tier3_005/x-ai_grok-4-fast/x-ai_grok-4-fast_20251008_224135.json",
    
    "logs/tier3_006/google_gemini-2.5-pro/google_gemini-2.5-pro_20251004_171301.json",
    "logs/tier3_006/deepseek_deepseek-chat-v3.1/deepseek_deepseek-chat-v3.1:free_20251004_154538.json",
    "logs/tier3_006/anthropic_claude-sonnet-4.5/anthropic_claude-sonnet-4.5_20251003_160958.json",
    "logs/tier3_006/anthropic_claude-opus-4.1/anthropic_claude-opus-4.1_20251004_144007.json",
    "logs/tier3_006/openai_o3/openai_o3_20251004_225827.json",
    "logs/tier3_006/x-ai_grok-code-fast-1/x-ai_grok-code-fast-1_20251008_181311.json",
    "logs/tier3_006/openai_gpt-5/openai_gpt-5_20251008_194712.json",
    "logs/tier3_006/anthropic_claude-sonnet-4/anthropic_claude-sonnet-4_20251008_181651.json",
    "logs/tier3_006/x-ai_grok-4-fast/x-ai_grok-4-fast_20251008_224147.json",
]

print(f"🔄 Retrying {len(failed_logs)} failed GPT-5 evaluations...")
print(f"=" * 80)

successful = 0
failed = 0
failed_list = []

for i, log_file in enumerate(failed_logs, 1):
    print(f"\n[{i}/{len(failed_logs)}] {log_file}")
    
    cmd = [
        "python", "llm_judge_evaluator.py",
        "--single", log_file,
        "--output-dir", "evaluations_gpt5",
        "--judge", "openai/gpt-5"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            print(f"   ✅ Success")
            successful += 1
        else:
            print(f"   ❌ Failed")
            print(f"   Error: {result.stderr[:200]}")
            failed += 1
            failed_list.append(log_file)
    except subprocess.TimeoutExpired:
        print(f"   ⏱️  Timeout (5 min)")
        failed += 1
        failed_list.append(log_file)
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:200]}")
        failed += 1
        failed_list.append(log_file)

print(f"\n" + "=" * 80)
print(f"📊 RETRY SUMMARY")
print(f"=" * 80)
print(f"✅ Successful: {successful}")
print(f"❌ Failed: {failed}")
print(f"📁 Output directory: evaluations_gpt5/")

if failed_list:
    print(f"\n⚠️  Still failed ({len(failed_list)} files):")
    for f in failed_list:
        print(f"  - {f}")

print(f"\n{'=' * 80}")
print(f"✅ Retry complete!")
print(f"{'=' * 80}")
