"""
Modules Package Initialization for GRE Enterprise Platform.
Exposes core service engines for analytics, email, questions, testing, and UI timers.
"""

from .analytics_engine import get_student_performance_telemetry
from .email_service import send_verification_email, verify_email_token
from .question_engine import seed_initial_question_bank
from .testing_engine import initialize_test_session, get_safe_active_section_payload, submit_answer_atomically
from .timer import render_isolated_timer

__all__ = [
    "get_student_performance_telemetry",
    "send_verification_email",
    "verify_email_token",
    "seed_initial_question_bank",
    "initialize_test_session",
    "get_safe_active_section_payload",
    "submit_answer_atomically",
    "render_isolated_timer",
]
