"""
Layer 3: Hardcoded Post-Validation
Validates LLM strategy decisions against safety rules and logical consistency.
"""
from typing import Dict, Any, Tuple, Optional
from models import AuctionContext, StrategyDecision


class StrategyValidator:
    """
    Validates LLM-generated strategy decisions against hard constraints.
    If validation fails, triggers fallback to rule-based logic.
    """

    @staticmethod
    def validate_bid_ceiling(decision: StrategyDecision, context: AuctionContext) -> Optional[str]:
        """
        HARD RULE: Bid amount cannot exceed 80% of estimated value.
        This is the absolute maximum allowed to prevent overpayment.
        """
        hard_ceiling = context.estimated_value * 0.80
        if decision.recommended_bid_amount > hard_ceiling:
            return (
                f"BID CEILING VIOLATION: Recommended bid (${decision.recommended_bid_amount:.2f}) "
                f"exceeds 80% of estimated value (${hard_ceiling:.2f}). "
                f"Maximum allowed: ${hard_ceiling:.2f}"
            )
        return None

    @staticmethod
    def validate_budget_check(decision: StrategyDecision, context: AuctionContext) -> Optional[str]:
        """
        HARD RULE: Cannot recommend bids exceeding available budget.
        Prevents impossible bidding scenarios.
        """
        if decision.recommended_bid_amount > context.budget_available:
            return (
                f"BUDGET VIOLATION: Recommended bid (${decision.recommended_bid_amount:.2f}) "
                f"exceeds available budget (${context.budget_available:.2f}). "
                f"Cannot execute this strategy."
            )
        return None

    @staticmethod
    def validate_logical_consistency(decision: StrategyDecision) -> Optional[str]:
        """
        Validate logical consistency within the decision itself.
        """
        # Rule 1: If strategy is do_not_bid, bid amount should be 0
        if decision.strategy == "do_not_bid" and decision.recommended_bid_amount > 0:
            return (
                "LOGICAL INCONSISTENCY: Strategy is 'do_not_bid' but recommended_bid_amount > 0. "
                "Cannot bid if strategy is to not participate."
            )

        # Rule 2: Confidence should match risk level
        risk_confidence_map = {
            "low": (0.7, 1.0),    # Low risk needs high confidence
            "medium": (0.5, 0.8), # Medium risk needs moderate confidence
            "high": (0.0, 0.6)    # High risk can have lower confidence
        }

        min_conf, max_conf = risk_confidence_map[decision.risk_level]
        if not (min_conf <= decision.confidence <= max_conf):
            return (
                f"CONFIDENCE MISMATCH: Risk level '{decision.risk_level}' requires confidence "
                f"between {min_conf:.1f}-{max_conf:.1f}, but got {decision.confidence:.2f}. "
                f"This suggests miscalibrated risk assessment."
            )

        # Rule 3: Wait for closeout only makes sense with minimal competition
        if decision.strategy == "wait_for_closeout":
            # This will be checked against context in the main validation method
            pass  # Context-dependent validation happens in validate_all

        return None

    @staticmethod
    def validate_reasoning_quality(decision: StrategyDecision) -> Optional[str]:
        """
        Validate that reasoning is substantive and detailed enough.
        Prevents superficial or inadequate explanations.
        """
        min_length = 100  # characters
        if len(decision.reasoning) < min_length:
            return (
                f"REASONING INSUFFICIENT: Explanation too brief ({len(decision.reasoning)} chars). "
                f"Minimum required: {min_length} characters. "
                f"Strategy decisions require detailed rationale."
            )

        # Check for meaningful content (not just filler)
        reasoning_lower = decision.reasoning.lower()
        required_keywords = ["profit", "risk", "competition", "strategy"]
        found_keywords = sum(1 for keyword in required_keywords if keyword in reasoning_lower)

        if found_keywords < 2:
            return (
                "REASONING SUPERFICIAL: Explanation lacks depth. "
                f"Should discuss profit margins, risks, competition, and strategic rationale. "
                f"Found only {found_keywords} of required elements."
            )

        return None

    @staticmethod
    def validate_strategy_context_fit(decision: StrategyDecision, context: AuctionContext) -> Optional[str]:
        """
        Validate that strategy makes sense given auction context.
        """
        # Wait for closeout only with minimal competition
        if decision.strategy == "wait_for_closeout" and context.num_bidders > 2:
            return (
                "STRATEGY CONTEXT MISMATCH: 'wait_for_closeout' selected but "
                f"{context.num_bidders} bidders present. Closeout unlikely with competition."
            )

        # Aggressive early only for very valuable domains or special cases
        if decision.strategy == "aggressive_early" and context.estimated_value < 500:
            return (
                "STRATEGY CONTEXT MISMATCH: 'aggressive_early' selected for low-value domain "
                f"(${context.estimated_value:.2f}). This strategy is for must-have domains only."
            )

        # Sniping should consider time remaining
        if decision.strategy == "last_minute_snipe" and context.hours_remaining > 2:
            # Allow but warn - could be valid for bot avoidance
            pass

        return None

    @classmethod
    def validate_all(cls, decision: StrategyDecision, context: AuctionContext) -> Tuple[bool, Optional[str]]:
        """
        Run all validation checks on a strategy decision.

        Returns:
            (is_valid: bool, error_message: Optional[str])
        """
        # Run all validation checks
        checks = [
            lambda: cls.validate_bid_ceiling(decision, context),
            lambda: cls.validate_budget_check(decision, context),
            lambda: cls.validate_logical_consistency(decision),
            lambda: cls.validate_reasoning_quality(decision),
            lambda: cls.validate_strategy_context_fit(decision, context),
        ]

        for check_func in checks:
            error = check_func()
            if error:
                return False, error

        return True, None



