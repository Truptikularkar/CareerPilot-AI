import re
from typing import List, Dict, Any
from careerpilot.core.constants import EvidenceStatus, EvidenceType, ProvenanceSourceType
from careerpilot.models.evidence import CandidateEvidence
from careerpilot.models.candidate import CandidateProfile


class EvidenceExtractor:
    """
    Extracts atomic, verifiable evidence items from a CandidateProfile.
    Ensures every claim on a resume or interview answer maps back to an atomic fact
    with complete data provenance (fact_id, source_type, source_id, source_document, section).
    """

    METRIC_PATTERN = re.compile(
        r"(\b\d+[\d,\.]*\s*(?:%|x|k|m|b|tb|gb|users|stars|seconds|ms|queries|requests|events/sec|\$|dollars|\+)?\b|\$\s*\d+[\d,\.]*)",
        re.IGNORECASE,
    )

    @classmethod
    def extract_metrics_from_text(cls, text: str) -> List[str]:
        """Detect numeric achievements, percentages, or cost savings in bullet points."""
        matches = cls.METRIC_PATTERN.findall(text)
        metrics = []
        for m in matches:
            m_clean = m.strip()
            if any(char in m_clean for char in ["%", "$", "k", "m", "b", "tb", "gb", "+", "users", "stars", "sec", "ms"]):
                metrics.append(m_clean)
            elif len(m_clean) > 2 and m_clean.replace(",", "").replace(".", "").isdigit():
                metrics.append(m_clean)
        return list(set(metrics))

    @classmethod
    def atomize_candidate_profile(cls, profile: CandidateProfile) -> List[CandidateEvidence]:
        """Decomposes a full candidate profile into a list of verified CandidateEvidence chunks with full provenance."""
        evidences: List[CandidateEvidence] = []

        # 1. Atomize Experiences
        for exp_idx, exp in enumerate(profile.experiences, 1):
            source_sec = f"Experience: {exp.title} at {exp.company} ({exp.start_date} - {exp.end_date})"
            for b_idx, resp in enumerate(exp.responsibilities, 1):
                detected_metrics = cls.extract_metrics_from_text(resp)
                detected_tech = [t for t in exp.technologies_used if t.lower() in resp.lower()]
                fact_id = f"EXP-{exp_idx:03d}-{b_idx:02d}"
                evidences.append(
                    CandidateEvidence(
                        id=fact_id,
                        fact_id=fact_id,
                        candidate_id=profile.id,
                        source_type=ProvenanceSourceType.PROFESSIONAL_EXPERIENCE,
                        source_id=exp.id or f"EXP-{exp_idx}",
                        source_document="SQLite Candidate Profile: Experience",
                        section="Professional Experience",
                        evidence_type=EvidenceType.WORK_EXPERIENCE,
                        evidence_status=EvidenceStatus.SUPPORTED,
                        source_section=source_sec,
                        content=resp,
                        skill_tags=exp.technologies_used,
                        technologies=detected_tech or exp.technologies_used,
                        metrics=detected_metrics or exp.verified_metrics,
                        confidence=1.0,
                        status=EvidenceStatus.SUPPORTED,
                        metadata={
                            "company": exp.company,
                            "role_title": exp.title,
                            "date_range": f"{exp.start_date} - {exp.end_date}",
                        },
                    )
                )

        # 2. Atomize Projects
        for proj_idx, proj in enumerate(profile.projects, 1):
            source_sec = f"Project: {proj.name} ({proj.project_type})"
            proj_source_type = (
                ProvenanceSourceType.PERSONAL_PROJECT
                if proj.project_type in ("PERSONAL_PROJECT", "PERSONAL")
                else (ProvenanceSourceType.OPEN_SOURCE if proj.project_type in ("OPEN_SOURCE", "GITHUB") else ProvenanceSourceType.PROFESSIONAL_EXPERIENCE)
            )
            # Project description chunk
            fact_desc_id = f"PROJ-{proj_idx:03d}-00"
            evidences.append(
                CandidateEvidence(
                    id=fact_desc_id,
                    fact_id=fact_desc_id,
                    candidate_id=profile.id,
                    source_type=proj_source_type,
                    source_id=proj.id or f"PROJ-{proj_idx}",
                    source_document="SQLite Candidate Profile: Projects",
                    section="Projects",
                    evidence_type=EvidenceType.PROJECT,
                    evidence_status=EvidenceStatus.SUPPORTED,
                    source_section=source_sec,
                    content=f"{proj.name}: {proj.description}" + (f" Architecture: {proj.architecture}" if proj.architecture else "") + (f" Outcome: {proj.outcome}" if proj.outcome else ""),
                    skill_tags=proj.technologies,
                    technologies=proj.technologies,
                    metrics=proj.metrics or proj.verified_metrics,
                    confidence=1.0,
                    status=EvidenceStatus.SUPPORTED,
                    metadata={
                        "project_name": proj.name,
                        "project_type": proj.project_type,
                        "url": proj.github_or_demo_url,
                        "architecture": proj.architecture,
                        "outcome": proj.outcome,
                    },
                )
            )
            # Project responsibilities and highlight bullets
            all_bullets = list(proj.highlights) + list(proj.responsibilities)
            for b_idx, hl in enumerate(all_bullets, 1):
                detected_metrics = cls.extract_metrics_from_text(hl)
                fact_hl_id = f"PROJ-{proj_idx:03d}-{b_idx:02d}"
                evidences.append(
                    CandidateEvidence(
                        id=fact_hl_id,
                        fact_id=fact_hl_id,
                        candidate_id=profile.id,
                        source_type=proj_source_type,
                        source_id=proj.id or f"PROJ-{proj_idx}",
                        source_document="SQLite Candidate Profile: Projects",
                        section="Projects",
                        evidence_type=EvidenceType.PROJECT,
                        evidence_status=EvidenceStatus.SUPPORTED,
                        source_section=source_sec,
                        content=hl,
                        skill_tags=proj.technologies,
                        technologies=proj.technologies,
                        metrics=detected_metrics or proj.metrics or proj.verified_metrics,
                        confidence=1.0,
                        status=EvidenceStatus.SUPPORTED,
                        metadata={
                            "project_name": proj.name,
                            "project_type": proj.project_type,
                        },
                    )
                )

        # 3. Atomize Skills
        for skill_idx, skill in enumerate(profile.skills, 1):
            is_verified = skill.evidence_status == "VERIFIED" or skill.evidence_level == "PROFESSIONAL"
            skill_source_type = ProvenanceSourceType.PROFESSIONAL_EXPERIENCE if is_verified else ProvenanceSourceType.LEARNING
            ev_status = EvidenceStatus.SUPPORTED if is_verified else EvidenceStatus.PARTIALLY_SUPPORTED
            fact_skill_id = f"SKILL-{skill_idx:03d}"
            evidences.append(
                CandidateEvidence(
                    id=fact_skill_id,
                    fact_id=fact_skill_id,
                    candidate_id=profile.id,
                    source_type=skill_source_type,
                    source_id=f"SKILL-{skill.name.upper().replace(' ', '_')}",
                    source_document="SQLite Candidate Profile: Skills",
                    section="Skills",
                    evidence_type=EvidenceType.SKILL,
                    evidence_status=ev_status,
                    source_section=f"Skill: {skill.name} ({skill.category.value if hasattr(skill.category, 'value') else skill.category})",
                    content=f"Proficiency in {skill.name} ({skill.proficiency_level}, {skill.years_of_experience or 0} yrs, Evidence Level: {skill.evidence_level}). {skill.context or ''}".strip(),
                    skill_tags=[skill.name],
                    technologies=[skill.name],
                    metrics=[],
                    confidence=1.0 if is_verified else 0.75,
                    status=ev_status,
                    metadata={
                        "category": skill.category.value if hasattr(skill.category, "value") else str(skill.category),
                        "years": skill.years_of_experience,
                        "evidence_level": skill.evidence_level,
                        "evidence_status": skill.evidence_status,
                    },
                )
            )

        # 4. Atomize Education & Certifications
        for edu_idx, edu in enumerate(profile.education, 1):
            fact_edu_id = f"EDU-{edu_idx:03d}"
            evidences.append(
                CandidateEvidence(
                    id=fact_edu_id,
                    fact_id=fact_edu_id,
                    candidate_id=profile.id,
                    source_type=ProvenanceSourceType.EDUCATION,
                    source_id=edu.institution,
                    source_document="SQLite Candidate Profile: Education",
                    section="Education",
                    evidence_type=EvidenceType.EDUCATION,
                    evidence_status=EvidenceStatus.SUPPORTED,
                    source_section="Education",
                    content=f"{edu.degree} in {edu.field_of_study} from {edu.institution} ({edu.graduation_year or ''}). {edu.gpa_or_honors or ''}".strip(),
                    skill_tags=[edu.field_of_study],
                    technologies=[],
                    metrics=[],
                    confidence=1.0,
                    status=EvidenceStatus.SUPPORTED,
                    metadata={"institution": edu.institution, "degree": edu.degree},
                )
            )

        for cert_idx, cert in enumerate(profile.certifications, 1):
            fact_cert_id = f"CERT-{cert_idx:03d}"
            evidences.append(
                CandidateEvidence(
                    id=fact_cert_id,
                    fact_id=fact_cert_id,
                    candidate_id=profile.id,
                    source_type=ProvenanceSourceType.CERTIFICATION,
                    source_id=f"CERT-{cert_idx}",
                    source_document="SQLite Candidate Profile: Certifications",
                    section="Certifications",
                    evidence_type=EvidenceType.CERTIFICATION,
                    evidence_status=EvidenceStatus.SUPPORTED,
                    source_section="Certifications",
                    content=f"Certified: {cert}",
                    skill_tags=[cert],
                    technologies=[],
                    metrics=[],
                    confidence=1.0,
                    status=EvidenceStatus.SUPPORTED,
                    metadata={"certification_name": cert},
                )
            )

        # 5. Atomize Achievements
        for ach_idx, ach in enumerate(getattr(profile, "achievements", []), 1):
            detected_metrics = cls.extract_metrics_from_text(f"{ach.description} {ach.metrics or ''}")
            fact_ach_id = f"ACH-{ach_idx:03d}"
            evidences.append(
                CandidateEvidence(
                    id=fact_ach_id,
                    fact_id=fact_ach_id,
                    candidate_id=profile.id,
                    source_type=ProvenanceSourceType.RESEARCH if "Publication" in ach.title or "Model" in ach.title else ProvenanceSourceType.PROFESSIONAL_EXPERIENCE,
                    source_id=ach.id or f"ACH-{ach_idx}",
                    source_document="SQLite Candidate Profile: Achievements",
                    section="Achievements",
                    evidence_type=EvidenceType.ACHIEVEMENT if hasattr(EvidenceType, "ACHIEVEMENT") else EvidenceType.WORK_EXPERIENCE,
                    evidence_status=EvidenceStatus.SUPPORTED,
                    source_section=f"Achievement: {ach.title}",
                    content=f"{ach.title}: {ach.description}" + (f" Metrics: {ach.metrics}" if ach.metrics else ""),
                    skill_tags=ach.technologies,
                    technologies=ach.technologies,
                    metrics=detected_metrics,
                    confidence=1.0,
                    status=EvidenceStatus.SUPPORTED,
                    metadata={"title": ach.title},
                )
            )

        return evidences


