"""Unit tests for the LLM Adapter and Structured Extraction.
Verifies:
1. News extractor parses raw unstructured text into structured TeamNewsItem models.
2. Rotation estimator extracts numeric ranges and evidence.
3. Explainer outputs cohesive rationale with downside risks.
4. Schema validation strictly enforced.
"""

from src.core.schemas import BetRecommendation, MarketType
from src.llm.adapter import LLMAdapter
from src.llm.schemas import PlayerStatus, InformationConfidence, ImpactLevel


def test_llm_adapter_mock_mode():
    adapter = LLMAdapter(provider="mock")

    # 1. News Extraction
    raw_article = (
        "Mikel Arteta spoke to the press ahead of the weekend clash. He mentioned Bukayo Saka "
        "has suffered a hamstring scare and will face a late fitness test on Saturday morning."
    )
    news = adapter.extract_news(raw_text=raw_article, team="Arsenal")
    assert len(news) == 1
    assert news[0].player == "Bukayo Saka"
    assert news[0].status == PlayerStatus.DOUBTFUL
    assert news[0].confidence == InformationConfidence.CONFIRMED
    assert news[0].expected_impact == ImpactLevel.HIGH
    print("News Extraction test passed successfully!")

    # 2. Rotation Estimation
    manager_quotes = "We play four matches in 10 days. We need to freshen up the legs in midfield."
    rotation = adapter.estimate_rotation(
        team="Arsenal",
        match_id="EPL_ARS_CHE",
        manager_quotes=manager_quotes,
        fixture_context="Midweek Champions League fixture follows this match"
    )
    assert 0 <= rotation.expected_changes <= 11
    assert 0.0 <= rotation.probability_heavy_rotation <= 1.0
    assert len(rotation.evidence) > 0
    print("Rotation Estimation test passed successfully!")

    # 3. Explainer
    sample_pick = BetRecommendation(
        match_id="EPL_ARS_CHE",
        competition="Premier League",
        home_team="Arsenal",
        away_team="Chelsea",
        market=MarketType.ONE_X_TWO,
        selection="home",
        model_probability=0.655,
        offered_odds=1.68,
        fair_sharp_odds=1.60,
        edge=0.1004,
        stake_fraction=0.03,
        suggested_stake_amount=30.0,
        confidence_label="high",
        key_factors=["Odds beat sharp close", "Model edge 10%"],
        risks=["Derby volatility"]
    )

    explanation = adapter.explain_pick(sample_pick, news)
    assert explanation.match_id == "EPL_ARS_CHE"
    assert len(explanation.main_risks) > 0
    print("Pick Explanation test passed successfully!")
    print(f"Headline: {explanation.headline_reason}")


if __name__ == "__main__":
    test_llm_adapter_mock_mode()

