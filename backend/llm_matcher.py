"""
llm_matcher.py

This is the part of the project that actually uses the LLM.
We send the resume text + job description to Claude and ask it to
rate the fit from 1-10 with a short justification. The prompt asks
for a strict JSON reply so we can parse it directly instead of
regexing free-form text.
"""

import os
import json
import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

MODEL = "claude-sonnet-4-6"

MATCH_PROMPT_TEMPLATE = """You are helping a recruiter screen candidates.

Compare the following resume with this job description and rate the
candidate's fit on a scale of 1-10, along with a short justification
(2-3 sentences) explaining the score. Focus on skills overlap,
relevant experience, and any obvious gaps.

Resume:
\"\"\"
{resume_text}
\"\"\"

Job Description:
\"\"\"
{job_description}
\"\"\"

Respond ONLY with valid JSON in exactly this format, nothing else:
{{"score": <integer 1-10>, "justification": "<2-3 sentence explanation>"}}
"""


def get_match_score(resume_text: str, job_description: str) -> dict:
    prompt = MATCH_PROMPT_TEMPLATE.format(
        resume_text=resume_text[:6000],  # keep prompt size reasonable
        job_description=job_description[:3000],
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )

    reply_text = response.content[0].text.strip()

    # the model should return clean JSON, but strip code fences just in case
    reply_text = reply_text.replace("```json", "").replace("```", "").strip()

    try:
        parsed = json.loads(reply_text)
        score = int(parsed.get("score", 0))
        justification = parsed.get("justification", "")
    except (json.JSONDecodeError, ValueError):
        # fallback if the model didn't return clean JSON for some reason
        score = 0
        justification = f"Could not parse model response: {reply_text[:200]}"

    return {"score": score, "justification": justification}
