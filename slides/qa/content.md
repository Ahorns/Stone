
## Slide 1

- UCL  ·  THE BARTLETT
- RESEARCH PLAN  ·  2026
- Waymo Open Sim Agents
- Challenge
- Task understanding and a research-oriented initial plan
- Using WOSAC as a benchmark to study realistic sim-agent design for autonomous driving
- Supervisor meeting  ·  28 April 2026

[Notes] Today I want to discuss the Waymo Open Sim Agents Challenge. My goal is not to chase a leaderboard ranking, but to use WOSAC as a standardised benchmark for studying simulation, behaviour modelling an...

## Slide 2

- Motivation: building research foundations for autonomous driving
- WOSAC · Research Plan
- 01
- Why I chose this task
- Sim agents sit at the intersection of behaviour modelling, motion prediction, multi-agent interaction, planning evaluation and safety-critical simulation. WOSAC turns these into a single, well-defined benchmark.
- 1
- Behaviour
- modelling
- 2
- Motion
- prediction
- 3
- Multi-agent
- interaction
- 4
- Planning
- evaluation
- 5
- Safety-critical
- simulation
- This project treats the challenge as a research platform — not as a competition submission.

[Notes] I chose this task because it systematically trains the core capabilities of autonomous driving — prediction, simulation, multi-agent interaction, behaviour modelling, planning evaluation. The aim is n...

## Slide 3

- Background: why realistic simulation matters
- WOSAC · Research Plan
- 02
- Real-world testing alone is not enough
- expensive to scale
- rare or risky scenarios appear infrequently
- evaluation feedback is slow and noisy
- hard to attribute failures to specific behaviours
- Simulation provides a scalable alternative
- test rare or risky scenarios at scale
- evaluate planning and behaviour models
- study multi-agent interactions in closed loop
- reduce real-world testing cost
- Simulation is useful only if the surrounding agents behave realistically.
- The key problem is not replaying logs, but generating realistic interactive traffic behaviour.

[Notes] Autonomous-driving systems are hard to evaluate by real-world driving alone — the cost is high, the risk is high, and many edge cases rarely appear. Simulation is therefore essential, but only if the ...

## Slide 4

- Task: simulating the future traffic world
- WOSAC · Research Plan
- 03
- INPUT — PAST 1 SECOND
- Vehicle, pedestrian, cyclist states
- Autonomous-vehicle (ADV) state
- Road map and lane structure
- Traffic-light states
- Sim-agent model
- OUTPUT — 32 ROLLOUTS × 8 S
- Joint future for all agents (incl. ADV)
- Each agent: x, y, z position + heading
- 32 stochastic rollouts per scenario
- Example rollout — each box is a simulated agent (position + heading) over 8 s.
- The model acts as a traffic-world simulator: it generates how the whole scene evolves, not a single trajectory.

[Notes] In plain terms, this task is to train a traffic-world simulator. Given roughly 1 second of real-road history — positions, speeds, pedestrians, cyclists, the road map, traffic lights — the model must g...

## Slide 5

- Framing: from competition task to sim-agent design problem
- WOSAC · Research Plan
- 04
- I want to use WOSAC as a controlled benchmark, not as a leaderboard target.
- COMPETITION OBJECTIVE
- Submit 32 future rollouts per scenario.
- fixed format and metric
- leaderboard ranking
- test-set attempts: 3 per 30 days
- MY RESEARCH OBJECTIVE
- Identify one modelling weakness and turn it into a strong sim-agent design.
- diagnose where baselines fail
- isolate one capability to optimise
- evaluate what the design improves
- WOSAC provides the dataset, simulator, metrics and protocol. My contribution should be a focused model improvement.

[Notes] This is the point I want to align on with you: I am not framing this project as 'compete in a challenge'. It already provides data, simulator, submission format and evaluation. So I want to use it as ...

## Slide 6

