import fitz  # PyMuPDF
import requests


def get_github_dna(username):
    """
    Recupera i dati dei progetti recenti da GitHub.
    """
    if not username:
        return ""

    try:
        # 1. Recupera le repo (ordinate per aggiornamento)
        url = f"https://api.github.com/users/{username}/repos?sort=updated&per_page=5"
        response = requests.get(url)

        if response.status_code != 200:
            return f"Errore GitHub: Utente {username} non trovato o API limit. Status: {response.status_code}"

        repos = response.json()

        context_str = "### GITHUB PORTFOLIO ###\n"

        for repo in repos:
            name = repo.get("name", "Unknown")
            desc = repo.get("description", "No description")
            lang = repo.get("language", "Unknown")

            # 2. Prendi il README raw per capire la logica del progetto
            readme_url = (
                f"https://raw.githubusercontent.com/{username}/{name}/main/README.md"
            )
            readme_response = requests.get(readme_url)
            # Se main fallisce, prova master
            if readme_response.status_code != 200:
                readme_url = f"https://raw.githubusercontent.com/{username}/{name}/master/README.md"
                readme_response = requests.get(readme_url)

            readme_content = (
                readme_response.text[:1000]
                if readme_response.status_code == 200
                else "No Readme found"
            )

            context_str += f"PROJECT: {name} (Main Lang: {lang})\n"
            context_str += f"DESC: {desc}\n"
            context_str += f"README SUMMARY: {readme_content}\n---\n"

        return context_str
    except Exception as e:
        return f"Errore durante l'analisi GitHub: {str(e)}"


def get_web_dna(urls_text):
    """
    Estrae contenuto da una lista di URL (separati da virgola o a capo)
    usando r.jina.ai per pulizia testo.
    """
    if not urls_text:
        return ""

    # Pulisce e separa gli URL
    urls = [u.strip() for u in urls_text.replace("\n", ",").split(",") if u.strip()]

    context_str = "### WEB & CREATIVE PORTFOLIO ###\n"

    for url in urls:
        if not url.startswith("http"):
            url = "https://" + url

        try:
            # Il trucco magico: prependi https://r.jina.ai/ all'URL
            jina_url = f"https://r.jina.ai/{url}"

            # Questo restituisce il testo della pagina già pulito per l'LLM
            response = requests.get(jina_url, timeout=10)

            if response.status_code == 200:
                # Tronchiamo per evitare overflow di token se la pagina è enorme
                clean_text = response.text[:2000]
                context_str += f"SOURCE: {url}\nCONTENT:\n{clean_text}\n---\n"
            else:
                context_str += f"SOURCE: {url} (Error {response.status_code})\n---\n"

        except Exception as e:
            context_str += f"SOURCE: {url} (Exception: {str(e)})\n---\n"

    return context_str


def validate_optional_link(url):
    """
    Ritorna una tupla (is_valid, error_message).
    Se l'URL è vuoto, è considerato valido (True).
    """
    # 1. Se il campo è vuoto, ignoriamo il controllo (Successo)
    if not url or url.strip() == "":
        return True, None

    # 2. Se l'utente ha dimenticato "http", glielo aggiungiamo noi per gentilezza
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        # Trucco: Ci fingiamo un browser vero (Chrome) per non essere bloccati da Behance
        fake_browser = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        # Facciamo una chiamata leggera (timeout 5 secondi per non bloccare l'app)
        response = requests.get(url, headers=fake_browser, timeout=5)

        # Se il codice è 200 (OK), il link esiste
        if response.status_code == 200:
            return True, None
        # Se è 403 (Forbidden) o 404 (Not Found) o altro
        else:
            return False, f"Server Error {response.status_code}"

    except requests.exceptions.MissingSchema:
        return False, "URL malformato"
    except requests.exceptions.ConnectionError:
        return False, "Sito irraggiungibile"
    except Exception as e:
        return False, str(e)


def extract_text_from_pdf(file_stream):
    """
    Estrae tutto il testo da un file stream PDF.
    Restituisce una stringa pulita.
    """
    text = ""
    try:
        # Apre il PDF direttamente dallo stream di byte di Streamlit
        with fitz.open(stream=file_stream.read(), filetype="pdf") as doc:
            for page in doc:
                text += page.get_text() + "\n"

        # --- Parsing Intelligente (Logica Utente) ---
        sezioni = {
            "Profilo": [],
            "Esperienza": [],
            "Formazione": [],
            "Competenze": [],
            "Lingue": [],
            "Altro": [],
        }

        current_section = "Altro"
        # Usiamo text.splitlines() per analizzare riga per riga
        for riga in text.splitlines():
            riga_clean = riga.strip()
            if not riga_clean:
                continue

            riga_lower = riga_clean.lower()

            # Euristiche semplici per cambio sezione
            if (
                "profilo" in riga_lower
                or "profile" in riga_lower
                or "summary" in riga_lower
            ):
                current_section = "Profilo"
            elif (
                "esperienza" in riga_lower
                or "experience" in riga_lower
                or "lavorativ" in riga_lower
            ):
                current_section = "Esperienza"
            elif (
                "formazione" in riga_lower
                or "education" in riga_lower
                or "istruzione" in riga_lower
            ):
                current_section = "Formazione"
            elif (
                "competenze" in riga_lower
                or "skills" in riga_lower
                or "capacità" in riga_lower
            ):
                current_section = "Competenze"
            elif "lingue" in riga_lower or "languages" in riga_lower:
                current_section = "Lingue"

            # Aggiunge contenuto
            sezioni[current_section].append(riga_clean)

        # Ricostruzione Testo Strutturato
        formatted_output = ""
        for sec_name, lines in sezioni.items():
            if lines:  # Solo se c'è contenuto
                formatted_output += f"\n--- {sec_name.upper()} ---\n"
                formatted_output += "\n".join(lines) + "\n"

        return formatted_output.strip()

    except Exception as e:
        return f"Errore nella lettura del PDF: {e}"
