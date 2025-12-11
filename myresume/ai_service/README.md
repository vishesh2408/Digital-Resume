# AI Service (FastAPI)

This small FastAPI service provides a single endpoint /analyze that accepts a resume file (PDF, DOCX, TXT) and a job_description string
and returns keyword match, TF-IDF similarity, combined score and lists of matched/missing JD keywords. It uses scikit-learn for TF-IDF and cosine similarity.

Quick start

1. Create and activate a virtual environment (recommended):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Run the service:

```powershell
uvicorn main:app --reload --port 8001
```

The endpoint: POST /analyze
- Form fields: job_description (string)
- File: upload (file)

Response: JSON with fields keyword_match_pct, tfidf_similarity_pct, combined_score_pct, jd_keywords, matched_keywords, missing_keywords
