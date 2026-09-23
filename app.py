import re
import html
import streamlit as st
import streamlit.components.v1 as components

from google import genai
from google.genai import types

from prompt_template import SYSTEM_PROMPT


st.set_page_config(
    page_title="AI 3D Science Lab",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .main {
            background:
                radial-gradient(circle at 10% 10%, rgba(59,130,246,.08), transparent 30%),
                radial-gradient(circle at 90% 20%, rgba(139,92,246,.08), transparent 30%);
        }
        .hero { padding: 1.5rem 0 1rem 0; }
        .hero-title {
            font-size: 2.6rem;
            font-weight: 800;
            letter-spacing: -0.04em;
            margin-bottom: .25rem;
        }
        .hero-subtitle {
            color: #94a3b8;
            font-size: 1.05rem;
            max-width: 850px;
            line-height: 1.6;
        }
        .status-card {
            padding: 1rem 1.2rem;
            border: 1px solid rgba(148,163,184,.15);
            border-radius: 14px;
            background: rgba(15,23,42,.55);
        }
        .stButton > button {
            width: 100%;
            border-radius: 10px;
            font-weight: 700;
            min-height: 2.8rem;
        }
        div[data-testid="stSidebar"] {
            border-right: 1px solid rgba(148,163,184,.12);
        }
        .simulation-label {
            font-size: .85rem;
            color: #94a3b8;
            margin-bottom: .4rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def clean_generated_html(raw_html: str) -> str:
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

    cleaned = cleaned.strip()

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

    closing_match = re.search(
        r"</html\s*>",
        cleaned,
        flags=re.IGNORECASE,
    )
    if closing_match:
        cleaned = cleaned[:closing_match.end()]

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
    ).strip()

    if not re.search(r"<html\b", cleaned, flags=re.IGNORECASE):
        raise ValueError("Generated response does not contain a valid <html> document.")

    if not re.search(r"</html\s*>", cleaned, flags=re.IGNORECASE):
        raise ValueError("Generated response is missing the closing </html> tag.")

    return cleaned


def get_gemini_client() -> genai.Client:
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except KeyError as exc:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. Add it to Streamlit Secrets."
        ) from exc

    if not str(api_key).strip():
        raise RuntimeError("GEMINI_API_KEY exists but is empty.")

    return genai.Client(api_key=str(api_key).strip())


def generate_simulation(domain: str, user_prompt: str) -> str:
    client = get_gemini_client()

    full_prompt = f"""
Scientific Domain:
{domain}

User's Visualization Request:
{user_prompt}

Create the complete interactive 3D educational simulation now.

Follow every requirement in the system instruction.
Return ONLY the raw HTML document.
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=full_prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.2,
        ),
    )

    if not response:
        raise RuntimeError("Gemini returned no response.")

    generated_text = getattr(response, "text", None)
    if not generated_text:
        raise RuntimeError("Gemini returned no text content.")

    return clean_generated_html(generated_text)


with st.sidebar:
    st.markdown("## 🔬 AI 3D Science Lab")
    st.caption("Generate interactive Three.js simulations with Gemini.")
    st.divider()

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
        "What should be visualized?",
        height=180,
        placeholder=(
            "Example: Create an interactive 3D simulation of projectile "
            "motion with launch angle, initial velocity, gravity, "
            "trajectory and velocity vectors."
        ),
    )

    generate_button = st.button(
        "🚀 Generate 3D Simulation",
        type="primary",
        use_container_width=True,
    )

    st.divider()
    st.caption(
        "Gemini generates the complete HTML/Three.js simulation dynamically."
    )


st.markdown(
    """
    <div class="hero">
        <div class="hero-title">AI 3D Science Lab</div>
        <div class="hero-subtitle">
            Turn a scientific concept into an interactive 3D learning
            experience using Gemini + Three.js.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


if "generated_html" not in st.session_state:
    st.session_state.generated_html = None

if "last_domain" not in st.session_state:
    st.session_state.last_domain = None

if "last_prompt" not in st.session_state:
    st.session_state.last_prompt = None


if generate_button:
    if not user_prompt.strip():
        st.warning("Please enter a scientific visualization request first.")
    else:
        with st.spinner("Gemini is engineering your interactive 3D simulation..."):
            try:
                generated_html = generate_simulation(
                    domain=domain,
                    user_prompt=user_prompt.strip(),
                )

                st.session_state.generated_html = generated_html
                st.session_state.last_domain = domain
                st.session_state.last_prompt = user_prompt.strip()

                st.success("3D simulation generated successfully.")

            except Exception as exc:
                st.session_state.generated_html = None
                st.error("The simulation could not be generated.")

                with st.expander("Technical error details"):
                    st.code(str(exc), language="text")


generated_html = st.session_state.generated_html

if generated_html:
    st.markdown(
        f"""
        <div class="simulation-label">
            LIVE SIMULATION · {html.escape(st.session_state.last_domain or "")}
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

    source_col, info_col = st.columns([2.2, 1])

    with source_col:
        with st.expander("🧩 Inspect Generated HTML Source"):
            st.code(generated_html, language="html")

    with info_col:
        st.markdown(
            """
            <div class="status-card">
                <strong>Simulation Status</strong><br><br>
                🟢 HTML generated<br>
                🟢 Markdown cleaned<br>
                🟢 Three.js scene injected<br>
                🟢 Interactive iframe active
            </div>
            """,
            unsafe_allow_html=True,
        )

else:
    st.info(
        "Choose a domain, describe the scientific concept in the sidebar, "
        "and click **Generate 3D Simulation**."
    )

    st.markdown(
        """
        ### Example ideas

        - **Physics:** Projectile motion with adjustable launch angle,
          velocity and gravity.
        - **Mathematics:** Interactive 3D plane, normal vector and axes.
        - **Chemistry:** Interactive molecular geometry and bond angles.
        - **Biology:** 3D cell visualization with selectable organelles.
        - **Astronomy:** Interactive orbital mechanics visualization.
        """
    )
