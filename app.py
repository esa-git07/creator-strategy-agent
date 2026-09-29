import streamlit as st

from app.agent.strategy import generate_recommendation
from app.agent.learning import record_result


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Creator Strategy Agent",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# SESSION STATE
# ============================================================

CREATOR_ID = "creator_ai_001"

if "recommendation" not in st.session_state:
    st.session_state.recommendation = None

if "last_result" not in st.session_state:
    st.session_state.last_result = None

if "last_question" not in st.session_state:
    st.session_state.last_question = ""


# Protect against an older response format
if (
    st.session_state.recommendation is not None
    and "answer" not in st.session_state.recommendation
):
    st.session_state.recommendation = None


# ============================================================
# FINAL VISUAL SYSTEM
# ============================================================

st.markdown(
    """
<style>

/* ============================================================
   PALETTE
   ============================================================

   Main background      #F4F2FF   soft lavender
   Sidebar              #29273D   deep plum
   Card                 #FFFFFF
   Lavender             #EEE9FF
   Powder blue          #EAF2FF
   Mint                 #E8F6EF
   Peach                #FFF0E6
   Primary accent       #7567D8
   Dark text            #29243D
   Muted text           #747084
   Border               #DED9EC
   ============================================================ */


/* ============================================================
   GLOBAL
   ============================================================ */

@import url(
    'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap'
);

html,
body,
[class*="css"] {
    font-family: "Inter", -apple-system, BlinkMacSystemFont,
    "Segoe UI", sans-serif;
}

.stApp {
    background: #F4F2FF;
    color: #29243D;
}


/* Remove Streamlit top chrome */

header[data-testid="stHeader"] {
    background: transparent !important;
    height: 0 !important;
}

header[data-testid="stHeader"] > div {
    display: none !important;
}

[data-testid="stToolbar"] {
    display: none !important;
}

.main .block-container {
    max-width: 1160px;
    padding-top: 2.5rem;
    padding-bottom: 4rem;
}


/* ============================================================
   SIDEBAR
   ============================================================ */

section[data-testid="stSidebar"] {
    background: #29273D;
    border-right: 1px solid #3C3854;
}

section[data-testid="stSidebar"] > div {
    padding: 1.7rem 1rem;
}


/* ------------------------------------------------------------
   Brand
   ------------------------------------------------------------ */

.brand {
    padding: 0 0.35rem 1.7rem 0.35rem;
}

.brand-mark {
    width: 40px;
    height: 40px;
    border-radius: 11px;
    background: #8F83EA;
    color: #FFFFFF;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 19px;
    font-weight: 600;
    margin-bottom: 14px;

    box-shadow:
        0 8px 22px rgba(143, 131, 234, 0.28);

    transition:
        transform 0.2s ease,
        box-shadow 0.2s ease;
}

.brand-mark:hover {
    transform: translateY(-2px) scale(1.03);
    box-shadow:
        0 11px 27px rgba(143, 131, 234, 0.38);
}


/*
IMPORTANT:
This is intentionally larger because it is the
actual project/product heading.
*/

.brand-title {
    font-size: 19px;
    line-height: 1.25;
    font-weight: 700;
    color: #FFFFFF;
    letter-spacing: -0.45px;
}

.brand-subtitle {
    font-size: 11px;
    line-height: 1.55;
    color: #BDB8CF;
    margin-top: 6px;
    max-width: 225px;
}


/* ------------------------------------------------------------
   Sidebar labels
   ------------------------------------------------------------ */

.sidebar-label {
    font-size: 9px;
    font-weight: 600;
    color: #9A94AF;
    text-transform: uppercase;
    letter-spacing: 0.13em;
    margin: 1.2rem 0 0.55rem 0.35rem;
}


/* ------------------------------------------------------------
   Active workspace
   ------------------------------------------------------------ */

.sidebar-active {
    display: flex;
    align-items: center;
    gap: 9px;

    padding: 11px 12px;

    border-radius: 9px;

    background: #45405F;

    color: #FFFFFF;

    font-size: 12px;
    font-weight: 600;

    border-left: 3px solid #B2A9FF;

    box-shadow:
        0 5px 15px rgba(20, 18, 35, 0.16);

    transition:
        transform 0.18s ease,
        background 0.18s ease,
        box-shadow 0.18s ease;
}

.sidebar-active:hover {
    transform: translateX(3px);
    background: #4D4869;

    box-shadow:
        0 7px 20px rgba(20, 18, 35, 0.22);
}

.sidebar-active-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #C4BEFF;

    box-shadow:
        0 0 8px rgba(196, 190, 255, 0.55);
}


/* ------------------------------------------------------------
   Actual MVP capabilities
   ------------------------------------------------------------ */

.sidebar-system {
    display: flex;
    align-items: center;
    gap: 9px;

    padding: 8px 10px;

    color: #C7C3D4;
    font-size: 11px;

    border-radius: 7px;

    transition:
        background 0.18s ease,
        color 0.18s ease,
        transform 0.18s ease;
}

.sidebar-system:hover {
    background: #343149;
    color: #F0EEF8;
    transform: translateX(2px);
}

.sidebar-system-dot {
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: #A9D4BD;
}


/* ------------------------------------------------------------
   Divider
   ------------------------------------------------------------ */

.sidebar-divider {
    height: 1px;
    background: #454159;
    margin: 1.3rem 0;
}


/* ------------------------------------------------------------
   Memory status
   ------------------------------------------------------------ */

.memory-status {
    background: #343149;
    border: 1px solid #4A4561;

    border-radius: 10px;

    padding: 13px;

    margin-top: 0.6rem;

    box-shadow:
        0 6px 18px rgba(18, 16, 30, 0.14);

    transition:
        transform 0.2s ease,
        box-shadow 0.2s ease;
}

.memory-status:hover {
    transform: translateY(-2px);

    box-shadow:
        0 9px 24px rgba(18, 16, 30, 0.20);
}

.memory-status-title {
    font-size: 11px;
    font-weight: 600;
    color: #F4F2FA;
}

.memory-status-text {
    font-size: 10px;
    color: #AAA6BA;
    margin-top: 4px;
    line-height: 1.5;
}

.status-dot {
    display: inline-block;

    width: 6px;
    height: 6px;

    border-radius: 50%;

    background: #A9D4BD;

    margin-right: 5px;
}

.loop-text {
    font-size: 9px;
    color: #89849F;
    line-height: 1.7;

    margin-top: 18px;

    padding: 0 5px;
}


/* ============================================================
   MAIN HEADER
   ============================================================ */

.eyebrow {
    font-size: 10px;
    font-weight: 600;

    color: #7567D8;

    text-transform: uppercase;
    letter-spacing: 0.13em;

    margin-bottom: 8px;
}

.page-title {
    font-size: 34px;
    line-height: 1.12;

    font-weight: 600;

    letter-spacing: -1.2px;

    color: #29243D;

    margin: 0;
}

.page-description {
    max-width: 730px;

    font-size: 13px;
    line-height: 1.7;

    color: #747084;

    margin-top: 10px;
}

.system-status {
    margin-top: 11px;

    font-size: 10px;

    color: #777286;
}

.system-status .status-dot {
    background: #7EAA91;
}


/* ============================================================
   SECTION HEADINGS
   ============================================================ */

.section-title {
    font-size: 12px;

    font-weight: 600;

    color: #514A69;

    text-transform: uppercase;
    letter-spacing: 0.10em;

    margin-bottom: 11px;
}

.result-heading {
    font-size: 19px;

    line-height: 1.3;

    font-weight: 600;

    color: #302A49;

    letter-spacing: -0.3px;

    margin-bottom: 12px;
}


/* ============================================================
   QUESTION FORM
   ============================================================ */

div[data-testid="stForm"] {
    background: #FFFFFF !important;

    border: 1px solid #DED9EC !important;

    border-radius: 12px !important;

    padding: 7px !important;

    box-shadow:
        0 7px 24px rgba(69, 59, 105, 0.07);
}

div[data-testid="stForm"] input {
    background: #FAF9FE !important;

    border: 1px solid #E1DDEC !important;

    border-radius: 8px !important;

    color: #29243D !important;

    font-size: 13px !important;
}

div[data-testid="stForm"] input:focus {
    border-color: #9C91EA !important;

    box-shadow:
        0 0 0 3px rgba(117, 103, 216, 0.10) !important;
}

div[data-testid="stForm"] button {
    background: #7567D8 !important;

    color: #FFFFFF !important;

    border: none !important;

    border-radius: 8px !important;

    font-size: 12px !important;

    font-weight: 600 !important;

    min-height: 38px !important;

    transition:
        transform 0.18s ease,
        background 0.18s ease,
        box-shadow 0.18s ease;
}

div[data-testid="stForm"] button:hover {
    background: #6558C5 !important;

    transform: translateY(-2px);

    box-shadow:
        0 6px 15px rgba(117, 103, 216, 0.25);
}


/* ============================================================
   CARD SYSTEM
   ============================================================ */

div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FFFFFF !important;

    border: 1px solid #DED9EC !important;

    border-radius: 13px !important;

    box-shadow:
        0 6px 22px rgba(69, 59, 105, 0.055);

    transition:
        transform 0.2s ease,
        box-shadow 0.2s ease,
        border-color 0.2s ease;
}

div[data-testid="stVerticalBlockBorderWrapper"] > div {
    background: transparent !important;
}


/* General card hover */

div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    transform: translateY(-2px);

    box-shadow:
        0 10px 28px rgba(69, 59, 105, 0.09);

    border-color: #D4CEE5 !important;
}


/* ============================================================
   PASTEL CARD VARIATIONS

   :has() allows us to keep native Streamlit containers
   while giving specific sections different pastel tones.
   ============================================================ */


/* Recommendation = lavender */

div[data-testid="stVerticalBlockBorderWrapper"]:has(
    .recommendation-label
) {
    background: #EEE9FF !important;

    border-color: #DDD5FA !important;
}


/* Evidence = powder blue */

div[data-testid="stVerticalBlockBorderWrapper"]:has(
    .evidence-item
) {
    background: #EEF4FF !important;

    border-color: #D9E5FA !important;
}


/* Hindsight = mint */

div[data-testid="stVerticalBlockBorderWrapper"]:has(
    .memory-title
) {
    background: #EAF6EF !important;

    border-color: #D6E9DD !important;
}


/* Next action = peach */

div[data-testid="stVerticalBlockBorderWrapper"]:has(
    .next-action-content
) {
    background: #FFF0E6 !important;

    border-color: #F5DED0 !important;
}


/* Learning = soft yellow */

div[data-testid="stVerticalBlockBorderWrapper"]:has(
    .learning-label
) {
    background: #FFF8E8 !important;

    border-color: #F1E5C8 !important;
}


/* Experiment = powder lavender */

div[data-testid="stVerticalBlockBorderWrapper"]:has(
    .experiment-description
) {
    background: #F2EEFF !important;

    border-color: #DED7F6 !important;
}


/* ============================================================
   RECOMMENDATION
   ============================================================ */

.recommendation-label {
    font-size: 11px;

    font-weight: 600;

    color: #6758C8;

    text-transform: uppercase;
    letter-spacing: 0.11em;

    margin-bottom: 10px;
}

.recommendation-text {
    font-size: 22px;

    line-height: 1.52;

    font-weight: 500;

    letter-spacing: -0.4px;

    color: #29243D;
}


/* ============================================================
   INFORMATION CARDS
   ============================================================ */

.info-title {
    font-size: 11px;

    font-weight: 600;

    color: #625A7B;

    text-transform: uppercase;
    letter-spacing: 0.10em;

    margin-bottom: 8px;
}

.info-text {
    font-size: 13px;

    line-height: 1.7;

    color: #464255;
}


/* ============================================================
   EVIDENCE
   ============================================================ */

.evidence-item {
    padding: 11px 0;

    border-bottom: 1px solid #DCE5F2;

    font-size: 12px;

    line-height: 1.65;

    color: #4E5668;
}

.evidence-item:last-child {
    border-bottom: none;
}

.evidence-dot {
    color: #6D7FD2;

    margin-right: 7px;
}


/* ============================================================
   HINDSIGHT MEMORY
   ============================================================ */

.memory-title {
    font-size: 11px;

    font-weight: 600;

    color: #4D755F;

    text-transform: uppercase;

    letter-spacing: 0.10em;
}

.memory-description {
    font-size: 11px;

    color: #68786E;

    line-height: 1.55;

    margin-top: 4px;
}

div[data-testid="stExpander"] {
    border: 1px solid #D3E4D9 !important;

    border-radius: 8px !important;

    background: #F7FBF8 !important;
}


/* ============================================================
   NEXT ACTION
   ============================================================ */

.next-action-content {
    font-size: 13px;

    line-height: 1.7;

    color: #514B52;
}


/* ============================================================
   LEARNING
   ============================================================ */

.learning-label {
    font-size: 11px;

    font-weight: 600;

    color: #746449;

    text-transform: uppercase;

    letter-spacing: 0.10em;
}

.learning-value {
    font-size: 13px;

    line-height: 1.65;

    color: #514B45;

    margin-top: 5px;
}


/* ============================================================
   EXPERIMENT
   ============================================================ */

.experiment-description {
    font-size: 12px;

    line-height: 1.65;

    color: #625C72;

    margin-bottom: 13px;
}


/* Experiment labels must be visible */

div[data-testid="stForm"] label,
div[data-testid="stForm"] label p,
div[data-testid="stTextInput"] label,
div[data-testid="stTextInput"] label p,
div[data-testid="stTextArea"] label,
div[data-testid="stTextArea"] label p {
    color: #514A69 !important;

    font-size: 12px !important;

    font-weight: 600 !important;
}


/* Experiment inputs */

div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea {
    background: #FFFDFE !important;

    color: #29243D !important;

    border: 1px solid #D9D4E4 !important;

    border-radius: 8px !important;
}

div[data-testid="stTextInput"] input:focus,
div[data-testid="stTextArea"] textarea:focus {
    border-color: #9A90E9 !important;

    box-shadow:
        0 0 0 3px rgba(117, 103, 216, 0.09) !important;
}


/* ============================================================
   BUTTONS
   ============================================================ */

.stButton button {
    border-radius: 8px !important;

    font-weight: 600 !important;

    transition:
        transform 0.18s ease,
        box-shadow 0.18s ease,
        background 0.18s ease;
}

.stButton button:hover {
    transform: translateY(-2px);

    box-shadow:
        0 6px 15px rgba(117, 103, 216, 0.18);
}


/* ============================================================
   ALERTS
   ============================================================ */

div[data-testid="stAlert"] {
    border-radius: 9px !important;
}


/* ============================================================
   MOBILE
   ============================================================ */

@media (max-width: 768px) {

    .main .block-container {
        padding: 1.4rem 1rem 3rem;
    }

    .page-title {
        font-size: 27px;
    }

    .brand-title {
        font-size: 17px;
    }

    .recommendation-text {
        font-size: 19px;
    }

    .section-title {
        font-size: 11px;
    }

    .result-heading {
        font-size: 17px;
    }
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
<div class="brand">
<div class="brand-mark">✦</div>
<div class="brand-title">Creator Strategy Agent</div>
<div class="brand-subtitle">
A persistent strategy workspace that learns from your creator journey.
</div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="sidebar-label">Current workspace</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
<div class="sidebar-active">
<span class="sidebar-active-dot"></span>
Strategy analysis
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="sidebar-label">Agent capabilities</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
<div class="sidebar-system">
<span class="sidebar-system-dot"></span>
Persistent Hindsight memory
</div>

<div class="sidebar-system">
<span class="sidebar-system-dot"></span>
Evidence-based recommendations
</div>

<div class="sidebar-system">
<span class="sidebar-system-dot"></span>
Experiment learning
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="sidebar-divider"></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="sidebar-label">System status</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
<div class="memory-status">
<div class="memory-status-title">
<span class="status-dot"></span>
Memory active
</div>

<div class="memory-status-text">
Hindsight is connected and available for persistent creator learning.
</div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
<div class="loop-text">
CREATE → PUBLISH → MEASURE<br>
REMEMBER → LEARN → RECOMMEND<br>
EXPERIMENT → LEARN AGAIN
</div>
""",
        unsafe_allow_html=True,
    )


