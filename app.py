import smtplib
from email.header import Header
from email.mime.text import MIMEText

import streamlit as st
from google import genai
from google.genai import types

from prompts import SUMMARY_REQUEST_PROMPT, SYSTEM_PROMPT, WELCOME_MESSAGE_TEMPLATE

MODEL_NAME = "gemini-3.5-flash"
EXPERIENCE_LEVELS = ["Fresher (0-1 yrs)", "Junior (1-3 yrs)", "Mid-level (3+ yrs)"]

st.set_page_config(page_title="InterviewSnap", page_icon="🎯")

try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    GMAIL_ADDRESS = st.secrets["GMAIL_ADDRESS"]
    GMAIL_APP_PASSWORD = st.secrets["GMAIL_APP_PASSWORD"].replace(" ", "")
except (KeyError, FileNotFoundError):
    st.error(
        "Secrets missing. Copy .streamlit/secrets.toml.example to "
        ".streamlit/secrets.toml and fill in your real values."
    )
    st.stop()


@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=GEMINI_API_KEY)


gemini_client = get_gemini_client()


def create_chat(name, level):
    system_instruction = (
        f"{SYSTEM_PROMPT}\n\nCandidate name: {name}\nExperience level: {level}"
    )
    return gemini_client.chats.create(
        model=MODEL_NAME,
        config=types.GenerateContentConfig(system_instruction=system_instruction),
    )


def render_message(message):
    with st.chat_message(message["role"]):
        if message["kind"] == "text":
            st.write(message["content"])
        elif message["kind"] == "image":
            st.image(message["content"])


def add_message(role, kind, content):
    st.session_state.messages.append({"role": role, "kind": kind, "content": content})
    render_message(st.session_state.messages[-1])


def ask_gemini(parts):
    try:
        return st.session_state.chat.send_message(parts).text
    except Exception as error:
        return f"Sorry, something went wrong: {error}"


def is_valid_email(email):
    return "@" in email and "." in email.split("@")[-1]


def send_email(to_address, subject, body):
    message = MIMEText(body, "plain", "utf-8")
    message["Subject"] = Header(subject, "utf-8")
    message["From"] = GMAIL_ADDRESS
    message["To"] = to_address

    errors = []

    # Attempt 1: SSL on port 465
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(message)
        return True, "sent"
    except Exception as error:
        errors.append(f"port 465: {error}")

    # Attempt 2: STARTTLS on port 587
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(message)
        return True, "sent"
    except Exception as error:
        errors.append(f"port 587: {error}")

    return False, " | ".join(errors)


# Onboarding
if "onboarded" not in st.session_state:
    st.title("🎯 InterviewSnap")
    st.caption("Snap the job post. Practise the interview. Email yourself the prep sheet.")
    with st.form("onboarding_form"):
        name = st.text_input("Your name")
        email = st.text_input(
            "Your email address",
            placeholder="you@example.com",
            help="Your prep sheet will be sent to this address.",
        )
        level = st.selectbox("Experience level", EXPERIENCE_LEVELS)
        submitted = st.form_submit_button("Start practising 🚀")
    if submitted:
        if not name.strip() or not email.strip():
            st.warning("Please fill in both your name and email address.")
        elif not is_valid_email(email.strip()):
            st.warning("Please enter a valid email address.")
        else:
            st.session_state.name = name.strip()
            st.session_state.email = email.strip()
            st.session_state.level = level
            st.session_state.chat = create_chat(name.strip(), level)
            st.session_state.messages = []
            st.session_state.onboarded = True
            st.rerun()
    st.stop()

# Sidebar (always visible, so the email button never scrolls away)
with st.sidebar:
    st.subheader("Session")
    st.write(f"👤 {st.session_state.name}")
    st.write(f"📧 {st.session_state.email}")
    st.write(f"🎓 {st.session_state.level}")

    has_user_message = any(m["role"] == "user" for m in st.session_state.messages)
    if st.button(
        "📧 Send prep sheet to Email",
        disabled=not has_user_message,
        use_container_width=True,
        type="primary",
    ):
        with st.spinner("Preparing your prep sheet..."):
            summary = ask_gemini([SUMMARY_REQUEST_PROMPT])
        success, info = send_email(
            st.session_state.email,
            "Your InterviewSnap prep sheet 🎯",
            f"Hi {st.session_state.name},\n\nHere is your interview prep sheet:\n\n{summary}\n\nAll the best!\n- InterviewSnap",
        )
        if success:
            st.session_state.last_summary = summary
            st.session_state.pop("failed_summary", None)
            st.success("Sent! Check your inbox 📬")
        else:
            # Keep the prep sheet so the user can still download it
            st.session_state.failed_summary = summary
            st.error(f"Couldn't send that: {info}")

    # Backup: shown after a failed send, and stays visible across reruns
    if "failed_summary" in st.session_state:
        st.download_button(
            "⬇️ Download prep sheet instead",
            data=st.session_state.failed_summary,
            file_name="InterviewSnap_prep_sheet.txt",
            mime="text/plain",
            use_container_width=True,
        )

    if st.button("🔄 New interview", use_container_width=True):
        st.session_state.chat = create_chat(
            st.session_state.name, st.session_state.level
        )
        st.session_state.messages = []
        st.session_state.pop("last_summary", None)
        st.session_state.pop("failed_summary", None)
        st.rerun()

    if "last_summary" in st.session_state:
        with st.expander("View the prep sheet that was sent"):
            st.text(st.session_state.last_summary)

# Main area
st.title("🎯 InterviewSnap")

# Chat history
if not st.session_state.messages:
    add_message(
        "assistant",
        "text",
        WELCOME_MESSAGE_TEMPLATE.format(name=st.session_state.name),
    )
else:
    for message in st.session_state.messages:
        render_message(message)

# Input: text and/or job description screenshot
user_input = st.chat_input(
    "Paste a job description, attach a screenshot, or answer the question",
    accept_file=True,
    file_type=["jpg", "jpeg", "png"],
)

if user_input:
    photo = user_input.files[0] if user_input.files else None
    text = user_input.text
    parts = []

    if photo is not None:
        photo_bytes = photo.getvalue()
        add_message("user", "image", photo_bytes)
        parts.append(types.Part.from_bytes(data=photo_bytes, mime_type=photo.type))
    if text:
        add_message("user", "text", text)
        parts.append(text)
    elif photo is not None:
        parts.append(
            "This is a job description screenshot. Summarise the role and "
            "start my mock interview with the first question."
        )

    with st.spinner("Thinking..."):
        answer = ask_gemini(parts)
    add_message("assistant", "text", answer)
    st.rerun()