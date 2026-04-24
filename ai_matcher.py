# used ChatGPT to help write this code; added comments where appropriate.
from pdfminer.high_level import extract_text

import requests
from bs4 import BeautifulSoup

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
from urllib.parse import quote

#had to run 'pip install openai', 'pip install beautifulsoup4', 'pip install pdfminer.six', 'pip install python-multipart', 'pip install requests', 'pip install scikit-learn'

# return text in resume
def extract_resume_text(pdf_path):
    try:
        return extract_text(pdf_path)
    except:
        return ""

def extract_job_text(url):
    headers = {"User-Agent": "Mozilla/5.0"}

    def _html_to_text(html: str) -> str:
        if not html:
            return ""
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.extract()
        text = soup.get_text(separator=" ", strip=True)
        return re.sub(r"\s+", " ", text).strip()

    def _safe_get_text(target_url: str, timeout: int = 10) -> str:
        try:
            response = requests.get(target_url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return _html_to_text(response.text)
        except Exception:
            return ""

    # Try to extract LinkedIn job id from common URL shapes.
    job_id = None
    patterns = [
        r"/jobs/view/(?:[^/]*-)?(\d+)",
        r"currentJobId=(\d+)",
        r"/view/(\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            job_id = match.group(1)
            break

    candidates = []

    # 1) LinkedIn guest endpoint tends to contain the cleaned job description.
    if job_id:
        api_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
        candidates.append(_safe_get_text(api_url))

    # 2) Original URL direct fetch.
    candidates.append(_safe_get_text(url))

    # 3) Fallback: text mirror for JS-heavy / bot-protected pages.
    # r.jina.ai returns a readable text version of many pages.
    if url.startswith("http://") or url.startswith("https://"):
        mirror_url = f"https://r.jina.ai/http://{url.split('://', 1)[1]}"
        candidates.append(_safe_get_text(mirror_url, timeout=15))

    best = max(candidates, key=len) if candidates else ""
    return best



# make all text lowercase and reformat it for consistency
def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text

SECTION_KEYWORDS = [ # most important parts of job postings that my algorithm should parse
    "requirements",
    "qualifications",
    "skills",
    "responsibilities",
    "preferred qualifications"
]


# ---------------------------------------------------------
# NEW FEATURE: Skill detection for AI skill gap analysis
# ---------------------------------------------------------

# predefined list of common technical skills
# you can easily expand this list later
SKILLS_DB = [
    "python", "java", "c++", "c#", "javascript", "typescript",
    "sql", "postgresql", "mysql", "mongodb",
    "machine learning", "deep learning", "data science",
    "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch",
    "docker", "kubernetes", "aws", "gcp", "azure",
    "linux", "git", "rest api", "fastapi", "flask",
    "spark", "hadoop", "tableau", "power bi", "AC/DC", "three phase power", "leadership"
]


def extract_skills(text): # look at the job posting and the resume and see what skills in SKILLS_DB these 2 have. Return the skills each data source has 
    """
    Extract skills from text using whole-word matching.
    Prevents substring matches like 'git' matching 'digital'.
    Normalizes both text and skill so that skills with special chars (e.g. AC/DC)
    match correctly after clean_text strips them (e.g. "ac dc").
    """

    text = clean_text(text)

    found_skills = set()

    for skill in SKILLS_DB:
        # Normalize the skill the same way we normalize text, so "AC/DC" matches "ac dc"
        normalized_skill = clean_text(skill)
        pattern = r"\b" + re.escape(normalized_skill) + r"\b"

        if re.search(pattern, text): # if a skill is in the text (resume or job posting), add it to found_skills
            found_skills.add(skill)

    return found_skills

# see how similar the resume and job postings are in terms of keywords, similar words/phrases, etc
def compute_match_score(resume_text, job_text):

    # Clean text
    resume_text = clean_text(resume_text) #standardize both texts
    job_text = clean_text(job_text)

    print("Resume length:", len(resume_text)) #make sure > 1000
    print("Job text length:", len(job_text))

    # Limit job posting size (job pages contain tons of junk)
    job_text = job_text[:5000]

    
    #print("Dashiell job text:", job_text)

    documents = [resume_text, job_text]

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1,2),   # match phrases like "machine learning" or similar phrases
        max_features=2000
    )

    tfidf = vectorizer.fit_transform(documents)

    similarity = cosine_similarity(tfidf[0:1], tfidf[1:2]) # see how similar the two columns (resume & job posting) of the vector of data are

    raw_score = float(similarity[0][0]) # compute a similarity score based off the similarity array

    # Rescale score to be less strict
    adjusted_score = min(100, raw_score * 300)

    return round(adjusted_score, 2) # return rounded decimal

# ---------------------------------------------------------
# NEW FEATURE: AI skill gap analysis
# ---------------------------------------------------------

def analyze_skill_gap(resume_text, job_text):

    resume_skills = extract_skills(resume_text) # extract skills (in SKILLS_DB) from resume and job posting 
    job_skills = extract_skills(job_text)

    matched_skills = sorted(list(resume_skills.intersection(job_skills))) # matched_skills are ones in the job posting and resume
    missing_skills = sorted(list(job_skills - resume_skills)) # matched_skills are ones in the job posting but not resume

    return matched_skills, missing_skills


def _strip_html(text):
    """Adzuna job descriptions are often HTML; strip tags before matching."""
    if not text:
        return ""
    s = str(text)
    if "<" in s and ">" in s:
        return BeautifulSoup(s, "html.parser").get_text(separator=" ")
    return s


def _token_jaccard(a: str, b: str) -> float:
    """Share of overlapping words between two already-cleaned strings."""
    ta, tb = set(a.split()), set(b.split())
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    union = len(ta | tb)
    return inter / union if union else 0.0


def rank_jobs(user_background_text, jobs):
    """
    Rank Adzuna jobs against the user's profile. Raw TF-IDF cosine similarity
    between a long profile and a short listing is usually very small (e.g. 0.02),
    which made UI percentages look like 0–2%. We combine scaled cosine similarity,
    SKILLS_DB overlap, and word-level Jaccard for more intuitive scores.
    """
    ranked = []

    for job in jobs:
        title = job.get("title") or ""
        desc = _strip_html(job.get("description") or "")
        job_text = clean_text(f"{title} {desc}")

        if not user_background_text.strip() or not job_text.strip():
            cos = 0.0
        else:
            vectorizer = TfidfVectorizer(
                stop_words="english",
                ngram_range=(1, 2),
                max_features=2000,
            )
            tfidf = vectorizer.fit_transform([user_background_text, job_text])
            cos = float(cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0])

        # Map small cosines into a friendlier 0–100 band (e.g. ~0.02 → ~25%)
        tfidf_component = min(100.0, 100.0 * cos / (cos + 0.06))

        user_skills = extract_skills(user_background_text)
        job_skills = extract_skills(job_text)
        if job_skills:
            skill_component = (len(user_skills & job_skills) / len(job_skills)) * 100.0
        else:
            skill_component = tfidf_component

        jaccard_component = _token_jaccard(user_background_text, job_text) * 100.0

        score = (
            0.45 * tfidf_component
            + 0.30 * skill_component
            + 0.25 * jaccard_component
        )
        score = round(min(100.0, max(0.0, score)), 2)

        ranked.append({
            "job": job,
            "score": score,
        })

    ranked.sort(key=lambda x: x["score"], reverse=True)

    return ranked