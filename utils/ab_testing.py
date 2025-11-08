"""
A/B Testing Framework - Statistical A/B testing for creatives.

Proper statistical analysis with:
- Sample size calculation
- Statistical significance (p-value)
- Confidence intervals
- Early stopping (when winner is clear)

Don't waste money testing when you already have a winner!
"""

from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from database.models import Creative
import math
from scipy import stats


class ABTest:
    """
    A/B testing framework with statistical rigor.
    """

    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id

    def calculate_sample_size(
        self,
        baseline_cvr: float,
        minimum_detectable_effect: float = 0.20,  # 20% improvement
        alpha: float = 0.05,  # 5% false positive rate
        power: float = 0.80  # 80% power
    ) -> int:
        """
        Calculate required sample size for A/B test.

        Args:
            baseline_cvr: Current CVR (e.g., 0.05 = 5%)
            minimum_detectable_effect: Minimum effect to detect (0.20 = 20% improvement)
            alpha: Significance level (0.05 = 95% confidence)
            power: Statistical power (0.80 = 80% chance to detect real effect)

        Returns:
            Required sample size per variant

        Example:
            baseline = 5% CVR
            want to detect 20% improvement (to 6%)
            → Need ~15,000 impressions per variant
        """
        # Z-scores for alpha and power
        z_alpha = stats.norm.ppf(1 - alpha / 2)  # Two-tailed
        z_beta = stats.norm.ppf(power)

        # Expected CVR for variant B
        variant_cvr = baseline_cvr * (1 + minimum_detectable_effect)

        # Pooled probability
        p_pooled = (baseline_cvr + variant_cvr) / 2

        # Sample size formula for proportions
        numerator = (z_alpha + z_beta) ** 2 * 2 * p_pooled * (1 - p_pooled)
        denominator = (variant_cvr - baseline_cvr) ** 2

        sample_size = int(math.ceil(numerator / denominator))

        return sample_size

    def analyze_test(
        self,
        creative_a_id: str,
        creative_b_id: str,
        metric: str = "cvr"
    ) -> Dict:
        """
        Analyze A/B test results with statistical significance.

        Args:
            creative_a_id: Control creative
            creative_b_id: Variant creative
            metric: Metric to compare (cvr, ctr, install_rate)

        Returns:
            {
                "winner": "B",
                "confidence": 0.95,
                "p_value": 0.02,
                "lift": 0.23,  # 23% improvement
                "recommendation": "Scale variant B",
                "statistical_significance": True
            }
        """
        creative_a = self.db.query(Creative).filter(
            Creative.id == creative_a_id,
            Creative.user_id == self.user_id
        ).first()

        creative_b = self.db.query(Creative).filter(
            Creative.id == creative_b_id,
            Creative.user_id == self.user_id
        ).first()

        if not creative_a or not creative_b:
            return {"error": "Creative not found"}

        # Get metric values
        if metric == "cvr":
            a_conversions = creative_a.conversions
            a_total = creative_a.clicks
            b_conversions = creative_b.conversions
            b_total = creative_b.clicks
        elif metric == "install_rate":
            a_conversions = creative_a.installs
            a_total = creative_a.clicks
            b_conversions = creative_b.installs
            b_total = creative_b.clicks
        elif metric == "ctr":
            a_conversions = creative_a.clicks
            a_total = creative_a.impressions
            b_conversions = creative_b.clicks
            b_total = creative_b.impressions
        else:
            return {"error": f"Unknown metric: {metric}"}

        # Check for sufficient data
        if a_total < 100 or b_total < 100:
            return {
                "status": "insufficient_data",
                "message": "Need at least 100 samples per variant",
                "samples_a": a_total,
                "samples_b": b_total
            }

        # Calculate rates
        rate_a = a_conversions / a_total if a_total > 0 else 0
        rate_b = b_conversions / b_total if b_total > 0 else 0

        # Two-proportion z-test
        pooled_rate = (a_conversions + b_conversions) / (a_total + b_total)
        se = math.sqrt(pooled_rate * (1 - pooled_rate) * (1/a_total + 1/b_total))

        if se == 0:
            z_score = 0
            p_value = 1.0
        else:
            z_score = (rate_b - rate_a) / se
            p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))  # Two-tailed

        # Lift calculation
        lift = (rate_b - rate_a) / rate_a if rate_a > 0 else 0

        # Confidence interval for lift (95%)
        ci_lower, ci_upper = self._confidence_interval(
            rate_a, rate_b, a_total, b_total
        )

        # Determine winner
        is_significant = p_value < 0.05
        if is_significant:
            winner = "B" if rate_b > rate_a else "A"
            recommendation = f"Scale variant {winner} - statistically significant winner"
        else:
            winner = "tie"
            recommendation = "No clear winner yet - continue testing or stop test"

        return {
            "creative_a": {
                "id": creative_a_id,
                "name": creative_a.name,
                "rate": round(rate_a, 4),
                "samples": a_total,
                "conversions": a_conversions
            },
            "creative_b": {
                "id": creative_b_id,
                "name": creative_b.name,
                "rate": round(rate_b, 4),
                "samples": b_total,
                "conversions": b_conversions
            },
            "winner": winner,
            "lift": round(lift, 3),
            "lift_percent": f"{round(lift * 100, 1)}%",
            "p_value": round(p_value, 4),
            "z_score": round(z_score, 3),
            "statistical_significance": is_significant,
            "confidence": round(1 - p_value, 3) if p_value < 1 else 0,
            "confidence_interval": {
                "lower": round(ci_lower, 3),
                "upper": round(ci_upper, 3)
            },
            "recommendation": recommendation,
            "metric": metric
        }

    def _confidence_interval(
        self,
        rate_a: float,
        rate_b: float,
        n_a: int,
        n_b: int,
        confidence: float = 0.95
    ) -> Tuple[float, float]:
        """Calculate confidence interval for lift."""
        z = stats.norm.ppf((1 + confidence) / 2)

        se_a = math.sqrt(rate_a * (1 - rate_a) / n_a) if n_a > 0 else 0
        se_b = math.sqrt(rate_b * (1 - rate_b) / n_b) if n_b > 0 else 0
        se_diff = math.sqrt(se_a**2 + se_b**2)

        diff = rate_b - rate_a
        margin = z * se_diff

        lift_lower = (diff - margin) / rate_a if rate_a > 0 else 0
        lift_upper = (diff + margin) / rate_a if rate_a > 0 else 0

        return (lift_lower, lift_upper)

    def multi_armed_bandit(
        self,
        creative_ids: List[str],
        epsilon: float = 0.1
    ) -> Dict:
        """
        Epsilon-greedy multi-armed bandit for continuous optimization.

        Args:
            creative_ids: List of creative IDs to test
            epsilon: Exploration rate (0.1 = explore 10%, exploit 90%)

        Returns:
            {
                "next_creative": "uuid-123",
                "allocation": {"uuid-123": 0.9, "uuid-456": 0.05, ...},
                "reason": "exploit_winner"
            }
        """
        import random

        creatives = self.db.query(Creative).filter(
            Creative.id.in_(creative_ids),
            Creative.user_id == self.user_id
        ).all()

        if not creatives:
            return {"error": "No creatives found"}

        # Calculate CVR for each creative
        results = []
        for creative in creatives:
            cvr = creative.cvr / 10000 if creative.cvr else 0
            results.append({
                "creative_id": str(creative.id),
                "cvr": cvr,
                "samples": creative.clicks or 0
            })

        # Sort by CVR
        results.sort(key=lambda x: x["cvr"], reverse=True)

        # Epsilon-greedy allocation
        if random.random() < epsilon:
            # Explore: random selection
            chosen = random.choice(results)
            reason = "explore"
        else:
            # Exploit: best performer
            chosen = results[0]
            reason = "exploit_winner"

        # Calculate allocation percentages
        allocation = {}
        exploit_pct = 1 - epsilon
        explore_pct_per_variant = epsilon / len(results)

        for r in results:
            if r["creative_id"] == chosen["creative_id"]:
                allocation[r["creative_id"]] = exploit_pct + explore_pct_per_variant
            else:
                allocation[r["creative_id"]] = explore_pct_per_variant

        return {
            "next_creative": chosen["creative_id"],
            "allocation": allocation,
            "reason": reason,
            "epsilon": epsilon,
            "leaderboard": results
        }
