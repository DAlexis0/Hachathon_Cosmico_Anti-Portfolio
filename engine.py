import streamlit as st
from pydantic import BaseModel, Field
from openai import OpenAI

# Nota: Usiamo st.secrets per le chiavi, non serve più dotenv


# --- CONFIGURAZIONE MOTORE ---
# Ora usiamo l'input dell'utente dalla sidebar
def get_client():
    # Recupera la chiave dai Secrets (Protetto per deploy)
    api_key = st.secrets.get("OPENROUTER_API_KEY")
    base_url = "https://openrouter.ai/api/v1"

    if not api_key:
        print("[ENGINE] Nessuna API Key OpenRouter trovata nei secrets.")
        raise ValueError("API Key mancante.")

    print("[ENGINE] MODALITÀ PROD: OpenRouter connesso con chiave Secrets.")
    return OpenAI(base_url=base_url, api_key=api_key)


# --- DATA MODELS ---
# Qui definisci la struttura del tuo portfolio.
# Come designer, apprezzerai la rigidità della griglia.


class Trajectory(BaseModel):
    title: str = Field(
        ...,
        description="Il titolo del ruolo futuro inventato (es. Neural Brand Architect)",
    )
    probability: str = Field(
        ..., description="Probabilità del percorso: High, Medium, Low"
    )
    description: str = Field(
        ..., description="Perché questo futuro è inevitabile basandosi sui dati passati"
    )
    hypothetical_project: str = Field(
        ..., description="Un progetto ipotetico che l'utente costruirà in questo ruolo"
    )


class CTSAnalysis(BaseModel):
    core_vector: str = Field(
        ...,
        description="Una frase singola che definisce la sintesi tecnica/creativa unica dell'utente",
    )
    trajectory_1_strategic: Trajectory
    trajectory_2_challenge: Trajectory
    trajectory_3_visionary: Trajectory


def generate_trajectory_simulation(
    cv_text: str,
    personality_text: str,
    github_data: str = "",
    web_data: str = "",
    api_model: str = None,
):
    """
    Analizza i dati per costruire un modello predittivo del 'Future Self' dell'utente.
    """

    system_prompt = """
    # SYSTEM ROLE: CAREER TRAJECTORY SIMULATOR (CTS)

**OBJECTIVE:**
Do NOT summarize the past. Your goal is to analyze the input data to construct a predictive model of the user's "Future Self" (3-5 years from now). You are identifying high-value market gaps where their specific, unique combination of skills creates a monopoly of competence.

**INPUT DATA ANALYSIS:**
1.  **Pattern Recognition:** Look for "Unfair Advantages" formed by intersection (e.g., Code + Design = Technical Art; Sales + Engineering = Solutions Architect).
2.  **Tone & Philosophy:** Extract the user's core drivers.
3.  **Code & Creative DNA:** Use GitHub and Web contexts to validate their current hard skills and aesthetic sensibilities.

**GENERATION PROTOCOL (The "Future-First" Approach):**
Instead of a bio, generate 3 distinct "Future Roles" or "Paths" this user is headed towards. For each path:
* **Invent the Job Title:** Do not use standard titles like "Frontend Dev". Create titles like "AI Interface Orchestrator", "Neural Brand Architect".
* **The "Why":** Explain strictly why their past data makes this future inevitable.
* **The Artifact:** Describe a hypothetical project they *will* build in this role (not one they have built).

**PATH TYPOLOGIES:**
1. **STRATEGIC PATH (High Probability):** The logical next step, but elevated.
2. **CHALLENGE PATH (Medium Probability):** A pivot requiring new skills but leveraging core strengths.
3. **VISIONARY PATH (Low Probability / Moonshot):** Highly speculative, high reward, creating a new category.

**STRICT CONSTRAINTS:**
* NO marketing fluff ("passionate", "dynamic", "rare talent"). Use cold, analytical precision.
* NO Gamification/Fantasy terms (No "Mages", "Scribes"). Use Industry/Corporate Strategic language.

**OUTPUT FORMAT (JSON):**
Return a JSON structure containing:
{
  "core_vector": "A single sentence defining their unique technical/creative synthesis.",
  "trajectory_1_strategic": { "title": "...", "probability": "High", "description": "...", "hypothetical_project": "..." },
  "trajectory_2_challenge": { "title": "...", "probability": "Medium", "description": "...", "hypothetical_project": "..." },
  "trajectory_3_visionary": { "title": "...", "probability": "Low", "description": "...", "hypothetical_project": "..." }
}
    """

    user_prompt = f"""
    --- OBIETTIVO ---
    Analizza questi dati ed estrai le 3 Traiettorie Future.

    --- DATI INPUT ---
    
    [TESTO CV GREZZO]
    {cv_text}
    
    [PERSONALITÀ/OPINIONI]
    {personality_text}

    [GITHUB CODE DNA]
    {github_data}

    [WEB/CREATIVE DNA]
    {web_data}
    """

    if api_model is None:
        api_model = "gpt-4o-mini"  # Default per produzione

    try:
        client = get_client()

        # Nota: Ollama con parse() richiede un modello recente e ben supportato.
        # Se 'llama3' fallisce con parse(), considerare l'uso di json mode manuale come in logic.py
        completion = client.beta.chat.completions.parse(
            model=api_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format=CTSAnalysis,  # Qui forziamo l'output strutturato
        )

        # Restituisce l'oggetto Pydantic validato
        return completion.choices[0].message.parsed

    except Exception as e:
        # In produzione qui loggheresti l'errore seriamente
        print(f"Errore nella generazione AI: {e}")
        return None
