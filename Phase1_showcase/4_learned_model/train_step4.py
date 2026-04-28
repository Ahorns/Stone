#!/usr/bin/env python3
"""Stage 2 — train the Step 4 next-step predictor on prepared data.

Reads waymo/results/step4/dataset/{train,val}.npz, fits an MLPNextStep,
saves checkpoints and a training log to waymo/results/step4/.

Usage:
    python waymo/scripts/train_step4.py                     # default 30 epochs
    python waymo/scripts/train_step4.py --epochs 50 --lr 5e-4
    python waymo/scripts/train_step4.py --device cpu        # force CPU
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from darwin_waymo import paths
from darwin_waymo.learned.train import TrainConfig, train


def parse_args():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dataset-dir", default=str(paths.RESULTS_DIR / "step4" / "dataset"))
    p.add_argument("--output-dir", default=str(paths.RESULTS_DIR / "step4"))
    p.add_argument("--epochs", type=int, default=30)
    p.add_argument("--batch-size", type=int, default=1024)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--weight-decay", type=float, default=1e-4)
    p.add_argument("--dropout", type=float, default=0.0)
    p.add_argument("--device", default=None,
                   help="cuda or cpu; default = cuda if available else cpu")
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


def main():
    args = parse_args()
    import torch
    if args.device is None:
        args.device = "cuda" if torch.cuda.is_available() else "cpu"

    cfg = TrainConfig(
        dataset_dir=args.dataset_dir,
        output_dir=args.output_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        weight_decay=args.weight_decay,
        dropout=args.dropout,
        device=args.device,
        seed=args.seed,
    )
    print("=" * 64)
    print("  Phase 1B · Step 4 · Stage 2 — Train next-step predictor")
    print("=" * 64)
    print(f"  dataset    : {cfg.dataset_dir}")
    print(f"  output     : {cfg.output_dir}")
    print(f"  epochs     : {cfg.epochs}   batch {cfg.batch_size}   lr {cfg.lr}")
    print(f"  device     : {cfg.device}")
    print("=" * 64)
    train(cfg)


if __name__ == "__main__":
    main()
