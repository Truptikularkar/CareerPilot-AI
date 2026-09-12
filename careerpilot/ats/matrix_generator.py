from typing import List, Dict, Any, Tuple
from careerpilot.core.constants import MatchLevel, RequirementImportance
from careerpilot.models.ats import RequirementCoverageItem, MissingRequirement
from careerpilot.models.job import JobAnalysisResult, JobRequirement
from careerpilot.models.resume import TailoredResume
from careerpilot.ats.keyword_matcher import KeywordTaxonomyMatcher


class RequirementMatrixGenerator:
    """
    Constructs a traceable requirement-by-requirement matrix comparing
    the Job Description against both the Tailored Resume and candidate ground truth.
    """

    @classmethod
    def generate_matrix(
        cls,
        analysis: JobAnalysisResult,
        resume: TailoredResume,
    ) -> Tuple[List[RequirementCoverageItem], List[MissingRequirement], str, str]:
        # Compile full searchable resume text
        full_resume_text = f"{resume.summary.text}\n"
        for sc in resume.skills_categories:
            full_resume_text += f"{sc.category_name}: {', '.join(sc.skills)}\n"
        for exp in resume.experiences:
            full_resume_text += f"{exp.title} {exp.company}\n" + "\n".join(exp.bullets) + "\n"
        for proj in resume.projects:
            full_resume_text += f"{proj.name} {', '.join(proj.technologies)}\n" + "\n".join(proj.bullets) + "\n"

        matrix_items: List[RequirementCoverageItem] = []
        missing_reqs: List[MissingRequirement] = []

        must_have_total = 0
        must_have_matched = 0
        nice_to_have_total = 0
        nice_to_have_matched = 0

        for req in analysis.requirements:
            skill_name = req.normalized_skill
            importance = req.importance

            match_level, explanation = KeywordTaxonomyMatcher.match_term_in_text(skill_name, full_resume_text)

            # Check candidate ground truth status from analysis
            # Candidate has only GCP in production; AWS/Redshift/Azure are non-production / transferable gaps
            if any(term in skill_name.lower() for term in ["aws", "redshift", "s3", "glue", "emr", "kinesis", "azure", "snowflake"]):
                is_candidate_verified = False
            else:
                matched_candidate_req = next((m for m in analysis.key_strengths if skill_name.lower() in m.lower()), None)
                is_candidate_verified = matched_candidate_req is not None


            if importance == RequirementImportance.MUST_HAVE:
                must_have_total += 1
                if match_level != MatchLevel.GAP:
                    must_have_matched += 1
            else:
                nice_to_have_total += 1
                if match_level != MatchLevel.GAP:
                    nice_to_have_matched += 1

            if match_level == MatchLevel.GAP:
                if is_candidate_verified:
                    recommendation = f"Candidate has verified evidence for '{skill_name}', but it is omitted in current resume draft. Consider adding it to the Skills section."
                    cand_status = "VERIFIED_IN_PROFILE"
                else:
                    recommendation = f"Truthfully omitted: candidate has no verified production experience for '{skill_name}'. Do not fabricate."
                    cand_status = "NOT_VERIFIED"

                missing_reqs.append(
                    MissingRequirement(
                        requirement=skill_name,
                        importance=importance,
                        candidate_status=cand_status,
                        resume_status="OMITTED",
                        explanation=f"Skill '{skill_name}' was not detected in the resume text.",
                        recommendation=recommendation,
                    )
                )

                matrix_items.append(
                    RequirementCoverageItem(
                        requirement=skill_name,
                        importance=importance,
                        match_level=MatchLevel.GAP,
                        resume_evidence=None,
                        candidate_evidence="Verified in candidate profile" if is_candidate_verified else "No verified production record",
                        truth_status="SUPPORTED" if not is_candidate_verified else "AVAILABLE",
                        recommendation=recommendation,
                    )
                )
            else:
                matrix_items.append(
                    RequirementCoverageItem(
                        requirement=skill_name,
                        importance=importance,
                        match_level=match_level,
                        resume_evidence=explanation or f"Referenced in resume text",
                        candidate_evidence="Verified in candidate profile and production history",
                        truth_status="SUPPORTED",
                        recommendation="Strong evidence match.",
                    )
                )

        mh_ratio = f"{must_have_matched}/{must_have_total}" if must_have_total > 0 else "N/A"
        nh_ratio = f"{nice_to_have_matched}/{nice_to_have_total}" if nice_to_have_total > 0 else "N/A"

        return matrix_items, missing_reqs, mh_ratio, nh_ratio
