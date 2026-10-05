import streamlit as st
import sqlite3
import subprocess
import sys
import os
from datetime import datetime
from authentication.face_liveness import check_liveness
from authentication.keystroke_auth import verify_typing
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
    "Secure Workspace",
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
    import time

    st.header("⌨️ Register Typing Pattern")

    email = st.text_input("Registered Email")

    sentence = "Artificial Intelligence improves cybersecurity"

    st.write("### Typing Test")
    st.code(sentence)

    if "typing_started" not in st.session_state:
        st.session_state["typing_started"] = False

    if st.button("▶️ Start Typing Test"):

        st.session_state["typing_started"] = True
        st.session_state["typing_start_time"] = time.time()

        st.success("Typing test started. Type the sentence now.")

    if st.session_state["typing_started"]:

        typed_text = st.text_area(
            "Type the sentence here",
            height=120
        )

        if st.button("💾 Save Typing Profile"):

            if email == "" or typed_text == "":
                st.error("Please enter email and typing sample.")

            else:

                duration = (
                    time.time()
                    - st.session_state["typing_start_time"]
                )

                speed = len(typed_text.strip()) / max(duration, 0.1)

                os.makedirs(
                    "storage/typing_profiles",
                    exist_ok=True
                )

                profile = {

                    "email": email,

                    "text": typed_text,

                    "length": len(typed_text),

                    "duration": round(duration, 2),

                    "speed": round(speed, 2)
                }

                path = (
                    f"storage/typing_profiles/"
                    f"{email}.json"
                )

                with open(path, "w") as file:

                    json.dump(
                        profile,
                        file,
                        indent=4
                    )

                st.success(
                    "✅ Typing Profile Registered Successfully!"
                )

                st.write(
                    f"Typing Speed: {round(speed, 2)} characters/sec"
                )

                st.session_state["typing_started"] = False
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
elif page == "Secure Workspace":

    import time
    import subprocess
    import sys

    from authentication.continuous_monitor import (
        analyze_typing,
        get_profile
    )

    from authentication.logger import log_event

    st.header("🛡️ Secure Workspace")

    # ==========================================
    # CHECK LOGIN
    # ==========================================

    if not st.session_state.get("logged_in", False):

        st.warning(
            "⚠️ Please login first to access the Secure Workspace."
        )

    else:

        email = st.session_state["user"]

        st.success(
            "🟢 CONTINUOUS AUTHENTICATION ACTIVE"
        )

        st.write(
            f"**Authenticated User:** {email}"
        )

        # ==========================================
        # GET TYPING PROFILE
        # ==========================================

        profile = get_profile(email)

        if not profile:

            st.error(
                "❌ Typing profile not found."
            )

            st.info(
                "Please register your typing pattern first."
            )

        else:

            baseline_speed = profile.get(
                "speed",
                0
            )

            # ==========================================
            # SESSION STATUS
            # ==========================================

            st.divider()

            col1, col2, col3 = st.columns(3)

            with col1:

                st.metric(
                    "🔐 Session",
                    "SECURE"
                )

            with col2:

                st.metric(
                    "⌨️ Baseline Speed",
                    f"{baseline_speed} char/s"
                )

            with col3:

                st.metric(
                    "🟢 Monitoring",
                    "ACTIVE"
                )

            st.divider()

            # ==========================================
            # WORKSPACE
            # ==========================================

            st.subheader(
                "💻 Protected Work Area"
            )

            st.write(
                "Continue working normally. "
                "The system monitors your typing behavior "
                "and checks for significant deviations."
            )

            work_text = st.text_area(
                "Type your work here",
                height=200,
                placeholder="Start typing your work..."
            )

            # Start timer when workspace opens
            if "workspace_start_time" not in st.session_state:

                st.session_state[
                    "workspace_start_time"
                ] = time.time()

            st.divider()

            # ==========================================
            # SECURITY CHECK
            # ==========================================

            if st.button(
                "🔍 Continue Working / Check Security"
            ):

                if work_text.strip() == "":

                    st.warning(
                        "Please type something before checking."
                    )

                else:

                    duration = (
                        time.time()
                        -
                        st.session_state[
                            "workspace_start_time"
                        ]
                    )

                    result = analyze_typing(
                        email,
                        work_text,
                        duration
                    )

                    current_deviation = result[
                        "deviation"
                    ]

                    # Save current behavioral information
                    st.session_state[
                        "typing_deviation"
                    ] = current_deviation

                    # ==================================
                    # DISPLAY ANALYSIS
                    # ==================================

                    st.subheader(
                        "📊 Live Behavioral Analysis"
                    )

                    col1, col2, col3, col4 = st.columns(4)

                    with col1:

                        st.metric(
                            "Current Speed",
                            f"{result['current_speed']} char/s"
                        )

                    with col2:

                        st.metric(
                            "Baseline",
                            f"{result['baseline_speed']} char/s"
                        )

                    with col3:

                        st.metric(
                            "Deviation",
                            f"{current_deviation}%"
                        )

                    with col4:

                        st.metric(
                            "Risk",
                            result["risk"]
                        )

                    st.divider()

                    # ==================================
                    # NORMAL BEHAVIOR
                    # ==================================

                    if not result["anomaly"]:

                        st.success(
                            "🟢 TYPING BEHAVIOR NORMAL"
                        )

                        st.success(
                            "🔐 Session remains secure."
                        )

                        log_event(
                            email,
                            "CONTINUOUS_CHECK_NORMAL"
                        )

                        # Reset timer for next monitoring cycle
                        st.session_state[
                            "workspace_start_time"
                        ] = time.time()

                    # ==================================
                    # ANOMALY DETECTED
                    # ==================================

                    else:

                        # Increase anomaly counter
                        st.session_state[
                            "previous_anomalies"
                        ] = (
                            st.session_state.get(
                                "previous_anomalies",
                                0
                            ) + 1
                        )

                        st.error(
                            "🚨 TYPING ANOMALY DETECTED"
                        )

                        st.warning(
                            f"Typing behavior changed by "
                            f"{current_deviation}%."
                        )

                        st.error(
                            "🔴 Additional authentication required."
                        )

                        log_event(
                            email,
                            "TYPING_ANOMALY"
                        )

                        # ==================================
                        # ADAPTIVE RISK CALCULATION
                        # ==================================

                        risk_score, risk_level, reasons = check_risk(
                            True,
                            True,
                            True,
                            current_deviation,
                            st.session_state[
                                "previous_anomalies"
                            ]
                        )

                        st.metric(
                            "Adaptive Risk Score",
                            f"{risk_score}/100"
                        )

                        st.write(
                            f"**Risk Level:** {risk_level}"
                        )

                        st.write(
                            "**Reason:** Behavioral typing "
                            "deviation detected."
                        )

                        # ==================================
                        # STEP-UP AUTHENTICATION
                        # ==================================

                        st.warning(
                            "📷 Opening camera for "
                            "face re-verification..."
                        )

                        result_camera = subprocess.run(
                            [
                                sys.executable,
                                "authentication/login.py",
                                email
                            ],
                            capture_output=True,
                            text=True
                        )

                        # ==================================
                        # FACE RE-VERIFICATION SUCCESS
                        # ==================================

                        if (
                            result_camera.returncode == 0
                            and
                            "Login Successful"
                            in result_camera.stdout
                        ):

                            st.success(
                                "✅ Face identity matched."
                            )

                            # Liveness check
                            live, score = check_liveness()

                            if live:

                                st.success(
                                    f"✅ Liveness verification passed "
                                    f"({score}%)"
                                )

                                log_event(
                                    email,
                                    "REAUTHENTICATION_SUCCESS"
                                )

                                st.success(
                                    "🔓 Identity verified."
                                )

                                st.success(
                                    "🟢 SESSION RESTORED"
                                )

                                # Reset current risk after successful re-auth
                                st.session_state[
                                    "typing_deviation"
                                ] = 0

                                st.session_state[
                                    "workspace_start_time"
                                ] = time.time()

                            else:

                                st.error(
                                    "❌ Liveness verification failed."
                                )

                                log_event(
                                    email,
                                    "REAUTHENTICATION_FAILED"
                                )

                                st.session_state[
                                    "logged_in"
                                ] = False

                                st.session_state[
                                    "user"
                                ] = ""

                                st.error(
                                    "🔒 SESSION LOCKED"
                                )

                        # ==================================
                        # FACE RE-VERIFICATION FAILED
                        # ==================================

                        else:

                            st.error(
                                "❌ Face re-verification failed."
                            )

                            log_event(
                                email,
                                "REAUTHENTICATION_FAILED"
                            )

                            st.session_state[
                                "logged_in"
                            ] = False

                            st.session_state[
                                "user"
                            ] = ""

                            st.error(
                                "🔒 SESSION LOCKED FOR SECURITY"
                            )

            st.divider()

            # ==========================================
            # ATTACK SIMULATION
            # ==========================================

            st.subheader(
                "🧪 Security Demonstration"
            )

            st.write(
                "Use this button during your project "
                "demonstration to simulate a suspicious user."
            )

            if st.button(
                "🚨 Simulate Suspicious User"
            ):

                # Create a strong anomaly
                simulated_deviation = 75

                st.session_state[
                    "typing_deviation"
                ] = simulated_deviation

                st.session_state[
                    "previous_anomalies"
                ] = (
                    st.session_state.get(
                        "previous_anomalies",
                        0
                    ) + 1
                )

                st.error(
                    "🚨 SIMULATED TYPING ANOMALY DETECTED"
                )

                st.warning(
                    "Typing behavior is significantly "
                    "different from the registered profile."
                )

                # Calculate risk
                risk_score, risk_level, reasons = check_risk(
                    True,
                    True,
                    True,
                    simulated_deviation,
                    st.session_state[
                        "previous_anomalies"
                    ]
                )

                st.error(
                    f"🔴 Risk Level: {risk_level}"
                )

                st.metric(
                    "Adaptive Risk Score",
                    f"{risk_score}/100"
                )

                log_event(
                    email,
                    "TYPING_ANOMALY_SIMULATION"
                )

                st.warning(
                    "📷 Step-up authentication required."
                )

                st.info(
                    "Opening camera for re-authentication..."
                )

                # Open camera
                result_camera = subprocess.run(
                    [
                        sys.executable,
                        "authentication/login.py",
                        email
                    ],
                    capture_output=True,
                    text=True
                )

                if (
                    result_camera.returncode == 0
                    and
                    "Login Successful"
                    in result_camera.stdout
                ):

                    st.success(
                        "✅ Face identity matched."
                    )

                    live, score = check_liveness()

                    if live:

                        st.success(
                            f"✅ Liveness passed ({score}%)"
                        )

                        log_event(
                            email,
                            "REAUTHENTICATION_SUCCESS"
                        )

                        st.success(
                            "🔓 SESSION RESTORED"
                        )

                        st.session_state[
                            "typing_deviation"
                        ] = 0
                        st.session_state[
    "previous_anomalies"
] = 0

                        st.session_state[
                            "workspace_start_time"
                        ] = time.time()

                    else:

                        st.error(
                            "❌ Liveness verification failed."
                        )

                        log_event(
                            email,
                            "REAUTHENTICATION_FAILED"
                        )

                        st.session_state[
                            "logged_in"
                        ] = False

                        st.session_state[
                            "user"
                        ] = ""

                        st.error(
                            "🔒 SESSION LOCKED"
                        )

                else:

                    st.error(
                        "❌ Face re-verification failed."
                    )

                    log_event(
                        email,
                        "REAUTHENTICATION_FAILED"
                    )

                    st.session_state[
                        "logged_in"
                    ] = False

                    st.session_state[
                        "user"
                    ] = ""

                    st.error(
                        "🔒 SESSION LOCKED FOR SECURITY"
                    )
