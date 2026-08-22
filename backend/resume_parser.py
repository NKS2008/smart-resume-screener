"""
resume_parser.py

Pulls raw text out of a resume (PDF or plain .txt) and then does some
basic rule-based extraction to pull out name, email, phone, skills,
experience and education sections. This part is intentionally NOT
LLM based - it's cheap regex/keyword matching so we don't burn API
calls just to find an email address. The LLM is used later, only for
the actual matching/scoring step (see llm_matcher.py).
"""

import re
import pdfplumber

# a fairly small, common list of tech skills to match against.
# not exhaustive, but good enough for a class project - could be
# extended later with a bigger skills database.
KNOWN_SKILLS = [
    "python", "java", "javascript", "typescript", "c++", "c#", "sql",
    "html", "css", "react", "angular", "vue", "node.js", "node",
    "express", "django", "flask", "fastapi", "spring", "spring boot",
    "mongodb", "mysql", "postgresql", "sqlite", "firebase",
    "aws", "azure", "gcp", "google cloud", "docker", "kubernetes",
    "git", "github", "machine learning", "deep learning", "nlp",
    "pandas", "numpy", "tensorflow", "pytorch", "scikit-learn",
    "data structures", "algorithms", "rest api", "graphql",
    "linux", "excel", "power bi", "tableau", "figma"
]

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_REGEX = re.compile(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3,5}\)?[-.\s]?\d{3}[-.\s]?\d{3,4}")


def extract_text_from_pdf(file_path: str) -> str:
    text_chunks = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_chunks.append(page_text)
    return "\n".join(text_chunks)


def extract_text(file_path: str) -> str:
    """Handles both PDF and plain text resumes."""
    if file_path.lower().endswith(".pdf"):
        return extract_text_from_pdf(file_path)
    # fallback for .txt uploads
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def guess_name(text: str) -> str:
    # crude heuristic: the first non-empty line that isn't an email/phone
    # and isn't too long is usually the candidate's name at the top of
    # the resume. Not perfect but works for most standard resume formats.
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    for line in lines[:5]:
        if EMAIL_REGEX.search(line) or PHONE_REGEX.search(line):
            continue
        if len(line.split()) <= 5 and len(line) < 60:
            return line
    return "Unknown"


def extract_skills(text: str) -> list:
    text_lower = text.lower()
    found = []
    for skill in KNOWN_SKILLS:
        if skill in text_lower:
            found.append(skill)
    return found


def extract_section(text: str, section_names: list) -> str:
    """
    Grabs the text under a heading like 'Experience' or 'Education'
    up until the next heading-looking line. Resume formats vary a lot
    so this is a best-effort approach, not bulletproof.
    """
    lines = text.split("\n")
    section_lines = []
    capturing = False

    for line in lines:
        stripped = line.strip()
        lower = stripped.lower().rstrip(":")

        if lower in section_names:
            capturing = True
            continue

        # stop if we hit what looks like the start of a new section header
        if capturing and stripped.isupper() and len(stripped.split()) <= 4 and stripped != "":
            break
        if capturing and lower in ["skills", "projects", "certifications",
                                    "experience", "education", "achievements"]:
            break

        if capturing and stripped:
            section_lines.append(stripped)

    return " ".join(section_lines[:15])  # cap it so we don't grab the whole doc


def parse_resume(file_path: str) -> dict:
    text = extract_text(file_path)

    email_match = EMAIL_REGEX.search(text)
    phone_match = PHONE_REGEX.search(text)

    return {
        "name": guess_name(text),
        "email": email_match.group(0) if email_match else "",
        "phone": phone_match.group(0) if phone_match else "",
        "skills": extract_skills(text),
        "experience": extract_section(text, ["experience", "work experience", "professional experience"]),
        "education": extract_section(text, ["education", "academic background"]),
        "raw_text": text,
    }
