# CareerPilot AI — Milestone 13 Architecture & Verification Report
## Secure Authentication, Multi-Device Access & Production Data Isolation

---

### Executive Summary

Milestone 13 introduces **secure authentication, session management, multi-device access, and complete production data isolation** into the CareerPilot AI platform. 

Prior to Milestone 13, CareerPilot stored candidate data dynamically in SQLite and ChromaDB with verified fact provenance, but lacked an authentication perimeter and relied on hardcoded identifier defaults (`"trupti_kularkar"`, `"Truptikularkar"`, and static LinkedIn URLs) across external integrations and repositories. 

Milestone 13 eliminates all hardcoded identity dependencies, replaces insecure network configurations with official CA-validated SSL contexts, adds high-entropy cryptographic sessions and RFC 9106 Argon2id password hashing, enforces strict candidate-level data isolation across SQLite ground truth and RAG stores, and expands application tracking to an authoritative 17-stage recruitment lifecycle.

**Full Regression Verification Result:**
- **226 / 226 tests passing** (100% success rate, 0 regressions against baseline 209 tests).

---

### 1. Security & Authentication Architecture

#### 1.1 Argon2id Password Hashing (RFC 9106)
- Implemented via `argon2-cffi` using the `PasswordHasher` standard parameters:
  - **Memory Cost (`m`):** 65,536 KiB (64 MiB)
  - **Time Cost (`t`):** 3 iterations
  - **Parallelism (`p`):** 4 threads
  - **Format:** `$argon2id$v=19$m=65536,t=3,p=4$...`
- **Security Attributes:**
  - Memory-hard algorithm providing optimal resistance against GPU and ASIC brute-force attacks.
  - Constant-time verification (`verify_password`) preventing timing side-channel analysis.
  - Zero plain-text persistence: Passwords are never saved to SQLite, logged to console, or transmitted in domain models.

#### 1.2 Password Complexity Enforcement
Passwords must satisfy enterprise strength requirements before acceptance:
- Minimum length of 8 characters.
- At least one uppercase alphabetic character (`[A-Z]`).
- At least one lowercase alphabetic character (`[a-z]`).
- At least one numeric digit (`[0-9]`).
- At least one special character (`[!@#$%^&*()-_=+...`).

#### 1.3 High-Entropy Cryptographic Session Tokens
- Tokens are generated using `secrets.token_urlsafe(32)` providing 256 bits of cryptographic entropy.
- **Token Hashing at Rest:** The raw session token is returned only once to the client (stored in Streamlit session state) and is **never stored in plaintext in the database**. The database stores only the SHA-256 hash (`token_hash`) of the token.
- **Session Validation:** When an incoming request presents a token, `AuthService.validate_session(token)` hashes the token and queries active, non-expired sessions in `user_sessions`. If expired, the session is immediately invalidated (`is_active = False`).
- **Session Expiry:** Configured with a default TTL of 7 days (168 hours) with sliding `last_activity_at` updates.

#### 1.4 Multi-Device Access (Laptop + Mobile Phone)
- CareerPilot supports multiple concurrent active sessions per user account.
- When logging in from a laptop (`ThinkPad / Windows 11 Chrome`) and a smartphone (`iPhone 15 / Safari Mobile`), independent session records are created in `user_sessions`.
- **Granular Session Revocation:** Logging out from a laptop revokes only the laptop's session token; the mobile device remains active and authenticated.
- **Global Invalidation on Password Change:** When a user changes their password, they can choose to revoke all other active sessions across devices while keeping their current session alive.

---

### 2. Database Schema & Data Isolation

#### 2.1 Schema Upgrades (`careerpilot/db/schema.py`)

##### `UserDB` (`users` table)
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `VARCHAR` | Primary Key | `usr_<12hex>` |
| `email` | `VARCHAR` | Unique, Indexed, Non-null | User login email (normalized lowercase) |
| `password_hash` | `VARCHAR` | Non-null | Argon2id hash string |
| `full_name` | `VARCHAR` | Non-null | User full legal name |
| `is_active` | `BOOLEAN` | Default `True` | Account activation flag |
| `last_login_at` | `DATETIME` | Nullable | Timestamp of latest login |
| `created_at` | `DATETIME` | Default `utc_now` | Account creation timestamp |
| `updated_at` | `DATETIME` | Default `utc_now` | Last update timestamp |

##### `UserSessionDB` (`user_sessions` table)
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `VARCHAR` | Primary Key | `sess_<12hex>` |
| `user_id` | `VARCHAR` | ForeignKey(`users.id`), Indexed | Owning user account |
| `token_hash` | `VARCHAR` | Unique, Indexed, Non-null | SHA-256 digest of session token |
| `device_info` | `VARCHAR` | Non-null | Device identifier (e.g. Laptop, iPhone) |
| `ip_address` | `VARCHAR` | Nullable | Client IP address |
| `expires_at` | `DATETIME` | Indexed, Non-null | Expiration boundary timestamp |
| `is_active` | `BOOLEAN` | Default `True` | Session validity flag |
| `created_at` | `DATETIME` | Default `utc_now` | Session start timestamp |
| `last_activity_at`| `DATETIME` | Default `utc_now` | Most recent activity timestamp |