# ---------------- DASHBOARD ---------------- #
elif page == "Dashboard":

    st.header("📊 AI Adaptive Authentication Dashboard")

    # ==============================
    # DATABASE
    # ==============================

    conn = sqlite3.connect("database/users.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    # ==============================
    # TOP METRICS
    # ==============================

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "👤 Registered Users",
            total_users
        )

    with col2:

        if st.session_state.get("logged_in", False):

            st.metric(
                "🔐 Authentication",
                "Verified"
            )

        else:

            st.metric(
                "🔐 Authentication",
                "Not Logged In"
            )

    with col3:

        if st.session_state.get("logged_in", False):

            st.metric(
                "🛡️ Session",
                "Secure"
            )

        else:

            st.metric(
                "🛡️ Session",
                "Inactive"
            )

    st.divider()

    # ==============================
    # ADAPTIVE SECURITY STATUS
    # ==============================

    st.subheader("🛡️ Adaptive Security Status")

    if st.session_state.get("logged_in", False):

        email = st.session_state["user"]

        face_verified = True
        liveness_verified = True
        keystroke_verified = True

        typing_deviation = st.session_state.get(
            "typing_deviation",
            0
        )

        previous_anomalies = st.session_state.get(
            "previous_anomalies",
            0
        )

        # Calculate adaptive risk
        risk_score, risk_level, reasons = check_risk(
            face_verified,
            liveness_verified,
            keystroke_verified,
            typing_deviation,
            previous_anomalies
        )

        # ==============================
        # SESSION STATUS
        # ==============================

        if risk_level == "LOW":

            st.success(
                "🟢 SESSION SECURE"
            )

        elif risk_level == "MEDIUM":

            st.warning(
                "🟡 SUSPICIOUS ACTIVITY"
            )

        else:

            st.error(
                "🔴 HIGH SECURITY RISK"
            )

        st.metric(
            "Security Risk Score",
            f"{risk_score}/100"
        )

        st.write(
            f"**Current User:** {email}"
        )

        st.divider()

        # ==============================
        # AUTHENTICATION FACTORS
        # ==============================

        st.subheader(
            "🔐 Authentication Factors"
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "Face",
                "✓ Verified"
            )

        with col2:

            st.metric(
                "Liveness",
                "✓ Passed"
            )

        with col3:

            st.metric(
                "Typing",
                "✓ Normal"
            )

        with col4:

            st.metric(
                "Monitoring",
                "🟢 ACTIVE"
            )

        st.divider()

        # ==============================
        # BEHAVIORAL ANALYSIS
        # ==============================

        st.subheader(
            "⌨️ Behavioral Analysis"
        )

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "Typing Deviation",
                f"{typing_deviation}%"
            )

        with col2:

            st.metric(
                "Previous Anomalies",
                previous_anomalies
            )

        if typing_deviation <= 20:

            st.success(
                "✓ Typing behavior matches the "
                "registered behavioral profile."
            )

        elif typing_deviation <= 40:

            st.warning(
                "⚠ Minor typing deviation detected."
            )

        else:

            st.error(
                "🚨 Significant behavioral deviation detected."
            )

        st.divider()

        # ==============================
        # EXPLAINABLE SECURITY DECISION
        # ==============================

        st.subheader(
            "🧠 Security Decision"
        )

        st.write(
            "The adaptive system evaluated "
            "the following signals:"
        )

        for reason in reasons:

            st.write(
                f"• {reason}"
            )

        if risk_level == "LOW":

            st.success(
                "Decision: Continue current session."
            )

        elif risk_level == "MEDIUM":

            st.warning(
                "Decision: Increase monitoring frequency."
            )

        else:

            st.error(
                "Decision: Additional authentication required."
            )

    else:

        st.warning(
            "⚠️ No Active Login"
        )

        st.info(
            "Please login to view adaptive "
            "security information."
        )

    st.divider()

    # ==============================
    # SECURITY EVENT HISTORY
    # ==============================

    st.subheader(
        "📜 Security Event History"
    )

    log_file = (
        "storage/authentication_logs/logs.txt"
    )

    if os.path.exists(log_file):

        with open(log_file, "r") as file:

            logs = file.readlines()

        if logs:

            # Show latest 10 events
            for log in reversed(logs[-10:]):

                log = log.strip()

                if "ANOMALY" in log:

                    st.error(
                        f"🚨 {log}"
                    )

                elif "REAUTHENTICATION_SUCCESS" in log:

                    st.success(
                        f"🔐 {log}"
                    )

                elif "FAILED" in log:

                    st.error(
                        f"❌ {log}"
                    )

                elif "SUCCESS" in log:

                    st.success(
                        f"✅ {log}"
                    )

                else:

                    st.info(
                        f"✓ {log}"
                    )

        else:

            st.info(
                "No security events recorded."
            )

    else:

        st.info(
            "No security events recorded."
        )

    st.divider()

    # ==============================
    # SYSTEM STATUS
    # ==============================

    st.subheader(
        "📈 System Status"
    )

    if os.path.exists(
        "models/trainer.yml"
    ):

        st.success(
            "✅ Face Recognition Model Loaded"
        )

    else:

        st.error(
            "❌ Face Recognition Model Not Found"
        )

    if os.path.exists(
        "database/users.db"
    ):

        st.success(
            "✅ Database Connected"
        )

    else:

        st.error(
            "❌ Database Not Found"
        )

    st.success(
        "✅ Authentication System Running"
    )

    st.success(
        "✅ Continuous Monitoring Ready"
    )

    st.success(
        "✅ Webcam Ready"
    )

    st.divider()

    # ==============================
    # LOGOUT
    # ==============================

    if st.session_state.get("logged_in", False):

        if st.button("🚪 Logout"):

            st.session_state["logged_in"] = False

            st.session_state["user"] = ""

            st.session_state["typing_deviation"] = 0

            st.session_state["previous_anomalies"] = 0

            st.success(
                "✅ Logged Out Successfully"
            )

            st.rerun()

    conn.close()