# ============================================================
# MAIN HEADER
# ============================================================

st.markdown(
    '<div class="eyebrow">Creator intelligence workspace</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="page-title">Strategy overview</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="page-description">
Your content history becomes a strategic memory.
Ask a question, understand the evidence, run an experiment,
and let the system learn from what happens next.
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="system-status">
<span class="status-dot"></span>
Persistent creator memory active
</div>
""",
    unsafe_allow_html=True,
)

st.write("")
st.write("")


# ============================================================
# ASK STRATEGY
# ============================================================

st.markdown(
    '<div class="section-title">Ask your strategy agent</div>',
    unsafe_allow_html=True,
)

with st.form("strategy_question_form"):

    question = st.text_input(
        "Strategy question",
        label_visibility="collapsed",
        placeholder=(
            "What should I create next based on everything I've learned?"
        ),
    )

    submitted = st.form_submit_button(
        "Ask Strategy Agent",
    )


if submitted:

    if not question.strip():

        st.warning("Enter a strategy question first.")

    else:

        st.session_state.last_question = question.strip()

        with st.spinner(
            "Recalling creator memory and analyzing evidence..."
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


# ============================================================
# LATEST LEARNING
# ============================================================

if st.session_state.last_result:

    st.write("")
    st.write("")

    st.markdown(
        '<div class="section-title">Latest learning</div>',
        unsafe_allow_html=True,
    )

    latest = st.session_state.last_result

    with st.container(border=True):

        st.markdown(
            '<div class="learning-label">Experiment result</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            f'<div class="learning-value">{latest["metrics"]}</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div style="height:10px;"></div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="learning-label">Creator observation</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            f'<div class="learning-value">{latest["observation"]}</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            """
<div style="
font-size:10px;
color:#7B7786;
margin-top:12px;
">
Saved to persistent Hindsight memory.
</div>
""",
            unsafe_allow_html=True,
        )


# ============================================================
# RESULT
# ============================================================

result = st.session_state.recommendation


if result:

    if "answer" not in result:

        st.session_state.recommendation = None

        st.warning(
            "The previous response used an older format. "
            "Please ask the question again."
        )

        st.stop()


    st.write("")
    st.write("")

    question_type = result.get(
        "question_type",
        "general",
    )

    headings = {
        "recommendation": "Recommendation",
        "performance": "Performance analysis",
        "weak_patterns": "Patterns to reduce",
        "audience": "Audience insights",
        "audience_profile": "Audience profile",
        "experiment": "Experiment",
        "learning": "What you've learned",
        "general": "Strategy insight",
    }

    heading = headings.get(
        question_type,
        "Strategy insight",
    )


    # ========================================================
    # RESULT HEADING
    # ========================================================

    st.markdown(
        f'<div class="result-heading">{heading}</div>',
        unsafe_allow_html=True,
    )


    # ========================================================
    # STRATEGIC ANSWER
    # ========================================================

    with st.container(border=True):

        st.markdown(
            '<div class="recommendation-label">Strategic answer</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            f'<div class="recommendation-text">'
            f'{result["answer"]}'
            f'</div>',
            unsafe_allow_html=True,
        )


    # ========================================================
    # INSIGHT + UNCERTAINTY
    # ========================================================

    st.write("")

    col1, col2 = st.columns(2)

    with col1:

        with st.container(border=True):

            st.markdown(
                '<div class="info-title">Key insight</div>',
                unsafe_allow_html=True,
            )

            st.markdown(
                f'<div class="info-text">'
                f'{result.get("insight", "")}'
                f'</div>',
                unsafe_allow_html=True,
            )

    with col2:

        with st.container(border=True):

            st.markdown(
                '<div class="info-title">Uncertainty</div>',
                unsafe_allow_html=True,
            )

            st.markdown(
                f'<div class="info-text">'
                f'{result.get("uncertainty", "")}'
                f'</div>',
                unsafe_allow_html=True,
            )


    # ========================================================
    # EVIDENCE
    # ========================================================

    st.write("")

    st.markdown(
        '<div class="result-heading">Evidence from your history</div>',
        unsafe_allow_html=True,
    )

    evidence = result.get(
        "evidence",
        [],
    )

    with st.container(border=True):

        if evidence:

            for item in evidence:

                st.markdown(
                    f"""
<div class="evidence-item">
<span class="evidence-dot">●</span>
{item}
</div>
""",
                    unsafe_allow_html=True,
                )

        else:

            st.markdown(
                """
<div class="info-text">
No specific evidence was found.
</div>
""",
                unsafe_allow_html=True,
            )


    # ========================================================
    # HINDSIGHT MEMORY
    # ========================================================

    st.write("")

    memories_used = result.get(
        "memories_used",
        [],
    )

    with st.container(border=True):

        st.markdown(
            '<div class="memory-title">Hindsight memory</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
<div class="memory-description">
{len(memories_used)} relevant memories were recalled to inform this response.
</div>
""",
            unsafe_allow_html=True,
        )

        if memories_used:

            with st.expander(
                "View recalled memories"
            ):

                for memory in memories_used:

                    st.markdown(
                        f"• {memory}"
                    )


    # ========================================================
    # NEXT ACTION
    # ========================================================

    next_action = result.get(
        "next_action"
    )

    if next_action:

        st.write("")

        st.markdown(
            '<div class="result-heading">Next action</div>',
            unsafe_allow_html=True,
        )

        with st.container(border=True):

            st.markdown(
                f'<div class="next-action-content">'
                f'{next_action}'
                f'</div>',
                unsafe_allow_html=True,
            )


    # ========================================================
    # EXPERIMENT / LEARNING LOOP
    # ========================================================

    if question_type in [
        "recommendation",
        "experiment",
    ]:

        st.write("")
        st.write("")

        st.markdown(
            '<div class="result-heading">'
            'Continue the learning loop'
            '</div>',
            unsafe_allow_html=True,
        )

        with st.container(border=True):

            st.markdown(
                """
<div class="experiment-description">
Run the recommendation in the real world.
Record what happened and the result becomes part of
your persistent creator memory.
</div>
""",
                unsafe_allow_html=True,
            )

            with st.form("experiment_form"):

                result_metrics = st.text_input(
                    "Result metrics",
                    placeholder=(
                        "18,600 views, 1,240 saves, 180 likes..."
                    ),
                )

                creator_observation = st.text_area(
                    "What did you observe?",
                    placeholder=(
                        "What worked, what failed, or what surprised you?"
                    ),
                )

                save_result = st.form_submit_button(
                    "Save Result to Hindsight",
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

                            record_result(
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

                            st.session_state.last_result = {
                                "metrics": result_metrics,
                                "observation": creator_observation,
                            }

                            st.success(
                                "Experiment result saved to Hindsight."
                            )

                            st.rerun()

                        except Exception as exc:

                            st.error(str(exc))


# ============================================================
# EMPTY STATE
# ============================================================

if not result:

    st.write("")
    st.write("")

    st.markdown(
        '<div class="result-heading">How the agent learns</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        with st.container(border=True):

            st.markdown(
                '<div class="info-title">01 · Remember</div>',
                unsafe_allow_html=True,
            )

            st.markdown(
                """
<div class="info-text">
Your content history, results and observations
become persistent strategic memory.
</div>
""",
                unsafe_allow_html=True,
            )

    with col2:

        with st.container(border=True):

            st.markdown(
                '<div class="info-title">02 · Learn</div>',
                unsafe_allow_html=True,
            )

            st.markdown(
                """
<div class="info-text">
New outcomes are compared with what happened
before instead of starting from zero.
</div>
""",
                unsafe_allow_html=True,
            )

    with col3:

        with st.container(border=True):

            st.markdown(
                '<div class="info-title">03 · Recommend</div>',
                unsafe_allow_html=True,
            )

            st.markdown(
                """
<div class="info-text">
Get evidence-backed strategy based on your
actual creator journey.
</div>
""",
                unsafe_allow_html=True,
            )