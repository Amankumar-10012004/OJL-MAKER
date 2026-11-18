import json
import re
import time
import urllib.request
from datetime import datetime

# You can change this to any OpenRouter model.
# Example: "google/gemini-2.5-flash", "anthropic/claude-3-haiku", "meta-llama/llama-3-8b-instruct"
OPENROUTER_MODEL = "google/gemini-2.5-flash"


# ─────────────────────────────────────────────
# ✅ PARSE STRUCTURED ENTRY (skip AI)
# ─────────────────────────────────────────────
def parse_structured_entry(work_text: str) -> dict:
    """
    Parse user-provided structured text into journal entry fields.
    Returns a dict with my_space, tasks_carried_out, key_learnings, tools_used, special_achievements.
    Always returns a valid dictionary if work_text is provided, filling in defaults for any missing fields.
    """
    if not work_text or not work_text.strip():
        return None

    # Normalize line breaks
    text = work_text.replace('\r\n', '\n').replace('\r', '\n')

    # Define flexible field header patterns
    field_headers = [
        ("my_space",             r"(?:^|\n)\s*(?:#{1,6}\s*|\*{0,2}\s*)(?:MY\s*SPACE|MY\s*NOTES|NOTES|REFLECTIONS?|THOUGHTS)[^\n:]*:?\s*\*{0,2}\s*"),
        ("tasks_carried_out",    r"(?:^|\n)\s*(?:#{1,6}\s*|\*{0,2}\s*)(?:Tasks?(?:\s*Carried\s*Out|\s*Done|\s*Performed|\s*Completed|\s*Today)?|Work\s*Done|Activities(?:\s*Performed)?|Daily\s*Tasks?)[^\n:]*:?\s*\*{0,2}\s*"),
        ("key_learnings",        r"(?:^|\n)\s*(?:#{1,6}\s*|\*{0,2}\s*)(?:Key\s*Learnings?|Key\s*Observations?|Learnings?|Observations?|Key\s*Takeaways?|Takeaways?)[^\n:]*:?\s*\*{0,2}\s*"),
        ("tools_used",           r"(?:^|\n)\s*(?:#{1,6}\s*|\*{0,2}\s*)(?:Tools?[\s,/&]*(?:Equipment|Technology|Technologies|Techniques|Used)*|Technologies?\s*Used|Tech\s*Stack|Equipment\s*Used|Tools?|Technologies?)[^\n:]*:?\s*\*{0,2}\s*"),
        ("special_achievements", r"(?:^|\n)\s*(?:#{1,6}\s*|\*{0,2}\s*)(?:Special\s*Achievements?|Achievements?|Accomplishments?|Milestones?)[^\n:]*:?\s*\*{0,2}\s*"),
    ]

    # Find all field positions
    positions = []
    for field_name, pattern in field_headers:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            positions.append((match.start(), match.end(), field_name))

    # Clean function for extracted text
    def _clean(val: str) -> str:
        val = val.strip()
        val = re.sub(r'^\*{2,}\s*', '', val)
        val = re.sub(r'\s*\*{2,}$', '', val)
        val = re.sub(r'^#{1,}\s*Day\s*\d+[^\n]*$', '', val, flags=re.MULTILINE | re.IGNORECASE)
        val = re.sub(r'^#\s+.*$', '', val, flags=re.MULTILINE)
        val = re.sub(r'^-{3,}\s*$', '', val, flags=re.MULTILINE)
        return val.strip()

    default_values = {
        "my_space": "Reflected on the day's tasks, methodologies, and progress.",
        "tasks_carried_out": "Carried out assigned operational and development tasks.",
        "key_learnings": "Gained practical experience and strengthened core concepts.",
        "tools_used": "Development tools, IDE, and documentation",
        "special_achievements": "Successfully completed all planned objectives for the day.",
    }

    if not positions:
        # No recognized field headers: treat entire text as tasks_carried_out
        res = dict(default_values)
        res["tasks_carried_out"] = _clean(text)
        return res

    # Sort by position in text
    positions.sort(key=lambda x: x[0])

    # Extract content between each header
    fields = dict(default_values)
    for i, (start, end, field_name) in enumerate(positions):
        if i + 1 < len(positions):
            content = text[end:positions[i + 1][0]]
        else:
            content = text[end:]
        cleaned = _clean(content)
        if cleaned:
            fields[field_name] = cleaned

    return fields


