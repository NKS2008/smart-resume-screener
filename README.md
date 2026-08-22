# Smart Resume Screener

A small full-stack app that parses resumes, extracts basic candidate
info, and uses an LLM (Claude) to score how well a candidate matches
a given job description.

Built as a college assignment to demonstrate resume parsing + LLM
based semantic matching.

## Features

- Upload a resume (PDF or TXT) and get structured data back: name,
  email, phone, skills, experience, education
- Add a job description
- Run an LLM-based match between a candidate and a job — get a
  1-10 score with a short justification
- View a ranked shortlist of candidates for a given job
- Simple browser dashboard, no frontend framework needed

## Architecture

```
smart-resume-screener/
├── backend/
│   ├── main.py            -> FastAPI app + all routes
│   ├── database.py        -> SQLite connection + table setup
│   ├── resume_parser.py   -> PDF/text extraction, regex-based field extraction
│   ├── llm_matcher.py     -> Calls Claude API for match scoring
│   └── models.py          -> Pydantic request models
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js          -> Calls the backend API with fetch()
├── sample_data/           -> sample resume + JD to try the app with
├── requirements.txt
└── .env.example
```

**Flow:**

1. Resume gets uploaded -> text is extracted with `pdfplumber` ->
   name/email/phone/skills/experience/education are pulled out using
   regex and a keyword list (no LLM call here, this is cheap and
   deterministic)
2. Job description gets saved as-is
3. When a match is requested, the candidate's full resume text and
   the job description text are sent to Claude, which returns a
   JSON object with a score (1-10) and a justification
4. Results are stored in SQLite so the shortlist can be viewed later
   without re-calling the LLM

I split the "extraction" step and the "matching" step on purpose —
extraction is just parsing, so it doesn't need an LLM call. The LLM
is only used where it's actually needed: judging semantic fit, which
regex can't really do.

## LLM Prompt Used

This is the exact prompt template from `llm_matcher.py`:

```
You are helping a recruiter screen candidates.

Compare the following resume with this job description and rate the
candidate's fit on a scale of 1-10, along with a short justification
(2-3 sentences) explaining the score. Focus on skills overlap,
relevant experience, and any obvious gaps.

Resume:
"""
{resume_text}
"""

Job Description:
"""
{job_description}
"""

Respond ONLY with valid JSON in exactly this format, nothing else:
{"score": <integer 1-10>, "justification": "<2-3 sentence explanation>"}
```

Model used: `claude-sonnet-4-6`

## Setup

1. Clone the repo and install dependencies:

```bash
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and add your Anthropic API key:

```bash
cp .env.example .env
```

3. Export the key (or use a tool like `python-dotenv` if you prefer):

```bash
export ANTHROPIC_API_KEY=your_key_here
```

4. Run the backend:

```bash
uvicorn backend.main:app --reload
```

5. Open the dashboard in your browser:

```
http://localhost:8000/app/index.html
```

## Trying it out with sample data

`sample_data/sample_resume.txt` and `sample_data/sample_job_description.txt`
are included so you can test the app without needing your own resume
on hand. Upload the resume, paste the JD, then run a match between
them.

## API Endpoints

| Method | Endpoint             | Description                          |
|--------|-----------------------|---------------------------------------|
| POST   | `/resumes/upload`     | Upload + parse a resume               |
| POST   | `/jobs`                | Create a job description              |
| POST   | `/match`               | Run LLM match for candidate + job     |
| GET    | `/shortlist/{job_id}`  | Ranked candidates for a job           |
| GET    | `/candidates`          | List all uploaded candidates          |

## Known Limitations

- Field extraction (skills/experience/education) is regex/keyword
  based, so it can miss things on resumes with unusual formatting.
  A more robust version could send the raw text to the LLM for
  extraction too, but that adds cost/latency for something regex
  handles fine most of the time.
- Skill matching only checks against a fixed list of common tech
  skills (`resume_parser.py`) — easy to extend but not exhaustive.
- No authentication - this was built as a class project, not a
  production system.

## Demo Video

A 2-3 minute walkthrough is linked here: `<add your demo video link>`
