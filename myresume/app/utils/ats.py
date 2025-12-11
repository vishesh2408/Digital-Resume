import re
from html import unescape
from typing import Dict, List
from io import BytesIO

try:
    from PyPDF2 import PdfReader  # optional
except Exception:  # pragma: no cover
    PdfReader = None

try:
    import docx  # python-docx, optional
except Exception:  # pragma: no cover
    docx = None

ACTION_VERBS = [
    'achieved','analyzed','built','collaborated','created','designed','developed','drove','executed','implemented',
    'improved','increased','launched','led','managed','optimized','owned','reduced','resolved','shipped','spearheaded',
    'streamlined','supported','trained','won'
]

RE_HTML_TAG = re.compile(r"<[^>]+>")
RE_WHITESPACE = re.compile(r"\s+")
RE_NUMBER = re.compile(r"(?:(?:\d+[\.,]?\d*)|(?:\d+))(?:\s*(?:%|k|K|m|M|x))?")
RE_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
RE_PHONE = re.compile(r"\+?\d[\d\s()\-]{7,}\d")

SECTIONS = [
    'summary','skills','training','projects','education','certificates'
]

STOPWORDS = set('''the a an and or for to in on of with by as at from into about over after before between out against during without within along across through more most other some such no nor not only own same so than too very can will just don should now is are was were be been being this that these those your you yours their they them our we us it its i me my mine he him his she her hers'''.split())


def strip_html(text: str) -> str:
    if not text:
        return ''
    text = unescape(text)
    text = RE_HTML_TAG.sub(' ', text)
    text = RE_WHITESPACE.sub(' ', text)
    return text.strip()


def tokenize(text: str) -> List[str]:
    return re.findall(r"[A-Za-z%]+|\d+[\w%]*", text.lower())


def analyze_text(raw_text: str) -> Dict:
    text = strip_html(raw_text)
    tokens = tokenize(text)
    words = [t for t in tokens if re.match(r"[a-z%]+$", t)]

    # Metrics
    action_verbs_found = [w for w in words if w in ACTION_VERBS]
    unique_action_verbs = sorted(set(action_verbs_found))
    quantifications = RE_NUMBER.findall(text)

    email_found = bool(RE_EMAIL.search(text))
    phone_found = bool(RE_PHONE.search(text))

    # Simple duplicates heuristic: words occurring > 10 times (likely overused)
    from collections import Counter
    counts = Counter(words)
    overused = [w for w, c in counts.items() if c > 10]

    length_words = len(words)
    length_score = 1.0 if 300 <= length_words <= 800 else 0.6 if 150 <= length_words < 300 or 800 < length_words <= 1200 else 0.3

    action_score = min(1.0, len(unique_action_verbs) / 10.0)
    quant_score = min(1.0, len(quantifications) / 10.0)
    contact_score = 1.0 if (email_found and phone_found) else 0.5 if (email_found or phone_found) else 0.0

    scores = {
        'length': round(length_score * 100, 1),
        'action_verbs': round(action_score * 100, 1),
        'quantification': round(quant_score * 100, 1),
        'contact_info': round(contact_score * 100, 1),
    }

    overall = round((scores['length'] + scores['action_verbs'] + scores['quantification'] + scores['contact_info']) / 4.0, 1)

    suggestions: List[str] = []
    if scores['action_verbs'] < 80:
        suggestions.append('Use more strong action verbs at the start of bullet points (e.g., implemented, led, optimized).')
    if scores['quantification'] < 80:
        suggestions.append('Add measurable impact with numbers or percentages (e.g., increased performance by 25%).')
    if scores['contact_info'] < 100:
        suggestions.append('Include both an email and a phone number in the header section.')
    if scores['length'] < 60:
        suggestions.append('Adjust resume length to 1–2 pages (~300–800 words) for optimal scanning.')
    if overused:
        suggestions.append('Reduce repetitive wording. Overused terms: ' + ', '.join(overused[:10]))

    result = {
        'text_length_words': length_words,
        'action_verbs_found': action_verbs_found,
        'unique_action_verbs': unique_action_verbs,
        'quantifications': quantifications,
        'email_found': email_found,
        'phone_found': phone_found,
        'overused_terms': overused,
        'scores': scores,
        'overall_score': overall,
        'suggestions': suggestions,
    }

    # Placeholder improvements; can be enriched with context via classify_improvements()
    result['improvements'] = {
        'high_priority': [],
        'medium_priority': [],
        'additional': []
    }
    return result


