from __future__ import annotations

import logging
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

logger = logging.getLogger(__name__)


@dataclass
class AutofillResult:
    filled: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return bool(self.filled)


# Patterns matched against name/id/aria-label/placeholder/label-for text.
PATTERNS: dict[str, list[str]] = {
    "first_name": [r"\bfirst[\s_-]?name\b", r"\bfname\b", r"\bgiven[\s_-]?name\b"],
    "last_name": [r"\blast[\s_-]?name\b", r"\blname\b", r"\bsurname\b", r"\bfamily[\s_-]?name\b"],
    "full_name": [r"\bfull[\s_-]?name\b", r"^name$", r"\byour[\s_-]?name\b"],
    "email": [r"\bemail\b", r"\be[-\s]?mail\b"],
    "phone": [r"\bphone\b", r"\bmobile\b", r"\btelephone\b"],
    "location": [r"\blocation\b", r"\bcity\b", r"\baddress\b", r"\bcountry\b", r"\bcurrent[\s_-]?city\b"],
    "linkedin": [r"\blinkedin\b"],
    "github": [r"\bgithub\b"],
    "portfolio": [r"\bportfolio\b", r"\bwebsite\b", r"\bpersonal[\s_-]?site\b"],
    "cover_letter": [r"\bcover[\s_-]?letter\b", r"\bwhy[\s_-]?(you|us|this|join)\b", r"\bmotivation\b"],
    "resume": [r"\bresume\b", r"\bcv\b", r"\bcurriculum\b"],
}


def _split_full_name(name: str) -> tuple[str, str]:
    parts = name.strip().split()
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


def _element_signature(driver: Any, elem: WebElement) -> str:
    """Combined searchable text from element attributes + associated label."""
    attrs: list[str] = []
    for attr in ("name", "id", "aria-label", "aria-labelledby", "placeholder", "data-qa", "data-testid", "autocomplete"):
        try:
            v = elem.get_attribute(attr)
            if v:
                attrs.append(v)
        except Exception:
            pass

    try:
        elem_id = elem.get_attribute("id")
        if elem_id:
            labels = driver.find_elements(By.XPATH, f"//label[@for='{elem_id}']")
            for label in labels[:1]:
                t = label.text or ""
                if t:
                    attrs.append(t)
    except Exception:
        pass

    return " ".join(attrs).lower()


def _classify(sig: str) -> str | None:
    for field_type, patterns in PATTERNS.items():
        for pat in patterns:
            if re.search(pat, sig):
                return field_type
    return None


def _classify_with_type(sig: str, input_type: str) -> str | None:
    """Classify by signature first; fall back to input type for email/tel/url."""
    field_type = _classify(sig)
    if field_type:
        return field_type
    if input_type == "email":
        return "email"
    if input_type == "tel":
        return "phone"
    if input_type == "url" and "linkedin" in sig:
        return "linkedin"
    if input_type == "url" and "github" in sig:
        return "github"
    return None


def _safe_send(elem: WebElement, value: str) -> bool:
    try:
        elem.clear()
    except Exception:
        pass
    try:
        elem.send_keys(value)
        return True
    except Exception as exc:
        logger.debug("send_keys failed: %s", exc)
        return False


def _cover_letter_temp_path(cover_letter: str) -> str:
    """Write cover letter content to a temp .txt file for upload, return absolute path."""
    fd, path = tempfile.mkstemp(prefix="cover_letter_", suffix=".txt")
    with open(fd, "w", encoding="utf-8") as f:
        f.write(cover_letter)
    return path


def _fill_in_current_frame(
    driver: Any,
    values: dict[str, str],
    cv_path: str | None,
    cover_letter_file: str | None,
    result: AutofillResult,
    frame_label: str,
) -> None:
    inputs = driver.find_elements(By.XPATH, "//input[not(@type='hidden')] | //textarea")
    for el in inputs:
        try:
            input_type = (el.get_attribute("type") or el.tag_name).lower()
            if input_type in ("submit", "button", "checkbox", "radio"):
                continue
            if not el.is_displayed():
                continue

            sig = _element_signature(driver, el)

            if input_type == "file":
                accept = (el.get_attribute("accept") or "").lower()
                is_cover = any(re.search(p, sig) for p in PATTERNS["cover_letter"])
                is_resume = any(re.search(p, sig) for p in PATTERNS["resume"]) or "resume" in accept
                if is_cover and cover_letter_file:
                    try:
                        el.send_keys(cover_letter_file)
                        result.filled.append(f"cover_letter (file){frame_label} <- {Path(cover_letter_file).name}")
                    except Exception as exc:
                        result.skipped.append(f"cover letter upload failed: {exc}")
                elif is_resume and cv_path:
                    try:
                        el.send_keys(str(Path(cv_path).resolve()))
                        result.filled.append(f"resume <- {Path(cv_path).name}{frame_label}")
                    except Exception as exc:
                        result.skipped.append(f"resume upload failed: {exc}")
                continue

            field_type = _classify_with_type(sig, input_type)
            if field_type and values.get(field_type):
                if _safe_send(el, values[field_type]):
                    result.filled.append(f"{field_type}{frame_label} ({sig[:60]})")
                else:
                    result.skipped.append(f"{field_type} send_keys failed ({sig[:60]})")
            elif not field_type and sig:
                result.skipped.append(f"unknown field{frame_label} ({sig[:60]})")
        except Exception as exc:
            logger.debug("autofill skip element: %s", exc)


def fill_application_form(
    driver: Any,
    profile: dict[str, Any],
    cv_path: str | None,
    cover_letter: str,
) -> AutofillResult:
    """Heuristically fill obvious application fields, including inside iframes.

    Never clicks submit, never solves captcha.
    """
    result = AutofillResult()

    full_name = profile.get("name", "")
    first, last = _split_full_name(full_name)
    values: dict[str, str] = {
        "first_name": first,
        "last_name": last,
        "full_name": full_name,
        "email": profile.get("email", ""),
        "phone": profile.get("phone", ""),
        "location": profile.get("location", ""),
        "linkedin": profile.get("linkedin_url", ""),
        "github": profile.get("github_url", ""),
        "portfolio": profile.get("portfolio_url", ""),
        "cover_letter": cover_letter,
    }

    cover_letter_file = _cover_letter_temp_path(cover_letter) if cover_letter else None

    # Top-level frame
    driver.switch_to.default_content()
    _fill_in_current_frame(driver, values, cv_path, cover_letter_file, result, frame_label="")

    # Walk into iframes (one level deep — most ATSs nest at most once)
    driver.switch_to.default_content()
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    for idx, frame in enumerate(iframes):
        try:
            src = frame.get_attribute("src") or ""
            # Skip captcha frames — fields inside are not user-fillable
            if any(token in src for token in ("recaptcha", "hcaptcha", "turnstile")):
                continue
            driver.switch_to.frame(frame)
            _fill_in_current_frame(driver, values, cv_path, cover_letter_file, result, frame_label=f" [iframe#{idx}]")
        except Exception as exc:
            logger.debug("iframe %s skipped: %s", idx, exc)
        finally:
            driver.switch_to.default_content()

    page = (driver.page_source or "").lower()
    if "recaptcha" in page or "hcaptcha" in page or "cf-turnstile" in page:
        result.notes.append("captcha present on page — solve manually before submitting")

    return result