##### `CandidateProfileDB` (`candidate_profiles` table)
- Added `user_id` (`VARCHAR`, `ForeignKey("users.id")`, nullable=True) column establishing a 1-to-1 relationship between `UserDB` and `CandidateProfileDB`.
- Seeded verified candidate (`cand_verified` / `trupti_kularkar`) is automatically linked to default user `kularkartrupti@gmail.com`.

#### 2.2 Strict Production Data Scoping

All data access repositories now scope data by candidate ID and verify permissions:

1. **`ApplicationRepository`**:
   - `create_application`: Attaches `candidate_id` to `ApplicationDB`.
   - `list_applications`: Filters by `candidate_id`.
   - `get_application`: Enforces `candidate_id` match.
   - `update_status` & `update_decision`: Raises `PermissionError` if an unauthorized user attempts to update another candidate's application.
2. **`ResumeRepository`**:
   - `save_resume_version` & `list_versions_for_job`: Strictly partitioned by `candidate_id`.
3. **`CandidateRepository`**:
   - `get_profile(candidate_id, user_id)`: Resolves candidate profile by authenticated user account ID or candidate ID.
4. **`AnalyticsRepository`**:
   - Metrics, pipeline conversions, and career intelligence insights accept `candidate_id` and aggregate only records belonging to the authenticated user.

---

### 3. Connector Security & External Profiles Hardening

#### 3.1 GitHub Connector (`careerpilot/integrations/github_connector.py`)
- **Elimination of Hardcoded Identity:** Removed `DEFAULT_USERNAME = "Truptikularkar"`. Added `resolve_username()` dynamically inspecting the candidate's database profile, arguments, or fallback.
- **SSL Certificate Verification:** Replaced insecure SSL contexts with `ssl.create_default_context(cafile=certifi.where())` using `certifi` CA root bundles. Prohibits `CERT_NONE`.
- **Token Passing:** Personal Access Tokens (`token` or `github_token`) are securely forwarded in `Authorization: Bearer <token>` headers without logging.

#### 3.2 LinkedIn Connector (`careerpilot/integrations/linkedin_connector.py`)
- **Zero Scraping Policy Enforced:** Browser automation is strictly prohibited (`scraping_permitted: False`).
- **Dynamic Profile Resolution:** `resolve_profile_url()` resolves URLs from the candidate record or explicit parameter rather than static defaults.
- **Manual Data Archive Ingestion:** Ingests official candidate data archives (`parse_manual_csv_export`, `import_manual_profile_text`) mapping records into `CandidateEvidenceDB` with `ProvenanceSourceType.LINKEDIN_EXPORT`.

#### 3.3 Naukri Connector (`careerpilot/integrations/naukri_connector.py`)
- Maintained zero-scraping compliance, with structured manual resume / job profile parsing.

#### 3.4 Canonical Cross-Source Job Deduplication (`careerpilot/analysis/job_deduplicator.py`)
- **Canonical URL Normalization:** `JobDeduplicator.normalize_url()` strips tracking tokens, query parameters (`refId`, `trackingId`), and trailing slashes.
- **Cross-Source Match Detection:** When a job is posted on both LinkedIn and Naukri (or Direct Company Portal), `JobDeduplicationRepository.find_canonical_match()` checks `source_url` against `CanonicalJobDB.source_urls_json`. Matches are assigned `match_type = "CANONICAL_URL_EXACT"` and unified under a single canonical job record.

---

### 4. Authoritative 17-Status Recruitment Lifecycle

The `ApplicationStatus` enum in `careerpilot/core/constants.py` was standardized into 17 authoritative lifecycle stages:

```
[DISCOVERED] -> [ANALYZED] -> [SAVED] -> [APPLIED] -> [ACKNOWLEDGED]
       |
       v
  [SCREENING] -> [OA] -> [INTERVIEWING]
                            |
           +----------------+---------------+
           |                |               |
           v                v               v
    [TECHNICAL_ROUND]  [HR_ROUND]    [FINAL_ROUND]
           |                |               |
           +----------------+---------------+
                            |
                            v
                         [OFFER] -> [ACCEPTED]
                            |
           +----------------+---------------+
           |                |               |
           v                v               v
      [REJECTED]       [WITHDRAWN]       [ON_HOLD] / [NO_RESPONSE]
```

**Backwards Compatibility:**
The enum utilizes an intelligent `_missing_` class method normalizing legacy strings:
- `"Interview"` -> `ApplicationStatus.INTERVIEWING`
- `"oa_scheduled"` / `"oa_submitted"` -> `ApplicationStatus.OA`
- `"technical_interview"` / `"system_design"` -> `ApplicationStatus.TECHNICAL_ROUND`
- `"behavioral_round"` / `"hr_interview"` -> `ApplicationStatus.HR_ROUND`
- `"SAVED_FOR_LATER"` -> `ApplicationStatus.SAVED`
- `"applying"` -> `ApplicationStatus.APPLIED`
- `"skipped"` -> `ApplicationStatus.WITHDRAWN`
- `"resume_viewed"` -> `ApplicationStatus.ACKNOWLEDGED`
- `"offer_received"` -> `ApplicationStatus.OFFER`

