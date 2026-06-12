# Contributing Agent Simulation Scenes to MatrAIx

MatrAIx is building an open platform for creating, running, and evaluating agent environments. One important part of the project is **agent simulation scenes**: reusable environments where multiple agents interact with each other, with tools, and with a changing world state.

This document explains how to contribute a new agent simulation scene to MatrAIx.

A scene can be inspired by systems such as:

* Social simulation environments, e.g. CAMEL-AI OASIS, where many agents interact on a simulated social platform through actions such as posting, commenting, following, liking, searching, and refreshing.
* Marketplace simulation environments, e.g. Microsoft Magentic Marketplace, where buyer agents and seller/service agents interact through search, recommendation, negotiation, and transaction protocols.

The goal of MatrAIx is not to copy a specific environment, but to provide a general interface so that different agentic worlds can be implemented, evaluated, and compared in a unified way.

---

## 1. What is an Agent Scene?

An **agent scene** is a self-contained simulation environment with:

1. **Agents**
   Autonomous or semi-autonomous entities that observe the environment and take actions.

2. **Environment State**
   The current state of the simulated world, such as posts, users, products, messages, tasks, offers, inventory, or reputation.

3. **Action Space**
   The set of actions available to agents. For example:

   * Social scene: create post, comment, like, follow, search, refresh feed.
   * Marketplace scene: search service, send inquiry, propose offer, accept offer, reject offer, leave review.
   * Collaboration scene: assign task, send message, edit document, call tool, submit result.

4. **Observation Function**
   The logic that decides what each agent can see at each simulation step.

5. **Transition Function**
   The logic that updates the environment after agents take actions.

6. **Evaluation Metrics**
   Quantitative or qualitative measures used to evaluate the simulation, such as task success, welfare, fairness, efficiency, engagement, information spread, robustness, or manipulation risk.

A MatrAIx scene should be implemented as a modular package that can be loaded and executed by the MatrAIx runtime.

---

## 2. Design Goals

When contributing a scene, please follow these design goals:

### 2.1 Reproducibility

A scene should be runnable with a fixed random seed. Given the same config, model, dataset, and seed, the simulation should produce comparable results.

### 2.2 Modularity

A scene should separate:

* Agent logic
* Environment state
* Action definitions
* Observation generation
* Simulation loop
* Evaluation metrics
* Dataset/configuration files

This makes the scene easier to debug, extend, and benchmark.

### 2.3 Scalability

The scene should support small local runs first, then scale to larger experiments. For example:

* Debug mode: 2-5 agents, 3-5 steps
* Small benchmark: 10-100 agents
* Large benchmark: 1,000+ agents, if supported

Do not assume every contributor has access to expensive LLM APIs or GPUs.

### 2.4 Model-Agnostic Agents

The scene should not be hard-coded to a single model provider. Agent policies should be pluggable, for example:

* OpenAI-compatible API
* Local model
* Rule-based baseline
* Random policy
* Human-controlled policy
* Replay policy from a saved trajectory

### 2.5 Clear Evaluation

Every scene should define what “good behavior” means. For example:

* In a marketplace scene, good behavior may mean high user utility, fair exposure for sellers, efficient matching, and low manipulation.
* In a social scene, good behavior may mean realistic information diffusion, stable community structure, diverse content exposure, or robustness against misinformation.
* In a collaboration scene, good behavior may mean task completion, low cost, low error rate, and high coordination quality.

---

## 3. Recommended Repository Structure

A contributed scene should follow this structure:

```text
MatrAIx/
  scenes/
    your_scene_name/
      README.md
      scene.py
      config.yaml
      actions.py
      agents.py
      environment.py
      observation.py
      metrics.py
      data/
        sample_agents.json
        sample_items.json
      examples/
        run_small.py
        run_debug.py
      tests/
        test_scene.py
        test_actions.py
        test_metrics.py
```

### File Responsibilities

#### `README.md`

Explains the scene:

* What the scene simulates
* What agents exist
* What actions are supported
* What data is required
* How to run a small example
* What metrics are reported

#### `scene.py`

Defines the top-level scene class. This is the main entry point used by MatrAIx.

#### `config.yaml`

Stores configurable parameters, such as:

```yaml
scene_name: social_feed
num_agents: 20
num_steps: 10
seed: 42

model:
  provider: openai
  name: gpt-4o-mini
  temperature: 0.7

environment:
  platform: social
  recommendation: hot_score
  max_observation_items: 20

logging:
  save_trajectory: true
  output_dir: runs/social_feed_debug
```

