"""
sample_data.py

Contains the five synthetic ArcVault requests from the assessment.
s
These sample requests are used for:
- local testing
- batch processing
- the Streamlit demo
- the FastAPI batch endpoint
"""

from app.schemas import CustomerRequest, RequestSource


# Five required sample requests from the assessment.
SAMPLE_REQUESTS = [
    CustomerRequest(
        request_id="REQ-001",
        source=RequestSource.EMAIL,
        raw_message=(
            "Hi, I tried logging in this morning and keep getting a 403 error. "
            "My account is arcvault.io/user/jsmith. This started after your update last Tuesday."
        ),
    ),
    CustomerRequest(
        request_id="REQ-002",
        source=RequestSource.WEB_FORM,
        raw_message=(
            "We'd love to see a bulk export feature for our audit logs. "
            "We're a compliance-heavy org and this would save us hours every month."
        ),
    ),
    CustomerRequest(
        request_id="REQ-003",
        source=RequestSource.SUPPORT_PORTAL,
        raw_message=(
            "Invoice #8821 shows a charge of $1,240 but our contract rate is $980/month. "
            "Can someone look into this?"
        ),
    ),
    CustomerRequest(
        request_id="REQ-004",
        source=RequestSource.EMAIL,
        raw_message=(
            "I'm not sure if this is the right place to ask, but is there a way to set up SSO with Okta? "
            "We're evaluating switching our auth provider."
        ),
    ),
    CustomerRequest(
        request_id="REQ-005",
        source=RequestSource.WEB_FORM,
        raw_message=(
            "Your dashboard stopped loading for us around 2pm EST. "
            "Checked our end — it's definitely on yours. Multiple users affected."
        ),
    ),
]