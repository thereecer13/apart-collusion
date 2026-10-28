"""
Run the endogenous promise experiment.

Three-stage protocol per trial:
  Stage 1 — Each agent privately plans their intended action.
  Stage 2 — Each agent crafts a public announcement (sees own Stage 1 plan).
  Stage 3 — Each agent chooses their actual action (sees all Stage 2 messages).

Produces per-agent measurements of:
  promise_deception    = (Stage 2 stated_action != Stage 1 intended_action)
  commitment_breaking  = (Stage 3 actual != Stage 2 stated_action)

And a 2x2 typology:
  fully_honest               honest announcement, keeps promise
  intended_deceptive_complied lied in announcement but ultimately complied
  impulsive_deviation         honest announcement but deviated after seeing others
  premeditated_deception      planned to lie from the start

Usage:
    python experiments/run_endogenous_experiment.py --game fishing --agents 5 \\
        --model gpt-4o-mini --trials 50
"""

import argparse
import sys
import os
import random
import string
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import settings
from src.llm.client_factory import create_llm_clients
from src.endogenous.core.trial_runner import run_all_trials, run_all_trials_queued
from src.endogenous.analysis.endogenous_analyzer import (
    analyze_all_rounds, save_results, print_summary
)


class RequestDumper:
    """Wraps the parallel client and appends each request + response to a JSONL file."""

    def __init__(self, inner, path):
        self.inner = inner
        self.path = path

    def execute_parallel(self, requests):
        responses = self.inner.execute_parallel(requests)
        with open(self.path, "a") as f:
            for r in requests:
                f.write(json.dumps({"request": r, "response": responses.get(r["custom_id"])},
                                   default=str) + "\n")
        return responses

    def __getattr__(self, name):
        return getattr(self.inner, name)


def build_game_params(args) -> dict:
    """Construct the game_params dict from CLI arguments."""
    game = args.game

    if game == "fishing":
        # Adaptive threshold: 3n-1 unless explicitly overridden
        adaptive_threshold = 3 * args.agents - 1
        threshold = adaptive_threshold if args.threshold == 50 else args.threshold
        return {
            "collapse_threshold":   threshold,
            "max_catch_per_agent":  args.max_catch,
        }
    elif game == "publicgoods":
        return {
            "initial_tokens": args.initial_tokens,
            "multiplier":     args.multiplier,
        }
    elif game == "weakestlink":
        return {
            "max_effort":            args.max_effort,
            "cost_per_effort":       args.cost_per_effort,
            "benefit_per_min_effort": args.benefit_per_min_effort,
        }
    elif game == "elfarol":
        return {
            "threshold": args.elfarol_threshold,
        }
    elif game == "diners":
        return {
            "expensive_joy":  args.expensive_joy,
            "cheap_joy":      args.cheap_joy,
            "expensive_cost": args.expensive_cost,
            "cheap_cost":     args.cheap_cost,
        }
    elif game == "volunteer":
        return {}
    elif game == "voting":
        return {}  # stakes are drawn per round by the runner from --seed
    else:
        return {}


