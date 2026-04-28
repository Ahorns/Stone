"""Tiny next-step predictor for Phase 1B Step 4.

Architecture:
    44-dim feature vector  →  MLP [44 → 256 → 256 → 6]  →  Gaussian over (Δfwd, Δlat, Δh)

The 6 outputs are (μ_fwd, μ_lat, μ_h, log σ_fwd, log σ_lat, log σ_h).
Predictions are in EGO frame. Convert back to world frame at rollout time.

Model size ≈ 80K params. Trains end-to-end on a single A100 in <2 min/epoch.
"""
from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn as nn
import torch.nn.functional as F


N_FEATURES = 44     # AgentFeatureExtractor.TOTAL_FEATURES
N_TARGETS = 3       # (Δforward, Δlateral, Δheading)


@dataclass
class ModelConfig:
    in_dim: int = N_FEATURES
    hidden_dims: tuple = (256, 256)
    out_dim: int = N_TARGETS
    log_sigma_min: float = -7.0     # σ_min ~ 1e-3 — guards against collapse
    log_sigma_max: float = 1.5      # σ_max ~ 4.5
    dropout: float = 0.0


class MLPNextStep(nn.Module):
    """Small Gaussian-head MLP."""

    def __init__(self, cfg: ModelConfig | None = None):
        super().__init__()
        cfg = cfg or ModelConfig()
        self.cfg = cfg

        layers: list[nn.Module] = []
        prev = cfg.in_dim
        for h in cfg.hidden_dims:
            layers.append(nn.Linear(prev, h))
            layers.append(nn.GELU())
            if cfg.dropout > 0:
                layers.append(nn.Dropout(cfg.dropout))
            prev = h
        self.backbone = nn.Sequential(*layers)
        # Output: 2 * out_dim (mean + log_sigma)
        self.head = nn.Linear(prev, 2 * cfg.out_dim)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """Args:
            x: (B, in_dim) feature tensor.

        Returns:
            mu       (B, out_dim)
            log_sigma (B, out_dim)  — clamped to a safe range.
        """
        h = self.backbone(x)
        out = self.head(h)
        mu, log_sigma = out.chunk(2, dim=-1)
        log_sigma = torch.clamp(log_sigma,
                                self.cfg.log_sigma_min,
                                self.cfg.log_sigma_max)
        return mu, log_sigma

    @torch.no_grad()
    def sample(self, x: torch.Tensor, generator: torch.Generator | None = None) -> torch.Tensor:
        """Draw one sample per row from the predicted Gaussian. (B, out_dim)."""
        mu, log_sigma = self.forward(x)
        sigma = log_sigma.exp()
        eps = torch.randn(mu.shape, generator=generator, device=mu.device)
        return mu + sigma * eps


def gaussian_nll(mu: torch.Tensor, log_sigma: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    """Mean Gaussian negative log-likelihood (per-element, summed over dims).

    NLL = 0.5 * ((y - μ)/σ)² + log σ  + 0.5*log(2π)
    The 0.5*log(2π) is constant w.r.t. params; we keep it for interpretability.
    """
    sigma = log_sigma.exp()
    z = (y - mu) / sigma
    per_dim = 0.5 * z.pow(2) + log_sigma + 0.5 * torch.log(torch.tensor(2 * torch.pi, device=mu.device))
    # mean over batch + sum over dims  →  scalar
    return per_dim.sum(dim=-1).mean()


def count_params(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters())
