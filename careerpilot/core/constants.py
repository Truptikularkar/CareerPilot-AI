from enum import Enum


class EvidenceStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    NOT_SUPPORTED = "NOT_SUPPORTED"


class EvidenceType(str, Enum):
    WORK_EXPERIENCE = "WORK_EXPERIENCE"
    PROJECT = "PROJECT"
    SKILL = "SKILL"
    EDUCATION = "EDUCATION"
    CERTIFICATION = "CERTIFICATION"
    ACHIEVEMENT = "ACHIEVEMENT"


class SeniorityLevel(str, Enum):
    INTERN = "INTERN"
    ENTRY = "ENTRY"
    JUNIOR = "JUNIOR"
    MID = "MID"
    SENIOR = "SENIOR"
    LEAD = "LEAD"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            val_upper = value.upper().replace("-", "_").replace(" ", "_")
            for member in cls:
                if member.value == val_upper or member.name == val_upper:
                    return member
                if member.value in val_upper:
                    return member
        return cls.UNKNOWN


class RoleCategory(str, Enum):
    DATA_ENGINEER = "DATA_ENGINEER"
    AI_DATA_ENGINEER = "AI_DATA_ENGINEER"
    AI_ENGINEER = "AI_ENGINEER"
    GENAI_ENGINEER = "GENAI_ENGINEER"
    GCP_DATA_ENGINEER = "GCP_DATA_ENGINEER"
    CLOUD_DATA_ENGINEER = "CLOUD_DATA_ENGINEER"
    DATA_SCIENTIST = "DATA_SCIENTIST"
    ML_ENGINEER = "ML_ENGINEER"
    ANALYTICS_ENGINEER = "ANALYTICS_ENGINEER"
    SOFTWARE_ENGINEER = "SOFTWARE_ENGINEER"
    OTHER = "OTHER"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            val_upper = value.upper().replace("-", "_").replace(" ", "_")
            for member in cls:
                if member.value == val_upper or member.name == val_upper:
                    return member
            if "AI_DATA" in val_upper:
                return cls.AI_DATA_ENGINEER
            if "GENAI" in val_upper or "GEN_AI" in val_upper:
                return cls.GENAI_ENGINEER
            if "GCP" in val_upper:
                return cls.GCP_DATA_ENGINEER
            if "DATA_ENG" in val_upper:
                return cls.DATA_ENGINEER
            if "AI_ENG" in val_upper:
                return cls.AI_ENGINEER
            if "ML" in val_upper:
                return cls.ML_ENGINEER
            if "DATA_SCI" in val_upper:
                return cls.DATA_SCIENTIST
        return cls.OTHER


class DecisionRecommendation(str, Enum):
    APPLY = "APPLY"
    REVIEW = "REVIEW"
    SKIP = "SKIP"
    PREPARE = "PREPARE"  # Preserved as user action trigger


class ProvenanceSourceType(str, Enum):
    PROFESSIONAL_EXPERIENCE = "PROFESSIONAL_EXPERIENCE"
    PERSONAL_PROJECT = "PERSONAL_PROJECT"
    OPEN_SOURCE = "OPEN_SOURCE"
    RESEARCH = "RESEARCH"
    EDUCATION = "EDUCATION"
    CERTIFICATION = "CERTIFICATION"
    LEARNING = "LEARNING"
    GITHUB = "GITHUB"
    LINKEDIN_EXPORT = "LINKEDIN_EXPORT"
    NAUKRI = "NAUKRI"
    RESUME_PDF = "RESUME_PDF"
    MANUAL_ENTRY = "MANUAL_ENTRY"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            val_upper = value.upper().replace("-", "_").replace(" ", "_")
            for member in cls:
                if member.value == val_upper or member.name == val_upper:
                    return member
        return cls.PERSONAL_PROJECT


class ExternalPlatform(str, Enum):
    GITHUB = "GITHUB"
    LINKEDIN = "LINKEDIN"
    NAUKRI = "NAUKRI"


class ApplicationStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    ANALYZED = "ANALYZED"
    SAVED = "SAVED"
    APPLIED = "APPLIED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    SCREENING = "SCREENING"
    OA = "OA"
    INTERVIEWING = "INTERVIEWING"
    TECHNICAL_ROUND = "TECHNICAL_ROUND"
    HR_ROUND = "HR_ROUND"
    FINAL_ROUND = "FINAL_ROUND"
    OFFER = "OFFER"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"
    ON_HOLD = "ON_HOLD"
    NO_RESPONSE = "NO_RESPONSE"

    # Backward compatibility aliases
    INTERVIEW = "INTERVIEWING"
    APPLYING = "APPLIED"
    SKIPPED = "WITHDRAWN"
    OA_SCHEDULED = "OA"
    OA_SUBMITTED = "OA"
    TECHNICAL_ROUND_1 = "TECHNICAL_ROUND"
    TECHNICAL_ROUND_2 = "TECHNICAL_ROUND"
    SYSTEM_DESIGN = "TECHNICAL_ROUND"
    BEHAVIORAL_ROUND = "HR_ROUND"
    RESUME_VIEWED = "ACKNOWLEDGED"
    OFFER_RECEIVED = "OFFER"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            val_upper = value.upper().replace("-", "_").replace(" ", "_")
            alias_map = {
                "INTERVIEW": cls.INTERVIEWING,
                "APPLYING": cls.APPLIED,
                "SKIPPED": cls.WITHDRAWN,
                "OA_SCHEDULED": cls.OA,
                "OA_SUBMITTED": cls.OA,
                "TECHNICAL_ROUND_1": cls.TECHNICAL_ROUND,
                "TECHNICAL_ROUND_2": cls.TECHNICAL_ROUND,
                "TECHNICAL_INTERVIEW": cls.TECHNICAL_ROUND,
                "SYSTEM_DESIGN": cls.TECHNICAL_ROUND,
                "BEHAVIORAL_ROUND": cls.HR_ROUND,
                "HR_INTERVIEW": cls.HR_ROUND,
                "RESUME_VIEWED": cls.ACKNOWLEDGED,
                "OFFER_RECEIVED": cls.OFFER,
            }


            if val_upper in alias_map:
                return alias_map[val_upper]
            for member in cls:
                if member.value == val_upper or member.name == val_upper:
                    return member
        return cls.SAVED




class RequirementImportance(str, Enum):
    MUST_HAVE = "MUST_HAVE"
    NICE_TO_HAVE = "NICE_TO_HAVE"
    UNKNOWN = "UNKNOWN"


# Alias for compatibility
RequirementType = RequirementImportance


class TaxonomyCategory(str, Enum):
    PROGRAMMING = "PROGRAMMING"
    DATABASE = "DATABASE"
    DATA_ENGINEERING = "DATA_ENGINEERING"
    CLOUD = "CLOUD"
    GENAI = "GENAI"
    MACHINE_LEARNING = "MACHINE_LEARNING"
    MLOPS = "MLOPS"
    DEVOPS = "DEVOPS"
    ORCHESTRATION = "ORCHESTRATION"
    DATA_QUALITY = "DATA_QUALITY"
    ANALYTICS = "ANALYTICS"
    SYSTEM_DESIGN = "SYSTEM_DESIGN"
    SOFT_SKILL = "SOFT_SKILL"
    DOMAIN = "DOMAIN"
    OTHER = "OTHER"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            val_upper = value.upper().replace("-", "_").replace(" ", "_").replace("&", "_").replace("/", "_")
            for member in cls:
                if member.value == val_upper or member.name == val_upper:
                    return member
                if member.name in val_upper:
                    return member
        return cls.OTHER


# Alias for compatibility
SkillCategory = TaxonomyCategory




class MatchStatus(str, Enum):
    MATCH = "MATCH"
    PARTIAL = "PARTIAL"
    GAP = "GAP"
    UNKNOWN = "UNKNOWN"


class CloudTransferabilityStatus(str, Enum):
    MATCH = "MATCH"
    TRANSFERABLE = "TRANSFERABLE"
    SIGNIFICANT_GAP = "SIGNIFICANT_GAP"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class RiskSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskType(str, Enum):
    EXPERIENCE_SHORTFALL = "EXPERIENCE_SHORTFALL"
    CRITICAL_SKILL_GAP = "CRITICAL_SKILL_GAP"
    CLOUD_MISMATCH = "CLOUD_MISMATCH"
    SENIORITY_MISMATCH = "SENIORITY_MISMATCH"
    ROLE_MISMATCH = "ROLE_MISMATCH"
    RESEARCH_HEAVY = "RESEARCH_HEAVY"
    UNSUPPORTED_TECH = "UNSUPPORTED_TECH"
    LOCATION_MISMATCH = "LOCATION_MISMATCH"
    MUST_HAVE_GAPS = "MUST_HAVE_GAPS"
    UNCLEAR_RESPONSIBILITIES = "UNCLEAR_RESPONSIBILITIES"


