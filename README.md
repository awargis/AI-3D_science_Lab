# 🔬 AI 3D Science Lab

AI 3D Science Lab converts a natural-language scientific visualization request into a premium interactive Three.js simulation using Gemini and Streamlit.

## Features

- Runtime Gemini API-key input.
- Gemini model selector.
- Premium Streamlit dashboard.
- Physics, Chemistry, Mathematics, Biology and other domains.
- Gemini-generated standalone Three.js HTML.
- OrbitControls for mouse rotation, pan and zoom.
- Functional simulation controls.
- Automatic HTML/Markdown cleanup.
- HTML source inspection.
- Safe handling of incompatible Live/Image models.

## Gemini model selector

The sidebar includes these requested model IDs:

```text
gemini-3.8-flash
gemini-3.8-live
gemini-3.8-live-extended-thinking
gemini-3.1-pro-preview
gemini-3.1-flash-image
gemini-3.5-flash
gemini-3.5-flash-lite
gemini-2.5-pro
gemini-2.5-flash
```

The Live and Image models are displayed in the dropdown but are deliberately not sent to the text `generate_content` workflow. Selecting one produces a clear UI message instead of an unhandled API failure.

For this particular application, use a text-generation model such as:

```text
gemini-3.8-flash
```

or:

```text
gemini-3.1-pro-preview
```

## Repository

```text
ai-3d-science-lab/
├── app.py
├── prompt_template.py
├── requirements.txt
├── README.md
└── .gitignore
```

## Local installation

```bash
git clone https://github.com/YOUR_USERNAME/ai-3d-science-lab.git
cd ai-3d-science-lab
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install:

```bash
pip install -r requirements.txt
```

Run:

```bash
streamlit run app.py
```

## API key

The application now allows the user to paste the Gemini API key directly into the sidebar.

The key is NOT stored in the project source code.

Do not commit a Gemini API key to GitHub.

## Streamlit Cloud

1. Push the repository to GitHub.
2. Open Streamlit Community Cloud.
3. Create a new application.
4. Select the GitHub repository.
5. Select `app.py` as the main file.
6. Deploy.
7. Paste the Gemini API key into the sidebar when using the app.

If you prefer server-side secret management, you can also use Streamlit Secrets and modify the application to read `st.secrets["GEMINI_API_KEY"]`.

## Architecture

```text
User
 ↓
Streamlit Dashboard
 ↓
API Key + Model + Domain + Topic
 ↓
Google GenAI Client
 ↓
Gemini text model
 ↓
Raw HTML
 ↓
Markdown/HTML cleanup
 ↓
HTML validation
 ↓
Streamlit iframe
 ↓
Three.js + OrbitControls
 ↓
Interactive 3D simulation
```

## Important model compatibility note

Not every Gemini model is a normal text-to-text model.

Live models are designed for real-time audio/live interactions, and image models are designed for image generation. They should not be treated as interchangeable with a normal HTML/code-generation model.

Therefore this application shows them in the model selector but prevents an incompatible selection from being submitted to the text-generation endpoint.

## Scientific quality

The system prompt strongly instructs Gemini to produce:

- scientifically meaningful 3D objects
- functional controls
- responsive rendering
- OrbitControls
- animation
- labels and annotations
- polished dark UI
- educational visual hierarchy
- robust JavaScript

AI-generated scientific simulations should still be reviewed before being used as authoritative teaching material.
