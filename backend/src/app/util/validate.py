import re

# Program-ish patterns: must look like a real offering
NAME_MUST = re.compile(
    r"""(?ix)
    (associate\s+in\s+(arts|science)\s*\|\s*code:\s*\d+\s*\|\s*\d+\s*credits) |
    (bachelor\s+of\s+(science|applied\s+science)\b) |
    (certificate\s+(of|in)\b) |
    (^associate\s+in\s+(arts|science)\b) |
    (\b(as|aa|bs|bas)\b.*\b(code|credits)\b)
    """
)

# Obvious non-program headings to exclude
DENY_SUBSTR = [
    "civic literacy", "admissions", "fees", "refund", "financial aid",
    "policies", "eligibility", "employment - visa", "duration of status",
    "application fee", "testing", "tabE", "graduation requirements",
    "articulation agreement", "standards of academic progress",
    "important information", "how to apply", "transfer guarantees",
    "general education core", "badge", "catalog", "mission", "history",
    "academic calendar"
]

AWARDS = {"AA","AS","BS","BAS","CERTIFICATE"}
PROGRAM_HINTS = {
    "accounting","animation","architecture","aviation","biomedical","biotechnology","business",
    "chemistry","civil","clinical","computer","construction","criminal","culinary","cyber","database",
    "dental","diagnostic","early childhood","electronics","engineering","entrepreneurship","fashion",
    "film","financial","fire","funeral","game","graphic","health","histologic","hospitality","human services",
    "information","interior","marketing","medical","music","network","nuclear","nursing","opticianry",
    "paralegal","photographic","physical therapist","pilot","radiation","radiography","respiratory","sign language",
    "surgical","translation","transportation","veterinary","web"
}
CODE_PATTERN = re.compile(r"\bCode:\s*\d{3,6}\b", re.I)
def looks_like_program_name(name: str) -> bool:
    if not name or len(name) < 8:
        return False
    # Degree prefixes are strong signals
    deg = name.lower()
    if any(deg.startswith(prefix) for prefix in (
        "associate in arts", "associate in science", "bachelor of science", "bachelor of applied science",
        "certificate", "advanced technical certificate"
    )):
        return True
    # Has an explicit program code
    if CODE_PATTERN.search(name):
        return True
    # Contains a known program hint
    nm = " " + deg + " "
    if any(f" {kw} " in nm for kw in PROGRAM_HINTS):
        return True
    return False

def _credits_plausible(award: str, total_credits: int) -> bool:
    if award == "AA" and total_credits in (60,):
        return True
    if award == "AS" and total_credits in (60, 61, 62, 64, 68, 72, 76, 77, 88):  # allow common AS variants
        return True
    if award in ("BS","BAS") and total_credits >= 120:
        return True
    if award == "CERTIFICATE" and 9 <= total_credits <= 36:
        return True
    # fallback: accept if within typical ranges
    if award in ("AA","AS") and 45 <= total_credits <= 80:
        return True
    if award in ("BS","BAS") and 108 <= total_credits <= 140:
        return True
    return False

def is_valid_program(row: dict) -> bool:
    try:
        award = (row.get("award_level") or "").upper().strip()
        name = (row.get("name") or "").strip()
        total = int(row.get("total_credits") or 0)
    except Exception:
        return False

    if award not in AWARDS:
        return False

    # sane credit ranges
    if award in {"AA", "AS"} and not (45 <= total <= 83):
        return False
    if award in {"BS", "BAS"} and not (100 <= total <= 132):
        return False
    if award == "CERTIFICATE" and not (9 <= total <= 45):
        return False

    # must look like a real program title, not a paragraph fragment
    if not looks_like_program_name(name):
        return False

    # reject rows that begin with lowercase or punctuation noise
    if name and name[0].islower():
        return False

    return True