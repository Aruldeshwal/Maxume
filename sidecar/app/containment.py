"""Stage D Hallucination Guard Containment Check logic."""

import re
from typing import List

# Common non-entity stopwords & sentence-starting action verbs
STOPWORDS = {
    "the", "in", "on", "at", "a", "an", "this", "that", "they", "we", "he", "she", "it",
    "according", "company", "recent", "new", "latest", "raised", "raising", "closed",
    "closing", "secured", "securing", "unveiled", "unveiling", "announced", "announcing",
    "released", "releasing", "joined", "joining", "led", "leading", "expanded", "expanding",
    "built", "building", "developed", "developing", "engineered", "partnered", "partnering",
    "acquired", "acquiring", "founded", "funding", "round", "for", "with", "from", "and",
    "to", "of", "by", "is", "are", "was", "were", "has", "have", "had", "will", "featuring",
    "including", "its", "their", "our", "your"
}

def passes_containment_check(summary_bullet: str, source_snippets: List[str]) -> bool:
    """
    Deterministic containment check (ADR 5 / apicontracts.md §5d):
    Extracts key named entities, proper nouns, and numbers from the summary bullet
    and verifies that each appears in at least one source snippet.
    """
    if not summary_bullet or not source_snippets:
        return False

    joined_snippets = " ".join(source_snippets).lower()

    # 1. Extract numeric and currency tokens (e.g. $45M, 99.8%, $2B, 500,000, 45M)
    numeric_tokens = re.findall(r'(?:\$\s*[\d,]+(?:\.\d+)?\s*(?:[kKMmBb](?:n|illion)?)?|[\d,]+(?:\.\d+)?\s*(?:%|[kKMmBb](?:n|illion)?|\b))', summary_bullet)
    clean_numeric = [n.strip().lower() for n in numeric_tokens if any(c.isdigit() for c in n)]

    for num in clean_numeric:
        # Normalize: check with/without $ and spaces
        num_clean = num.replace(" ", "").replace(",", "")
        num_no_curr = num_clean.lstrip("$")
        digits_only = re.sub(r'[^\d.]', '', num_clean)
        
        found = (
            num_clean in joined_snippets.replace(" ", "").replace(",", "") or
            num_no_curr in joined_snippets or
            (len(digits_only) >= 2 and digits_only in joined_snippets)
        )
        if not found:
            return False

    # 2. Extract capitalized named entities & proper nouns
    # Ignore the first word if it's a common capitalized sentence-starter
    words = re.findall(r'\b[A-Za-z0-9_\-]+\b', summary_bullet)
    candidate_entities = []
    
    for i, w in enumerate(words):
        if w.lower() in STOPWORDS:
            continue
        # Check if capitalized or alphanumeric like v3, Series, Sequoia, Capital
        if (w[0].isupper() or any(c.isdigit() for c in w)) and len(w) > 1:
            candidate_entities.append(w.lower())

    for entity in candidate_entities:
        if entity not in joined_snippets:
            return False

    return True
