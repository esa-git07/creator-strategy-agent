from datetime import datetime, timezone

from app.memory.hindsight_client import get_hindsight_client


def record_result(
    creator_id: str,
    recommendation: str,
    experiment: str,
    result_metrics: str,
    creator_observation: str,
) -> dict:
    """
    Store the outcome of a strategy experiment in Hindsight.
    """

    content = f"""
Creator strategy experiment result.

Recommendation:
{recommendation}

Experiment:
{experiment}

Result metrics:
{result_metrics}

Creator observation:
{creator_observation}

Date:
{datetime.now(timezone.utc).isoformat()}

This result should be considered when making future content strategy recommendations.
"""

    try:
        client = get_hindsight_client()

        result = client.retain_memory(
            bank_id=creator_id,
            content=content,
            metadata={
                "type": "experiment_result",
                "creator_id": creator_id,
            },
        )

        return {
            "success": True,
            "message": "Experiment result saved to Hindsight.",
            "hindsight_result": result,
        }

    except Exception as exc:
        raise RuntimeError(
            "Failed to save experiment result to Hindsight"
        ) from exc