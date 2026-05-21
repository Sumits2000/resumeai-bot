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

_client = genai.Client(api_key=GEMINI_API_KEY)

_RESUME_CONFIG = types.GenerateContentConfig(
    temperature=0.7,
    max_output_tokens=3000,   # enough for a full resume
)

_COVER_CONFIG = types.GenerateContentConfig(
    temperature=0.7,
    max_output_tokens=1500,   # cover letters are shorter
)


def _resume_prompt(job: str, experience: str, skills: str, education: str) -> str:
    return f"""You are an expert resume writer with 10+ years of experience helping candidates land jobs at top companies.

Create a COMPLETE, professional, ATS-friendly resume for this candidate. Do NOT cut it short.

TARGET ROLE: {job}
WORK EXPERIENCE: {experience}
SKILLS: {skills}
EDUCATION: {education}

OUTPUT THE RESUME IN THIS EXACT FORMAT (plain text, ALL CAPS for section titles):

[Candidate Full Name]
[City, India] | [email@example.com] | [+91-XXXXXXXXXX] | [linkedin.com/in/handle]

PROFESSIONAL SUMMARY
Write 3 compelling sentences tailored to the target role. Highlight years of experience, key strength, and value offered.

WORK EXPERIENCE
Job Title | Company Name | Month Year – Month Year
• Achievement bullet with quantified result (e.g., increased X by Y%)
• Achievement bullet with quantified result
• Achievement bullet with quantified result

SKILLS
Technical: [list all relevant technical skills separated by commas]
Soft Skills: [list relevant soft skills]

EDUCATION
Degree | Institution Name | Year

RULES:
- Output the COMPLETE resume — do not truncate or summarise
- Quantify every achievement possible (%, numbers, ₹, users, time saved)
- Use strong action verbs: Led, Built, Increased, Reduced, Delivered, Architected
- Keep ATS-friendly — no tables, no columns, plain text only
- Mark placeholder contact info clearly as [PLACEHOLDER]
- Output ONLY the resume — no intro sentence, no explanation after
"""


def _cover_letter_prompt(job: str, experience: str, skills: str) -> str:
    return f"""You are an expert career coach writing compelling cover letters that get interviews.

Write a COMPLETE professional cover letter for this candidate.

TARGET ROLE: {job}
EXPERIENCE SUMMARY: {experience}
KEY SKILLS: {skills}

OUTPUT FORMAT (plain text):

[Today's Date]

Hiring Manager
[Company Name]

Dear Hiring Manager,

[Opening paragraph — strong hook, name the exact role, say why this company excites you]

[Body paragraph 1 — your most relevant achievement with a specific number or result]

[Body paragraph 2 — how your skills directly match what they need]

[Closing paragraph — confident call to action, express enthusiasm, invite interview]

Sincerely,
[Your Full Name]
[email@example.com | +91-XXXXXXXXXX]

RULES:
- Write all 4 paragraphs in full — do not skip any
- Under 350 words total
- No clichés: avoid "I am writing to apply", "I am a hard worker", "passionate team player"
- Reference the exact job title in the opening
- Output ONLY the cover letter — no explanation before or after
"""


async def _call_gemini(prompt: str, config: types.GenerateContentConfig) -> str:
    loop = asyncio.get_event_loop()

    def _sync():
        response = _client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=config,
        )
        return response.text

    text = await loop.run_in_executor(None, _sync)
    if not text or not text.strip():
        raise ValueError("Gemini returned an empty response. Please try again.")
    return text.strip()


async def generate_resume(job: str, experience: str, skills: str, education: str) -> str:
    logger.info(f"Generating resume for: {job[:60]}")
    return await _call_gemini(_resume_prompt(job, experience, skills, education), _RESUME_CONFIG)


async def generate_cover_letter(job: str, experience: str, skills: str) -> str:
    logger.info(f"Generating cover letter for: {job[:60]}")
    return await _call_gemini(_cover_letter_prompt(job, experience, skills), _COVER_CONFIG)
