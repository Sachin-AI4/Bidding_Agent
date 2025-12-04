# Domain Auction Strategy AI System

A production-grade multi-agent system using LangGraph for intelligent domain auction bidding strategy. Combines safety filters, LLM reasoning, validation, and proxy bidding logic to make optimal bidding decisions across GoDaddy, NameJet, and Dynadot platforms.

## Features

### 🛡️ Safety First Architecture
- **Hardcoded Safety Filters**: Prevent overpayment, portfolio concentration, and budget violations
- **Overpayment Protection**: Blocks bids above 130% of estimated value (winner's curse zone)
- **Portfolio Limits**: No single domain can consume >50% of remaining budget
- **Budget Validation**: Minimum $100 budget requirement for participation

### 🤖 Hybrid AI Decision Making
- **LLM Strategy Reasoning**: Claude/GPT integration for intelligent strategy selection
- **Rule-Based Fallback**: Deterministic rules when AI fails
- **Multi-Layer Validation**: Ensures AI decisions meet safety and logical requirements
- **Proxy Bidding Logic**: Smart handling of outbid scenarios

### 🎯 Platform-Aware Strategies
- **GoDaddy**: Respects 5-minute extension rules, optimized sniping
- **NameJet**: Fast-paced auctions, immediate execution
- **Dynadot**: Variable increments, dynamic adjustments

### 📊 Strategy Options
- `proxy_max`: Set maximum proxy bid, let platform auto-bid
- `last_minute_snipe`: Time bids for final moments
- `incremental_test`: Small bids to test competition
- `wait_for_closeout`: Wait for auction end with minimal bids
- `aggressive_early`: Rare, for must-have domains
- `do_not_bid`: Walk away when profit impossible

## Installation

```bash
pip install -r requirements.txt
```

## Environment Setup

Set your API keys for LLM access:

```bash
# For Anthropic Claude (recommended)
export ANTHROPIC_API_KEY="your-anthropic-key"

# Or for OpenAI GPT
export OPENAI_API_KEY="your-openai-key"
```

## Quick Start

```python
from models import AuctionContext, BidderAnalysis
from hybrid_strategy_selector import HybridStrategySelector

# Initialize the strategy selector
selector = HybridStrategySelector(
    llm_provider="anthropic",  # or "openai"
    model="claude-3-5-sonnet-20241022"
)

# Create auction context
context = AuctionContext(
    domain="PremiumDomain.com",
    platform="godaddy",
    estimated_value=2500.0,
    current_bid=800.0,
    num_bidders=4,
    hours_remaining=2.5,
    your_current_proxy=750.0,
    budget_available=5000.0,
    bidder_analysis=BidderAnalysis(
        bot_detected=True,
        corporate_buyer=False,
        aggression_score=8.5,
        reaction_time_avg=0.8
    )
)

# Get strategy decision
decision = selector.select_strategy(context)

print(f"Strategy: {decision.strategy}")
print(f"Recommended Bid: ${decision.recommended_bid_amount}")
print(f"Should Increase Proxy: {decision.should_increase_proxy}")
print(f"Reasoning: {decision.reasoning}")
```

## Architecture

### 4-Layer Decision Pipeline

1. **Layer 1 - Safety Pre-Filters**: Hardcoded rules block unsafe auctions
2. **Layer 2 - LLM Strategy**: AI generates intelligent bidding strategies
3. **Layer 3 - Validation**: Ensures AI decisions are safe and logical
4. **Layer 4 - Proxy Logic**: Handles outbid scenarios and proxy adjustments

### LangGraph Multi-Agent Flow

```
safety_prefilter_node -> llm_strategy_node -> llm_validation_node -> proxy_logic_node -> finalize_node
                     -> finalize_node (if blocked)              -> rule_fallback_node -> proxy_logic_node (if invalid)
```

## Key Scenarios Handled

### Outbid Situations
```python
# Scenario: Proxy was $100, current bid now $120
# Safe max = $105 (70% of $150 value)
# Result: Accept loss - cannot profitably continue
```

### Platform-Specific Rules
```python
# GoDaddy: <1 hour remaining triggers sniping to respect 5-min extensions
# NameJet: Fast-paced, prefer immediate proxy max
# Dynadot: Variable increments, monitor closely
```

### Bot Detection Response
```python
# Bots detected: Prefer sniping to minimize reaction window
# Humans: More flexible, can use proxy strategies
```

## Testing

Run the comprehensive test suite:

```bash
python test_strategy_system.py
```

Tests cover:
- High-value domains with bot detection
- Low-value domains with closeout opportunities
- Outbid scenarios (both loss and increase cases)
- Safety blocks (overpayment, concentration)
- Platform-specific timing rules

## Performance Monitoring

```python
# Get performance statistics
stats = selector.get_performance_stats()
print(f"LLM Success Rate: {stats['llm_success_rate']:.1%}")
print(f"Fallback Rate: {stats['fallback_rate']:.1%}")
print(f"Safety Block Rate: {stats['safety_block_rate']:.1%}")
```

## Financial Safety Rules

- **Safe Maximum**: 70% of estimated value (30% profit margin)
- **Hard Ceiling**: Never bid above 80% of estimated value
- **Portfolio Limit**: Single domain ≤ 50% of remaining budget
- **Overpayment Protection**: Block bids >130% of value

## API Reference

### AuctionContext
Input data model containing all auction information.

### FinalDecision
Output containing strategy, reasoning, and proxy details.

### HybridStrategySelector
Main interface class with `select_strategy()` method.

## Contributing

The system is designed for extensibility:
- Add new platforms in `proxy_logic.py`
- Extend strategies in `rule_based_strategy.py`
- Add ML models in the LLM layer
- Customize safety rules in `safety_filters.py`

## License

Production-ready domain auction strategy system for intelligent bidding decisions.

