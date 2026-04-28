"""Waymo Evolver — evolve driving policies using Darwin.

Maps Darwin's FloatGenes to BehavioralParams in the rule engine.
Each organism = one driving policy with different behavioral parameters.
Fitness = how well it drives across a batch of scenarios.
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional

import numpy as np
from tqdm import tqdm

from darwin.core.gene import FloatGene
from darwin.core.genome import Genome
from darwin.core.organism import Organism
from darwin.core.population import Population
from darwin.operators.selection import TournamentSelection
from darwin.operators.crossover import UniformCrossover
from darwin.operators.mutation import GaussianMutation
from darwin.utils.rng import DarwinRNG

from darwin_waymo.features.scenario_parser import ParsedScenario, AgentState
from darwin_waymo.features.map_features import MapFeatureExtractor
from darwin_waymo.policies.rule_engine import RuleEngine, BehavioralParams
from darwin_waymo.policies.kinematic_model import KinematicModel, KinematicState
from darwin_waymo.evolution.waymo_fitness import compute_proxy_fitness


# Gene definitions: name -> (default, low, high, mutation_sigma)
BEHAVIORAL_GENES = {
    "speed_factor":       (0.9, 0.5, 1.3, 0.1),
    "follow_time_gap":    (1.5, 0.5, 3.0, 0.3),
    "min_follow_dist":    (3.0, 1.0, 8.0, 0.5),
    "lane_steer_gain":    (1.5, 0.5, 4.0, 0.3),
    "heading_steer_gain": (2.0, 0.8, 5.0, 0.4),
    "stop_decel":         (-3.0, -6.0, -1.0, 0.5),
    "yield_distance":     (15.0, 5.0, 30.0, 3.0),
    "noise_scale":        (0.01, 0.001, 0.05, 0.005),
}


def genome_to_params(genome: Genome) -> BehavioralParams:
    """Convert a Darwin genome into BehavioralParams."""
    return BehavioralParams(
        speed_factor=genome.genes["speed_factor"].value,
        follow_time_gap=genome.genes["follow_time_gap"].value,
        min_follow_dist=genome.genes["min_follow_dist"].value,
        lane_steer_gain=genome.genes["lane_steer_gain"].value,
        heading_steer_gain=genome.genes["heading_steer_gain"].value,
        stop_decel=genome.genes["stop_decel"].value,
        yield_distance=genome.genes["yield_distance"].value,
        noise_scale=genome.genes["noise_scale"].value,
    )


def create_template_genome() -> Genome:
    """Create the template genome for behavioral parameter evolution."""
    genes = {}
    for name, (default, low, high, sigma) in BEHAVIORAL_GENES.items():
        genes[name] = FloatGene(name, default, low, high, sigma)
    return Genome(genes)


class WaymoEvolver:
    """Evolves driving policies on Waymo scenarios using Darwin.

    Each organism's genome encodes BehavioralParams.
    Fitness = average proxy fitness across a batch of scenarios.
    """

    def __init__(
        self,
        scenarios: List[ParsedScenario],
        population_size: int = 50,
        generations: int = 100,
        elite_fraction: float = 0.1,
        mutation_rate: float = 0.4,
        tournament_size: int = 5,
        seed: int = 42,
        n_rollouts_per_eval: int = 1,  # rollouts per scenario per organism
    ):
        self.scenarios = scenarios
        self.population_size = population_size
        self.generations = generations
        self.elite_fraction = elite_fraction
        self.mutation_rate = mutation_rate
        self.n_rollouts_per_eval = n_rollouts_per_eval

        self.selector = TournamentSelection(tournament_size)
        self.crossover = UniformCrossover()
        self.mutation = GaussianMutation(mutation_rate)
        self.rng_state = DarwinRNG(seed)
        self.kinematic = KinematicModel()

        self.template = create_template_genome()
        self.population = Population()
        self.history = []

        # Pre-compute map extractors (expensive, do once)
        print("  Pre-computing map features...")
        self.map_extractors = {}
        for sc in scenarios:
            self.map_extractors[sc.scenario_id] = MapFeatureExtractor(sc)

    def evolve(self) -> List[BehavioralParams]:
        """Run evolution and return the top-32 diverse parameter sets.

        Returns:
            List of BehavioralParams, one per rollout.
        """
        rng = self.rng_state.get()

        # Initialize population
        self.population.initialize(self.template, self.population_size, rng)
        print(f"  Population: {self.population_size} organisms, {self.generations} generations")
        print(f"  Scenarios: {len(self.scenarios)}, rollouts/eval: {self.n_rollouts_per_eval}")

        best_ever = None
        best_fitness = -float('inf')

        pbar = tqdm(range(self.generations), desc="Evolving", unit="gen", ncols=100)
        for gen in pbar:
            # Evaluate all organisms
            for org in self.population.organisms:
                org.fitness = self._evaluate_organism(org, rng)

            # Track best
            stats = self.population.statistics()
            self.history.append(stats)

            current_best = self.population.best
            if current_best and current_best.fitness > best_fitness:
                best_fitness = current_best.fitness
                best_ever = current_best

            pbar.set_postfix(
                best=f"{stats.get('best_fitness', 0):.4f}",
                mean=f"{stats.get('mean_fitness', 0):.4f}",
            )

            # Select + reproduce
            self.population.select_and_reproduce(
                self.selector, self.crossover, self.mutation,
                self.elite_fraction, rng,
            )

        # Final evaluation
        for org in self.population.organisms:
            org.fitness = self._evaluate_organism(org, rng)

        # Return top 32 diverse parameter sets
        return self._select_diverse_top(32)

    def _evaluate_organism(self, organism: Organism, rng: np.random.Generator) -> float:
        """Evaluate one organism across all scenarios."""
        params = genome_to_params(organism.genome)
        policy = RuleEngine(params)

        total_fitness = 0.0
        n_evals = 0

        for sc in self.scenarios:
            map_ext = self.map_extractors[sc.scenario_id]

            for rollout_idx in range(self.n_rollouts_per_eval):
                sim_states = self._run_single_rollout(
                    sc, policy, map_ext, rng, rollout_idx
                )
                fitness = compute_proxy_fitness(sim_states, sc, map_ext)
                total_fitness += fitness
                n_evals += 1

        return total_fitness / max(n_evals, 1)

    def _run_single_rollout(
        self,
        scenario: ParsedScenario,
        policy: RuleEngine,
        map_ext: MapFeatureExtractor,
        rng: np.random.Generator,
        rollout_idx: int,
    ) -> np.ndarray:
        """Run one 80-step rollout for a scenario. Returns (n_agents, 80, 4)."""
        t0 = scenario.current_time_index
        sim_ids = scenario.sim_agent_ids
        n_agents = len(sim_ids)
        n_steps = 80

        # Initialize kinematic states
        current = {}
        agent_types = {}
        for aid in sim_ids:
            track = scenario.agents[aid]
            state = track.last_valid_state(t0)
            if state is not None:
                current[aid] = KinematicState.from_agent_state(state)
                agent_types[aid] = track.agent_type
            else:
                current[aid] = KinematicState(0, 0, 0, 0, 0, 0, 0)
                agent_types[aid] = 1

        result = np.zeros((n_agents, n_steps, 4), dtype=np.float32)

        for step in range(n_steps):
            # Build agent states for feature extraction
            current_states = {}
            for aid, ks in current.items():
                track = scenario.agents[aid]
                current_states[aid] = AgentState(
                    x=ks.x, y=ks.y, z=ks.z, heading=ks.heading,
                    vx=ks.vx, vy=ks.vy, speed=ks.speed,
                    length=track.states[t0, 7], width=track.states[t0, 8],
                    height=track.states[t0, 9], valid=True,
                )

            # Step each agent
            for idx, aid in enumerate(sim_ids):
                accel, steer = policy.compute_action(
                    agent_state=current_states[aid],
                    agent_type=agent_types[aid],
                    map_extractor=map_ext,
                    all_agents=current_states,
                    agent_id=aid,
                    timestep=t0 + step + 1,
                    scenario=scenario,
                    rng=rng,
                )
                new_ks = self.kinematic.step(current[aid], accel, steer, agent_types[aid])
                current[aid] = new_ks
                result[idx, step] = new_ks.to_array()

        return result

    def _select_diverse_top(self, n: int) -> List[BehavioralParams]:
        """Select top-n diverse organisms from the population."""
        # Sort by fitness
        sorted_orgs = sorted(
            self.population.organisms,
            key=lambda o: o.fitness or 0,
            reverse=True,
        )

        selected = []
        selected_params = []

        for org in sorted_orgs:
            if len(selected) >= n:
                break

            params = genome_to_params(org.genome)

            # Check diversity: must differ from all selected
            is_diverse = True
            for existing in selected_params:
                dist = self._params_distance(params, existing)
                if dist < 0.05:  # too similar
                    is_diverse = False
                    break

            if is_diverse:
                selected.append(org)
                selected_params.append(params)

        # If not enough diverse, fill with top organisms
        while len(selected_params) < n:
            idx = len(selected_params) % len(sorted_orgs)
            params = genome_to_params(sorted_orgs[idx].genome)
            # Add noise for diversity
            params.speed_factor += np.random.normal(0, 0.1)
            params.noise_scale = max(0.005, params.noise_scale + np.random.normal(0, 0.01))
            selected_params.append(params)

        return selected_params

    @staticmethod
    def _params_distance(a: BehavioralParams, b: BehavioralParams) -> float:
        """Normalized distance between two parameter sets."""
        diffs = [
            (a.speed_factor - b.speed_factor) / 0.8,
            (a.follow_time_gap - b.follow_time_gap) / 2.5,
            (a.min_follow_dist - b.min_follow_dist) / 7.0,
            (a.lane_steer_gain - b.lane_steer_gain) / 3.5,
            (a.heading_steer_gain - b.heading_steer_gain) / 4.2,
            (a.noise_scale - b.noise_scale) / 0.05,
        ]
        return float(np.sqrt(np.mean(np.array(diffs) ** 2)))
