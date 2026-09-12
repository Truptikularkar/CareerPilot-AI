import re
from typing import List, Dict, Any, Tuple
from careerpilot.core.constants import ClaimType, TruthValidationStatus
from careerpilot.models.resume import TruthClaimCheck


class ClaimClassifier:
    """
    Extracts and categorizes atomic claims from resume text for rigorous verification.
    """

    METRIC_PATTERN = re.compile(
        r"(\b\d+(?:\.\d+)?%|\b~\d+(?:\.\d+)?%|\b\d+[kKmMbB]\+?|\b\d+\+\s*(?:years?|yrs?))\b"
    )

    UNSUPPORTED_TECH_PATTERNS = [
        ("AWS Production", re.compile(r"\b(?:aws\s+(?:production|architect|engineer)|experienced\s+in\s+aws\s+production|aws\s+glue\s+in\s+production)\b", re.IGNORECASE)),
        ("Kubernetes Production", re.compile(r"\b(?:kubernetes\s+cluster\s+management|k8s\s+production\s+deployment)\b", re.IGNORECASE)),
        ("Spark Production", re.compile(r"\b(?:spark\s+streaming\s+in\s+production|spark\s+cluster\s+admin)\b", re.IGNORECASE)),
        ("Client RAG", re.compile(r"\b(?:built\s+production\s+rag\s+platform\s+for\s+client|client\s+rag\s+system)\b", re.IGNORECASE)),
    ]

    @classmethod
    def extract_claims(cls, text: str, section_name: str = "general") -> List[TruthClaimCheck]:
        """Extracts atomic metric, technology, and tenure claims from text."""
        claims: List[TruthClaimCheck] = []

        # 1. Metric claims
        for match in cls.METRIC_PATTERN.finditer(text):
            metric_val = match.group(0)
            # Find the sentence containing this metric
            start = max(0, text.rfind(".", 0, match.start()) + 1)
            end = text.find(".", match.end())
            if end == -1:
                end = len(text)
            sentence = text[start:end].strip()

            claims.append(
                TruthClaimCheck(
                    claim_text=f"{metric_val} in '{sentence}'",
                    claim_type=ClaimType.METRIC,
                    status=TruthValidationStatus.PASS,
                )
            )

        # 2. Unsupported Tech / Production claims
        for label, pattern in cls.UNSUPPORTED_TECH_PATTERNS:
            if pattern.search(text):
                claims.append(
                    TruthClaimCheck(
                        claim_text=f"Detected claim '{label}' in section '{section_name}'",
                        claim_type=ClaimType.TECHNOLOGY,
                        status=TruthValidationStatus.BLOCK,
                        violation_reason=f"Candidate evidence does not support {label}.",
                    )
                )

        # 3. Experience type check
        if section_name.lower() in ("experience", "professional experience"):
            if any(w in text.lower() for w in ["local rag sandbox", "personal project", "faiss + bm25 sandbox"]):
                claims.append(
                    TruthClaimCheck(
                        claim_text="Personal project content placed under Professional Experience",
                        claim_type=ClaimType.EXPERIENCE_TYPE,
                        status=TruthValidationStatus.BLOCK,
                        violation_reason="Personal projects must remain exclusively in the PROJECTS section.",
                    )
                )

        return claims
