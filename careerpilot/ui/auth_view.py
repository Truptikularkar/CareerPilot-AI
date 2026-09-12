import streamlit as st
from careerpilot.services.auth_service import AuthService
from careerpilot.models.auth import UserCreate
from careerpilot.core.config import settings
from careerpilot.core.logging import get_logger

logger = get_logger("careerpilot.ui.auth")


def render_login_page():
    """
    Renders the dedicated CareerPilot Login & Sign Up view.
    Used as an authentication gatekeeper in app.py.
    """
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="font-size: 2.6rem; color: #1E293B; margin-bottom: 0.2rem;">🚀 CareerPilot AI</h1>
        <p style="font-size: 1.15rem; color: #64748B; margin-bottom: 0.5rem;">Your Career Intelligence & Personal Job Agent</p>
        <span style="background-color: #E0E7FF; color: #3730A3; padding: 4px 12px; border-radius: 12px; font-weight: 600; font-size: 0.85rem;">
            SECURE AUTHENTICATION & MULTI-DEVICE SESSION
        </span>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        tab_login, tab_signup = st.tabs(["🔑 Sign In", "📝 Create Account"])

        with tab_login:
            st.markdown("### Welcome Back")
            st.caption("Sign in to access your candidate profile, tailored resumes, and applications.")

            st.info(
                "💡 **Sign In Credentials:**\n\n"
                "- **Email:** `kularkartrupti123@gmail.com`\n"
                "- **Password:** `9834055766@Liza`\n\n"
                "*Pre-filled below for instant access. Or click **'📝 Create Account'** to create or reset with your own password.*"
            )

            with st.form("login_form"):
                email = st.text_input("Email Address:", value="kularkartrupti123@gmail.com").strip()
                password = st.text_input("Password:", type="password", value="9834055766@Liza").strip()
                device_type = st.selectbox(
                    "Device Type:",
                    ["Desktop / Laptop", "Mobile Phone", "Tablet / Workstation"],
                    index=0,
                )
                submitted = st.form_submit_button("Sign In to CareerPilot", type="primary", use_container_width=True)

                if submitted:
                    if not email or not password:
                        st.error("Please enter both email and password.")
                    else:
                        with st.spinner("Verifying credentials with Argon2id..."):
                            try:
                                user, token = AuthService.authenticate(
                                    email=email,
                                    password=password,
                                    device_info=device_type,
                                )
                                st.session_state["authenticated_user"] = user
                                st.session_state["authenticated_candidate_id"] = user.candidate_id
                                st.session_state["auth_session_token"] = token
                                st.success(f"✓ Welcome back, {user.full_name}!")
                                st.rerun()
                            except ValueError as e:
                                st.error(f"Authentication Failed: {e}")
                            except Exception as e:
                                logger.error(f"Unexpected login error: {e}")
                                st.error("An error occurred during authentication. Please try again.")

            with st.expander("ℹ️ Forgot Password?"):
                st.info(
                    "**Automated Password Reset Notice:**\n\n"
                    "Automated email recovery requires an enterprise SMTP email gateway, which is scheduled for future cloud deployments. "
                    "In local and private installations, you can change your password securely while logged in under **Settings**, "
                    "or sign in with your default verified account."
                )

        with tab_signup:
            st.markdown("### Create or Reset Account")
            st.caption("Register an account or reset password for your candidate profile.")

            st.info("💡 You can register a new account or set a new password for `kularkartrupti123@gmail.com` below.")

            with st.form("signup_form"):
                reg_name = st.text_input("Full Name:", value="Trupti Kularkar").strip()
                reg_email = st.text_input("Email Address:", value="kularkartrupti123@gmail.com").strip()
                reg_password = st.text_input("New Password (min 8 chars, letters & numbers):", type="password")
                reg_confirm = st.text_input("Confirm Password:", type="password")

                reg_submit = st.form_submit_button("Save Account & Sign In", type="primary", use_container_width=True)

                if reg_submit:
                    if not reg_name or not reg_email or not reg_password:
                        st.error("All fields are required.")
                    elif reg_password != reg_confirm:
                        st.error("Passwords do not match.")
                    else:
                        try:
                            user_in = UserCreate(
                                email=reg_email,
                                password=reg_password,
                                full_name=reg_name,
                            )
                            with st.spinner("Creating secure account..."):
                                new_user = AuthService.register_user(user_in)
                                # Automatically log in
                                user, token = AuthService.authenticate(
                                    email=reg_email,
                                    password=reg_password,
                                    device_info="Desktop / Laptop",
                                )
                                st.session_state["authenticated_user"] = user
                                st.session_state["authenticated_candidate_id"] = user.candidate_id
                                st.session_state["auth_session_token"] = token
                                st.success(f"✓ Account created! Welcome, {new_user.full_name}.")
                                st.rerun()
                        except ValueError as e:
                            st.error(f"Registration Failed: {e}")
                        except Exception as e:
                            logger.error(f"Unexpected signup error: {e}")
                            st.error(f"Failed to create account: {e}")
