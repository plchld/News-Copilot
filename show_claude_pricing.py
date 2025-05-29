#!/usr/bin/env python3
"""
Quick script to show Claude pricing updates
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

from backend.apps.core.claude_pricing import ClaudeModel

print("🤖 Claude Model Pricing (2025)")
print("=" * 60)
print()

# Group models by family
opus_models = [m for m in ClaudeModel if 'OPUS' in m.name]
sonnet_models = [m for m in ClaudeModel if 'SONNET' in m.name]
haiku_models = [m for m in ClaudeModel if 'HAIKU' in m.name]

print("📚 OPUS MODELS (Flagship)")
for model in sorted(opus_models, key=lambda m: m.model_id, reverse=True):
    print(f"  {model.model_id}")
    print(f"    💰 ${model.input_price_per_million} / ${model.output_price_per_million} per million tokens")
    print(f"    📏 {model.context_window:,} context, {model.max_output_tokens:,} max output")
    print()

print("🎯 SONNET MODELS (Balanced)")
for model in sorted(sonnet_models, key=lambda m: m.model_id, reverse=True):
    print(f"  {model.model_id}")
    print(f"    💰 ${model.input_price_per_million} / ${model.output_price_per_million} per million tokens")
    print(f"    📏 {model.context_window:,} context, {model.max_output_tokens:,} max output")
    print()

print("⚡ HAIKU MODELS (Fast & Affordable)")
for model in sorted(haiku_models, key=lambda m: m.model_id, reverse=True):
    print(f"  {model.model_id}")
    print(f"    💰 ${model.input_price_per_million} / ${model.output_price_per_million} per million tokens")
    print(f"    📏 {model.context_window:,} context, {model.max_output_tokens:,} max output")
    print()

print("🔥 NEW MODELS:")
print("  • Opus 4.0: 2.5x larger context (500K), 5x more output (20K)")
print("  • Sonnet 3.7: 3.4x larger context (680K), lower cost than 3.5")
print()