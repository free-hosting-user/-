import re
import unicodedata
from urllib.parse import urlparse

SHORT_URL_DOMAINS = {
    "bit.ly", "tinyurl.com", "goo.gl", "is.gd", "buff.ly", "ow.ly", "t.co", "rebrand.ly"
}

SCAM_KEYWORDS = [
    r"\bcrypto\b", r"\bbitcoin\b", r"\binvestment\b", r"\bguaranteed profit\b",
    r"\bgiveaway\b", r"\bfree usdt\b", r"\bairdrop\b", r"\bdm me\b", r"\btelegram channel\b",
    r"\bwhatsapp\b", r"\bearn \$", r"\bmake money fast\b"
]

SUSPICIOUS_TLDS = {".xyz", ".top", ".work", ".click", ".loan", ".gq", ".cf", ".ml", ".tk"}

def contains_hidden_links(message_text: str, entities: list) -> bool:
    if not entities or not message_text:
        return False
    for entity in entities:
        if entity.type == "text_link":
            displayed_text = message_text[entity.offset:entity.offset + entity.length]
            if displayed_text.startswith("http://") or displayed_text.startswith("https://"):
                if displayed_text != entity.url:
                    return True
    return False

def contains_invisible_chars(text: str) -> bool:
    for char in text:
        category = unicodedata.category(char)
        if category in ["Cf", "Zw"] and ord(char) not in [0x20, 0x0A, 0x0D]:
            return True
    return False

def count_mass_mentions(text: str, entities: list) -> int:
    if not entities:
        return 0
    return sum(1 for e in entities if e.type in ["mention", "text_mention"])

def is_spam(text: str, entities: list, mode: str = "normal", active_user: bool = False) -> tuple[bool, str]:
    if not text:
        return False, ""

    if contains_invisible_chars(text):
        return True, "Invisible/Unicode spam characters"

    if contains_hidden_links(text, entities):
        return True, "Hidden or deceptive link target"

    mentions_count = count_mass_mentions(text, entities)
    max_mentions = 5 if mode == "normal" else (3 if mode == "strict" else 2)
    if mentions_count >= max_mentions:
        return True, f"Mass mentions ({mentions_count}+)"

    urls = re.findall(r'https?://[^\s]+', text)
    for url in urls:
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()
        
        if any(netloc == domain or netloc.endswith("." + domain) for domain in SHORT_URL_DOMAINS):
            return True, "URL Shortener"
            
        if any(netloc.endswith(tld) for tld in SUSPICIOUS_TLDS):
            return True, "Suspicious TLD"

    lowered_text = text.lower()
    matches = sum(1 for kw in SCAM_KEYWORDS if re.search(kw, lowered_text))
    
    threshold = 3 if mode == "normal" else (2 if mode == "strict" else 1)
    if active_user:
        threshold += 1

    if matches >= threshold:
        return True, "Scam/Giveaway pattern detected"

    return False, ""