class QuestionCategory(str, Enum):
    RECRUITER = "Recruiter Screening"
    RESUME_DEEP_DIVE = "Resume Deep Dive"
    TECHNICAL_CONCEPT = "Technical Concept"
    IMPLEMENTATION = "Hands-on Implementation"
    SCENARIO = "Scenario & Problem Solving"
    PRODUCTION = "Production & Troubleshooting"
    SYSTEM_DESIGN = "System & Architecture Design"
    BEHAVIORAL_STAR = "Behavioral (STAR)"
    ROLE_MOTIVATION = "Company & Role Motivation"


class InterviewDifficulty(str, Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"


class LLMProviderType(str, Enum):
    GEMINI = "gemini"
    OLLAMA = "ollama"
    MOCK = "mock"


class ResumeStrategyType(str, Enum):
    AUTO = "AUTO"
    AI_DATA_ENGINEER = "AI_DATA_ENGINEER"
    DATA_ENGINEER = "DATA_ENGINEER"
    GENAI_ENGINEER = "GENAI_ENGINEER"
    GCP_DATA_ENGINEER = "GCP_DATA_ENGINEER"
    AI_ENGINEER = "AI_ENGINEER"
    DATA_SCIENTIST = "DATA_SCIENTIST"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            val_upper = value.upper().replace("-", "_").replace(" ", "_").replace("STRATEGY", "").strip("_")
            for member in cls:
                if member.value == val_upper or member.name == val_upper:
                    return member
            if "AI_DATA" in val_upper:
                return cls.AI_DATA_ENGINEER
            if "GENAI" in val_upper or "GEN_AI" in val_upper:
                return cls.GENAI_ENGINEER
            if "GCP" in val_upper:
                return cls.GCP_DATA_ENGINEER
            if "DATA_ENG" in val_upper:
                return cls.DATA_ENGINEER
            if "AI" in val_upper:
                return cls.AI_DATA_ENGINEER
        return cls.AI_DATA_ENGINEER


class TruthValidationStatus(str, Enum):
    PASS = "PASS"
    FLAG = "FLAG"
    BLOCK = "BLOCK"


class ClaimType(str, Enum):
    METRIC = "METRIC"
    TECHNOLOGY = "TECHNOLOGY"
    EXPERIENCE_TYPE = "EXPERIENCE_TYPE"
    RESPONSIBILITY = "RESPONSIBILITY"
    ROLE_TITLE = "ROLE_TITLE"
    TENURE = "TENURE"


class MatchLevel(str, Enum):
    EXACT_MATCH = "EXACT_MATCH"
    SYNONYM_MATCH = "SYNONYM_MATCH"
    SEMANTIC_MATCH = "SEMANTIC_MATCH"
    GAP = "GAP"


class KeywordDensityRisk(str, Enum):
    HEALTHY = "HEALTHY"
    LOW_COVERAGE = "LOW_COVERAGE"
    POTENTIAL_STUFFING = "POTENTIAL_STUFFING"


class FormattingRiskType(str, Enum):
    TABLE_LAYOUT = "TABLE_LAYOUT"
    MULTI_COLUMN = "MULTI_COLUMN"
    TEXT_BOX = "TEXT_BOX"
    HEADER_FOOTER_CONTENT = "HEADER_FOOTER_CONTENT"
    UNUSUAL_FONT = "UNUSUAL_FONT"
    INCONSISTENT_DATES = "INCONSISTENT_DATES"
    SUSPICIOUS_SPACING = "SUSPICIOUS_SPACING"
    EXCESSIVE_SYMBOLS = "EXCESSIVE_SYMBOLS"
    GENERAL = "GENERAL"


class SuggestionPriority(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class QuestionCategory(str, Enum):
    HR_SCREENING = "HR_SCREENING"
    RESUME_WALKTHROUGH = "RESUME_WALKTHROUGH"
    TECHNICAL_FUNDAMENTALS = "TECHNICAL_FUNDAMENTALS"
    JD_TECHNICAL = "JD_TECHNICAL"
    RESUME_DEEP_DIVE = "RESUME_DEEP_DIVE"
    PROJECT_DEEP_DIVE = "PROJECT_DEEP_DIVE"
    SCENARIO_BASED = "SCENARIO_BASED"
    SYSTEM_DESIGN = "SYSTEM_DESIGN"
    CLOUD = "CLOUD"
    DATA_ENGINEERING = "DATA_ENGINEERING"
    GENAI = "GENAI"
    RAG = "RAG"
    PYTHON = "PYTHON"
    SQL = "SQL"
    AIRFLOW = "AIRFLOW"
    BIGQUERY = "BIGQUERY"
    GCP = "GCP"
    BEHAVIORAL = "BEHAVIORAL"
    EXPERIENCE_GAP = "EXPERIENCE_GAP"
    FOLLOW_UP = "FOLLOW_UP"
    CANDIDATE_QUESTIONS = "CANDIDATE_QUESTIONS"
    CODING_CHALLENGE = "CODING_CHALLENGE"


class QuestionPriority(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class DifficultyLevel(str, Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"
    EXPERT = "EXPERT"


class AnswerLengthMode(str, Enum):
    SHORT = "SHORT"          # 30-45 seconds
    STANDARD = "STANDARD"    # 60-90 seconds
    DETAILED = "DETAILED"    # 2-3 minutes


class InterviewerPersona(str, Enum):
    RECRUITER = "RECRUITER"
    TECHNICAL_ENGINEER = "TECHNICAL_ENGINEER"
    SENIOR_ENGINEER = "SENIOR_ENGINEER"
    AI_ENGINEER = "AI_ENGINEER"
    DATA_ENGINEER = "DATA_ENGINEER"
    CLOUD_ENGINEER = "CLOUD_ENGINEER"
    HIRING_MANAGER = "HIRING_MANAGER"
    MANAGER = "MANAGER"


class MockInterviewMode(str, Enum):
    FULL_INTERVIEW = "FULL_INTERVIEW"
    TECHNICAL_ONLY = "TECHNICAL_ONLY"
    RESUME_DEEP_DIVE = "RESUME_DEEP_DIVE"
    PROJECT_DEEP_DIVE = "PROJECT_DEEP_DIVE"
    SYSTEM_DESIGN = "SYSTEM_DESIGN"
    BEHAVIORAL = "BEHAVIORAL"
    GENAI_RAG = "GENAI_RAG"
    DATA_ENGINEERING = "DATA_ENGINEERING"
    GCP_CLOUD = "GCP_CLOUD"
    WEAKNESS_FOCUS = "WEAKNESS_FOCUS"


class InterviewDifficulty(str, Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"
    EXPERT = "EXPERT"
    ADAPTIVE = "ADAPTIVE"


class HintMode(str, Enum):
    NO_HINT = "NO_HINT"
    SMALL_HINT = "SMALL_HINT"
    FULL_HINT = "FULL_HINT"


class FeedbackMode(str, Enum):
    INTERVIEW_MODE = "INTERVIEW_MODE"
    COACHING_MODE = "COACHING_MODE"


class SessionStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"


class EvaluationDimension(str, Enum):
    TECHNICAL_CORRECTNESS = "TECHNICAL_CORRECTNESS"
    RELEVANCE = "RELEVANCE"
    COMPLETENESS = "COMPLETENESS"
    DEPTH = "DEPTH"
    EVIDENCE_GROUNDING = "EVIDENCE_GROUNDING"
    COMMUNICATION_CLARITY = "COMMUNICATION_CLARITY"
    STRUCTURE = "STRUCTURE"
    CONFIDENCE = "CONFIDENCE"
    CONCRETE_EXAMPLES = "CONCRETE_EXAMPLES"
    FOLLOW_UP_HANDLING = "FOLLOW_UP_HANDLING"


class AppEnvironmentMode(str, Enum):
    DEMO = "DEMO"
    LOCAL_PRIVATE = "LOCAL_PRIVATE"
    HOSTED_PRIVATE = "HOSTED_PRIVATE"


class HealthStatus(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"





