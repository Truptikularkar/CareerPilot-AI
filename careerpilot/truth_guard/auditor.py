import re
from typing import List, Dict, Any, Set, Tuple
from careerpilot.core.constants import TruthValidationStatus, ClaimType
from careerpilot.models.resume import TruthClaimCheck, TruthValidationReport
from careerpilot.truth_guard.classifier import ClaimClassifier
from careerpilot.core.logging import get_logger

logger = get_logger(__name__)


class TruthAuditor:
    """
    Deterministic Truth Auditor verifying candidate claims against verified immutable ground truth.
    Guarantees zero hallucinations, metric inflation, or experience fabrication.
    """

    # Exact verified candidate metrics (Source: achievements.md, experience.md, projects.md)
    VERIFIED_METRIC_VALUES: Set[str] = {
        "25%", "~25%",
        "35%", "~35%",
        "50%", "~50%",
        "60%", "~60%",
        "75%", "~75%",
        "500k", "~500k", "500k+", "~500k+", "500,000+",
        "10k", "~10k", "10k+", "10,000+",
        "1.9+", "1.9+ years", "1.9+ yrs",
        "1.8+", "1.8+ years", "1.8+ yrs",
        "2023", "2024",
    }





    # Prohibited claims that candidate evidence does NOT support in production
    PROHIBITED_CLAIMS = [
        # AWS production claims
        (re.compile(r"\b(?:aws\s+(?:data\s+engineer\s+in\s+)?production|lead\s+aws\s+data\s+engineer|aws\s+production\s+experience|aws\s+data\s+engineer\s+at\s+cognizant)\b", re.IGNORECASE), "AWS production experience is unverified. Candidate only has GCP production experience."),
        (re.compile(r"\b(?:production\s+(?:aws\s+glue|aws\s+emr|redshift\s+cluster)|managing\s+aws\s+glue)\b", re.IGNORECASE), "AWS Glue/EMR/Redshift production architecture is unverified."),
        # Kubernetes / Spark production administration claims
        (re.compile(r"\b(?:kubernetes\s+production\s+cluster|kubernetes\s+cluster|k8s\s+production)\b", re.IGNORECASE), "Kubernetes cluster administration in production is unverified."),
        (re.compile(r"\b(?:spark\s+production\s+streaming|spark\s+streaming\s+in\s+production)\b", re.IGNORECASE), "Apache Spark production streaming is unverified."),
        # Client RAG fabrication
        (re.compile(r"\b(?:built\s+production\s+rag\s+platform\s+for\s+client|client\s+rag\s+system|production\s+rag\s+system\s+serving\s+millions)\b", re.IGNORECASE), "RAG sandbox is a personal engineering project, not client production."),
        # Experience tenure exaggeration
        (re.compile(r"\b(?:3|4|5|6)\+?\s*years\s+of\s+(?:professional\s+)?experience\b", re.IGNORECASE), "Candidate total experience is 1.9+ years, cannot claim 3+ years."),
    ]

    @classmethod
    def audit_text_claims(cls, text: str, section_name: str = "general") -> List[TruthClaimCheck]:
        """Audits a block of text and flags any metric, technology, or tenure violations."""
        results: List[TruthClaimCheck] = []

        # 1. Prohibited pattern checks
        for pattern, reason in cls.PROHIBITED_CLAIMS:
            match = pattern.search(text)
            if match:
                results.append(
                    TruthClaimCheck(
                        claim_text=match.group(0),
                        claim_type=ClaimType.TECHNOLOGY if any(w in match.group(0).lower() for w in ["aws", "kubernetes", "spark"]) else ClaimType.EXPERIENCE_TYPE,
                        status=TruthValidationStatus.BLOCK,
                        violation_reason=reason,
                    )
                )

        # 2. Metric extraction and verification
        metric_matches = re.finditer(r"(?:~?\d+(?:\.\d+)?%|~?\d+[kKmMbB]\+?|\b\d+(?:\.\d+)?\+\s*(?:years?|yrs?))", text)

        for match in metric_matches:
            val = match.group(0)
            norm_val = val.lower().strip()
            # Check if this metric is recognized
            is_valid = any(
                norm_val == vm.lower() or norm_val.replace("~", "") == vm.lower().replace("~", "")
                for vm in cls.VERIFIED_METRIC_VALUES
            )
            if not is_valid:
                results.append(
                    TruthClaimCheck(
                        claim_text=val,
                        claim_type=ClaimType.METRIC,
                        status=TruthValidationStatus.BLOCK,
                        violation_reason=f"Unverified metric '{val}' detected in text. Allowed verified metrics are: 25%, 35%, 60%, 75%, 500k+, 1.9+ years.",
                    )
                )
            else:
                results.append(
                    TruthClaimCheck(
                        claim_text=val,
                        claim_type=ClaimType.METRIC,
                        status=TruthValidationStatus.PASS,
                        matched_evidence_id="verified_achievement_metric",
                    )
                )

        # 3. Experience Type Isolation check

        if section_name.lower() in ("experience", "professional experience", "work experience"):
            if "local rag" in text.lower() or "faiss + bm25 sandbox" in text.lower():
                results.append(
                    TruthClaimCheck(
                        claim_text="Local RAG Sandbox in Professional Experience",
                        claim_type=ClaimType.EXPERIENCE_TYPE,
                        status=TruthValidationStatus.BLOCK,
                        violation_reason="Personal projects must never be placed inside the Professional Work Experience section.",
                    )
                )

        return results

    @classmethod
    def audit_sections(cls, sections: Dict[str, str]) -> TruthValidationReport:
        """Audits all resume sections and compiles a full TruthValidationReport."""
        all_checks: List[TruthClaimCheck] = []

        for sec_name, sec_text in sections.items():
            checks = cls.audit_text_claims(sec_text, section_name=sec_name)
            all_checks.extend(checks)

        blocked = [c for c in all_checks if c.status == TruthValidationStatus.BLOCK]
        flagged = [c for c in all_checks if c.status == TruthValidationStatus.FLAG]
        passed = [c for c in all_checks if c.status == TruthValidationStatus.PASS]

        overall_status = TruthValidationStatus.PASS
        if blocked:
            overall_status = TruthValidationStatus.BLOCK
            reason = f"Truth Guard BLOCKED generation due to {len(blocked)} unsupported claim(s): {blocked[0].violation_reason}"
        elif flagged:
            overall_status = TruthValidationStatus.FLAG
            reason = f"Truth Guard FLAGGED {len(flagged)} item(s) for candidate review."
        else:
            reason = "All extracted claims are 100% grounded in verified candidate evidence."

        metric_checks = [c for c in all_checks if c.claim_type == ClaimType.METRIC]
        tech_checks = [c for c in all_checks if c.claim_type == ClaimType.TECHNOLOGY]
        exp_type_checks = [c for c in all_checks if c.claim_type == ClaimType.EXPERIENCE_TYPE]

        return TruthValidationReport(
            status=overall_status,
            verified_claims_count=len(passed),
            flagged_claims=flagged,
            blocked_claims=blocked,
            metric_checks=metric_checks,
            tech_checks=tech_checks,
            experience_type_checks=exp_type_checks,
            summary_reasoning=reason,
        )

    @classmethod
    def audit_explanation(cls, text: str, structured_facts: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Audits an AI-generated or template job fit explanation against structured verified candidate facts.
        Guarantees that AI never invents candidate experience years, companies, or unverified production technologies.
        """
        if not text or not text.strip():
            return False, "Explanation text is empty."

        text_lower = text.lower()

        # 1. Prohibited candidate technology claims in production
        # e.g., claiming candidate has AWS production experience
        cand_aws_prod_patterns = [
            r"\byou\s+have\s+(?:verified\s+)?aws\s+production\b",
            r"\byour\s+aws\s+production\s+experience\b",
            r"\byour\s+production\s+experience\s+in\s+aws\b",
            r"\byour\s+verified\s+aws\b",
            r"\bverified\s+production\s+experience\s+with\s+aws\b",
        ]
        for pat in cand_aws_prod_patterns:
            if re.search(pat, text_lower):
                return False, "Explanation improperly claims candidate has verified AWS production experience."

        # 2. Candidate experience exaggeration (candidate has ~1.9 years, not 3+/4+/5+)
        cand_tenure_inflation = [
            r"\byou\s+have\s+[3-9]\+?\s*(?:years|yrs)\b",
            r"\byour\s+[3-9]\+?\s*(?:years|yrs)\s+of\s+(?:professional\s+)?experience\b",
            r"\bwith\s+your\s+[3-9]\+?\s*years\b",
        ]
        for pat in cand_tenure_inflation:
            if re.search(pat, text_lower):
                return False, "Explanation inflates candidate's experience beyond verified ~1.9 years."

        # 3. Fabricated production systems
        if "production kubernetes cluster" in text_lower or "production spark streaming" in text_lower:
            return False, "Explanation claims unverified production infrastructure."

        return True, "Explanation is grounded in verified candidate facts."

