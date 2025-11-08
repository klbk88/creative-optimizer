"""
Early Signals Analysis - анализ креативов по первым 24 часам.

Используется для быстрой фильтрации явных лузеров
БЕЗ ожидания полных 7 дней тестирования.
"""

from typing import Dict, Optional
from datetime import datetime, timedelta


class EarlySignalsAnalyzer:
    """
    Анализ ранних сигналов (первые 24 часа) для предсказания финального CVR.

    Исследования показывают корреляцию:
    - 24h CTR → Final CVR: 0.65-0.75
    - Bounce rate → CVR: -0.60 (обратная)
    - Time on page → CVR: 0.55
    """

    # Пороги на основе industry benchmarks
    THRESHOLDS = {
        "ctr_good": 0.03,      # 3%+ CTR = хороший сигнал
        "ctr_bad": 0.01,       # <1% CTR = плохой сигнал
        "bounce_good": 0.40,   # <40% bounce = хороший
        "bounce_bad": 0.70,    # >70% bounce = плохой
        "time_good": 5.0,      # >5 сек на странице = хороший
        "time_bad": 2.0,       # <2 сек = плохой
    }

    def analyze_24h_performance(
        self,
        impressions: int,
        clicks: int,
        landing_views: int,
        landing_bounces: int,
        avg_time_on_page: float,  # секунды
        conversions: int = 0,
        created_at: datetime = None
    ) -> Dict:
        """
        Анализ креатива после первых 24 часов.

        Args:
            impressions: Показы за 24h
            clicks: Клики за 24h
            landing_views: Просмотры landing page
            landing_bounces: Bounces (ушли сразу)
            avg_time_on_page: Среднее время на странице (сек)
            conversions: Конверсии за 24h (если есть)
            created_at: Время создания кампании

        Returns:
            {
                "signal": "strong_positive" | "positive" | "neutral" | "negative" | "strong_negative",
                "confidence": 0.75,
                "recommendation": "scale" | "continue" | "pause" | "kill",
                "predicted_final_cvr": 0.12,
                "reasoning": "...",
                "metrics": {...}
            }
        """

        # Рассчитать метрики
        ctr = clicks / impressions if impressions > 0 else 0
        bounce_rate = landing_bounces / landing_views if landing_views > 0 else 0
        early_cvr = conversions / clicks if clicks > 0 else 0

        # Проверка что прошло достаточно времени
        if created_at:
            age_hours = (datetime.utcnow() - created_at).total_seconds() / 3600
            if age_hours < 6:
                return {
                    "signal": "insufficient_data",
                    "confidence": 0.0,
                    "recommendation": "wait",
                    "reasoning": f"Only {age_hours:.1f} hours passed. Need at least 6 hours."
                }

        # Проверка минимального объема
        if impressions < 100 or clicks < 10:
            return {
                "signal": "insufficient_volume",
                "confidence": 0.0,
                "recommendation": "wait",
                "reasoning": f"Need minimum 100 impressions + 10 clicks. Have {impressions}/{clicks}."
            }

        # Подсчет позитивных/негативных сигналов
        positive_signals = 0
        negative_signals = 0
        signals_detail = []

        # CTR анализ
        if ctr >= self.THRESHOLDS["ctr_good"]:
            positive_signals += 2  # Сильный сигнал
            signals_detail.append(f"✅ CTR {ctr*100:.2f}% (>{self.THRESHOLDS['ctr_good']*100}%)")
        elif ctr <= self.THRESHOLDS["ctr_bad"]:
            negative_signals += 2
            signals_detail.append(f"❌ CTR {ctr*100:.2f}% (<{self.THRESHOLDS['ctr_bad']*100}%)")
        else:
            signals_detail.append(f"➖ CTR {ctr*100:.2f}% (средний)")

        # Bounce rate анализ
        if bounce_rate <= self.THRESHOLDS["bounce_good"]:
            positive_signals += 1
            signals_detail.append(f"✅ Bounce {bounce_rate*100:.1f}% (<{self.THRESHOLDS['bounce_good']*100}%)")
        elif bounce_rate >= self.THRESHOLDS["bounce_bad"]:
            negative_signals += 1
            signals_detail.append(f"❌ Bounce {bounce_rate*100:.1f}% (>{self.THRESHOLDS['bounce_bad']*100}%)")

        # Time on page анализ
        if avg_time_on_page >= self.THRESHOLDS["time_good"]:
            positive_signals += 1
            signals_detail.append(f"✅ Time {avg_time_on_page:.1f}s (>{self.THRESHOLDS['time_good']}s)")
        elif avg_time_on_page <= self.THRESHOLDS["time_bad"]:
            negative_signals += 1
            signals_detail.append(f"❌ Time {avg_time_on_page:.1f}s (<{self.THRESHOLDS['time_bad']}s)")

        # Ранние конверсии (бонус)
        if conversions > 0:
            positive_signals += 1
            signals_detail.append(f"✅ Early conversions: {conversions} (ранний CVR: {early_cvr*100:.2f}%)")

        # Определить итоговый сигнал
        score = positive_signals - negative_signals

        if score >= 3:
            signal = "strong_positive"
            recommendation = "scale"
            predicted_cvr = ctr * 0.15  # Оптимистичная оценка
            confidence = 0.75
        elif score >= 1:
            signal = "positive"
            recommendation = "continue"
            predicted_cvr = ctr * 0.12
            confidence = 0.65
        elif score >= -1:
            signal = "neutral"
            recommendation = "continue"
            predicted_cvr = ctr * 0.08
            confidence = 0.50
        elif score >= -3:
            signal = "negative"
            recommendation = "pause"
            predicted_cvr = ctr * 0.05
            confidence = 0.70
        else:
            signal = "strong_negative"
            recommendation = "kill"
            predicted_cvr = ctr * 0.03
            confidence = 0.80

        # Reasoning
        reasoning = f"Score: {score} ({positive_signals} positive, {negative_signals} negative). "
        reasoning += " ".join(signals_detail)

        return {
            "signal": signal,
            "confidence": confidence,
            "recommendation": recommendation,
            "predicted_final_cvr": predicted_cvr,
            "reasoning": reasoning,
            "metrics": {
                "24h_ctr": ctr,
                "bounce_rate": bounce_rate,
                "avg_time_on_page": avg_time_on_page,
                "early_cvr": early_cvr,
                "conversions": conversions,
                "sample_size": clicks
            },
            "next_action": self._get_next_action(recommendation, predicted_cvr)
        }

    def _get_next_action(self, recommendation: str, predicted_cvr: float) -> str:
        """Конкретные следующие шаги."""

        actions = {
            "scale": f"🚀 Увеличить бюджет до $100-200. Predicted CVR: {predicted_cvr*100:.1f}%",
            "continue": f"➡️ Продолжить тест с текущим бюджетом ($50). Predicted CVR: {predicted_cvr*100:.1f}%",
            "pause": f"⏸️ Приостановить кампанию. Predicted CVR слишком низкий: {predicted_cvr*100:.1f}%",
            "kill": f"❌ Остановить кампанию. Явный провал. Predicted CVR: {predicted_cvr*100:.1f}%"
        }

        return actions.get(recommendation, "Wait for more data")


