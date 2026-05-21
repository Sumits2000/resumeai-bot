"""
Gemini AI integration — resume and cover letter generation.
Uses the free Gemini 2.5 Flash API.
"""
import asyncio
import logging
import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)

# Configure Gemini once at import time
genai.configure(api_key=GEMINI_API_KEY)
_model = genai.GenerativeModel(GEMINI_MODEL)

SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT",        "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH",       "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

GENERATION_CONFIG = genai.GenerationConfig(
    temperature=0.7,
    max_output_tokens=1500,
)


def _build_resume_prompt(job: str, experience: str, skills: str, education: str) -> str:
    return f"""You are an expert resume writer with 10+ years of experience helping candidates land jobs.

Create a professional, ATS-friendly resume for the following candidate.

TARGET ROLE: {job}
WORK EXPERIENCE: {experience}
SKILLS: {skills}
EDUCATION: {education}

FORMAT THE RESUME EXACTLY LIKE THIS (use plain text, no markdown headers, use ALL CAPS for section titles):

[CANDIDATE NAME]
[City, India] | [email@example.com] | [+91-XXXXXXXXXX] | [linkedin.com/in/handle]

PROFESSIONAL SUMMARY
Write 2–3 compelling sentences tailored to the target role.

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

IMPORTANT RULES:
- Quantify achievements wherever logical (%, ₹, numbers)
- Keep it to 1 page worth of content
- Make it ATS-friendly — no tables, no columns
- Use action verbs: Led, Built, Increased, Reduced, Delivered, etc.
- Fill in placeholder contact details clearly marked as [PLACEHOLDER]
- Do NOT include any preamble or explanation — output ONLY the resume
"""


def _build_cover_letter_prompt(job: str, experience: str, skills: str) -> str:
    return f"""You are an expert career coach who writes compelling cover letters.

Write a professional cover letter for the following candidate.

TARGET ROLE: {job}
EXPERIENCE SUMMARY: {experience}
KEY SKILLS: {skills}

FORMAT:
[Date]

Hiring Manager
[Company Name]

Dear Hiring Manager,

[Opening paragraph — hook + why this role]

[Body paragraph 1 — most relevant experience & achievement]

[Body paragraph 2 — skills alignment + value you bring]

[Closing paragraph — call to action, enthusiasm]

Sincerely,
[Your Name]
[Contact: email | phone]

RULES:
- Confident but not arrogant tone
- Specific, not generic — reference the job title explicitly
- 3–4 paragraphs, under 300 words total
- No fluff phrases like "I am writing to apply"
- Do NOT include any preamble — output ONLY the cover letter
"""


async def _call_gemini(prompt: str) -> str:
    """
    Run the blocking Gemini SDK call in a thread pool so it doesn't
    block the asyncio event loop.
    """
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: _model.generate_content(
            prompt,
            generation_config=GENERATION_CONFIG,
            safety_settings=SAFETY_SETTINGS,
        ),
    )
    if not response.text:
        raise ValueError("Gemini returned an empty response. Please try again.")
    return response.text.strip()


async def generate_resume(job: str, experience: str, skills: str, education: str) -> str:
    prompt = _build_resume_prompt(job, experience, skills, education)
    logger.info(f"Generating resume for job: {job[:50]}")
    return await _call_gemini(prompt)


async def generate_cover_letter(job: str, experience: str, skills: str) -> str:
    prompt = _build_cover_letter_prompt(job, experience, skills)
    logger.info(f"Generating cover letter for job: {job[:50]}")
    return await _call_gemini(prompt)