def analyze_resume_instance(resume) -> Dict:
    # Concatenate significant sections for analysis
    parts = [
        getattr(resume, s, '') or '' for s in SECTIONS
    ]
    header = f"{resume.full_name} {resume.email} {resume.phone}"
    analysis = analyze_text(header + "\n" + "\n".join(parts))
    # Basic context-driven improvements classification
    context = {
        'has_linkedin': bool(getattr(resume, 'linkedin', '') or ''),
        'has_location': bool(getattr(resume, 'location', '') or ''),
        'has_experience': hasattr(resume, 'experience_items') and resume.experience_items.exists(),
        'employment_dates_present': all([(e.start_date or e.end_date) for e in getattr(resume, 'experience_items').all()]) if hasattr(resume, 'experience_items') and resume.experience_items.exists() else False,
        'education_graduation_year_present': any([bool(ed.end_date) for ed in getattr(resume, 'education_items').all()]) if hasattr(resume, 'education_items') and resume.education_items.exists() else False,
    }
    analysis['improvements'] = classify_improvements(context=context, analysis=analysis)
    return analysis


def build_resume_text(resume) -> str:
    parts = [getattr(resume, s, '') or '' for s in SECTIONS]
    header = f"{resume.full_name} {resume.email} {resume.phone}"
    return header + "\n" + "\n".join(parts)


def extract_text_from_pdf(data: bytes) -> str:
    if not PdfReader:
        return ''
    try:
        reader = PdfReader(BytesIO(data))
        pages = []
        for p in getattr(reader, 'pages', []) or []:
            try:
                pages.append(p.extract_text() or '')
            except Exception:
                continue
        return "\n".join(pages)
    except Exception:
        return ''


def extract_text_from_docx(data: bytes) -> str:
    if not docx:
        return ''
    try:
        d = docx.Document(BytesIO(data))
        return "\n".join([p.text for p in d.paragraphs])
    except Exception:
        return ''


def analyze_text_with_jd(resume_text: str, jd_text: str) -> Dict:
    """Compute JD/resume keyword overlap and return match details.
    Adds a 'jd_match' sub-dict to the base analysis.
    """
    base = analyze_text(resume_text)
    def norm_tokens(txt: str):
        return [t for t in tokenize(strip_html(txt)) if t.isalpha() and len(t) > 3 and t not in STOPWORDS]

    rtoks_list = norm_tokens(resume_text)
    jtoks = norm_tokens(jd_text)
    rtoks = set(rtoks_list)
    jset = set(jtoks)
    if not jset:
        coverage = 0.0
        matched = []
        missing = []
    else:
        matched = sorted(rtoks.intersection(jset))
        missing = sorted(jset.difference(rtoks))
        coverage = round(100.0 * (len(matched) / max(1, len(jset))), 1)

    # Cosine similarity using simple term-frequency vectors (no sklearn)
    from collections import Counter
    rtf = Counter(rtoks_list)
    jtf = Counter(jtoks)
    vocab = set(rtf.keys()) | set(jtf.keys())
    if not vocab:
        sim_pct = 0.0
    else:
        # dot product
        dot = sum(rtf[w] * jtf[w] for w in vocab)
        import math
        rnorm = math.sqrt(sum(v*v for v in rtf.values()))
        jnorm = math.sqrt(sum(v*v for v in jtf.values()))
        sim = (dot / (rnorm * jnorm)) if (rnorm and jnorm) else 0.0
        sim_pct = round(sim * 100.0, 1)
    base['jd_match'] = {
        'coverage_pct': coverage,
        'matched_keywords': matched[:100],
        'missing_keywords': missing[:100],
        'jd_keywords_count': len(jset),
        'similarity_pct': sim_pct,
    }
    return base


def classify_improvements(context: Dict, analysis: Dict) -> Dict:
    """Return categorized improvements using context flags and analysis metrics.
    context keys (optional): has_linkedin, has_location, has_experience,
    employment_dates_present, education_graduation_year_present.
    """
    high: List[str] = []
    medium: List[str] = []
    additional: List[str] = []

    # High priority
    if not context.get('has_linkedin', False):
        high.append('Contact Information - LinkedIn profile: No LinkedIn profile found. Add your LinkedIn URL.')

    # Medium priority
    if analysis.get('scores', {}).get('length', 0) < 60:
        medium.append('Format & Readability - Resume length: Resume appears too short. Aim for at least 300-600 words.')
    if not context.get('has_experience', False):
        additional.append('Work Experience - Experience section: No clear work experience section found. Create a dedicated section for your work history.')
    if not context.get('employment_dates_present', False):
        additional.append('Work Experience - Employment dates: Include dates for each position (MM/YYYY - MM/YYYY).')
    if not context.get('education_graduation_year_present', False):
        additional.append('Education - Graduation year: Include your graduation year or expected graduation date.')
    if not context.get('has_location', False):
        additional.append('Contact Information - Location information: Add at least city and state.')

    # Suggestions from analysis
    for s in analysis.get('suggestions', []) or []:
        # Heuristic: map contact info suggestion to medium, others to additional
        if 'email and a phone number' in s:
            medium.append(s)
        else:
            additional.append(s)

    return {
        'high_priority': high,
        'medium_priority': medium,
        'additional': additional,
    }
