#!/usr/bin/env python3
"""
Red Team Benchmarking Script for PAD/Replay Threshold Tuning

This script evaluates PAD and replay detection performance across different thresholds
using the seeded red team dataset. It computes TPR@FPR metrics and generates
optimization recommendations for production thresholds.

Usage: python scripts/benchmark_red_team.py
"""

import os
import json
import numpy as np
from pathlib import Path
from sqlalchemy.orm import sessionmaker
from db.database import engine, SessionLocal
from db.models import KycSession, PadResult, DeepfakeResult
from sklearn.metrics import roc_curve, auc
import matplotlib.pyplot as plt

def load_red_team_results():
    """Load PAD and deepfake results from red team sessions"""
    db = SessionLocal()
    try:
        # Get all sessions with PAD results
        results = db.query(
            PadResult.score,
            PadResult.passed,
            DeepfakeResult.score.label('replay_score'),
            DeepfakeResult.passed.label('replay_passed')
        ).join(KycSession).join(DeepfakeResult).all()

        pad_scores = [r.score for r in results]
        pad_labels = [1 - r.passed for r in results]  # 1 for attack (failed genuine check)
        replay_scores = [r.replay_score for r in results]
        replay_labels = [1 - r.replay_passed for r in results]

        return pad_scores, pad_labels, replay_scores, replay_labels
    finally:
        db.close()

def compute_tpr_at_fpr(scores, labels, target_fpr=0.01):
    """Compute TPR at specific FPR level"""
    fpr, tpr, thresholds = roc_curve(labels, scores)

    # Find the threshold that gives FPR closest to target
    idx = np.argmin(np.abs(fpr - target_fpr))
    return tpr[idx], thresholds[idx], fpr[idx]

def benchmark_thresholds(scores, labels, threshold_range, service_name):
    """Benchmark different thresholds for a service"""
    results = []

    for threshold in threshold_range:
        predictions = [1 if score > threshold else 0 for score in scores]
        tp = sum(1 for pred, label in zip(predictions, labels) if pred == 1 and label == 1)
        fp = sum(1 for pred, label in zip(predictions, labels) if pred == 1 and label == 0)
        tn = sum(1 for pred, label in zip(predictions, labels) if pred == 0 and label == 0)
        fn = sum(1 for pred, label in zip(predictions, labels) if pred == 0 and label == 1)

        tpr = tp / (tp + fn) if (tp + fn) > 0 else 0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0

        results.append({
            'threshold': threshold,
            'tpr': tpr,
            'fpr': fpr,
            'precision': precision,
            'tp': tp, 'fp': fp, 'tn': tn, 'fn': fn
        })

    return results

def plot_roc_curve(scores, labels, service_name, output_path):
    """Plot ROC curve"""
    fpr, tpr, _ = roc_curve(labels, scores)
    roc_auc = auc(fpr, tpr)

    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (area = {roc_auc:.2f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title(f'{service_name} ROC Curve - Red Team Evaluation')
    plt.legend(loc="lower right")
    plt.savefig(output_path)
    plt.close()

def main():
    print("🔬 Starting Red Team Benchmarking...")

    # Load data
    pad_scores, pad_labels, replay_scores, replay_labels = load_red_team_results()

    if not pad_scores:
        print("❌ No red team data found. Run seed_red_team.py first.")
        return

    print(f"📊 Loaded {len(pad_scores)} red team samples")

    # Define threshold ranges
    pad_thresholds = np.linspace(0.1, 0.9, 17)
    replay_thresholds = np.linspace(0.1, 0.9, 17)

    # Benchmark PAD
    print("\n🛡️  Benchmarking PAD thresholds...")
    pad_results = benchmark_thresholds(pad_scores, pad_labels, pad_thresholds, "PAD")

    # Benchmark Replay
    print("🎬 Benchmarking Replay thresholds...")
    replay_results = benchmark_thresholds(replay_scores, replay_labels, replay_thresholds, "Replay")

    # Compute TPR@FPR=1e-2
    pad_tpr_at_fpr, pad_opt_threshold, pad_actual_fpr = compute_tpr_at_fpr(pad_scores, pad_labels, 0.01)
    replay_tpr_at_fpr, replay_opt_threshold, replay_actual_fpr = compute_tpr_at_fpr(replay_scores, replay_labels, 0.01)

    # Generate plots
    os.makedirs('benchmark_results', exist_ok=True)
    plot_roc_curve(pad_scores, pad_labels, "PAD", 'benchmark_results/pad_roc.png')
    plot_roc_curve(replay_scores, replay_labels, "Replay", 'benchmark_results/replay_roc.png')

    # Save results
    results = {
        'pad': {
            'tpr_at_fpr_0_01': pad_tpr_at_fpr,
            'optimal_threshold': pad_opt_threshold,
            'actual_fpr': pad_actual_fpr,
            'threshold_sweep': pad_results
        },
        'replay': {
            'tpr_at_fpr_0_01': replay_tpr_at_fpr,
            'optimal_threshold': replay_opt_threshold,
            'actual_fpr': replay_actual_fpr,
            'threshold_sweep': replay_results
        },
        'recommendations': {
            'pad_threshold': pad_opt_threshold,
            'replay_threshold': replay_opt_threshold,
            'target_kpis': {
                'pad_tpr_at_fpr_1e-2': '>= 0.95',
                'current_pad_tpr': f'{pad_tpr_at_fpr:.3f}',
                'current_replay_tpr': f'{replay_tpr_at_fpr:.3f}'
            }
        }
    }

    with open('benchmark_results/benchmark_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print("\n✅ Benchmarking Complete!")
    print(f"📈 PAD TPR@FPR=1e-2: {pad_tpr_at_fpr:.3f} (threshold: {pad_opt_threshold:.3f})")
    print(f"📈 Replay TPR@FPR=1e-2: {replay_tpr_at_fpr:.3f} (threshold: {replay_opt_threshold:.3f})")
    print("📊 Results saved to benchmark_results/")
    print("📈 Check ROC curves in benchmark_results/*.png")

    # KPI Check
    if pad_tpr_at_fpr >= 0.95:
        print("✅ PAD KPI met: TPR@FPR=1e-2 >= 0.95")
    else:
        print("⚠️  PAD KPI not met. Consider retraining or adjusting thresholds.")

if __name__ == '__main__':
    # Ensure we're in the server directory
    os.chdir(Path(__file__).parent.parent)
    main()