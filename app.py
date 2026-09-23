import re
import html
import streamlit as st
import streamlit.components.v1 as components

from google import genai
from google.genai import types

from prompt_template import SYSTEM_PROMPT


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AI 3D Science Lab",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# MODEL CATALOG
#
# All requested models are shown in the dropdown.
# Capability is tracked so incompatible Live/Image models
# do not cause an API crash when selected.
# ============================================================

MODEL_CATALOG = {
    "Gemini 3.8 Flash": {
        "id": "gemini-3.8-flash",
        "type": "text",
        "description": "Frontier-class general-purpose Flash model.",
    },
    "Gemini 3.8 Live": {
        "id": "gemini-3.8-live",
        "type": "live",
        "description": "Real-time audio/live model — not a text HTML generation endpoint.",
    },
    "Gemini 3.8 Live Extended Thinking": {
        "id": "gemini-3.8-live-extended-thinking",
        "type": "live",
        "description": "High-reasoning Live audio model — not a text HTML generation endpoint.",
    },
    "Gemini 3.1 Pro Preview": {
        "id": "gemini-3.1-pro-preview",
        "type": "text",
        "description": "Advanced reasoning and coding model.",
    },
    "Gemini 3.1 Flash Image / Nano Banana 2": {
        "id": "gemini-3.1-flash-image",
        "type": "image",
        "description": "Image-generation model — not used for HTML text generation.",
    },
    "Gemini 3.5 Flash": {
        "id": "gemini-3.5-flash",
        "type": "text",
        "description": "High-performance Flash model.",
    },
    "Gemini 3.5 Flash-Lite": {
        "id": "gemini-3.5-flash-lite",
        "type": "text",
        "description": "Cost-efficient high-volume Flash-Lite model.",
    },
    "Gemini 2.5 Pro": {
        "id": "gemini-2.5-pro",
        "type": "text",
        "description": "High-capability reasoning and coding model.",
    },
    "Gemini 2.5 Flash": {
        "id": "gemini-2.5-flash",
        "type": "text",
        "description": "Balanced speed/intelligence model.",
    },
}


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>
        .stApp {
            background:
                radial-gradient(
                    circle at 5% 0%,
                    rgba(37, 99, 235, 0.11),
                    transparent 28%
                ),
                radial-gradient(
                    circle at 95% 10%,
                    rgba(124, 58, 237, 0.10),
                    transparent 30%
                );
        }

        .hero {
            padding: 1.0rem 0 1.2rem 0;
        }

        .hero-kicker {
            color: #60a5fa;
            font-size: .78rem;
            font-weight: 800;
            letter-spacing: .14em;
            text-transform: uppercase;
            margin-bottom: .4rem;
        }

        .hero-title {
            font-size: clamp(2rem, 4vw, 3.4rem);
            line-height: 1.05;
            font-weight: 850;
            letter-spacing: -.055em;
            margin: 0;
        }

        .hero-subtitle {
            color: #94a3b8;
            max-width: 850px;
            font-size: 1.02rem;
            line-height: 1.65;
            margin-top: .75rem;
        }

        .glass-card {
            border: 1px solid rgba(148, 163, 184, .16);
            border-radius: 16px;
            padding: 1rem 1.15rem;
            background: rgba(15, 23, 42, .50);
        }

        .mini-label {
            color: #94a3b8;
            font-size: .76rem;
            font-weight: 700;
            letter-spacing: .08em;
            text-transform: uppercase;
        }

        .simulation-label {
            color: #94a3b8;
            font-size: .78rem;
            font-weight: 700;
            letter-spacing: .08em;
            margin: .6rem 0;
        }

        .api-note {
            color: #94a3b8;
            font-size: .72rem;
            line-height: 1.45;
        }

        .model-note {
            color: #94a3b8;
            font-size: .72rem;
            line-height: 1.4;
            margin-top: -.2rem;
        }

        div[data-testid="stSidebar"] {
            border-right: 1px solid rgba(148, 163, 184, .12);
        }

        .stButton > button {
            border-radius: 10px;
            min-height: 2.8rem;
            font-weight: 750;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

defaults = {
    "generated_html": None,
    "last_domain": None,
    "last_prompt": None,
    "last_model": None,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# HTML CLEANUP
# ============================================================

def clean_generated_html(raw_html: str) -> str:
    """Remove Markdown fences and accidental surrounding text."""

    if not raw_html:
        raise ValueError("Gemini returned an empty response.")

    cleaned = raw_html.strip()

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

    doctype = re.search(
        r"<!DOCTYPE\s+html\s*>",
        cleaned,
        flags=re.IGNORECASE,
    )

    html_start = re.search(
        r"<html\b",
        cleaned,
        flags=re.IGNORECASE,
    )

    if doctype:
        cleaned = cleaned[doctype.start():]
    elif html_start:
        cleaned = cleaned[html_start.start():]

    html_end = re.search(
        r"</html\s*>",
        cleaned,
        flags=re.IGNORECASE,
    )

    if html_end:
        cleaned = cleaned[:html_end.end()]

    cleaned = cleaned.strip()

    if not re.search(r"<html\b", cleaned, flags=re.IGNORECASE):
        raise ValueError(
            "The AI response did not contain a valid HTML document."
        )

    if not re.search(r"</html\s*>", cleaned, flags=re.IGNORECASE):
        raise ValueError(
            "The AI response is missing the closing </html> tag."
        )

    return cleaned


# ============================================================
# GEMINI
# ============================================================

def create_client(api_key: str) -> genai.Client:
    api_key = (api_key or "").strip()

    if not api_key:
        raise ValueError("Please enter your Gemini API key.")

    return genai.Client(api_key=api_key)


def generate_simulation(
    api_key: str,
    model_id: str,
    domain: str,
    user_prompt: str,
) -> str:

    client = create_client(api_key)

    request = f"""
Scientific domain:
{domain}

User request:
{user_prompt}

Generate the complete premium interactive 3D educational simulation.

Return ONLY raw executable HTML.
"""

    # Do not send Live/Image models to generate_content.
    # This validation prevents confusing API failures.
    model_info = next(
        (
            item
            for item in MODEL_CATALOG.values()
            if item["id"] == model_id
        ),
        None,
    )

    if model_info is None:
        raise ValueError("Selected Gemini model is not recognized.")

    if model_info["type"] != "text":
        raise ValueError(
            f"The selected model `{model_id}` is a "
            f"{model_info['type']} model and is not compatible with "
            "this application's HTML-generation workflow. "
            "Please select a text-generation model such as Gemini 3.8 "
            "Flash or Gemini 3.1 Pro Preview."
        )

    # Keep the request compatible across the supported text models.
    # The latest Gemini models have their own reasoning defaults.
    response = client.models.generate_content(
        model=model_id,
        contents=request,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
        ),
    )

    generated_text = getattr(response, "text", None)

    if not generated_text:
        raise RuntimeError(
            "Gemini returned no text. The selected model may not "
            "support this Generate Content request with the current API key."
        )

    return clean_generated_html(generated_text)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## 🔬 AI 3D Science Lab")
    st.caption("Premium scientific visualization generator.")

    st.divider()

    st.markdown("### 🔑 Gemini API")

    api_key = st.text_input(
        "API Key",
        type="password",
        placeholder="Paste your Gemini API key",
        help="Used only for the current app session.",
    )

    st.markdown(
        """
        <div class="api-note">
        🔒 Runtime input only. Never paste your API key into GitHub,
        app.py, prompt_template.py, or README.md.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("")

    st.markdown("### 🤖 Gemini Model")

    model_labels = list(MODEL_CATALOG.keys())

    selected_label = st.selectbox(
        "Model",
        model_labels,
        index=0,
    )

    selected_info = MODEL_CATALOG[selected_label]
    selected_model_id = selected_info["id"]

    st.markdown(
        f"""
        <div class="model-note">
        <b>{html.escape(selected_model_id)}</b><br>
        {html.escape(selected_info["description"])}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown("### 🧪 Simulation")

    domain = st.selectbox(
        "Scientific Domain",
        [
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
    )

    user_prompt = st.text_area(
        "Describe the simulation",
        height=200,
        placeholder=(
            "Example:\n\n"
            "Create a premium interactive 3D visualization of projectile "
            "motion. Show the trajectory, velocity vector, gravity vector, "
            "launch angle and initial velocity. Add sliders for launch "
            "angle, initial velocity and animation speed."
        ),
    )

    generate_button = st.button(
        "🚀 Generate 3D Simulation",
        type="primary",
        use_container_width=True,
    )

    st.divider()

    st.caption(
        "For this app, use a text-generation model. "
        "Live and image models are displayed for reference but are "
        "not sent to the HTML-generation endpoint."
    )


# ============================================================
# MAIN HEADER
# ============================================================

st.markdown(
    """
    <div class="hero">
        <div class="hero-kicker">Gemini × Three.js × Streamlit</div>

        <div class="hero-title">
            AI 3D Science Lab
        </div>

        <div class="hero-subtitle">
            Turn a scientific concept into a premium interactive 3D
            learning experience. Describe what you want to teach and
            Gemini engineers the visualization, animation and controls.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# GENERATION
# ============================================================

if generate_button:

    if not api_key.strip():

        st.warning(
            "🔑 Paste your Gemini API key in the sidebar first."
        )

    elif not user_prompt.strip():

        st.warning(
            "📝 Describe the scientific concept you want to visualize."
        )

    elif selected_info["type"] != "text":

        st.warning(
            f"⚠️ `{selected_model_id}` is not a text HTML-generation "
            "model. Select a text model such as Gemini 3.8 Flash."
        )

    else:

        with st.spinner(
            f"Engineering the 3D simulation with {selected_model_id}..."
        ):

            try:

                result = generate_simulation(
                    api_key=api_key,
                    model_id=selected_model_id,
                    domain=domain,
                    user_prompt=user_prompt.strip(),
                )

                st.session_state.generated_html = result
                st.session_state.last_domain = domain
                st.session_state.last_prompt = user_prompt.strip()
                st.session_state.last_model = selected_model_id

                st.success(
                    "✨ Simulation generated successfully."
                )

            except Exception as exc:

                st.session_state.generated_html = None

                st.error(
                    "The simulation could not be generated."
                )

                with st.expander("Technical details"):

                    st.code(
                        str(exc),
                        language="text",
                    )


# ============================================================
# SIMULATION
# ============================================================

generated_html = st.session_state.generated_html

if generated_html:

    st.markdown(
        f"""
        <div class="simulation-label">
            LIVE 3D SIMULATION
            · {html.escape(st.session_state.last_domain or "")}
            · {html.escape(st.session_state.last_model or "")}
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

    source_col, status_col = st.columns(
        [2.25, 1],
        gap="large",
    )

    with source_col:

        with st.expander(
            "🧩 Inspect Generated HTML Source"
        ):

            st.code(
                generated_html,
                language="html",
            )

    with status_col:

        st.markdown(
            """
            <div class="glass-card">

            <div class="mini-label">
            Generation Status
            </div>

            <br>

            🟢 AI response received

            <br><br>

            🟢 HTML cleaned

            <br><br>

            🟢 HTML validated

            <br><br>

            🟢 Three.js injected

            <br><br>

            🟢 Interactive scene active

            </div>
            """,
            unsafe_allow_html=True,
        )

else:

    st.markdown(
        """
        <div class="glass-card">

        <div class="mini-label">
        READY TO GENERATE
        </div>

        <h3>Build a scientific world from a sentence.</h3>

        <p style="color:#94a3b8;line-height:1.6;">
        Paste your Gemini API key, choose a model, describe the concept,
        and generate a complete interactive Three.js simulation.
        </p>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(
            """
            **⚛️ Physics**

            Projectile motion, fields, waves, vectors,
            collisions and dynamics.
            """
        )

    with c2:
        st.markdown(
            """
            **📐 Mathematics**

            3D geometry, planes, surfaces, transformations,
            vectors and coordinate systems.
            """
        )

    with c3:
        st.markdown(
            """
            **🧬 Science**

            Molecules, cells, astronomy, structures and
            interactive scientific processes.
            """
        )
