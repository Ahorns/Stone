"""Training loop for the Step 4 next-step predictor.

Reads train.npz / val.npz produced by prepare_dataset.py, fits an MLPNextStep
under Gaussian NLL, checkpoints the best validation model.

Outputs (under --output, default = waymo/results/step4/):
    checkpoints/last.pt         — final-epoch weights
    checkpoints/best_val.pt     — best-validation-NLL weights
    training_log.csv            — per-epoch train/val NLL + wall time
    train_summary.json          — final stats + config
"""
from __future__ import annotations

import csv
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader, TensorDataset

from darwin_waymo.learned.model import (
    MLPNextStep, ModelConfig, count_params, gaussian_nll,
)
from darwin_waymo.learned.dataset import load_npz


@dataclass
class TrainConfig:
    dataset_dir: str
    output_dir: str
    epochs: int = 30
    batch_size: int = 1024
    lr: float = 1e-3
    weight_decay: float = 1e-4
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    seed: int = 42
    # Standardise inputs only (targets are small numbers, no need)
    normalise_inputs: bool = True
    # Optional dropout
    dropout: float = 0.0
    # Number of dataloader workers
    num_workers: int = 2


def _build_loaders(cfg: TrainConfig):
    train_X, train_Y, train_T, _ = load_npz(Path(cfg.dataset_dir) / "train.npz")
    val_X, val_Y, val_T, _ = load_npz(Path(cfg.dataset_dir) / "val.npz")

    if cfg.normalise_inputs:
        # Per-feature mean/std from training set
        x_mean = train_X.mean(axis=0).astype(np.float32)
        x_std = train_X.std(axis=0).astype(np.float32) + 1e-6
        train_X = (train_X - x_mean) / x_std
        val_X = (val_X - x_mean) / x_std
    else:
        x_mean = np.zeros(train_X.shape[1], dtype=np.float32)
        x_std = np.ones(train_X.shape[1], dtype=np.float32)

    tr = TensorDataset(torch.from_numpy(train_X), torch.from_numpy(train_Y))
    vl = TensorDataset(torch.from_numpy(val_X), torch.from_numpy(val_Y))
    train_loader = DataLoader(tr, batch_size=cfg.batch_size, shuffle=True,
                              num_workers=cfg.num_workers, pin_memory=True, drop_last=True)
    val_loader = DataLoader(vl, batch_size=cfg.batch_size, shuffle=False,
                            num_workers=cfg.num_workers, pin_memory=True)

    return train_loader, val_loader, x_mean, x_std, train_X.shape[0], val_X.shape[0]


def _eval(model, loader, device):
    model.eval()
    total_nll = 0.0
    n = 0
    with torch.no_grad():
        for X, Y in loader:
            X = X.to(device, non_blocking=True); Y = Y.to(device, non_blocking=True)
            mu, log_sigma = model(X)
            loss = gaussian_nll(mu, log_sigma, Y)
            total_nll += loss.item() * X.size(0)
            n += X.size(0)
    return total_nll / max(n, 1)


def train(cfg: TrainConfig):
    torch.manual_seed(cfg.seed)
    out_dir = Path(cfg.output_dir)
    ckpt_dir = out_dir / "checkpoints"
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    train_loader, val_loader, x_mean, x_std, n_train, n_val = _build_loaders(cfg)
    print(f"  train samples : {n_train}")
    print(f"  val samples   : {n_val}")

    model_cfg = ModelConfig(dropout=cfg.dropout)
    model = MLPNextStep(model_cfg).to(cfg.device)
    print(f"  model params  : {count_params(model):,}")
    print(f"  device        : {cfg.device}")

    opt = torch.optim.AdamW(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)

    log_path = out_dir / "training_log.csv"
    log_fh = open(log_path, "w", newline="")
    log_writer = csv.writer(log_fh)
    log_writer.writerow(["epoch", "train_nll", "val_nll", "epoch_seconds"])
    log_fh.flush()

    best_val = float("inf")
    t0 = time.time()
    for epoch in range(1, cfg.epochs + 1):
        model.train()
        t_ep = time.time()
        running = 0.0
        n = 0
        for X, Y in train_loader:
            X = X.to(cfg.device, non_blocking=True); Y = Y.to(cfg.device, non_blocking=True)
            mu, log_sigma = model(X)
            loss = gaussian_nll(mu, log_sigma, Y)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            running += loss.item() * X.size(0)
            n += X.size(0)
        train_nll = running / max(n, 1)
        val_nll = _eval(model, val_loader, cfg.device)
        ep_secs = time.time() - t_ep

        log_writer.writerow([epoch, train_nll, val_nll, round(ep_secs, 1)])
        log_fh.flush()
        print(f"  epoch {epoch:>3d}: train {train_nll:.4f}  val {val_nll:.4f}  ({ep_secs:.1f}s)")

        # Save last
        torch.save({
            "model_state": model.state_dict(),
            "model_cfg": asdict(model_cfg),
            "x_mean": x_mean, "x_std": x_std,
            "epoch": epoch, "val_nll": val_nll,
        }, ckpt_dir / "last.pt")
        # Save best by val
        if val_nll < best_val:
            best_val = val_nll
            torch.save({
                "model_state": model.state_dict(),
                "model_cfg": asdict(model_cfg),
                "x_mean": x_mean, "x_std": x_std,
                "epoch": epoch, "val_nll": val_nll,
            }, ckpt_dir / "best_val.pt")

    elapsed = time.time() - t0
    log_fh.close()

    summary = {
        "config": asdict(cfg),
        "model_cfg": asdict(model_cfg),
        "n_train_samples": n_train,
        "n_val_samples": n_val,
        "model_params": count_params(model),
        "epochs_run": cfg.epochs,
        "best_val_nll": best_val,
        "elapsed_seconds": round(elapsed, 1),
    }
    (out_dir / "train_summary.json").write_text(json.dumps(summary, indent=2))
    print(f"\nDone in {elapsed:.1f}s. best val NLL = {best_val:.4f}")
    print(f"  checkpoints   : {ckpt_dir}")
    print(f"  training log  : {log_path}")
    return summary
