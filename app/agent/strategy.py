import json

from app.llm.groq_client import generate_strategy
from app.memory.hindsight_client import get_hindsight_client


def detect_question_type(question: str) -> str:
    """Classify the creator's question into the most useful response type."""

    q = question.lower().strip()

    if any(phrase in q for phrase in [
        "what did my audience say",
        "what is my audience saying",
        "audience feedback",
        "what feedback",
        "what did people say",
        "what are people saying",
    ]):
        return "audience"

    if any(phrase in q for phrase in [
        "what should i stop",
        "what should i avoid",
        "what should i reduce",
        "what is not working",
        "what isn't working",
        "what performs worst",
        "worst performing",
        "weakest content",
    ]):
        return "weak_patterns"

    if (
        any(word in q for word in [
            "perform",
            "performance",
            "engagement",
            "best content",
            "best-performing",
            "successful",
            "works best",
            "working best",
        ])
        and "what should i create" not in q
    ):
        return "performance"

    if any(phrase in q for phrase in [
        "who is my audience",
        "what audience",
        "which audience",
        "who should i target",
        "target audience",
        "who engages",
    ]):
        return "audience_profile"

    if any(phrase in q for phrase in [
        "latest experiment",
        "recent experiment",
        "latest result",
        "recent result",
        "what did i learn",
        "what have i learned",
    ]):
        return "learning"

    if any(phrase in q for phrase in [
        "what experiment",
        "what should i test",
        "what should i experiment",
        "what test should",
    ]):
        return "experiment"

    if any(phrase in q for phrase in [
        "what should i create",
        "what should i make",
        "what do i create next",
        "what should i post",
        "what should i publish",
    ]):
        return "recommendation"

    return "general"


def generate_recommendation(
    creator_id: str,
    question: str = (
        "Based on everything I have created and learned so far, "
        "what should I create next?"
    ),
) -> dict:
    """Recall creator memories and answer the creator's actual question."""

    question_type = detect_question_type(question)

    try:
        hindsight = get_hindsight_client()

        memories = hindsight.recall_memories(
            bank_id=creator_id,
            query=question,
        )

    except Exception as exc:
        raise RuntimeError(
            "Failed to retrieve memories from Hindsight"
        ) from exc

    if not memories:
        raise RuntimeError(
            "I couldn't find relevant memories for this question."
        )

    memories = memories[:12]

    memory_context = "\n\n".join(
        str(memory.get("text", memory))
        for memory in memories
    )

    prompt = f"""
You are an AI content strategy analyst for a creator.

Creator ID:
{creator_id}

USER QUESTION:
{question}

QUESTION TYPE:
{question_type}

The following information was retrieved from the creator's persistent
memory using Hindsight.

--- CREATOR MEMORY ---
{memory_context}
--- END MEMORY ---

Your most important job is to answer the USER QUESTION directly.

Do NOT automatically turn every question into a
"what should I create next?" recommendation.

Use ONLY information supported by the supplied memory.

Never invent:
- posts
- metrics
- comments
- audience opinions
- dates
- events
- experiments
- platform performance

If the memory does not contain enough information to answer something,
say that clearly.

EVIDENCE PRIORITY:

1. Actual published-content results and measured metrics
2. Explicit audience feedback or requests
3. Creator observations about actual results
4. Experiment results
5. Previous strategy recommendations

A previous AI recommendation is NOT proof that a strategy works.

Do not repeat an old recommendation merely because it appears in memory.
Use observed outcomes to decide whether that recommendation was validated.

QUESTION-SPECIFIC RULES:

If QUESTION TYPE is "recommendation":
Give ONE specific recommendation for what the creator should create next.
Explain why it follows from the evidence.
Suggest ONE experiment.

If QUESTION TYPE is "performance":
Identify the strongest content patterns.
Use concrete evidence and metrics where available.

If QUESTION TYPE is "weak_patterns":
Identify content patterns that appear weaker.
Explain the evidence.

If QUESTION TYPE is "audience":
Summarize actual audience feedback and requests found in memory.
Separate explicit feedback from inference.
If there is no evidence for the requested period, say so.

If QUESTION TYPE is "audience_profile":
Describe audience signals supported by the creator history.

If QUESTION TYPE is "experiment":
Suggest ONE experiment based on an identified uncertainty or gap.

If QUESTION TYPE is "learning":
Explain what the creator has learned from recent experiments.

If QUESTION TYPE is "general":
Answer the question directly using the strongest relevant evidence.

Return EXACTLY one JSON object:

{{
  "question_type": "{question_type}",
  "answer": "direct answer to the user's question",
  "evidence": [
    "specific evidence supporting the answer"
  ],
  "insight": "the most important strategic insight from the evidence",
  "next_action": "one useful next action, only when appropriate",
  "uncertainty": "what remains uncertain"
}}

Rules:
- Answer the actual question.
- Do not force every answer into the same content recommendation.
- Do not repeat the same recommendation unless evidence genuinely supports it.
- Use the creator's actual history.
- Prefer specific evidence over generic advice.
- Return valid JSON only.
"""

    try:
        response_text = generate_strategy(prompt)

    except Exception as exc:
        raise RuntimeError(
            f"Failed to generate recommendation via Groq: {exc}"
        ) from exc

    try:
        result = json.loads(response_text)

    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Groq returned invalid JSON"
        ) from exc

    required_fields = [
        "question_type",
        "answer",
        "evidence",
        "insight",
        "next_action",
        "uncertainty",
    ]

    missing = [
        field
        for field in required_fields
        if field not in result
    ]

    if missing:
        raise RuntimeError(
            f"Groq output validation failed; missing fields: {missing}"
        )

    # Add the exact Hindsight memories used for this response.
    result["memories_used"] = [
        memory.get("text", str(memory))
        for memory in memories
    ]

    return result