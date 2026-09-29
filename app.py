import streamlit as st

from app.agent.strategy import generate_recommendation
from app.agent.learning import record_result


st.set_page_config(
    page_title="Creator Strategy Agent",
    page_icon="🎯",
    layout="wide",
)

st.title("🎯 Creator Strategy Agent")
st.caption(
    "An AI strategist that remembers your content journey, "
    "learns from results, and helps you decide what to do next."
)

CREATOR_ID = "creator_ai_001"


# -----------------------------
# Session state
# -----------------------------

if "recommendation" not in st.session_state:
    st.session_state.recommendation = None

if "last_result" not in st.session_state:
    st.session_state.last_result = None


# Clear old response format from previous versions
if (
    st.session_state.recommendation is not None
    and "answer" not in st.session_state.recommendation
):
    st.session_state.recommendation = None


# -----------------------------
# Ask a strategy question
# -----------------------------

st.header("Ask Your Strategy Question")

st.caption(
    "Ask about your content, audience, performance, "
    "experiments, or what you should create next."
)

with st.form("strategy_question_form"):

    question = st.text_input(
        "Your question",
        placeholder="Example: What should I create next?",
    )

    submitted = st.form_submit_button(
        "Ask Strategy Agent",
        type="primary",
    )


if submitted:

    if not question.strip():

        st.warning("Please enter a question.")

    else:

        with st.spinner(
            "Recalling your history and analyzing your question..."
        ):

            try:

                st.session_state.recommendation = (
                    generate_recommendation(
                        CREATOR_ID,
                        question=question.strip(),
                    )
                )

            except Exception as exc:

                st.error(str(exc))


# -----------------------------
# Display latest learning
# -----------------------------

if st.session_state.last_result:

    st.divider()

    st.subheader("🧠 Latest Learning")

    result = st.session_state.last_result

    st.write(
        f"**Result:** {result['metrics']}"
    )

    st.write(
        f"**Observation:** {result['observation']}"
    )

    st.caption(
        "This result has been added to the creator's persistent "
        "Hindsight memory."
    )


# -----------------------------
# Display strategy answer
# -----------------------------

result = st.session_state.recommendation

if result:

    # Safety check for old response format
    if "answer" not in result:

        st.session_state.recommendation = None

        st.warning(
            "Previous strategy format cleared. "
            "Please ask your question again."
        )

        st.stop()


    st.divider()


    # -----------------------------
    # Dynamic response heading
    # -----------------------------

    question_type = result.get(
        "question_type",
        "general",
    )

    if question_type == "recommendation":

        st.header("🎯 Recommendation")

    elif question_type == "performance":

        st.header("📊 Performance Analysis")

    elif question_type == "weak_patterns":

        st.header("⚠️ Patterns to Reduce")

    elif question_type == "audience":

        st.header("💬 Audience Insights")

    elif question_type == "audience_profile":

        st.header("👥 Audience Profile")

    elif question_type == "experiment":

        st.header("🧪 Experiment")

    elif question_type == "learning":

        st.header("🧠 What You've Learned")

    else:

        st.header("💡 Strategy Insight")


    # -----------------------------
    # Answer
    # -----------------------------

    st.subheader("Answer")

    st.write(
        result.get(
            "answer",
            "No answer was generated.",
        )
    )


    # -----------------------------
    # Evidence
    # -----------------------------

    st.subheader("Evidence from your history")

    evidence = result.get(
        "evidence",
        [],
    )

    if evidence:

        for item in evidence:

            st.write(
                f"• {item}"
            )

    else:

        st.write(
            "No specific supporting evidence was found."
        )
    st.subheader("🧠 Hindsight Memories Used")

    memories_used = result.get("memories_used", [])

    if memories_used:
        with st.expander(
            f"View {len(memories_used)} memories recalled from Hindsight"
        ):
            for memory in memories_used:
                st.write(f"• {memory}")
    else:
        st.caption("No memory details available.")

    # -----------------------------
    # Key insight
    # -----------------------------

    st.subheader("Key Insight")

    st.write(
        result.get(
            "insight",
            "No additional insight was generated.",
        )
    )


    # -----------------------------
    # Next action
    # -----------------------------

    next_action = result.get(
        "next_action"
    )

    if next_action:

        st.subheader("Next Action")

        st.write(
            next_action
        )


    # -----------------------------
    # Uncertainty
    # -----------------------------

    st.subheader("Uncertainty")

    st.write(
        result.get(
            "uncertainty",
            "No uncertainty was specified.",
        )
    )


    # -----------------------------
    # Record experiment result
    # Only relevant for recommendation
    # and experiment questions
    # -----------------------------

    if question_type in [
        "recommendation",
        "experiment",
    ]:

        st.divider()

        st.header(
            "🧪 Record Experiment Result"
        )

        st.caption(
            "Record what happened after acting on a strategy. "
            "This becomes persistent memory for future questions."
        )

        with st.form("experiment_form"):

            result_metrics = st.text_input(
                "Result metrics",
                placeholder=(
                    "Example: 18,600 views, 1,240 saves, "
                    "180 likes, 76 comments"
                ),
            )

            creator_observation = st.text_area(
                "What did you observe?",
                placeholder=(
                    "Example: The problem-first hook performed "
                    "better than my usual tutorial openings."
                ),
            )

            save_result = st.form_submit_button(
                "Save Result to Hindsight"
            )


            if save_result:

                if (
                    not result_metrics.strip()
                    and not creator_observation.strip()
                ):

                    st.warning(
                        "Please enter a result or observation."
                    )

                else:

                    try:

                        saved = record_result(
                            creator_id=CREATOR_ID,
                            recommendation=result["answer"],
                            experiment=result.get(
                                "next_action",
                                "",
                            ),
                            result_metrics=result_metrics,
                            creator_observation=(
                                creator_observation
                            ),
                        )


                        # Keep the latest learning visible
                        st.session_state.last_result = {
                            "metrics": result_metrics,
                            "observation": (
                                creator_observation
                            ),
                        }


                        st.success(
                            "Experiment result saved to Hindsight."
                        )

                        st.info(
                            "This result is now part of your "
                            "persistent memory. Ask another "
                            "strategy question to see the agent "
                            "learn from it."
                        )

                        st.rerun()


                    except Exception as exc:

                        st.error(
                            str(exc)
                        )