# ─────────────────────────────────────────────
# ✅ PARSE MULTI-DAY STRUCTURED TEXT (skip AI splitting)
# ─────────────────────────────────────────────
def parse_multi_day_text(work_description: str, dates: list, num_days: int) -> list:
    """
    Parse a multi-day structured work description into per-day entries.
    Splits on Day headers (e.g. '### Day 1', 'Day 1:', 'Day 1 - Topic', '**Day 1**').
    Returns list of {day, date, work} dicts.
    """
    if not work_description or not work_description.strip():
        return None

    # Normalize line breaks
    text = work_description.replace('\r\n', '\n').replace('\r', '\n').strip()

    # Split by day headers: ## Day 1, ### Day 1: Topic, Day 1 - Date, **Day 1**, etc.
    day_pattern = r'(?:^|\n)\s*(?:#{1,6}\s*|\*{1,2}\s*)?Day\s*0*(\d+)\b[^\n]*'
    splits = re.split(day_pattern, text, flags=re.IGNORECASE)

    day_entries = []
    # If day headers were found (splits >= 3: [before_first, num1, content1, ...])
    if len(splits) >= 3:
        i = 1
        while i < len(splits) - 1:
            try:
                day_num = int(splits[i])
            except ValueError:
                day_num = len(day_entries) + 1
            day_content = splits[i + 1].strip()
            if day_content:
                day_entries.append((day_num, day_content))
            i += 2

    # If no day headers were found, treat input as single-day or divide across days
    if not day_entries:
        if num_days <= 1:
            day_entries.append((1, text))
        else:
            # Check if text has paragraph splits
            paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
            if len(paragraphs) >= num_days:
                for idx in range(num_days):
                    day_entries.append((idx + 1, paragraphs[idx]))
            else:
                for idx in range(num_days):
                    if idx < len(paragraphs):
                        day_entries.append((idx + 1, paragraphs[idx]))
                    else:
                        day_entries.append((idx + 1, f"Worked on assigned tasks and project development for day {idx + 1}."))

    # Ensure we fill any missing days up to num_days
    template_placeholder = (
        "**MY SPACE (My thoughts / My Sketch / My Notes / Things to Remember):** Reflected on project objectives.\n"
        "**Tasks Carried Out Today:** Worked on project tasks.\n"
        "**Key Learnings/Observations:** Strengthened technical understanding.\n"
        "**Tools, Equipment, Technology or Techniques Used:** Development tools\n"
        "**Special Achievements:** Completed day's schedule."
    )

    result = []
    for idx in range(num_days):
        formatted_date = format_date(dates[idx]) if idx < len(dates) else ""
        if idx < len(day_entries):
            content = day_entries[idx][1]
        else:
            content = template_placeholder

        result.append({
            "day": idx + 1,
            "date": formatted_date,
            "work": content
        })

    return result


# ─────────────────────────────────────────────
# ✅ DATE FORMATTER
# ─────────────────────────────────────────────
def format_date(date_str: str) -> str:
    def _ordinal(day: int) -> str:
        if 11 <= day <= 13:
            return f"{day}th"
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
        return f"{day}{suffix}"

    try:
        for fmt in ["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%y"]:
            try:
                parsed = datetime.strptime(date_str, fmt)
                # Format as "2nd February 2026"
                return f"{_ordinal(parsed.day)} {parsed.strftime('%B')} {parsed.year}"
            except ValueError:
                continue
        return date_str
    except Exception:
        return date_str


# ─────────────────────────────────────────────
# ✅ SAFE OPENROUTER CALL (handles 429)
# ─────────────────────────────────────────────
def call_openrouter(api_key, prompt, retries=3):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000", # Required by OpenRouter
        "X-Title": "OJT Journal Maker" # Required by OpenRouter
    }
    data = {
        "model": OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.4,
        "top_p": 0.9,
        "max_tokens": 4000,
    }

    for i in range(retries):
        try:
            req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers)
            with urllib.request.urlopen(req) as response:
                response_data = json.loads(response.read().decode('utf-8'))
                
                text = response_data['choices'][0]['message']['content'].strip()
                # Remove markdown code fences (```json ... ``` or ``` ... ```)
                text = re.sub(r'^```(?:json)?\s*\n?', '', text, flags=re.MULTILINE)
                text = re.sub(r'\n?\s*```\s*$', '', text, flags=re.MULTILINE)
                # Remove any text before the first [ or {
                json_start = None
                for idx, ch in enumerate(text):
                    if ch in '[{':
                        json_start = idx
                        break
                if json_start is not None:
                    text = text[json_start:]
                # Remove any text after the last ] or }
                json_end = None
                for idx in range(len(text) - 1, -1, -1):
                    if text[idx] in ']}':
                        json_end = idx
                        break
                if json_end is not None:
                    text = text[:json_end + 1]
                # Remove backtick characters inside strings (e.g. `npx create-next-app`)
                text = text.replace('`', '')
                return text

        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(5) # Wait before retry
            else:
                error_body = e.read().decode()
                raise Exception(f"OpenRouter Error {e.code}: {error_body}")
        except Exception as e:
            if "429" in str(e):
                time.sleep(5)
            else:
                raise e
    raise Exception("OpenRouter API failed after retries")


