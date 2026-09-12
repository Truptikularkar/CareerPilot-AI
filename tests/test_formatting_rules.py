from careerpilot.core.constants import FormattingRiskType, RiskSeverity, ResumeStrategyType
from careerpilot.models.resume import TailoredResume, ResumeHeader, ResumeSummary, ResumeExperienceEntry, ResumeStrategy
from careerpilot.ats.formatting_rules import FormattingRulesEngine


def test_formatting_rules_missing_contact():
    resume = TailoredResume(
        job_id="job_001",
        strategy=ResumeStrategy(strategy_type=ResumeStrategyType.AI_DATA_ENGINEER, target_role="AI Data Engineer"),
        header=ResumeHeader(full_name="Trupti Kularkar", email="", phone=""),
        summary=ResumeSummary(text="AI Data Engineer...", target_title="AI Data Engineer"),
    )
    risks = FormattingRulesEngine.evaluate_resume_formatting(resume)
    assert any(r.risk_type == FormattingRiskType.HEADER_FOOTER_CONTENT for r in risks)
    assert any(r.severity == RiskSeverity.HIGH for r in risks)


def test_formatting_rules_inconsistent_dates():
    resume = TailoredResume(
        job_id="job_001",
        strategy=ResumeStrategy(strategy_type=ResumeStrategyType.AI_DATA_ENGINEER, target_role="AI Data Engineer"),
        header=ResumeHeader(full_name="Trupti Kularkar", email="kularkartrupti@gmail.com", phone="+91 9834055766"),
        summary=ResumeSummary(text="AI Data Engineer...", target_title="AI Data Engineer"),
        experiences=[
            ResumeExperienceEntry(company="Cognizant", title="Programmer Analyst", start_date="2023", end_date="Present", bullets=["Built pipelines."]),
            ResumeExperienceEntry(company="Intern", title="Data Intern", start_date="Jan 2022", end_date="Jun 2022", bullets=["Assisted ETL."]),
        ],
    )
    risks = FormattingRulesEngine.evaluate_resume_formatting(resume)
    assert any(r.risk_type == FormattingRiskType.INCONSISTENT_DATES for r in risks)