- Benchmark platform: data, simulator, submission
- WOSAC · Research Plan
- 05
- Dataset — Waymo Open Motion Dataset
- Real-world scenarios: agent trajectories, object types, map features, traffic-light states.
- Simulator — Waymax
- Scenario loading, multi-agent rollout interface, baseline agents, submission generation.
- Rollout format
- 32 rollouts × 8 s (80 steps @ 10 Hz). Position + heading per agent. 150 serialized protos per submission. 3 test-set attempts per 30 days.
- Required factorization (2025 rule)
- ADV (blue) and world (orange) states must be conditionally independent given the previous joint state. Object dimensions are fixed from the final history frame.
- A standardised environment for testing whether a sim-agent design improves realism.

[Notes] The benefit of this benchmark is that it is bounded. Data comes from the Waymo Open Motion Dataset; simulation and evaluation can be done in Waymax; the submission is a set of trajectory rollouts, not...

## Slide 7

- Evaluation: distribution matching, not trajectory error
- WOSAC · Research Plan
- 06
- WOSAC scores submissions as a distribution-matching problem: the simulated rollout distribution is compared with the real-world distribution.
- Motion realism (kinematic)
- linear speed + acceleration
- angular speed + acceleration
- 2025: smoother estimation
- Interaction realism
- collision (capsule shape — 2025)
- distance to nearest object
- time-to-collision (vehicles; new filter)
- Map adherence
- off-road behaviour
- distance to road edges
- traffic-light violation (2025: NEW)
- per-feature negative log-likelihood   →   weighted-mean meta-metric   →   higher = more realistic
- 2025 metric updates mean older leaderboard scores are not directly comparable.

[Notes] This is not standard trajectory prediction. The model produces 32 futures, those form a simulated behaviour distribution, and the score asks how well that distribution matches the real-driving distrib...

## Slide 8

- Candidate optimisation points
- WOSAC · Research Plan
- 07
- Four directions where baseline sim agents typically fail — the project should pick one.
- A
- Closed-loop stability
- PROBLEM
- Small one-step errors accumulate over 80 steps.
- POSSIBLE FOCUS
- Train a model that stays stable during long autoregressive rollout.
- B
- Interaction realism
- PROBLEM
- Independent prediction causes collisions or unrealistic yielding.
- POSSIBLE FOCUS
- Agent–agent attention or graph-based interaction modelling.
- C
- Map adherence
- PROBLEM
- Agents drift off-road or violate lane / traffic constraints.
- POSSIBLE FOCUS
- Map-conditioned decoding or constraint-aware rollout.
- D
- Multimodal generation
- PROBLEM
- One deterministic future cannot represent real-world uncertainty.
- POSSIBLE FOCUS
- Latent / mixture / token-based sampling for diverse rollouts.

[Notes] I do not want to start with one big complex model. The more reasonable path is to run the benchmark, diagnose where baselines fail, then pick the most worthwhile direction — closed-loop stability, int...

## Slide 9

- Proposed initial focus: stable, interaction-aware sim agents
- WOSAC · Research Plan
- 08
- A good sim agent must remain stable and socially plausible across an 80-step closed-loop rollout — not just predict the next position accurately.
- 1
- Autoregressive sim-agent model
- 2
- Agent–agent interaction encoding
- 3
- Map-conditioned state update
- 4
- Loss terms: collision · off-road · smoothness
- First research goal
- Design a sim agent that improves closed-loop realism — not just open-loop prediction accuracy.

[Notes] I lean towards starting on closed-loop stability and interaction realism, because the essence of a sim agent is not whether the next step is accurate, but whether 80-step rollouts stay stable, plausib...

## Slide 10

- Proposed roadmap
- WOSAC · Research Plan
- 09
- Diagnosis-driven: understand failures first, then design a focused improvement.
- 1
- Understand data, metrics, rollout format
- 2
- Reproduce Waymax baseline pipeline
- 3
- Diagnose baseline failure modes
- 4
- Select one research focus
- 5
- Design improved sim-agent model
- 6
- Compare against simple baselines
- 7
- Analyse improvements and limitations
- Phased breakdown
- Phase 1 Stages 1–3 — reproduce + diagnose      
- Phase 2 Stages 4–5 — focused model design      
- Phase 3 Stages 6–7 — evaluate + analyse

[Notes] I do not want to jump straight to a complex model. A safer route is to understand the data and metrics, reproduce the Waymax pipeline, then use simple baselines to expose where the failures are — off-...