# ─────────────────────────────────────────────
# ✅ SPLIT WORK INTO DAYS
# ─────────────────────────────────────────────
def split_work_into_days(api_key: str, work_description: str, dates: list, num_days: int) -> list:
    prompt = f"""
You are a professional OJT training supervisor.

Divide the following work into EXACTLY {num_days} day-wise entries.

RULES:
- No HR / meetings / company talk
- Only technical/project work
- Each day must be unique
- Maintain progression:
  understanding → planning → implementation → debugging → improvement
- Each day: 2–4 meaningful sentences
- No generic phrases
- No repetition
- No empty or incomplete entries
- Use college/student-level tools (avoid professional tools like Jira, Azure, enterprise software)

OUTPUT JSON ONLY:
[
  {{ "day": 1, "work": "..." }}
]

WORK:
{work_description}
"""

    text = call_openrouter(api_key, prompt)
    daily_splits = json.loads(text)

    result = []
    for i, item in enumerate(daily_splits[:num_days]):
        formatted_date = format_date(dates[i]) if i < len(dates) else ""
        result.append({
            "day": i + 1,
            "date": formatted_date,
            "work": item["work"]
        })

    return result


# ─────────────────────────────────────────────
# ✅ GENERATE ALL JOURNAL ENTRIES IN ONE CALL 🚀
# ─────────────────────────────────────────────
def generate_all_journals(api_key: str, daily_data: list) -> list:
    combined_input = "\n".join([
        f"Day {d['day']} ({d['date']}): {d['work']}"
        for d in daily_data
    ])

    prompt = f"""
Generate professional OJT daily journal entries for college students.

RULES:
- Each day must be unique
- No repetition
- No HR/company content
- Keep concise and realistic
- Avoid professional/enterprise tools (no Jira, Azure, Salesforce, etc.)
- Use college-friendly tools: Python, JavaScript, Git, SQL, VS Code, Linux, React, etc.

For EACH day return:
- my_space: Minimum 4 lines of detailed personal reflection
- tasks_carried_out: List items separated by NEWLINE (NOT array)
- key_learnings: List items separated by NEWLINE (NOT array)
- tools_used: comma-separated list
- special_achievements: 1-2 lines (NEVER "N/A")

OUTPUT JSON (use plain text with newlines for multi-line fields):
[
  {{
    "day": 1,
    "my_space": "reflection text",
    "tasks_carried_out": "Task 1\\nTask 2\\nTask 3",
    "key_learnings": "Learning 1\\nLearning 2",
    "tools_used": "tool1, tool2, tool3",
    "special_achievements": "achievement text"
  }}
]

INPUT:
{combined_input}
"""

    text = call_openrouter(api_key, prompt)
    return json.loads(text)


# ─────────────────────────────────────────────
# ✅ SINGLE JOURNAL ENTRY (for backward compatibility)
# ─────────────────────────────────────────────
def generate_journal_entry(api_key: str, date: str, work: str) -> dict:
    formatted_date = format_date(date)

    prompt = f"""Generate a professional internship daily journal entry for a college student.

Date: {formatted_date}
Work Done: {work}

Return ONLY a valid JSON object (no markdown, no explanation):
{{
  "my_space": "Detailed personal reflection (Minimum 4 sentences/lines)",
  "tasks_carried_out": "Task 1\\nTask 2\\nTask 3\\nTask 4",
  "key_learnings": "Learning 1\\nLearning 2\\nLearning 3",
  "tools_used": "tool1, tool2, tool3",
  "special_achievements": "Achievement description (1-2 sentences)"
}}

IMPORTANT:
- Use college/student-level tools only (Python, JavaScript, Git, VS Code, Linux, React, etc.)
- AVOID professional tools like Jira, Azure, Salesforce, enterprise software
- Use plain newlines (\\n) between items for multi-line fields, NOT JSON arrays
- Each task/learning should be a complete sentence
- Keep it concise, professional, realistic, and non-repetitive"""

    text = call_openrouter(api_key, prompt)
    return json.loads(text)