#### `actions.py`

Defines all valid actions in the scene.

Example:

```python
from enum import Enum
from pydantic import BaseModel
from typing import Optional, Dict, Any


class ActionType(str, Enum):
    DO_NOTHING = "do_nothing"
    CREATE_POST = "create_post"
    CREATE_COMMENT = "create_comment"
    LIKE_POST = "like_post"
    FOLLOW_USER = "follow_user"
    SEARCH = "search"


class AgentAction(BaseModel):
    agent_id: str
    action_type: ActionType
    action_args: Dict[str, Any] = {}
```

#### `agents.py`

Defines agent profiles and policies.

Example:

```python
from pydantic import BaseModel
from typing import Optional, Dict, Any


class AgentProfile(BaseModel):
    agent_id: str
    name: str
    role: str
    persona: Optional[str] = None
    memory: Dict[str, Any] = {}
```

The actual policy can be LLM-based, rule-based, random, or replay-based.

#### `environment.py`

Stores and updates the world state.

Example responsibilities:

* Store users, posts, comments, messages, products, offers, or tasks.
* Validate whether actions are legal.
* Apply actions to the state.
* Return updated state after each step.

#### `observation.py`

Controls what each agent sees.

This is important because agents should not always observe the full environment. For example:

* In a social scene, an agent may only see its feed, notifications, search results, and own profile.
* In a marketplace scene, a buyer may see search results and seller responses, while a seller may only see incoming requests.
* In a collaboration scene, an agent may only see assigned tasks and shared messages.

#### `metrics.py`

Computes evaluation metrics after or during the simulation.

Example metrics:

```python
class SceneMetrics:
    def compute(self, trajectory, final_state):
        return {
            "num_actions": len(trajectory.actions),
            "num_successful_interactions": 0,
            "average_response_time": 0.0,
            "task_success_rate": 0.0,
        }
```

---

## 4. Required Scene Interface

Every scene should implement the following interface.

```python
class BaseScene:
    def reset(self, seed: int | None = None):
        """
        Reset the scene to its initial state.
        Return the initial observations for all active agents.
        """
        raise NotImplementedError

    def step(self, actions: dict):
        """
        Execute one simulation step.

        Args:
            actions: A dictionary mapping agent_id to AgentAction.

        Returns:
            observations: New observations for agents.
            rewards: Optional reward dictionary.
            done: Whether the simulation is finished.
            info: Extra debugging and logging information.
        """
        raise NotImplementedError

    def render(self):
        """
        Optional: return a human-readable view of the current state.
        """
        raise NotImplementedError

    def evaluate(self):
        """
        Compute final metrics for the scene.
        """
        raise NotImplementedError
```

The minimum implementation should support:

```python
scene = YourScene(config)
obs = scene.reset(seed=42)

for step in range(config.num_steps):
    actions = {}
    for agent_id, agent_obs in obs.items():
        actions[agent_id] = agent_policy(agent_obs)
    obs, rewards, done, info = scene.step(actions)
    if done:
        break

metrics = scene.evaluate()
print(metrics)
```

---

## 5. Scene Lifecycle

A MatrAIx scene runs in the following lifecycle:

```text
Load config
    ↓
Initialize environment
    ↓
Load agent profiles
    ↓
Reset scene
    ↓
For each timestep:
    Generate observations
    Agents produce actions
    Validate actions
    Apply actions to environment
    Log transition
    Compute intermediate metrics
    Check termination
    ↓
Compute final metrics
    ↓
Save trajectory and report
```

---

## 6. Action Design

Actions should be explicit, typed, and easy to validate.

A good action should answer:

1. Who performs the action?
2. What action type is it?
3. What arguments are required?
4. What state does it modify?
5. Can it fail?
6. How is failure represented?

Example social actions:

```text
CREATE_POST(content)
CREATE_COMMENT(post_id, content)
LIKE_POST(post_id)
FOLLOW_USER(target_user_id)
SEARCH(query)
DO_NOTHING()
```

Example marketplace actions:

```text
SEARCH_SERVICE(query, constraints)
CONTACT_SELLER(seller_id, message)
MAKE_OFFER(seller_id, item_id, price)
ACCEPT_OFFER(offer_id)
REJECT_OFFER(offer_id)
LEAVE_REVIEW(transaction_id, rating, text)
DO_NOTHING()
```

