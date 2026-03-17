from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from google import genai
import os
import json
import re

app = FastAPI()

BASE_DIR = "/var/www/vokabular"
STATIC_DIR = os.path.join(BASE_DIR, "static")
WORDS_DIR = os.path.join(BASE_DIR, "words")

os.makedirs(WORDS_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/words", StaticFiles(directory=WORDS_DIR), name="words")

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

def make_module_name(prompt):
    text = prompt.lower()
    text = re.sub(r'[^a-zа-яёäöüß0-9 ]', ' ', text)
    words = [w for w in text.split() if len(w) > 3 and not w.isdigit()]
    if not words:
        return "modul"
    return "_".join(words[:3])[:30]

def extract_word_count(prompt: str) -> int:
    m = re.search(r'(\d+)', prompt)
    if not m:
        return 10
    count = int(m.group(1))
    if count < 1:
        return 10
    if count > 300:
        return 300
    return count

@app.get("/themes")
def themes():
    modules = []
    for f in os.listdir(WORDS_DIR):
        if f.endswith(".json"):
            path = os.path.join(WORDS_DIR, f)
            try:
                with open(path, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    modules.append({
                        "name": f.replace(".json", ""),
                        "count": len(data),
                        "file": f
                    })
            except Exception:
                pass
    return modules

@app.post("/generate")
async def generate(request: Request):
    prompt = request.query_params.get("prompt", "").strip()
    filename = request.query_params.get("filename", "").strip()

    print("====== REQUEST ======")
    print("prompt:", prompt)
    print("filename:", filename)
    print("=====================")

    if not prompt:
        return {"error": "empty prompt", "count": 0}

    if not filename:
        filename = make_module_name(prompt)

    requested_count = extract_word_count(prompt)

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"""
Erstelle genau {requested_count} deutsche Wörter mit russischer Übersetzung zum Thema: {prompt}

WICHTIG:
- Genau {requested_count} Einträge
- Keine Erklärungen
- Keine Kommentare
- Nur JSON
- Jedes Element muss "de" und "ru" haben

Format:
[
  {{"de":"Haus","ru":"дом"}},
  {{"de":"Schule","ru":"школа"}}
]
"""
        )

        text = response.text if response.text else ""

        print("====== AI RESPONSE ======")
        print(text)
        print("=========================")

        m = re.search(r"\[.*\]", text, re.S)
        words = json.loads(m.group(0)) if m else []

        if not isinstance(words, list):
            words = []

        cleaned = []
        for item in words:
            if isinstance(item, dict):
                de = str(item.get("de", "")).strip()
                ru = str(item.get("ru", "")).strip()
                if de and ru:
                    cleaned.append({"de": de, "ru": ru})

        print("PARSED WORDS:", len(cleaned))
        print("REQUESTED WORDS:", requested_count)

        path = os.path.join(WORDS_DIR, filename + ".json")

        with open(path, "w", encoding="utf-8") as f:
            json.dump(cleaned, f, ensure_ascii=False, indent=2)

        return {
            "file": filename,
            "count": len(cleaned),
            "requested": requested_count
        }

    except Exception as e:
        print("ERROR:", e)
        return {"error": str(e), "count": 0}

@app.delete("/delete/{filename}")
def delete(filename: str):
    path = os.path.join(WORDS_DIR, filename)
    if os.path.exists(path):
        os.remove(path)
        return {"status": "deleted"}
    raise HTTPException(status_code=404)

@app.get("/module/{filename}")
def module(filename: str):
    path = os.path.join(WORDS_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404)

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