## Slide 11

- Phase 1: reproduce and diagnose baselines
- WOSAC · Research Plan
- 10
- Goal — build a working benchmark pipeline and understand where simple agents fail.
- Tasks
- Load WOMD scenarios via Waymax
- Visualise agents, maps, traffic lights
- Generate valid 32-rollout simulations
- Run constant-velocity / rule-based baselines
- Score against the official meta-metric
- Failure modes to characterise
- Collisions between agents
- Off-road drift on curves and intersections
- Unrealistic acceleration profiles
- Lack of diversity across the 32 rollouts
- Traffic-light violations (2025 metric)
- Diagnosis decides which modelling weakness is worth optimising.

[Notes] Phase 1 is about pipeline and diagnosis, not performance. Constant-velocity may look fine in the short term but will likely drift off lane in complex intersections, cause collisions, or lack diversity...

## Slide 12

- Phase 2: design a focused sim-agent model
- WOSAC · Research Plan
- 11
- The goal is not the largest model — it is a model that clearly improves one important capability.
- Scene state
- (agent history + map + traffic lights)
- Interaction +
- map encoder
- Stochastic
- state decoder
- Next scene
- state
- repeat for 80 steps
- Autoregressive update
- Roll the scene forward step by step.
- Interaction encoder
- Attention or GNN over neighbouring agents.
- Map-conditioned decoder
- Anchor predictions to lanes and signals.
- Stochastic sampling
- Latent variable for diverse 32 rollouts.
- Constraint-aware loss
- Penalise collision, off-road, jerk.
- Success = a clear design improvement with interpretable gains, not necessarily a top score.

[Notes] Phase 2 is not about building the biggest, most complex model. It is about a model with a clear purpose. If I pick interaction realism, the architecture and loss should both target agent–agent interac...

## Slide 13

- Phase 3: evaluate the design, not only the score
- WOSAC · Research Plan
- 12
- Baselines to compare
- Constant-velocity
- Simple rule-based
- Initial learned baseline
- Dimensions to analyse
- Motion realism
- Interaction realism
- Map adherence
- Closed-loop stability
- Diversity across 32 rollouts
- Key research question
- Which failure mode does the design reduce most clearly?
- Does the gain hold across scenario types?
- Where does it still fail?
- The final result should explain why the model works, where it improves, and where it still fails.

[Notes] Evaluation should not be a single aggregate score. The harder question is: what specifically did this design improve? Fewer collisions? Less off-road? More stable 80-step rollouts? More plausible dive...

## Slide 14

- Discussion questions
- WOSAC · Research Plan
- 13
- Q1
- Is this a suitable benchmark for building autonomous-driving research foundations?
- Q2
- Which research focus is most valuable: closed-loop stability, interaction realism, map adherence, or multimodal generation?
- Q3
- Should I start with rule-based diagnosis or a small learned baseline?
- Q4
- What would a convincing 4–6 week milestone look like?
- Q5
- What kind of final output would be most useful — pipeline, model, failure-mode analysis, technical report?
- Goal of this meeting — align on scope, focus, and the first milestone.

[Notes] What I hope this meeting yields is not a yes/no on 'should I enter the competition'. It is alignment on whether this benchmark is the right research vehicle, and which specific direction to optimise f...

## Slide 15

- References
- WOSAC · Research Plan
- 14
- 1
- Montali et al. — The Waymo Open Sim Agents Challenge.
- 2
- Gulino et al. — Waymax: An Accelerated, Data-Driven Simulator for Large-Scale Autonomous Driving Research.
- 3
- Waymo Open Dataset 2025 Sim Agents Challenge — waymo.com/open/challenges/2025/sim-agents/
- 4
- Waymax WOSAC submission tutorial (official GitHub).
- 5
- Waymo Open Dataset Sim Agents tutorial.
- 6
- Recent WOSAC 2024–2025 technical reports.
- These are the materials I will read and reproduce; their content is folded into the earlier slides.

[Notes] These are the materials I will read and reproduce. The presentation has folded their content into the earlier slides rather than dedicating a slide per paper....