Example collaboration actions:

```text
SEND_MESSAGE(channel_id, content)
ASSIGN_TASK(task_id, agent_id)
EDIT_DOCUMENT(document_id, patch)
CALL_TOOL(tool_name, args)
SUBMIT_RESULT(task_id, result)
DO_NOTHING()
```

---

## 7. Observation Design

Observation design is one of the most important parts of an agent simulation.

Each observation should include only information available to that agent at that moment.

Example social observation:

```json
{
  "agent_id": "user_001",
  "time_step": 3,
  "profile": {
    "name": "Alice",
    "interests": ["AI", "startups", "robotics"]
  },
  "feed": [
    {
      "post_id": "post_123",
      "author_id": "user_009",
      "content": "New robotics demo released today.",
      "num_likes": 12,
      "num_comments": 3
    }
  ],
  "notifications": [],
  "available_actions": [
    "CREATE_POST",
    "CREATE_COMMENT",
    "LIKE_POST",
    "FOLLOW_USER",
    "SEARCH",
    "DO_NOTHING"
  ]
}
```

Example marketplace observation:

```json
{
  "agent_id": "buyer_001",
  "time_step": 2,
  "goal": "Find a contractor to renovate a small kitchen under $8000.",
  "search_results": [
    {
      "seller_id": "seller_031",
      "service": "Kitchen renovation",
      "rating": 4.7,
      "estimated_price": 7500
    }
  ],
  "messages": [
    {
      "from": "seller_031",
      "content": "We can schedule an inspection this week."
    }
  ],
  "available_actions": [
    "SEARCH_SERVICE",
    "CONTACT_SELLER",
    "MAKE_OFFER",
    "ACCEPT_OFFER",
    "REJECT_OFFER",
    "DO_NOTHING"
  ]
}
```

---

## 8. Transition Function

The transition function defines how actions change the environment.

For every action, define:

```text
precondition → state update → side effect → logged event
```

Example:

```text
Action: LIKE_POST(post_id)

Precondition:
- post_id exists
- agent has not liked this post before

State update:
- Add agent_id to post.likes
- Increment post.num_likes

Side effect:
- The post author receives a notification

Logged event:
- {time, agent_id, action_type, post_id, success}
```

The transition function should be deterministic when the random seed is fixed.

---

## 9. Agent Policy

A scene should support multiple types of agent policies.

### 9.1 Rule-Based Policy

Useful for debugging.

```python
class RandomPolicy:
    def act(self, observation):
        return AgentAction(
            agent_id=observation["agent_id"],
            action_type="DO_NOTHING",
            action_args={},
        )
```

### 9.2 LLM Policy

Useful for realistic behavior.

The LLM policy should receive:

* Agent profile
* Current observation
* Available actions
* Output schema
* Optional memory

The LLM should output a structured action, not free-form text.

Example output schema:

```json
{
  "action_type": "CREATE_COMMENT",
  "action_args": {
    "post_id": "post_123",
    "content": "This is very interesting."
  }
}
```

### 9.3 Replay Policy

Useful for deterministic testing.

A replay policy loads actions from a saved trajectory and replays them step by step.

---

## 10. Logging and Trajectory Format

Every scene should save a trajectory file.

Recommended format:

```json
{
  "scene_name": "social_feed",
  "run_id": "2026-01-01-12-00-00",
  "config": {},
  "steps": [
    {
      "time_step": 0,
      "observations": {
        "agent_001": {}
      },
      "actions": {
        "agent_001": {
          "action_type": "CREATE_POST",
          "action_args": {
            "content": "Hello world"
          }
        }
      },
      "events": [
        {
          "event_type": "post_created",
          "agent_id": "agent_001",
          "post_id": "post_001"
        }
      ],
      "metrics": {}
    }
  ],
  "final_metrics": {}
}
```

Trajectory logging is important because it allows us to:

* Debug agent behavior
* Reproduce failures
* Compare different models
* Build training data
* Run offline evaluation
* Analyze emergent behavior

---

## 11. Evaluation Metrics

A scene should include at least one default metric.

### 11.1 General Metrics

```text
num_steps
num_agents
num_actions
action_success_rate
average_tokens_per_agent
average_latency_per_step
total_cost
```

### 11.2 Social Simulation Metrics

