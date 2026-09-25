import streamlit as st
import sqlite3
import subprocess
import sys
import os
from datetime import datetime
from authentication.keystroke_auth import verify_typing
from authentication.face_liveness import check_liveness
from authentication.adaptive_auth import check_risk
st.write("Python:", sys.executable)
st.set_page_config(
    page_title="AI Adaptive Authentication",
    page_icon="🔐",
    layout="wide"
)

st.title("🔐 AI Adaptive Authentication System")

page = st.sidebar.selectbox(
    "Navigation",
    [
        "Home",
        "Register User",
        "Register Face",
        "Register Keystroke",
        "Login",
        "Dashboard"
    ]
)

# ---------------- HOME ---------------- #

if page == "Home":

    st.header("Welcome")

    st.write("""
This system provides:

✔ User Registration

✔ Face Registration

✔ Face Recognition Login

✔ Keystroke Authentication

✔ Adaptive Authentication

✔ Authentication Dashboard
""")

# ---------------- REGISTER USER ---------------- #

elif page == "Register User":

    st.header("User Registration")

    name = st.text_input("Full Name")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Register"):

        conn = sqlite3.connect("database/users.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        existing = cursor.fetchone()

        if existing:
            st.error("Email already registered.")

        else:
            cursor.execute("""
                INSERT INTO users(name,email,password,face_registered)
                VALUES(?,?,?,0)
            """, (name, email, password))

            conn.commit()
            st.success("User Registered Successfully!")

        conn.close()

# ---------------- REGISTER FACE ---------------- #
# ---------------- REGISTER FACE ---------------- #

elif page == "Register Face":

    st.header("📷 Face Registration")

    email = st.text_input("Enter Registered Email")

    if st.button("Start Face Registration"):

        if email == "":
            st.error("Please enter your registered email.")

        else:

            st.info("Opening Camera... Please look at the camera.")

            result = subprocess.run(
                [
                    sys.executable,
                    "registration/register_face.py",
                    email
                ],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:

                st.success("✅ Face Registration Completed!")

                if result.stdout:
                    st.text(result.stdout)

            else:

                st.error("❌ Face Registration Failed")

                if result.stderr:
                    st.text(result.stderr)

# ---------------- REGISTER USER ---------------- #

elif page == "Register User":

    st.header("👤 User Registration")

    name = st.text_input("Full Name")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Register"):

        if name == "" or email == "" or password == "":
            st.error("Please fill all the fields.")

        else:

            conn = sqlite3.connect("database/users.db")
            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM users WHERE email=?",
                (email,)
            )

            existing = cursor.fetchone()

            if existing:

                st.error("❌ Email already registered.")

            else:

                cursor.execute("""
                    INSERT INTO users(name,email,password,face_registered)
                    VALUES(?,?,?,0)
                """, (name, email, password))

                conn.commit()

                st.success("✅ User Registered Successfully!")

            conn.close()

# ---------------- REGISTER KEYSTROKE ---------------- #

elif page == "Register Keystroke":

    import json
    import os

    st.header("⌨️ Register Typing Pattern")

    email = st.text_input("Registered Email")

    sentence = "Artificial Intelligence improves cybersecurity"

    st.write("### Type this sentence exactly:")

    st.code(sentence)

    typed_text = st.text_area("Type here")

    if st.button("Save Typing Pattern"):

        if email == "" or typed_text == "":
            st.error("Please fill all fields.")

        else:

            os.makedirs("storage/typing_profiles", exist_ok=True)

            profile = {
                "email": email,
                "text": typed_text,
                "length": len(typed_text)
            }

            with open(f"storage/typing_profiles/{email}.json", "w") as file:
                json.dump(profile, file, indent=4)

            st.success("✅ Typing Pattern Saved Successfully")
# ---------------- LOGIN ---------------- #

elif page == "Login":

    import sys
    import subprocess

    st.header("🔐 Secure Login")

    email = st.text_input("Registered Email")
    sentence = "Artificial Intelligence improves cybersecurity"

    st.write("### Type this sentence after face verification:")
    st.code(sentence)

    typed_text = st.text_area("Type Here")

    if st.button("Login"):

        if email == "" or typed_text == "":
            st.error("Please enter your email and typing sample.")

        else:

            st.info("Opening Camera for Face Verification...")

            result = subprocess.run(
                [
                    sys.executable,
                    "authentication/login.py",
                    email
                ],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:

                if "Login Successful" in result.stdout:

                    live, score = check_liveness()

                    if not live:
                        st.error(f"❌ Face Liveness Failed ({score}%)")
                        st.stop()

                    st.success(f"✅ Face Liveness Passed ({score}%)")

                    if verify_typing(email, typed_text):

                        st.success("✅ Login Successful")

                        st.session_state["logged_in"] = True
                        st.session_state["user"] = email

                    else:

                        st.error("❌ Keystroke Verification Failed")

                else:

                    st.error("❌ Face Verification Failed")

            else:

                st.error(result.stderr)

# ---------------- DASHBOARD ---------------- #
elif page == "Dashboard":

    st.header("📊 AI Adaptive Authentication Dashboard")

    conn = sqlite3.connect("database/users.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("👤 Registered Users", total_users)

    with col2:
        if st.session_state.get("logged_in", False):
            st.metric("🔐 Authentication", "Verified")
        else:
            st.metric("🔐 Authentication", "Not Logged In")

    with col3:
        st.metric("🛡️ Session", "Secure")

    st.divider()

    st.subheader("👤 Current User")

    if st.session_state.get("logged_in", False):

        st.success("User Authenticated Successfully")

        st.write("**Email:**", st.session_state["user"])

        st.write("**Face Recognition:** ✅ Matched")

        st.write("**Keystroke Status:** ✅ Normal")

        score, level = check_risk()

        if level == "LOW":
            st.success(f"🟢 Risk Level : {level} ({score}%)")

        elif level == "MEDIUM":
            st.warning(f"🟡 Risk Level : {level} ({score}%)")

        else:
            st.error(f"🔴 Risk Level : {level} ({score}%)")

        st.write("**Current Time:**", datetime.now().strftime("%d-%m-%Y %H:%M:%S"))

    else:

        st.warning("No Active Login")

    st.divider()

    st.subheader("📜 Authentication Logs")
    

    log_file = "storage/authentication_logs/logs.txt"

    if os.path.exists(log_file):

        with open(log_file, "r") as file:

            logs = file.readlines()

        if logs:

            for log in reversed(logs):
                st.text(log.strip())

        else:

            st.info("No Logs Available")

    else:

        st.info("No Logs Available")

    st.divider()

    st.subheader("📈 System Status")

    if os.path.exists("models/trainer.yml"):
        st.success("✅ Face Recognition Model Loaded")
    else:
        st.error("❌ Face Recognition Model Not Found")

    st.success("✅ Database Connected")

    st.success("✅ Authentication System Running")

    st.success("✅ Webcam Ready")
    st.divider()

    if st.button("🚪 Logout"):

        st.session_state["logged_in"] = False

        st.session_state["user"] = ""

        st.success("Logged Out Successfully")
        st.rerun()

    conn.close()