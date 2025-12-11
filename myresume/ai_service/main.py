from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import io
import os
import re

from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.metrics.pairwise import cosine_similarity

try:
    from docx import Document
except Exception:
    Document = None

try:
    from pdfminer.high_level import extract_text as extract_pdf_text
except Exception:
    extract_pdf_text = None

app = FastAPI(title="Resume ATS AI Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def extract_text_from_docx(file_bytes: bytes) -> str:
    if Document is None:
        return ""
    bio = io.BytesIO(file_bytes)
    doc = Document(bio)
    parts = [p.text for p in doc.paragraphs]
    return "\n".join(parts)


def extract_text_from_pdf(file_bytes: bytes) -> str:
    if extract_pdf_text is None:
        return ""
    bio = io.BytesIO(file_bytes)
    try:
        return extract_pdf_text(bio)
    except Exception:
        return ""


def extract_text_from_file(upload: UploadFile) -> str:
    if not upload:
        return ""
    filename = upload.filename.lower()
    data = upload.file.read()
    if filename.endswith('.docx'):
        return extract_text_from_docx(data)
    if filename.endswith('.pdf'):
        return extract_text_from_pdf(data)
    # fallback: assume text
    try:
        return data.decode('utf-8', errors='ignore')
    except Exception:
        return ""


def tokenize(text: str) -> List[str]:
    if not text:
        return []
    text = text.lower()
    # keep words and numbers
    tokens = re.findall(r"[a-z0-9\-\+]+", text)
    tokens = [t for t in tokens if t not in ENGLISH_STOP_WORDS and len(t) > 1]
    return tokens


def extract_top_keywords(text: str, top_n: int = 30) -> List[str]:
    if not text:
        return []
    vect = TfidfVectorizer(stop_words='english', ngram_range=(1, 2), max_df=0.85)
    tfidf = vect.fit_transform([text])
    feature_array = vect.get_feature_names_out()
    # single document, use tf-idf vector values
    scores = tfidf.toarray()[0]
    idxs = scores.argsort()[::-1]
    keywords = []
    for idx in idxs:
        kw = feature_array[idx]
        if kw.isdigit():
            continue
        keywords.append(kw)
        if len(keywords) >= top_n:
            break
    return keywords


class AnalyzeResponse(BaseModel):
    keyword_match_pct: float
    tfidf_similarity_pct: float
    combined_score_pct: float
    jd_keywords: List[str]
    matched_keywords: List[str]
    missing_keywords: List[str]


@app.post('/analyze', response_model=AnalyzeResponse)
async def analyze(
    job_description: Optional[str] = Form(None),
    upload: Optional[UploadFile] = File(None)
):
    jd_text = (job_description or "").strip()
    resume_text = ""
    if upload is not None:
        resume_text = extract_text_from_file(upload) or ""

    # Fallback: if no resume file, check job_description as resume_text (edge-case)
    # but typical flow: both provided

    # Extract keywords from JD using TF-IDF single-doc ranking
    jd_keywords = extract_top_keywords(jd_text, top_n=30) if jd_text else []

    resume_tokens = set(tokenize(resume_text))
    # normalize jd keywords for token comparison
    jd_kw_tokens = set()
    for kw in jd_keywords:
        parts = re.findall(r"[a-z0-9\-\+]+", kw.lower())
        for p in parts:
            if p and p not in ENGLISH_STOP_WORDS:
                jd_kw_tokens.add(p)

    matched = [k for k in jd_keywords if any(p in resume_tokens for p in re.findall(r"[a-z0-9\-\+]+", k.lower()))]
    missing = [k for k in jd_keywords if k not in matched]
    keyword_match_pct = (len(matched) / len(jd_keywords) * 100) if jd_keywords else 0.0

    # TF-IDF similarity across the two documents
    tfidf_similarity_pct = 0.0
    try:
        if jd_text.strip() and resume_text.strip():
            vect = TfidfVectorizer(stop_words='english')
            X = vect.fit_transform([jd_text, resume_text])
            sim = cosine_similarity(X[0:1], X[1:2])[0][0]
            tfidf_similarity_pct = float(sim * 100)
    except Exception:
        tfidf_similarity_pct = 0.0

    # Combine scores (weights can be tuned)
    combined = 0.6 * keyword_match_pct + 0.4 * tfidf_similarity_pct

    return AnalyzeResponse(
        keyword_match_pct=round(keyword_match_pct, 2),
        tfidf_similarity_pct=round(tfidf_similarity_pct, 2),
        combined_score_pct=round(combined, 2),
        jd_keywords=jd_keywords,
        matched_keywords=matched,
        missing_keywords=missing
    )