---

### 5. Streamlit UI Gatekeeper & Account Management

1. **`careerpilot/ui/auth_view.py`**:
   - Modern, branded authentication screen rendered when unauthenticated.
   - Separate tabs for **Sign In** (with device type selector: Laptop / Mobile / Tablet) and **Create Account**.
   - Clear guidance on password requirements and forgot password notices.
2. **`careerpilot/ui/app.py`**:
   - Integrates `AuthService.require_auth()`. If the user is unauthenticated, halts execution and renders `auth_view.py`.
   - Sidebar displays user status (`🟢 Authenticated: <Name>`), email, active candidate profile, and a one-click **Sign Out** button.
3. **`careerpilot/ui/pages/10_Settings.py`**:
   - Added **🔐 Account & Multi-Device Security** section.
   - Displays active account identifier, session status, and password update form with option to revoke other device sessions.
4. **All 12 Sub-Pages Protected**:
   - Auth guards (`AuthService.require_auth()`) injected across all 12 Streamlit application pages in `careerpilot/ui/pages/`.

---

### 6. Test Suite & Verification Summary

#### 6.1 Milestone 13 Test Suite (`tests/test_milestone_13.py`)
| Test Name | Focus Area | Status |
| :--- | :--- | :--- |
| `test_user_registration_and_argon2id_hashing` | Argon2id `$argon2id$v=19$` format, cost params, hash verification | **PASSED** |
| `test_password_strength_validation` | Enforces 8+ chars, uppercase, lowercase, digit, special character | **PASSED** |
| `test_duplicate_registration_fails` | Prevents registering existing email address | **PASSED** |
| `test_login_success_and_session_token_generation` | Token entropy >= 32 bytes, SHA-256 token hash stored | **PASSED** |
| `test_login_invalid_password_fails` | Rejects incorrect password with clean error | **PASSED** |
| `test_login_unknown_email_fails` | Rejects non-existent email | **PASSED** |
| `test_multi_device_login_and_independent_sessions`| Concurrent Laptop + Mobile sessions, independent token revocation | **PASSED** |
| `test_session_expiration_fails` | Auto-invalidates expired sessions | **PASSED** |
| `test_password_change_with_verification_and_session_revocation`| Password change, old password invalidation, multi-session revocation | **PASSED** |
| `test_cross_user_isolation_candidate_profile` | User A and User B have separate candidate ground truth | **PASSED** |
| `test_cross_user_isolation_applications` | User B cannot view or update User A's applications (`PermissionError`) | **PASSED** |
| `test_cross_user_isolation_resume_versions` | Resume snapshots isolated by candidate ID | **PASSED** |
| `test_github_connector_dynamic_username_and_ssl_safety` | Dynamic username resolution, certifi SSL context, token forwarding | **PASSED** |
| `test_linkedin_connector_dynamic_profile_url` | Dynamic URL resolution, zero-scraping compliance | **PASSED** |
| `test_enhanced_cross_source_job_deduplication` | Canonical URL normalization, cross-source matching | **PASSED** |
| `test_application_status_17_lifecycle_and_legacy_mapping` | All 17 authoritative statuses, alias mapping | **PASSED** |
| `test_default_verified_user_auto_seeded` | Auto-seeding of `kularkartrupti@gmail.com` linked to `cand_verified` | **PASSED** |

#### 6.2 Full Regression Test Suite Execution
- **Total Tests Executed:** 226
- **Passed:** 226
- **Failed:** 0
- **Duration:** 70.04s
- **Zero regressions** against Milestone 12 and previous milestones.

---

### 7. Multi-Device Deployment Guide (Laptop & Mobile Access)

To access CareerPilot from both your laptop and smartphone:

1. **Local Access (Laptop):**
   ```bash
   streamlit run careerpilot/ui/app.py
   ```
   Open `http://localhost:8501` in your desktop browser.

2. **LAN Multi-Device Access (Laptop + Phone on Same Wi-Fi):**
   ```bash
   streamlit run careerpilot/ui/app.py --server.address=0.0.0.0 --server.port=8501
   ```
   - On Laptop: Open `http://localhost:8501`
   - On Mobile Phone: Open `http://<LAPTOP_LOCAL_IP>:8501` (e.g., `http://192.168.1.15:8501`)
   - Sign in using your CareerPilot account credentials. Both devices share the same SQLite database and live candidate status.

3. **Production / Hosted Deployment:**
   - Configure reverse proxy (Nginx / Caddy / Cloudflare Tunnel) with HTTPS TLS termination.
   - Set environment variable: `CAREERPILOT_MODE=HOSTED_PRIVATE`.
