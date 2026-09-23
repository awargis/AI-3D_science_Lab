# 🔬 AI 3D Science Lab

AI 3D Science Lab converts a natural-language scientific visualization request into an interactive 3D educational simulation using Gemini and Three.js.

## Stack

- Python
- Streamlit
- Google `google-genai`
- Gemini 2.5 Flash
- Three.js
- OrbitControls

## Repository

```text
ai-3d-science-lab/
├── app.py
├── prompt_template.py
├── requirements.txt
└── README.md
```

## Local Setup

### 1. Clone

```bash
git clone https://github.com/YOUR_USERNAME/ai-3d-science-lab.git
cd ai-3d-science-lab
```

### 2. Create a virtual environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the Gemini API key

Create:

```text
.streamlit/secrets.toml
```

with:

```toml
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
```

Never commit this file.

Recommended `.gitignore`:

```text
.streamlit/secrets.toml
.venv/
__pycache__/
*.pyc
```

### 5. Run

```bash
streamlit run app.py
```

Open the URL shown by Streamlit, normally:

```text
http://localhost:8501
```

## Streamlit Community Cloud

1. Push `app.py`, `prompt_template.py`, `requirements.txt`, and `README.md` to GitHub.
2. Open Streamlit Community Cloud.
3. Create a new app.
4. Select your GitHub repository.
5. Set the main file to `app.py`.
6. Open **Advanced settings**.
7. In **Secrets**, enter:

```toml
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
```

8. Save and deploy.

Do not put the API key in GitHub source code.

## How It Works

```text
User request
     ↓
Streamlit sidebar
     ↓
Gemini 2.5 Flash
     ↓
Raw HTML + Three.js
     ↓
Markdown/code-fence cleanup
     ↓
HTML validation
     ↓
Streamlit iframe
     ↓
Interactive 3D simulation
```

The application also exposes the generated HTML source in an expander for inspection and debugging.

## Important

Generated simulations are AI-generated code. Review scientifically important simulations before using them as authoritative teaching material.

Three.js and OrbitControls are loaded from a CDN, so the rendered simulation normally requires internet access.
