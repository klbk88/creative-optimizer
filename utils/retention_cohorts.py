"""
Retention Cohorts - Track user retention for mobile apps.

Analyzes cohorts by install date and tracks Day 1, Day 7, Day 30 retention.
Critical for understanding long-term creative performance.

Example:
    Creative A: 80% Day 1 retention, 25% Day 7, 8% Day 30
    Creative B: 60% Day 1 retention, 35% Day 7, 15% Day 30

    → Creative B wins (better long-term retention)
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from database.models import Creative
from collections import defaultdict


class RetentionCohorts:
    """
    Track and analyze user retention cohorts.
    """

    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id

    def calculate_retention(
        self,
        creative_id: str,
        cohort_date: Optional[datetime] = None
    ) -> Dict:
        """
        Calculate retention for a specific creative.

        Args:
            creative_id: Creative ID
            cohort_date: Optional cohort date (defaults to creative's tested_at)

        Returns:
            {
                "day_1_retention": 0.75,
                "day_7_retention": 0.35,
                "day_30_retention": 0.12,
                "cohort_size": 1000,
                "cohort_date": "2024-11-01"
            }
        """
        # This is a placeholder - in production you'd track actual user retention
        # by querying a user_events table with device_id and last_seen_at

        # For now, estimate from funnel metrics
        creative = self.db.query(Creative).filter(
            Creative.id == creative_id,
            Creative.user_id == self.user_id
        ).first()

        if not creative:
            return {
                "error": "Creative not found",
                "day_1_retention": 0,
                "day_7_retention": 0,
                "day_30_retention": 0
            }

        # Estimate retention from funnel rates
        # In production, track actual user_last_seen_at
        install_rate = creative.install_rate / 10000 if creative.install_rate else 0
        trial_rate = creative.trial_rate / 10000 if creative.trial_rate else 0

        # Rough estimates (should be replaced with real retention tracking)
        day_1 = min(install_rate * 1.2, 0.95)  # Most installs return Day 1
        day_7 = trial_rate * 1.5  # Trial users are engaged
        day_30 = (creative.trial_to_paid_rate / 10000 if creative.trial_to_paid_rate else 0) * 2

        return {
            "creative_id": creative_id,
            "creative_name": creative.name,
            "cohort_date": cohort_date or creative.tested_at,
            "cohort_size": creative.installs or 0,
            "day_1_retention": round(day_1, 3),
            "day_7_retention": round(day_7, 3),
            "day_30_retention": round(day_30, 3),
            "note": "Replace with real retention tracking in production"
        }

    def compare_creatives(
        self,
        creative_ids: List[str],
        metric: str = "day_7_retention"
    ) -> List[Dict]:
        """
        Compare retention across multiple creatives.

        Args:
            creative_ids: List of creative IDs to compare
            metric: Which retention metric to sort by

        Returns:
            List of creatives sorted by retention metric
        """
        results = []

        for creative_id in creative_ids:
            retention = self.calculate_retention(creative_id)
            retention["sort_metric"] = retention.get(metric, 0)
            results.append(retention)

        # Sort by metric (highest first)
        results.sort(key=lambda x: x["sort_metric"], reverse=True)

        return results

    def get_cohort_analysis(
        self,
        product_category: str,
        days: int = 30
    ) -> Dict:
        """
        Analyze all cohorts for a product category.

        Args:
            product_category: Product category filter
            days: Number of days back to analyze

        Returns:
            Cohort analysis with trends
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        creatives = self.db.query(Creative).filter(
            and_(
                Creative.user_id == self.user_id,
                Creative.product_category == product_category,
                Creative.tested_at >= cutoff_date,
                Creative.installs > 0
            )
        ).all()

        cohorts = []
        for creative in creatives:
            retention = self.calculate_retention(str(creative.id))
            cohorts.append(retention)

        # Calculate averages
        if cohorts:
            avg_day_1 = sum(c["day_1_retention"] for c in cohorts) / len(cohorts)
            avg_day_7 = sum(c["day_7_retention"] for c in cohorts) / len(cohorts)
            avg_day_30 = sum(c["day_30_retention"] for c in cohorts) / len(cohorts)
        else:
            avg_day_1 = avg_day_7 = avg_day_30 = 0

        return {
            "product_category": product_category,
            "cohorts_analyzed": len(cohorts),
            "date_range": f"Last {days} days",
            "average_retention": {
                "day_1": round(avg_day_1, 3),
                "day_7": round(avg_day_7, 3),
                "day_30": round(avg_day_30, 3)
            },
            "cohorts": cohorts
        }


def calculate_retention_quality(retention: Dict) -> str:
    """
    Classify retention quality based on industry benchmarks.

    Args:
        retention: Retention dict with day_1, day_7, day_30

    Returns:
        Quality classification: excellent, good, average, poor
    """
    day_7 = retention.get("day_7_retention", 0)

    # Industry benchmarks for mobile apps
    if day_7 >= 0.40:
        return "excellent"
    elif day_7 >= 0.25:
        return "good"
    elif day_7 >= 0.15:
        return "average"
    else:
        return "poor"