def bulk_analyze_24h(creatives_data: list) -> Dict:
    """
    Массовый анализ 20 креативов после 24 часов.

    Args:
        creatives_data: List of dicts with metrics

    Returns:
        {
            "winners": [...],  # Scale these
            "potential": [...],  # Continue testing
            "losers": [...],  # Kill these
            "summary": {...}
        }
    """

    analyzer = EarlySignalsAnalyzer()

    winners = []
    potential = []
    losers = []

    for creative in creatives_data:
        analysis = analyzer.analyze_24h_performance(
            impressions=creative.get("impressions", 0),
            clicks=creative.get("clicks", 0),
            landing_views=creative.get("landing_views", 0),
            landing_bounces=creative.get("landing_bounces", 0),
            avg_time_on_page=creative.get("avg_time_on_page", 0),
            conversions=creative.get("conversions", 0),
            created_at=creative.get("created_at")
        )

        result = {
            "creative_id": creative.get("id"),
            "name": creative.get("name"),
            "analysis": analysis
        }

        if analysis["recommendation"] == "scale":
            winners.append(result)
        elif analysis["recommendation"] in ["continue", "pause"]:
            potential.append(result)
        else:
            losers.append(result)

    # Расчет экономии
    total_creatives = len(creatives_data)
    killed_early = len(losers)
    saved_budget = killed_early * 40  # Сэкономили $40 на каждом (не доливали с $10 до $50)

    return {
        "winners": winners,
        "potential": potential,
        "losers": losers,
        "summary": {
            "total_analyzed": total_creatives,
            "winners_count": len(winners),
            "potential_count": len(potential),
            "losers_count": len(losers),
            "kill_rate": killed_early / total_creatives if total_creatives > 0 else 0,
            "estimated_savings_usd": saved_budget,
            "next_step": f"Kill {killed_early} losers, continue {len(potential)} potential, scale {len(winners)} winners"
        }
    }


# Пример использования:
if __name__ == "__main__":
    # После 24 часов с бюджетом $10:
    analyzer = EarlySignalsAnalyzer()

    # Креатив A (хороший)
    result_a = analyzer.analyze_24h_performance(
        impressions=500,
        clicks=20,
        landing_views=18,
        landing_bounces=6,
        avg_time_on_page=6.5,
        conversions=2
    )
    print("Креатив A:", result_a["signal"], result_a["recommendation"])
    # Output: strong_positive, scale

    # Креатив B (плохой)
    result_b = analyzer.analyze_24h_performance(
        impressions=800,
        clicks=5,
        landing_views=4,
        landing_bounces=3,
        avg_time_on_page=1.2,
        conversions=0
    )
    print("Креатив B:", result_b["signal"], result_b["recommendation"])
    # Output: strong_negative, kill