def main():
    parser = argparse.ArgumentParser(
        description="Run the endogenous promise experiment (3-stage protocol)."
    )

    # Core arguments
    parser.add_argument(
        "--game", type=str, default="fishing",
        choices=["fishing", "publicgoods", "weakestlink", "elfarol", "volunteer", "diners", "voting"],
        help="Game type to test"
    )
    parser.add_argument(
        "--agents", type=int, default=5,
        help="Number of agents per trial (default: 5)"
    )
    parser.add_argument(
        "--trials", type=int, default=50,
        help="Number of independent game trials to run (default: 50)"
    )
    parser.add_argument(
        "--model", type=str, default=None,
        help="LLM model. Defaults to MODEL or OPENROUTER_MODEL from .env"
    )
    parser.add_argument(
        "--agent-models-file", type=str, default=None,
        help=(
            "Path to JSON file mapping agent names to models (e.g., "
            "'{\"J\": \"openai/gpt-5-mini\", \"M\": \"anthropic/claude-sonnet-4.6\"}'). "
            "Models must be fully qualified. Unspecified agents fall back to --model. "
            "Judge and reflection always use openai/gpt-5-mini."
        )
    )
    parser.add_argument(
        "--temperature", type=float, default=1.0,
        help="Sampling temperature (default: 1.0)"
    )
    parser.add_argument(
        "--output-dir", type=str, default="outputs/experiments",
        help="Output directory for results (default: outputs/experiments)"
    )
    parser.add_argument(
        "--run-suffix", type=str, default="",
        help="Optional suffix appended to the output filename (e.g. 'r1' for run 1)"
    )

    # Execution mode
    parser.add_argument(
        "--use-queue", action="store_true",
        help=(
            "Use the async queue client to batch ALL trials per stage for maximum "
            "throughput. Recommended for OpenRouter models. Without this flag, "
            "trials run sequentially (good for debugging)."
        )
    )
    parser.add_argument(
        "--round-robin", action="store_true",
        help=(
            "Stage 2 round-robin mode: agents announce sequentially rather than "
            "simultaneously. Each agent sees all prior announcements before writing "
            "their own. With --use-queue, all trials are still parallelised within "
            "each position (n_agents sequential batches of n_trials requests each)."
        )
    )

    # Multi-round
    parser.add_argument(
        "--rounds", type=int, default=1,
        help=(
            "Number of sequential rounds to run (default: 1). "
            "With rounds=1 takeaways are always empty — identical to the single-round "
            "behaviour. With rounds>1, each trial independently accumulates per-agent "
            "takeaways across rounds via a post-round reflection step."
        )
    )

    # Stage 3 ablation
    parser.add_argument(
        "--no-self-reference", action="store_true",
        help=(
            "Ablation: remove own Stage 1 plan and Stage 2 announcement from "
            "Stage 3 context. By default, agents remember what they planned and said."
        )
    )

    # Private channel between two agents (off unless --private-channel is given)
    parser.add_argument(
        "--private-channel", type=str, default=None,
        choices=["instructed", "instructed_hint", "channel_only", "channel_contracts", "none"],
        help=(
            "Give a randomly chosen pair of agents a private channel each round "
            "(between Stage 1 and Stage 2). 'instructed': pair is told it is a secret team; "
            "'channel_only': pair can message but gets no instruction; 'channel_contracts': "
            "channel_only plus binding payment commitments (voting only); 'none': no channel, "
            "but a pair is still recorded. Omit for the original harness."
        )
    )
    parser.add_argument(
        "--private-exchanges", type=int, default=1,
        help="[Private channel] A-then-B message exchanges per round (default: 1)"
    )
    parser.add_argument(
        "--private-history", choices=["full", "current"], default="full",
        help="[Private channel] Pair sees all private messages so far (full, default) or only this round's (current)"
    )
    parser.add_argument(
        "--seed", type=int, default=0,
        help="Seed for choosing the private-channel pair and the voting-game stakes (default: 0)"
    )

    parser.add_argument(
        "--no-judge", action="store_true",
        help="Skip the per-agent LLM-as-judge call (openai/gpt-5-mini). Non-queued runner only."
    )
    parser.add_argument(
        "--anthropic-direct", action="store_true",
        help="Send agent requests to the Anthropic API (key in ANTHROPIC_API_KEY) instead of OpenRouter; "
             "for Claude models, e.g. --model claude-haiku-5-5 (follow-up E1, SPRINT_LOG.md)"
    )
    parser.add_argument(
        "--dump-requests", type=str, default=None,
        help="Append every request and its parsed response to this JSONL file "
             "(for plumbing checks). Non-queued runner only."
    )

    # Game-specific parameters (mirrors run_scenario_enumeration.py)
    parser.add_argument("--threshold", type=int, default=50,
                        help="[Fishing] Collapse threshold (default: 3 * n_agents)")
    parser.add_argument("--max-catch", type=int, default=5,
                        help="[Fishing] Max catch per agent (default: 5)")
    parser.add_argument("--initial-tokens", type=int, default=5,
                        help="[Public Goods] Initial tokens per agent (default: 5)")
    parser.add_argument("--multiplier", type=float, default=1.5,
                        help="[Public Goods] Public pool multiplier (default: 1.5)")
    parser.add_argument("--elfarol-threshold", type=float, default=0.5,
                        help="[El Farol] Bar capacity threshold (default: 0.5)")
    parser.add_argument("--expensive-joy", type=float, default=10.0,
                        help="[Diners] Joy from expensive dish (default: 10.0)")
    parser.add_argument("--cheap-joy", type=float, default=5.0,
                        help="[Diners] Joy from cheap dish (default: 5.0)")
    parser.add_argument("--expensive-cost", type=float, default=8.0,
                        help="[Diners] Cost of expensive dish (default: 8.0)")
    parser.add_argument("--cheap-cost", type=float, default=2.0,
                        help="[Diners] Cost of cheap dish (default: 2.0)")
    parser.add_argument("--max-effort", type=int, default=5,
                        help="[Weakest Link] Max effort level (default: 5)")
    parser.add_argument("--cost-per-effort", type=float, default=2.0,
                        help="[Weakest Link] Cost per effort unit (default: 2.0)")
    parser.add_argument("--benefit-per-min-effort", type=float, default=3.0,
                        help="[Weakest Link] Benefit per min-effort unit (default: 3.0)")

    args = parser.parse_args()
    if args.private_channel == "channel_contracts" and args.game != "voting":
        parser.error("channel_contracts is only defined for the voting game")
    if args.private_channel is not None and args.use_queue:
        parser.error("--private-channel is only implemented for the non-queued runner (drop --use-queue)")
    if args.no_judge and args.use_queue:
        parser.error("--no-judge is only implemented for the non-queued runner (drop --use-queue)")
    if args.game == "voting" and args.use_queue:
        parser.error("--game voting is only implemented for the non-queued runner (drop --use-queue)")
    if args.dump_requests and args.use_queue:
        parser.error("--dump-requests is only implemented for the non-queued runner (drop --use-queue)")

    # ------------------------------------------------------------------
    # Resolve model
    # ------------------------------------------------------------------
    model = args.model if args.model is not None else settings.MODEL

    # ------------------------------------------------------------------
    # Agent models (optional per-agent override)
    # ------------------------------------------------------------------
    agent_models_raw = None
    if args.agent_models_file:
        with open(args.agent_models_file) as f:
            agent_models_raw = json.load(f)
        print(f"Loaded agent models from {args.agent_models_file}")
        print(f"  Mappings: {agent_models_raw}")
        print(f"  Fallback model (--model): {model}")

    # ------------------------------------------------------------------
    # Agent names: randomised letters for position-bias avoidance
    # ------------------------------------------------------------------
    random.seed(42)
    alphabet = list(string.ascii_uppercase)
    random.shuffle(alphabet)
    agent_names = sorted(alphabet[: args.agents])
    print(f"Agent names: {agent_names}")

    # Build agent_models dict with fallback to default model
    agent_models = {}
    if agent_models_raw:
        for name in agent_names:
            agent_models[name] = agent_models_raw.get(name, model)
    else:
        for name in agent_names:
            agent_models[name] = model

    print(f"Agent model assignments: {agent_models}")

    # ------------------------------------------------------------------
    # LLM clients (routes to OpenAI for GPT, OpenRouter for others)
    # ------------------------------------------------------------------
    if args.anthropic_direct:
        from src.llm.providers.parallel_anthropic import AnthropicLLM, AnthropicParallelClient
        if args.use_queue or agent_models_raw:
            parser.error("--anthropic-direct supports one model and the non-queued runner only")
        llm_client, parallel_client = AnthropicLLM(model, args.temperature), AnthropicParallelClient(max_concurrent=20)
        print(f"Using the Anthropic API with model: {model}")
    else:
        llm_client, parallel_client = create_llm_clients(
            model=model,
            openrouter_api_key=settings.OPENROUTER_API_KEY,
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=args.temperature,
            max_workers=20,
        )
    if args.dump_requests:
        parallel_client = RequestDumper(parallel_client, args.dump_requests)

    # ------------------------------------------------------------------
    # Game parameters
    # ------------------------------------------------------------------
    game_params    = build_game_params(args)
    self_reference = not args.no_self_reference
    round_robin    = args.round_robin
    n_rounds       = args.rounds

    print(f"\nProtocol:       endogenous (3-stage)")
    print(f"Self-reference: {self_reference}")
    print(f"Stage 2 mode:   {'round-robin' if round_robin else 'simultaneous'}")
    print(f"Rounds:         {n_rounds}")
    if not self_reference:
        print("  (ablation: Stage 3 does NOT include own plan/announcement)")

    # ------------------------------------------------------------------
    # Run experiment
    # ------------------------------------------------------------------
    if args.use_queue:
        from src.llm.providers.queued_openrouter import QueuedOpenRouterClient
        from src.llm.providers.queued_openai import QueuedOpenAIClient
        from src.llm.client_factory import is_openai_model

        # Determine which providers we need based on agent models
        has_openai = any(is_openai_model(m) for m in agent_models.values())
        has_openrouter = any(not is_openai_model(m) for m in agent_models.values())

        # Create queued clients for needed providers
        queued_openai_client = None
        queued_openrouter_client = None

        if has_openai:
            queued_openai_client = QueuedOpenAIClient(
                api_key=settings.OPENAI_API_KEY,
                max_workers=25,
                timeout=120,
                max_retries=5,
            )
            print("Created OpenAI queued client (max_workers=25)")

        if has_openrouter:
            queued_openrouter_client = QueuedOpenRouterClient(
                api_key=settings.OPENROUTER_API_KEY,
                max_workers=25,
                timeout=120,
                max_retries=5,
            )
            print("Created OpenRouter queued client (max_workers=25)")

        rounds = run_all_trials_queued(
            game_type=args.game,
            agent_names=agent_names,
            game_params=game_params,
            llm_client=llm_client,
            queued_client=queued_openrouter_client,  # Legacy parameter (kept for compatibility)
            queued_openai_client=queued_openai_client,
            queued_openrouter_client=queued_openrouter_client,
            n_trials=args.trials,
            n_rounds=n_rounds,
            self_reference=self_reference,
            round_robin=round_robin,
            show_progress=True,
            agent_models=agent_models,
        )
    else:
        rounds = run_all_trials(
            game_type=args.game,
            agent_names=agent_names,
            game_params=game_params,
            llm_client=llm_client,
            parallel_client=parallel_client,
            n_trials=args.trials,
            n_rounds=n_rounds,
            self_reference=self_reference,
            round_robin=round_robin,
            show_progress=True,
            agent_models=agent_models,
            private_channel=args.private_channel,
            private_exchanges=args.private_exchanges,
            private_history=args.private_history,
            seed=args.seed,
            run_judge=not args.no_judge,
        )

    # ------------------------------------------------------------------
    # Analyse and save
    # ------------------------------------------------------------------
    analysis = analyze_all_rounds(
        rounds=rounds,
        game_type=args.game,
        model=model,
        n_agents=args.agents,
        self_reference=self_reference,
        n_rounds=n_rounds,
    )

    print_summary(analysis)

    if args.private_channel is not None:
        analysis["metadata"]["private_channel"] = {
            "condition":   args.private_channel,
            "n_exchanges": args.private_exchanges,
            "seed":        args.seed,
        }
        if args.private_history != "full":
            analysis["metadata"]["private_channel"]["history"] = args.private_history

    if args.anthropic_direct:
        analysis["metadata"]["provider"] = "anthropic"
        analysis["metadata"]["anthropic_usage"] = dict(parallel_client.usage)
        print(f"Anthropic usage: {parallel_client.usage}")

    save_results(
        rounds=rounds,
        analysis=analysis,
        output_dir=args.output_dir,
        model_name=model,
        run_suffix=args.run_suffix,
    )


if __name__ == "__main__":
    main()
