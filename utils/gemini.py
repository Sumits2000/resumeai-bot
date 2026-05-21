"""
Gemini AI integration — resume and cover letter generation.
Uses google-genai SDK (new, actively maintained).
Free tier: gemini-2.5-flash — 1,500 requests/day, no credit card needed.
"""
import asyncio
import logging
from google import genai
from google.genai import types
from config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)

# One client instance reused across all calls
_client = genai.Client(api_key=GEMINI_API_KEY)

_GENERATE_CONFIG = types.GenerateContentConfig(
    temperature=0.7,
    max_output_tokens=1500,
)


# ── Prompts ───────────────────────────────────────────────────────────────────

def _resume_prompt(job: str, experience: str, skills: str, education: str) -> str:
    return f"""You are an expert resume writer with 10+ years of experience helping candidates land jobs at top companies.

Create a professional, ATS-friendly resume for this candidate.

TARGET ROLE: {job}
WORK EXPERIENCE: {experience}
SKILLS: {skills}
EDUCATION: {education}

FORMAT THE RESUME EXACTLY LIKE THIS (plain text, ALL CAPS for section titles):

[CANDIDATE NAME]
[City, India] | [email@example.com] | [+91-XXXXXXXXXX] | [linkedin.com/in/handle]

PROFESSIONAL SUMMARY
Write 2-3 compelling sentences tailored to the target role.

WORK EXPERIENCE
Job Title | Company Name | Month Year – Month Year
• Achievement-focused bullet (quantify where possible)
• Achievement-focused bullet
• Achievement-focused bullet

SKILLS
Technical: list relevant technical skills
Soft Skills: list relevant soft skills

EDUCATION
Degree | Institution | Year

RULES:
- Quantify achievements wherever logical (%, numbers, ₹)
- Keep it to 1 page worth of content
- ATS-friendly — no tables, no columns, no images
- Use strong action verbs: Led, Built, Increased, Reduced, Delivered
- Mark placeholder contact info clearly as [PLACEHOLDER]
- Output ONLY the resume — no preamble, no explanation
"""


def _cover_letter_prompt(job: str, experience: str, skills: str) -> str:
    return f"""You are an expert career coach writing compelling cover letters that get interviews.

Write a professional cover letter for this candidate.

TARGET ROLE: {job}
EXPERIENCE SUMMARY: {experience}
KEY SKILLS: {skills}

FORMAT:
[Date]

Hiring Manager
[Company Name]

Dear Hiring Manager,

[Opening paragraph — strong hook + why this specific role excites you]

[Body paragraph 1 — most relevant achievement with numbers]

[Body paragraph 2 — skills match + unique value you bring]

[Closing paragraph — confident call to action]

Sincerely,
[Your Name]
[email@example.com | +91-XXXXXXXXXX]

RULES:
- Confident but not arrogant tone
- Reference the exact job title
- Under 300 words total
- No clichés like "I am writing to apply" or "I am a hard worker"
- Output ONLY the cover letter — no preamble, no explanation
"""


# ── Core generation ───────────────────────────────────────────────────────────

async def _call_gemini(prompt: str) -> str:
    """Run the blocking Gemini SDK call in a thread pool."""
    loop = asyncio.get_event_loop()

    def _sync_call():
        response = _client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=_GENERATE_CONFIG,
        )
        return response.text

    text = await loop.run_in_executor(None, _sync_call)
    if not text or not text.strip():
        raise ValueError("Gemini returned an empty response. Please try again.")
    return text.strip()


async def generate_resume(job: str, experience: str, skills: str, education: str) -> str:
    logger.info(f"Generating resume for: {job[:60]}")
    return await _call_gemini(_resume_prompt(job, experience, skills, education))


async def generate_cover_letter(job: str, experience: str, skills: str) -> str:
    logger.info(f"Generating cover letter for: {job[:60]}")
    return await _call_gemini(_cover_letter_prompt(job, experience, skills))