```text
engagement_rate
number_of_posts
number_of_comments
information_spread
follower_graph_density
content_diversity
polarization_score
misinformation_exposure
```

### 11.3 Marketplace Metrics

```text
buyer_utility
seller_revenue
transaction_success_rate
market_efficiency
welfare
fairness_of_exposure
search_bias
first_proposal_bias
manipulation_success_rate
```

### 11.4 Collaboration Metrics

```text
task_success_rate
time_to_completion
number_of_messages
tool_call_success_rate
coordination_error_rate
redundant_work_rate
```

---

## 12. Minimal Example: Social Feed Scene

```python
class SocialFeedScene(BaseScene):
    def __init__(self, config):
        self.config = config
        self.state = None
        self.time_step = 0

    def reset(self, seed=None):
        set_seed(seed)
        self.time_step = 0
        self.state = {
            "users": load_users(self.config["data"]["users"]),
            "posts": {},
            "comments": {},
            "follows": {},
        }
        return self._get_observations()

    def step(self, actions):
        events = []

        for agent_id, action in actions.items():
            event = self._apply_action(agent_id, action)
            events.append(event)

        self.time_step += 1

        observations = self._get_observations()
        rewards = {}
        done = self.time_step >= self.config["num_steps"]
        info = {"events": events}

        return observations, rewards, done, info

    def evaluate(self):
        return {
            "num_posts": len(self.state["posts"]),
            "num_comments": len(self.state["comments"]),
        }

    def _get_observations(self):
        observations = {}
        for user_id in self.state["users"]:
            observations[user_id] = build_social_observation(
                user_id=user_id,
                state=self.state,
                time_step=self.time_step,
            )
        return observations

    def _apply_action(self, agent_id, action):
        if action.action_type == "CREATE_POST":
            return create_post(self.state, agent_id, action.action_args)
        elif action.action_type == "CREATE_COMMENT":
            return create_comment(self.state, agent_id, action.action_args)
        elif action.action_type == "LIKE_POST":
            return like_post(self.state, agent_id, action.action_args)
        elif action.action_type == "DO_NOTHING":
            return {"event_type": "do_nothing", "agent_id": agent_id}
        else:
            return {
                "event_type": "invalid_action",
                "agent_id": agent_id,
                "reason": f"Unknown action type: {action.action_type}",
            }
```

---

## 13. Minimal Example: Marketplace Scene

```python
class MarketplaceScene(BaseScene):
    def __init__(self, config):
        self.config = config
        self.state = None
        self.time_step = 0

    def reset(self, seed=None):
        set_seed(seed)
        self.time_step = 0
        self.state = {
            "buyers": load_buyers(self.config["data"]["buyers"]),
            "sellers": load_sellers(self.config["data"]["sellers"]),
            "items": load_items(self.config["data"]["items"]),
            "messages": [],
            "offers": {},
            "transactions": {},
        }
        return self._get_observations()

    def step(self, actions):
        events = []

        for agent_id, action in actions.items():
            event = self._apply_action(agent_id, action)
            events.append(event)

        self.time_step += 1

        observations = self._get_observations()
        rewards = self._compute_rewards(events)
        done = self.time_step >= self.config["num_steps"]
        info = {"events": events}

        return observations, rewards, done, info

    def evaluate(self):
        return {
            "num_transactions": len(self.state["transactions"]),
            "total_revenue": sum(
                tx["price"] for tx in self.state["transactions"].values()
            ),
            "transaction_success_rate": self._transaction_success_rate(),
        }

    def _apply_action(self, agent_id, action):
        if action.action_type == "SEARCH_SERVICE":
            return search_service(self.state, agent_id, action.action_args)
        elif action.action_type == "CONTACT_SELLER":
            return contact_seller(self.state, agent_id, action.action_args)
        elif action.action_type == "MAKE_OFFER":
            return make_offer(self.state, agent_id, action.action_args)
        elif action.action_type == "ACCEPT_OFFER":
            return accept_offer(self.state, agent_id, action.action_args)
        elif action.action_type == "REJECT_OFFER":
            return reject_offer(self.state, agent_id, action.action_args)
        elif action.action_type == "DO_NOTHING":
            return {"event_type": "do_nothing", "agent_id": agent_id}
        else:
            return {
                "event_type": "invalid_action",
                "agent_id": agent_id,
                "reason": f"Unknown action type: {action.action_type}",
            }
```

---

