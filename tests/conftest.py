import pytest
from pathlib import Path
from careerpilot.core.config import settings
from careerpilot.parsers.candidate_parser import CandidateParser
from careerpilot.parsers.jd_parser import JobDescriptionParser
from careerpilot.models.candidate import CandidateProfile
from careerpilot.models.job import JobDescription


@pytest.fixture(scope="session")
def sample_candidate_path() -> Path:
    return settings.SAMPLE_DATA_DIR / "sample_candidate_profile.json"


@pytest.fixture(scope="session")
def sample_ai_jd_path() -> Path:
    return settings.SAMPLE_DATA_DIR / "sample_jds" / "ai_engineer_jd.txt"


@pytest.fixture(scope="session")
def sample_data_eng_jd_path() -> Path:
    return settings.SAMPLE_DATA_DIR / "sample_jds" / "data_engineer_jd.txt"


@pytest.fixture(scope="session")
def sample_candidate(sample_candidate_path: Path) -> CandidateProfile:
    return CandidateParser.from_json_file(sample_candidate_path)


@pytest.fixture(scope="session")
def sample_ai_jd(sample_ai_jd_path: Path) -> JobDescription:
    return JobDescriptionParser.parse_file(sample_ai_jd_path)


@pytest.fixture(scope="session")
def sample_data_eng_jd(sample_data_eng_jd_path: Path) -> JobDescription:
    return JobDescriptionParser.parse_file(sample_data_eng_jd_path)
