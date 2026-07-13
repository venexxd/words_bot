"""Умная проверка ответов: регистр, пробелы, артикли, ё/е, синонимы, опечатки."""
import re

_ARTICLES = re.compile(r"^(a|an|the|to)\s+", re.IGNORECASE)
_PUNCT = re.compile(r"[.,!?;:\"'«»()]")


def normalize(text: str) -> str:
    t = text.strip().lower().replace("ё", "е")
    t = _PUNCT.sub("", t)
    t = _ARTICLES.sub("", t)
    t = re.sub(r"\s+", " ", t)
    return t


def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a or not b:
        return max(len(a), len(b))
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _typo_ok(answer: str, variant: str) -> bool:
    """Допускаем мелкие опечатки в длинных словах."""
    n = len(variant)
    if n >= 8:
        return levenshtein(answer, variant) <= 2
    if n >= 5:
        return levenshtein(answer, variant) <= 1
    return False


def check_answer(user_answer: str, variants: list[str]) -> tuple[bool, bool]:
    """
    Возвращает (верно, была_опечатка).
    variants — все допустимые ответы (переводы + синонимы).
    """
    answer = normalize(user_answer)
    norm_variants = [normalize(v) for v in variants if v]
    if answer in norm_variants:
        return True, False
    for v in norm_variants:
        if _typo_ok(answer, v):
            return True, True
    return False, False
