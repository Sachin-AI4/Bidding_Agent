import os
import json
import sys
from typing import Dict, Any
from pathlib import Path

# --- CONFIGURATION ---
# Replace with your actual key or set it in your environment variables
# os.environ["OPENAI_API_KEY"] = "sk-..." 

def load_env_file(env_path: str = ".env") -> None:
    """
    Loads key=value pairs from a local env file into os.environ
    without overriding any variables that are already set.
    """
    path = Path(env_path)
    if not path.exists():
        return

    with path.open("r", encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


load_env_file()

try:
    from openai import OpenAI

    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Missing OPENROUTER_API_KEY or OPENAI_API_KEY.")

    client = OpenAI(
        api_key=api_key,
        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
    )
except ImportError:
    print("Error: Please install openai: 'pip install openai'")
    sys.exit(1)
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    print("Ensure your OPENROUTER_API_KEY (or OPENAI_API_KEY) is set.")
    sys.exit(1)

# --- THE MASTER PROMPT ---
SYSTEM_PROMPT = """
### ROLE
You are the "Strategist," an elite Domain Auction AI. Your goal is to acquire domains at the lowest possible price while ensuring a win. You are playing a game of incomplete information against other humans and bots.

### INPUT DATA
You will receive a JSON object containing:
1. `auction_state`: {current_price, time_remaining_seconds, min_increment}
2. `opponent_profile`: {type (BOT/HUMAN/UNKNOWN), aggression_score (1-10), reaction_time_avg}
3. `my_constraints`: {max_budget}
4. `last_event`: Description of what just happened.

### STRATEGIC LOGIC FRAMEWORK
You must reason through these steps before deciding:

PHASE 1: THREAT ASSESSMENT
- If `time_remaining` > 600 (10 mins): We are in the "Discovery Phase." Do not reveal high value.
- If `time_remaining` < 300 (5 mins): We are in the "War Phase." Aggression is required.

PHASE 2: OPPONENT COUNTER-MEASURES
- **SCENARIO A: PROXY BOT DETECTED** (Fast reaction < 1s, Fixed increments)
   - *Insight:* Bots have hidden caps (usually round numbers like $100, $200, $500).
   - *Tactic:* The "Piercing Bid." Do not bid +$10. Bid to break the likely round-number cap.
   - *Math:* `Next_Bid = (Current_Price rounded up to next 100) + Min_Increment + 13`.
   
- **SCENARIO B: AGGRESSIVE HUMAN** (Large jumps, erratic timing)
   - *Insight:* Humans are emotional. They hate losing by small amounts but fear overpaying.
   - *Tactic:* The "Bully Anchor." Place a strong bid to show deep pockets.
   - *Math:* `Next_Bid = Current_Price + (Min_Increment * 4)`.

- **SCENARIO C: THE CROWD** (>3 active bidders)
   - *Tactic:* "Dark Mode." Stop bidding. Let them fight.
   - *Action:* Wait until `time_remaining < 90` seconds.

PHASE 3: EXECUTION TIMING (The "90-Second Rule")
- If `time_remaining` < 300: Do not bid immediately unless necessary.
- Plan the bid execution for `time_remaining = 90`. This prevents "Panic Bidding" wars at the 5-minute mark.

### SAFETY RULES
1. **Hard Cap:** NEVER bid above `max_budget`. If the calculated strategy exceeds it, return Action: "ABORT".

### OUTPUT FORMAT
You must reply in strict JSON format only. Do not include markdown.

{
  "thought_process": "Brief reasoning about the opponent and phase.",
  "identified_opponent": "PROXY_BOT" | "HUMAN" | "UNKNOWN",
  "strategy_selected": "PIERCING" | "BULLYING" | "SNIPING" | "WAITING" | "ABORT",
  "bid_amount": <float or null>,
  "execution_trigger_time": <int seconds_remaining>
}
"""

class AIStrategist:
    def __init__(self):
        self.model = os.getenv("OPENROUTER_MODEL", "openai/gpt-5.1")

    def get_strategy(self, scenario_data: Dict[str, Any]) -> Dict:
        """
        Sends the simulation scenario to the LLM and parses the JSON response.
        """
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": json.dumps(scenario_data)}
                ],
                response_format={"type": "json_object"},
                temperature=0.2 # Low temperature for consistent logic
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            return {"error": str(e)}

# --- SIMULATION SCENARIOS ---
def run_tests():
    brain = AIStrategist()
    
    print("Initializing AI Strategist Lab...\n")

    # SCENARIO 1: The "Proxy Wall"
    # We suspect a bot because it outbids us instantly. 
    # Expectation: AI should suggest a "Piercing Bid" (odd number).
    scenario_proxy = {
        "scenario_name": "FIGHTING A PROXY BOT",
        "auction_state": {
            "current_price": 100,
            "time_remaining_seconds": 350, # < 5 mins, so WAR PHASE
            "min_increment": 10
        },
        "opponent_profile": {
            "type": "BOT",
            "aggression_score": 8,
            "reaction_time_avg": 0.4 # Super fast
        },
        "my_constraints": {
            "max_budget": 500
        },
        "last_event": "We bid 90, were outbid to 100 in 0.4 seconds."
    }

    # SCENARIO 2: The "Aggressive Human"
    # Opponent makes a big jump.
    # Expectation: AI should suggest a "Bully Anchor" or "Sniping".
    scenario_human = {
        "scenario_name": "FIGHTING AN AGGRESSIVE HUMAN",
        "auction_state": {
            "current_price": 450,
            "time_remaining_seconds": 120,
            "min_increment": 10
        },
        "opponent_profile": {
            "type": "HUMAN",
            "aggression_score": 9,
            "reaction_time_avg": 45.0 # Slow thinker
        },
        "my_constraints": {
            "max_budget": 1200
        },
        "last_event": "Opponent jumped price from 300 to 450 instantly."
    }
    
    # SCENARIO 3: Budget Exceeded
    # Expectation: ABORT
    scenario_poor = {
        "scenario_name": "BUDGET SAFETY CHECK",
        "auction_state": {
            "current_price": 1050,
            "time_remaining_seconds": 60,
            "min_increment": 50
        },
        "opponent_profile": {
            "type": "UNKNOWN",
            "aggression_score": 5,
            "reaction_time_avg": 10
        },
        "my_constraints": {
            "max_budget": 1000
        },
        "last_event": "Price increased normally."
    }

    # Run the simulations
    scenarios = [scenario_proxy, scenario_human, scenario_poor]
    
    for sc in scenarios:
        print(f"--- TEST: {sc['scenario_name']} ---")
        print(f"Input State: Price=${sc['auction_state']['current_price']}, Time={sc['auction_state']['time_remaining_seconds']}s")
        print(f"Constraint: Max Budget=${sc['my_constraints']['max_budget']}")
        
        # Ask the AI
        decision = brain.get_strategy(sc)
        
        # Print Result
        print("\n>> AI DECISION:")
        print(f"   Identified Opponent: {decision.get('identified_opponent')}")
        print(f"   Strategy:            {decision.get('strategy_selected')}")
        print(f"   Reasoning:           {decision.get('thought_process')}")
        print(f"   Next Bid:            ${decision.get('bid_amount')}")
        print(f"   Execute At:          T-minus {decision.get('execution_trigger_time')} seconds")
        print("-" * 60 + "\n")

if __name__ == "__main__":
    run_tests()