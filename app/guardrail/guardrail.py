import re
from app.core.logger import logger
from app.config.setting import settings

_gr = settings.guardrails
_gr_pii_masking = settings.pii_masking

_SQL_INJECTION_ENABLED = _gr["sql_injection"]["enable"]
_SQL_INJECTION_PATTERNS = [
  re.compile(p) for p in _gr["sql_injection"]["patterns"]
]

_PII_ENABLED = _gr_pii_masking["enabled"]
_PII_MASKING =[
    {"name": r["name"], "pattern":re.compile(r["pattern"]), "mask":r["mask"]}
    for r in _gr_pii_masking["rules"]
]


def check_sql_injections(query:str)->tuple[bool,list[str]]:
    if not _SQL_INJECTION_ENABLED:
        return False, []
    
    flags = []
    for pattern in _SQL_INJECTION_PATTERNS:
        if pattern.search(query):
            flags.append(f"sql injection pattern:{pattern.pattern[:40]}")
    if flags:
        logger.warning(f"SQL injection blocked — query='{query[:80]}', flags={flags}")
        return True, ["sql_injection"]
    return False, []


def run_input_guardrail(query:str)->dict:
    blocked, flags = check_sql_injections(query)
    return { "guardrail_blocked" : blocked , "guardrail_flags" : flags}


def masking_pii(text:str)->tuple[str,list]:
    if not _PII_ENABLED and not text:
        return text,[]
    
    flags = []
    masked = text
    for rule in _PII_MASKING:
        if rule["pattern"].search(masked):
            flags.append(rule["name"])
            masked = rule["pattern"].sub(rule["mask"],masked)
    if flags:
        logger.info(f"PII Information found -> Masking the data")
    
    return masked, list(dict.fromkeys(masked))