## 14. Testing Requirements

Every scene should include basic tests.

Minimum tests:

```text
test_reset_returns_observations
test_valid_action_updates_state
test_invalid_action_does_not_crash
test_step_is_deterministic_with_seed
test_evaluate_returns_metrics
```

Example:

```python
def test_reset_returns_observations():
    scene = SocialFeedScene(config)
    obs = scene.reset(seed=42)
    assert isinstance(obs, dict)
    assert len(obs) > 0


def test_invalid_action_does_not_crash():
    scene = SocialFeedScene(config)
    obs = scene.reset(seed=42)

    actions = {
        "agent_001": AgentAction(
            agent_id="agent_001",
            action_type="UNKNOWN_ACTION",
            action_args={},
        )
    }

    obs, rewards, done, info = scene.step(actions)
    assert "events" in info
```

---

## 15. Contribution Checklist

Before submitting a scene, please make sure:

* [ ] The scene has a clear README.
* [ ] The scene can run with a small example.
* [ ] The scene defines typed actions.
* [ ] The scene defines agent observations.
* [ ] The scene implements `reset`, `step`, `render`, and `evaluate`.
* [ ] The scene logs trajectories.
* [ ] The scene supports fixed random seeds.
* [ ] The scene includes at least one rule-based or random baseline policy.
* [ ] The scene includes at least one evaluation metric.
* [ ] The scene has basic tests.
* [ ] The scene does not require private API keys for basic tests.
* [ ] The scene avoids committing large generated files or private data.

---

## 16. Pull Request Format

When opening a pull request, please include:

```text
## Scene Name

Briefly describe the scene.

## Motivation

Why is this scene useful for agent simulation?

## Agents

What types of agents are included?

## Actions

List the supported actions.

## Environment State

Describe the main state objects.

## Observations

Describe what each agent can observe.

## Metrics

List the evaluation metrics.

## Example Run

Show the command used to run the scene.

## Limitations

Describe known limitations or assumptions.
```

---

## 17. Example PR Summary

```text
## Scene Name

Social Feed Simulation

## Motivation

This scene simulates how LLM agents interact on a social feed. It can be used to study information diffusion, content engagement, and group-level behavior.

## Agents

The scene includes user agents with profiles, interests, and memory.

## Actions

CREATE_POST, CREATE_COMMENT, LIKE_POST, FOLLOW_USER, SEARCH, DO_NOTHING.

## Environment State

The environment stores users, posts, comments, follows, likes, and notifications.

## Observations

Each agent observes its own profile, feed, notifications, and available actions.

## Metrics

The scene reports engagement rate, number of posts, number of comments, information spread, and action success rate.

## Example Run

python scenes/social_feed/examples/run_small.py

## Limitations

The current version uses a simple feed ranking function and does not yet model long-term memory decay.
```

---

## 18. Reference Scene Types We Want

We are especially interested in the following types of scenes:

### 18.1 Social Platform Scenes

Inspired by large-scale social simulators.

Possible topics:

* Information spread
* Herd behavior
* Group polarization
* Recommendation feedback loops
* Misinformation robustness
* Multi-agent content creation

### 18.2 Marketplace Scenes

Inspired by two-sided agentic marketplaces.

Possible topics:

* Buyer-seller matching
* Search and recommendation
* Negotiation
* Seller competition
* Market fairness
* Consumer welfare
* Manipulation and bias

### 18.3 Collaborative Work Scenes

Possible topics:

* Multi-agent coding
* Research collaboration
* Document editing
* Task assignment
* Tool-use coordination
* Project management simulation

### 18.4 Game or Strategy Scenes

Possible topics:

* Resource allocation
* Negotiation
* Coalition formation
* Hidden information games
* Long-horizon planning

### 18.5 Web or App Interaction Scenes

Possible topics:

* Agents operating websites
* Agents using mobile apps
* UI-based task completion
* Human-agent workflow simulation
* App testing before release

---

## 19. Design Principle

A good MatrAIx scene should not only be a demo. It should be an environment where we can ask serious questions about agent behavior:

* What happens when many agents interact?
* How do agents change the environment?
* How does the environment influence future agent behavior?
* Which agents benefit or lose under different rules?
* Can the system be manipulated?
* Are outcomes fair, efficient, and robust?
* Can the scene generate useful training or evaluation data?

If your scene helps answer one of these questions, it is a valuable contribution to MatrAIx.

