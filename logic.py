import streamlit as st
from openai import OpenAI
import json

# --- CONFIGURAZIONE MOTORE ---
# Recuperiamo la chiave dai Secrets (Protetto per deploy)
try:
    api_key = st.secrets["OPENROUTER_API_KEY"]
    base_url = "https://openrouter.ai/api/v1"

    client = OpenAI(base_url=base_url, api_key=api_key)
    # Prefisso openai/ richiesto da OpenRouter per questo modello
    MODEL_NAME = "openai/gpt-4o-mini"
    print("MODALITÀ PROD: OpenRouter connesso su gpt-4o-mini")

except Exception as e:
    client = None
    MODEL_NAME = "openai/gpt-4o-mini"
    print(f"Errore configurazione Client: {e}")


# --- 2. LA FUNZIONE PRINCIPALE ---
def get_archetype_analysis(user_text):
    """
    Prende il testo grezzo dell'utente e restituisce un dizionario Python (JSON)
    con l'analisi dell'archetipo.
    """

    # SYSTEM PROMPT: Le istruzioni per l'AI
    # Nota: Dobbiamo essere molto specifici sul JSON per evitare errori
    system_prompt = """
    Sei "The Potentiality Engine", un'AI che analizza profili professionali.
    NON guardare ai Job Title. Guarda ai pattern di pensiero, ai fallimenti e alle ambizioni.
    
    Il tuo compito è assegnare un ARCHETIPO all'utente, cioe' quello che sarà in futuro grazie alle sua personalità e competenze.
    
    DEVI rispondere SOLAMENTE con un oggetto JSON valido. Nessun testo prima o dopo.
    Struttura JSON richiesta:
    {
        "archetype_title": "Titolo in Inglese, Epico e Professionale (es. Full-Stack Visionary)",
        "archetype_category": "Scegli una tra: DESIGN, TECH, MARKETING",
        "power_color": "Un codice HEX colore adatto all'archetipo (es. #00FF00)",
        "analysis_summary": "Breve analisi profonda (2 frasi) in ITALIANO.",
        "future_prediction": "Una predizione sul ruolo futuro in ITALIANO.",
        "key_skills": ["Skill 1", "Skill 2", "Skill 3"]
    }
    """

    try:
        # Chiamata all'API
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analizza questi dati: {user_text}"},
            ],
            temperature=0.7,  # Creatività bilanciata
            # response_format={"type": "json_object"} # Abilitalo solo con GPT-4/3.5, Ollama a volte crasha con questo
        )

        content = response.choices[0].message.content

        # --- 3. PULIZIA DATI (HACK PER OLLAMA) ---
        # Ollama a volte chiacchiera ("Ecco il JSON..."). Puliamo tutto.
        # Cerchiamo la prima graffa aperta '{' e l'ultima chiusa '}'
        start_index = content.find("{")
        end_index = content.rfind("}")

        if start_index != -1 and end_index != -1:
            json_str = content[start_index : end_index + 1]
        else:
            json_str = content  # Speriamo bene

        # Parsing finale
        data = json.loads(json_str)
        return data

    except json.JSONDecodeError:
        # Se l'AI ha sbagliato a scrivere il JSON
        return {
            "error": "Errore di decodifica neurale. Il futuro è confuso.",
            "raw_content": content,  # Utile per debuggare e vedere cosa ha scritto
        }
    except Exception as e:
        # Qualsiasi altro errore (es. Ollama spento)
        return {"error": f"Errore di connessione: {str(e)}"}
