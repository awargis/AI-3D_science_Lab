import re
import html
import streamlit as st
import streamlit.components.v1 as components

from google import genai
from google.genai import types

from prompt_template import SYSTEM_PROMPT


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="AI 3D Science Lab",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>
        .main {
            background:
                radial-gradient(
                    circle at 10% 10%,
                    rgba(59, 130, 246, 0.08),
                    transparent 30%
                ),
                radial-gradient(
                    circle at 90% 20%,
                    rgba(139, 92, 246, 0.08),
                    transparent 30%
                );
        }

        .hero {
            padding: 1.5rem 0 1rem 0;
        }

        .hero-title {
            font-size: 2.6rem;
            font-weight: 800;
            letter-spacing: -0.04em;
            margin-bottom: 0.25rem;
        }

        .hero-subtitle {
            color: #94a3b8;
            font-size: 1.05rem;
            max-width: 850px;
            line-height: 1.6;
        }

        .status-card {
            padding: 1rem 1.2rem;
            border: 1px solid rgba(148, 163, 184, 0.15);
            border-radius: 14px;
            background: rgba(15, 23, 42, 0.55);
        }

        .stButton > button {
            width: 100%;
            border-radius: 10px;
            font-weight: 700;
            min-height: 2.8rem;
        }

        div[data-testid="stSidebar"] {
            border-right: 1px solid rgba(148, 163, 184, 0.12);
        }

        .simulation-label {
            font-size: 0.85rem;
            color: #94a3b8;
            margin-bottom: 0.4rem;
        }

        .api-note {
            font-size: 0.75rem;
            color: #94a3b8;
            line-height: 1.4;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# SESSION STATE
# =========================================================

if "generated_html" not in st.session_state:
    st.session_state.generated_html = None

if "last_domain" not in st.session_state:
    st.session_state.last_domain = None

if "last_prompt" not in st.session_state:
    st.session_state.last_prompt = None


# =========================================================
# HTML CLEANUP
# =========================================================

def clean_generated_html(raw_html: str) -> str:
    """
    Removes accidental Markdown fences and surrounding text
    from Gemini's response and validates the HTML document.
    """

    if not raw_html:
        raise ValueError("Gemini returned an empty response.")

    cleaned = raw_html.strip()

    # Remove opening Markdown fence.
    cleaned = re.sub(
        r"^\s*```(?:html|HTML|htm)?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    # Remove closing Markdown fence.
    cleaned = re.sub(
        r"\s*```\s*$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    cleaned = cleaned.strip()

    # Find beginning of actual HTML document.
    doctype_match = re.search(
        r"<!DOCTYPE\s+html\s*>",
        cleaned,
        flags=re.IGNORECASE,
    )

    html_match = re.search(
        r"<html\b",
        cleaned,
        flags=re.IGNORECASE,
    )

    if doctype_match:
        cleaned = cleaned[doctype_match.start():]
    elif html_match:
        cleaned = cleaned[html_match.start():]

    # Remove anything after </html>.
    closing_match = re.search(
        r"</html\s*>",
        cleaned,
        flags=re.IGNORECASE,
    )

    if closing_match:
        cleaned = cleaned[:closing_match.end()]

    # Final Markdown cleanup.
    cleaned = re.sub(
        r"^\s*```(?:html|HTML|htm)?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(
        r"\s*```\s*$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    cleaned = cleaned.strip()

    # Validate.
    if not re.search(r"<html\b", cleaned, flags=re.IGNORECASE):
        raise ValueError(
            "Gemini response does not contain a valid <html> document."
        )

    if not re.search(r"</html\s*>", cleaned, flags=re.IGNORECASE):
        raise ValueError(
            "Gemini response is missing the closing </html> tag."
        )

    return cleaned


# =========================================================
# GEMINI CLIENT
# =========================================================

def get_gemini_client(api_key: str) -> genai.Client:
    """
    Creates the modern Google GenAI client.
    """

    if not api_key:
        raise ValueError("Please enter your Gemini API key.")

    api_key = api_key.strip()

    if not api_key:
        raise ValueError("Gemini API key cannot be empty.")

    return genai.Client(api_key=api_key)


# =========================================================
# GEMINI GENERATION
# =========================================================

def generate_simulation(
    api_key: str,
    model_name: str,
    domain: str,
    user_prompt: str,
) -> str:
    """
    Generate the complete interactive Three.js HTML simulation.
    """

    client = get_gemini_client(api_key)

    full_prompt = f"""
Scientific Domain:
{domain}

User's Visualization Request:
{user_prompt}

Create the complete interactive 3D educational simulation now.

Follow every requirement in the system instruction.

Return ONLY the raw HTML document.
Do not use Markdown code fences.
"""

    response = client.models.generate_content(
        model=model_name,
        contents=full_prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.2,
        ),
    )

    if not response:
        raise RuntimeError(
            "Gemini returned no response."
        )

    generated_text = getattr(response, "text", None)

    if not generated_text:
        raise RuntimeError(
            "Gemini returned no text content."
        )

    return clean_generated_html(generated_text)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown("## 🔬 AI 3D Science Lab")

    st.caption(
        "Generate interactive scientific simulations "
        "with Gemini + Three.js."
    )

    st.divider()

    # -----------------------------------------------------
    # API KEY
    # -----------------------------------------------------

    st.markdown("### 🔑 Gemini API")

    api_key = st.text_input(
        "Gemini API Key",
        type="password",
        placeholder="Paste your Gemini API key here",
        help=(
            "Your API key is used only for the current "
            "Streamlit session and is not written to the "
            "project files."
        ),
    )

    st.markdown(
        """
        <div class="api-note">
        🔒 Your key is entered at runtime and is not stored
        in the GitHub project.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("")

    # -----------------------------------------------------
    # MODEL SELECTION
    # -----------------------------------------------------

    st.markdown("### 🤖 Gemini Model")

    model_options = {
        "Gemini 2.5 Flash — Recommended": "gemini-2.5-flash",
        "Gemini 2.5 Pro — Higher reasoning": "gemini-2.5-pro",
    }

    selected_model_label = st.selectbox(
        "Select model",
        options=list(model_options.keys()),
        index=0,
        help=(
            "Flash is generally faster and more economical. "
            "Pro is intended for more demanding generation tasks."
        ),
    )

    selected_model = model_options[selected_model_label]

    st.caption(
        f"Selected model: `{selected_model}`"
    )

    st.divider()

    # -----------------------------------------------------
    # SCIENTIFIC DOMAIN
    # -----------------------------------------------------

    st.markdown("### 🧪 Visualization")

    domain = st.selectbox(
        "Scientific Domain",
        options=[
            "Physics",
            "Chemistry",
            "Mathematics",
            "Biology",
            "Computer Science",
            "Astronomy",
            "Earth Science",
            "Engineering",
            "Other",
        ],
        index=0,
    )

    # -----------------------------------------------------
    # USER PROMPT
    # -----------------------------------------------------

    user_prompt = st.text_area(
        "What should be visualized?",
        height=190,
        placeholder=(
            "Example:\n\n"
            "Create an interactive 3D simulation of projectile "
            "motion. Show the trajectory, velocity vector and "
            "gravity vector. Add sliders for launch angle and "
            "initial velocity."
        ),
    )

    st.markdown("")

    # -----------------------------------------------------
    # GENERATE
    # -----------------------------------------------------

    generate_button = st.button(
        "🚀 Generate 3D Simulation",
        type="primary",
        use_container_width=True,
    )

    st.divider()

    st.caption(
        "The selected Gemini model generates the complete "
        "Three.js HTML simulation dynamically."
    )


# =========================================================
# MAIN HEADER
# =========================================================

st.markdown(
    """
    <div class="hero">
        <div class="hero-title">
            AI 3D Science Lab
        </div>

        <div class="hero-subtitle">
            Turn any scientific concept into an interactive
            3D learning experience using Gemini + Three.js.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# GENERATE SIMULATION
# =========================================================

if generate_button:

    if not api_key.strip():

        st.warning(
            "🔑 Please paste your Gemini API key in the sidebar."
        )

    elif not user_prompt.strip():

        st.warning(
            "📝 Please enter a scientific visualization request."
        )

    else:

        with st.spinner(
            f"Gemini is generating your 3D simulation using "
            f"{selected_model}..."
        ):

            try:

                generated_html = generate_simulation(
                    api_key=api_key,
                    model_name=selected_model,
                    domain=domain,
                    user_prompt=user_prompt.strip(),
                )

                st.session_state.generated_html = generated_html
                st.session_state.last_domain = domain
                st.session_state.last_prompt = user_prompt.strip()

                st.success(
                    "✅ 3D simulation generated successfully."
                )

            except Exception as exc:

                st.session_state.generated_html = None

                st.error(
                    "❌ The simulation could not be generated."
                )

                with st.expander(
                    "Technical error details"
                ):
                    st.code(
                        str(exc),
                        language="text",
                    )


# =========================================================
# DISPLAY SIMULATION
# =========================================================

generated_html = st.session_state.generated_html


if generated_html:

    st.markdown(
        f"""
        <div class="simulation-label">
            LIVE SIMULATION ·
            {html.escape(st.session_state.last_domain or "")}
        </div>
        """,
        unsafe_allow_html=True,
    )

    components.html(
        generated_html,
        height=700,
        scrolling=False,
    )

    st.divider()

    source_col, info_col = st.columns(
        [2.2, 1]
    )

    with source_col:

        with st.expander(
            "🧩 Inspect Generated HTML Source",
            expanded=False,
        ):

            st.code(
                generated_html,
                language="html",
            )

    with info_col:

        st.markdown(
            """
            <div class="status-card">

            <strong>Simulation Status</strong>

            <br><br>

            🟢 Gemini response received

            <br>

            🟢 Markdown cleaned

            <br>

            🟢 HTML validated

            <br>

            🟢 Three.js scene injected

            <br>

            🟢 Interactive iframe active

            </div>
            """,
            unsafe_allow_html=True,
        )

else:

    st.info(
        "Choose a Gemini model, enter your API key, "
        "describe the scientific concept, and click "
        "**Generate 3D Simulation**."
    )

    st.markdown(
        """
        ### 💡 Example ideas

        **Physics**
        - Projectile motion
        - Electric field
        - SHM
        - Wave propagation

        **Mathematics**
        - 3D planes
        - Vector geometry
        - Parametric surfaces
        - Coordinate transformations

        **Chemistry**
        - Molecular geometry
        - Bond angles
        - Atomic structures

        **Biology**
        - 3D cell
        - DNA
        - Biological processes

        **Astronomy**
        - Planetary orbits
        - Gravity
        - Solar systems
        """
    )
