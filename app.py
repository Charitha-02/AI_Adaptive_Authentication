import streamlit as st



import sqlite3



import subprocess



import sys



import os



import time



from datetime import datetime







from authentication.face_liveness import check_liveness
from authentication.keystroke_auth import verify_typing



from authentication.adaptive_auth import check_risk


# Always run from the project root so database/model/storage paths work
# regardless of how Streamlit was started.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)


FACE_RECHECK_INTERVAL = 20


def face_check_success(result):
    """Return True only when the face-authentication process explicitly succeeds."""
    output = ((result.stdout or "") + "\n" + (result.stderr or "")).lower()
    return (
        result.returncode == 0
        and (
            "authenticated" in output
            or "login successful" in output
            or "access granted" in output
        )
    )


def run_face_check(email):
    """Run the same strict LBPH face verification used for login/re-auth."""
    return subprocess.run(
        [sys.executable, os.path.join(BASE_DIR, "authentication", "login.py"), email],
        capture_output=True,
        text=True,
        cwd=BASE_DIR,
    )











# ============================================================



# ⚙️ PAGE CONFIGURATION



# ============================================================







st.set_page_config(



    page_title="AI Adaptive Authentication",



    page_icon="🔐",



    layout="wide",
    initial_sidebar_state="expanded"



)











# ============================================================



# 🎨 PROFESSIONAL CYBERSECURITY UI



# ============================================================







st.markdown("""<style>
/* ============================================================
   PREMIUM CYBERSECURITY UI
   UI ONLY — APPLICATION LOGIC IS UNCHANGED
   ============================================================ */

:root{
    --bg:#f7f8fc;
    --surface:#ffffff;
    --surface-soft:#fbfcfe;
    --border:#e7eaf0;
    --text:#171a21;
    --muted:#6b7280;
    --sidebar:#0b1020;
    --sidebar-2:#11182b;
    --sidebar-text:#d8deea;
    --sidebar-muted:#7f8aa3;
    --accent:#635bff;
    --accent-2:#4f46e5;
    --success:#16a34a;
    --danger:#dc2626;
}


/* ---------- KEEP SIDEBAR ALWAYS VISIBLE ---------- */
section[data-testid="stSidebar"]{
    display:block!important;
    visibility:visible!important;
    opacity:1!important;
    transform:none!important;
    width:278px!important;
    min-width:278px!important;
    max-width:278px!important;
    left:0!important;
}
section[data-testid="stSidebar"][aria-expanded="false"]{
    display:block!important;
    visibility:visible!important;
    opacity:1!important;
    transform:none!important;
    width:278px!important;
    min-width:278px!important;
    max-width:278px!important;
}
[data-testid="stSidebarCollapsedControl"]{
    display:none!important;
    visibility:hidden!important;
}
button[data-testid="stSidebarCollapseButton"]{
    display:none!important;
}

/* ---------- APP CANVAS ---------- */
.stApp{
    background:var(--bg)!important;
    color:var(--text)!important;
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,Helvetica,Arial,sans-serif!important;
}
[data-testid="stHeader"]{background:transparent!important;height:0!important}
#MainMenu,footer{visibility:hidden}
.main .block-container{
    padding:1.35rem 2.2rem 4rem!important;
    max-width:1480px!important;
}

/* ---------- TYPOGRAPHY / FIX INVISIBLE TEXT ---------- */
h1,h2,h3,h4,h5,h6,
.stMarkdown p,.stMarkdown li,.stCaption,
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li{
    color:var(--text)!important;
}
h1{font-size:2rem!important;font-weight:780!important;letter-spacing:-.8px!important;line-height:1.15!important}
h2{font-size:1.45rem!important;font-weight:750!important;letter-spacing:-.35px!important}
h3{font-size:1.05rem!important;font-weight:720!important}
p,li{color:#596273!important;line-height:1.55!important}
small,.stCaption,[data-testid="stCaptionContainer"]{color:#7a8495!important}

/* ---------- SIDEBAR ---------- */
section[data-testid="stSidebar"]{
    background:linear-gradient(180deg,#0a0f1d 0%,#0d1323 55%,#0a0f1b 100%)!important;
    border-right:1px solid #1c2436!important;
    min-width:278px!important;
    max-width:278px!important;
}
section[data-testid="stSidebar"]>div{
    padding:22px 15px 108px!important;
}
section[data-testid="stSidebar"] h2{
    color:#f8fafc!important;
    font-size:18px!important;
    font-weight:780!important;
    letter-spacing:-.25px!important;
    margin:0!important;
}
section[data-testid="stSidebar"] h3{
    color:#aab3c5!important;
    font-size:11px!important;
    font-weight:700!important;
    letter-spacing:.5px!important;
    text-transform:uppercase!important;
    margin:4px 0 2px!important;
}
section[data-testid="stSidebar"] .stCaption{
    color:#66738c!important;
    font-size:9px!important;
    font-weight:700!important;
    letter-spacing:1.5px!important;
}
section[data-testid="stSidebar"] hr{border-color:#20283a!important;margin:13px 0!important}

section[data-testid="stSidebar"] div[role="radiogroup"]{gap:4px!important}
section[data-testid="stSidebar"] div[role="radiogroup"] label{
    min-height:42px!important;
    padding:0 12px!important;
    margin:0!important;
    border-radius:10px!important;
    border:1px solid transparent!important;
    background:transparent!important;
    transition:all .16s ease!important;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover{
    background:#151c2e!important;
    border-color:#202a40!important;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked){
    background:linear-gradient(90deg,#242052,#1b2140)!important;
    border-color:#3b3b73!important;
    box-shadow:inset 3px 0 0 #7c72ff,0 5px 18px rgba(0,0,0,.18)!important;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label p{
    color:#9ca8bd!important;
    font-size:13px!important;
    font-weight:560!important;
    margin:0!important;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p{
    color:#ffffff!important;
    font-weight:700!important;
}
section[data-testid="stSidebar"] div[role="radiogroup"] input{display:none!important}

.sidebar-user{
    position:fixed;left:15px;bottom:62px;width:248px;
    background:rgba(20,27,44,.96);
    border:1px solid #273149;
    border-radius:13px;
    padding:12px;
    box-sizing:border-box;
    z-index:9999;
    box-shadow:0 10px 30px rgba(0,0,0,.24);
}
.sidebar-user-row{display:flex;align-items:center;gap:10px}
.sidebar-avatar{
    width:34px;height:34px;border-radius:10px;
    background:linear-gradient(135deg,#635bff,#8b5cf6);
    display:flex;align-items:center;justify-content:center;
    color:#fff;font-weight:800;font-size:13px;flex:none;
    box-shadow:0 4px 12px rgba(99,91,255,.25);
}
.sidebar-user-name{color:#f8fafc!important;font-size:12px;font-weight:750;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sidebar-user-email{color:#7f8ba2!important;font-size:9px;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
section[data-testid="stSidebar"] .stButton{
    position:fixed!important;left:15px!important;bottom:14px!important;width:248px!important;z-index:10000!important;
}
section[data-testid="stSidebar"] .stButton>button{
    width:248px!important;height:40px!important;min-height:40px!important;
    padding:0 14px!important;
    background:#ffffff!important;
    border:1px solid #d8deea!important;
    border-radius:10px!important;
    color:#26324a!important;
    text-align:left!important;
    justify-content:flex-start!important;
    font-size:12px!important;font-weight:750!important;
    box-shadow:0 5px 16px rgba(0,0,0,.16)!important;
    opacity:1!important;
}
section[data-testid="stSidebar"] .stButton>button p,
section[data-testid="stSidebar"] .stButton>button span{
    color:#26324a!important;
    opacity:1!important;
    font-weight:750!important;
}
section[data-testid="stSidebar"] .stButton>button:hover{
    background:#f4f2ff!important;
    border-color:#7c72ff!important;
    color:#4f46e5!important;
    box-shadow:0 8px 22px rgba(99,91,255,.22)!important;
    transform:translateY(-1px)!important;
}
section[data-testid="stSidebar"] .stButton>button:hover p,
section[data-testid="stSidebar"] .stButton>button:hover span{
    color:#4f46e5!important;
}

/* ---------- TOP BAR ---------- */
.app-topbar{
    display:flex;align-items:center;justify-content:space-between;gap:20px;
    background:rgba(255,255,255,.82);
    border:1px solid var(--border);
    border-radius:15px;
    padding:13px 16px;
    margin:0 0 24px;
    box-shadow:0 8px 28px rgba(15,23,42,.045);
    backdrop-filter:blur(12px);
}
.app-brand{display:flex;align-items:center;gap:11px}
.app-logo{
    width:39px;height:39px;border-radius:11px;
    display:flex;align-items:center;justify-content:center;
    background:linear-gradient(135deg,#635bff,#4f46e5);
    color:#fff;font-size:19px;
    box-shadow:0 6px 16px rgba(99,91,255,.25);
}
.app-name{color:#171a21!important;font-size:16px;font-weight:800;line-height:1.1}
.app-sub{color:#8992a3!important;font-size:8px;letter-spacing:1.45px;font-weight:700;margin-top:4px}
.app-status{
    display:flex;align-items:center;gap:7px;color:#16803b!important;
    font-size:10px;font-weight:750;background:#f0fdf4;
    border:1px solid #ccefd7;border-radius:999px;padding:7px 11px;
}
.status-dot{width:7px;height:7px;border-radius:50%;background:#22c55e;box-shadow:0 0 0 4px rgba(34,197,94,.10),0 0 10px rgba(34,197,94,.45)}

/* ---------- CARDS ---------- */
.security-card,.metric-card,.hero{
    background:var(--surface)!important;
    border:1px solid var(--border)!important;
    border-radius:14px!important;
    box-shadow:0 6px 24px rgba(15,23,42,.045)!important;
}
.security-card{padding:22px!important;margin:12px 0!important}
.security-card h3,.hero h3{color:#171a21!important;margin-top:0!important}
.security-card p,.hero p{color:#697386!important}
.hero{padding:30px!important;margin-bottom:22px!important}

/* ---------- METRICS ---------- */
[data-testid="stMetric"]{
    background:#fff!important;border:1px solid var(--border)!important;
    border-radius:13px!important;padding:16px!important;
    box-shadow:0 5px 20px rgba(15,23,42,.04)!important;
}
[data-testid="stMetricLabel"]{color:#778195!important;font-size:11px!important;font-weight:650!important}
[data-testid="stMetricValue"]{color:#171a21!important;font-weight:780!important}
[data-testid="stMetricDelta"]{font-weight:650!important}

/* ---------- INPUTS ---------- */
.stTextInput label,.stTextArea label,.stSelectbox label,.stNumberInput label{
    color:#3d4656!important;font-weight:650!important;font-size:12px!important;
}
.stTextInput input,.stTextArea textarea,.stSelectbox div[data-baseweb="select"]>div,.stNumberInput input{
    background:#fff!important;color:#171a21!important;
    border:1px solid #dfe4ec!important;border-radius:10px!important;
    box-shadow:0 1px 2px rgba(15,23,42,.02)!important;
}
.stTextInput input::placeholder,.stTextArea textarea::placeholder{color:#a0a8b6!important}
.stTextInput input:focus,.stTextArea textarea:focus,.stNumberInput input:focus{
    border-color:#756cff!important;box-shadow:0 0 0 3px rgba(99,91,255,.10)!important;
}
.stSelectbox [data-baseweb="select"] span{color:#202633!important}

/* ---------- BUTTONS ---------- */
.stButton>button{
    border-radius:10px!important;
    border:1px solid #5b54ed!important;
    background:linear-gradient(135deg,#635bff,#554ce8)!important;
    color:#fff!important;font-weight:700!important;
    min-height:40px!important;padding:0 16px!important;
    box-shadow:0 5px 14px rgba(99,91,255,.18)!important;
    transition:all .16s ease!important;
}
.stButton>button:hover{
    background:linear-gradient(135deg,#7069ff,#4f46e5)!important;
    border-color:#4f46e5!important;
    transform:translateY(-1px)!important;
    box-shadow:0 8px 20px rgba(99,91,255,.23)!important;
}
.stButton>button:active{transform:translateY(0)!important}

/* ---------- ALERTS / STATUS ---------- */
div[data-testid="stAlert"]{
    border-radius:11px!important;border:1px solid rgba(0,0,0,.06)!important;
}
.status-secure{background:#effcf3;border:1px solid #ccefd7;color:#15803d;padding:11px 14px;border-radius:10px;font-weight:700}
.status-warning{background:#fff9e8;border:1px solid #f6df9b;color:#a16207;padding:11px 14px;border-radius:10px;font-weight:700}
.status-danger{background:#fff1f2;border:1px solid #fecdd3;color:#be123c;padding:11px 14px;border-radius:10px;font-weight:700}

/* ---------- CODE / CHALLENGE BLOCKS ---------- */
[data-testid="stCodeBlock"]{
    border-radius:12px!important;border:1px solid #262d3b!important;
    box-shadow:0 5px 18px rgba(15,23,42,.08)!important;overflow:hidden!important;
}
[data-testid="stCodeBlock"] pre{background:#101522!important}
[data-testid="stCodeBlock"] code{color:#eef2ff!important}

/* ---------- TABS / EXPANDERS / DATA ---------- */
.stTabs [data-baseweb="tab-list"]{gap:5px!important;border-bottom:1px solid #e5e8ee!important}
.stTabs [data-baseweb="tab"]{color:#697386!important;font-weight:650!important;padding:10px 13px!important}
.stTabs [aria-selected="true"]{color:#5148df!important;border-bottom-color:#635bff!important}
.streamlit-expanderHeader{color:#252b36!important;font-weight:700!important}
[data-testid="stDataFrame"]{border:1px solid var(--border)!important;border-radius:12px!important;overflow:hidden!important}

/* ---------- PROGRESS / DIVIDERS / CHARTS ---------- */
.stProgress>div>div>div{background:linear-gradient(90deg,#635bff,#8b5cf6)!important}
hr{border-color:#e7eaf0!important}
.stLineChart{background:#fff!important;border:1px solid var(--border)!important;border-radius:12px!important}

/* ---------- REMOVE STREAMLIT CHROME ---------- */
[data-testid="stToolbar"]{visibility:hidden!important}
[data-testid="stDecoration"]{display:none!important}
</style>""", unsafe_allow_html=True)











# ============================================================



# 🔐 APPLICATION TITLE



# ============================================================







st.markdown("""

<div class="app-topbar"><div class="app-brand"><div class="app-logo">🛡️</div><div><div class="app-name">AI Adaptive Authentication</div><div class="app-sub">CONTINUOUS SECURITY PLATFORM</div></div></div><div class="app-status"><span class="status-dot"></span> SYSTEM ACTIVE</div></div>

""", unsafe_allow_html=True)











# ============================================================



# 🧭 SIDEBAR NAVIGATION



# ============================================================







st.sidebar.markdown("## 🛡️ AI Adaptive")

st.sidebar.markdown("### Authentication")

st.sidebar.caption("CONTINUOUS SECURITY")

st.sidebar.markdown("---")



page_labels = {

    "Home": "⌂  Dashboard",

    "Register User": "👤  Register User",

    "Register Face": "◉  Register Face",

    "Register Keystroke": "⌨  Keystroke Profile",

    "Login": "🔐  Secure Login",

    "Secure Workspace": "▣  Secure Workspace",

    "Dashboard": "▦  Security Dashboard",

}



page = st.sidebar.radio("Navigation", list(page_labels.keys()), format_func=lambda x: page_labels[x], label_visibility="collapsed")



# Fixed bottom user profile and logout, matching the reference dashboard layout.

current_user = st.session_state.get("user", "")

if current_user:

    try:

        conn_side = sqlite3.connect("database/users.db")

        cur_side = conn_side.cursor()

        cur_side.execute("SELECT name FROM users WHERE email=?", (current_user,))

        row_side = cur_side.fetchone()

        conn_side.close()

        sidebar_name = row_side[0] if row_side and row_side[0] else current_user.split("@")[0]

    except Exception:

        sidebar_name = current_user.split("@")[0]

    sidebar_email = current_user

else:

    sidebar_name = "Guest User"

    sidebar_email = "Not signed in"



sidebar_initial = sidebar_name[:1].upper() if sidebar_name else "G"

st.sidebar.markdown(

    f"<div class='sidebar-user'><div class='sidebar-user-row'><div class='sidebar-avatar'>{sidebar_initial}</div><div style='min-width:0'><div class='sidebar-user-name'>{sidebar_name}</div><div class='sidebar-user-email'>{sidebar_email}</div></div></div></div>",

    unsafe_allow_html=True

)



if st.sidebar.button("↪  Log out", key="sidebar_logout"):

    # Clear only session/authentication state.
    # All project files, models, profiles, and registered data remain untouched.
    st.session_state["logged_in"] = False
    st.session_state["user"] = ""

    # Reset continuous-authentication state for the next login.
    st.session_state["typing_deviation"] = 0
    st.session_state["previous_anomalies"] = 0
    st.session_state["security_check_count"] = 0
    st.session_state["behavior_history"] = []
    st.session_state["monitor_start_time"] = None
    st.session_state["last_text_length"] = 0
    st.session_state["reauthentication_running"] = False

    # Return to the dashboard after logout.
    st.rerun()



# ---------------- HOME ---------------- #







if page == "Home":







    st.markdown("""



<div style="background: linear-gradient(135deg, #172554, #312e81); padding: 35px; border-radius: 20px; margin-bottom: 30px; border: 1px solid #4f46e5;">



<h1 style="color: white; font-size: 38px; margin-bottom: 10px;">



🔐 AI Adaptive Authentication



</h1>







<p style="color: #dbeafe; font-size: 18px;">



Continuous identity protection using facial verification,



liveness detection and behavioral authentication.



</p>



</div>



""", unsafe_allow_html=True)











    st.markdown("### 🛡️ System Status")







    col1, col2, col3 = st.columns(3)







    with col1:



        st.markdown("""



<div style="background: #ffffff; padding: 22px; border-radius: 15px; border: 1px solid #e5e7eb; box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06); min-height: 120px;">



<h3 style="color: #172033 !important;">🟢 Authentication</h3>



<p style="color: #667085 !important;">



Multi-factor verification is active.



</p>



</div>



""", unsafe_allow_html=True)







    with col2:



        st.markdown("""



<div style="background: #ffffff; padding: 22px; border-radius: 15px; border: 1px solid #e5e7eb; box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06); min-height: 120px;">



<h3 style="color: #172033 !important;">👁️ Face Verification</h3>



<p style="color: #667085 !important;">



Face identity and liveness are monitored.



</p>



</div>



""", unsafe_allow_html=True)







    with col3:



        st.markdown("""



<div style="background: #ffffff; padding: 22px; border-radius: 15px; border: 1px solid #e5e7eb; box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06); min-height: 120px;">



<h3 style="color: #172033 !important;">⌨️ Behavior Analysis</h3>



<p style="color: #667085 !important;">



Typing behavior is continuously analyzed.



</p>



</div>



""", unsafe_allow_html=True)











    st.markdown("---")







    st.markdown("### 🚀 How the System Protects You")







    col1, col2 = st.columns(2)







    with col1:



        st.markdown("""



<div style="background: #ffffff; padding: 25px; border-radius: 15px; border: 1px solid #e5e7eb; box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);">



<h3 style="color: #172033 !important;">



🔑 Initial Authentication



</h3>







<p style="color: #667085 !important;">



The system verifies the user's identity using multiple authentication factors.



</p>







<p style="color: #475467 !important;">✓ Face Recognition</p>



<p style="color: #475467 !important;">✓ Liveness Verification</p>



<p style="color: #475467 !important;">✓ Typing Pattern Verification</p>







</div>



""", unsafe_allow_html=True)







    with col2:



        st.markdown("""



<div style="background: #ffffff; padding: 25px; border-radius: 15px; border: 1px solid #e5e7eb; box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);">



<h3 style="color: #172033 !important;">



🛡️ Continuous Authentication



</h3>







<p style="color: #667085 !important;">



Authentication does not stop after login.



The system continues monitoring user behavior.



</p>







<p style="color: #475467 !important;">✓ Typing Behavior Monitoring</p>



<p style="color: #475467 !important;">✓ Adaptive Risk Analysis</p>



<p style="color: #475467 !important;">✓ Automatic Re-authentication</p>







</div>



""", unsafe_allow_html=True)











    st.markdown("---")







    st.info(



        "💡 If suspicious behavior is detected, "



        "the system automatically requests additional face verification."



    )











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
    import statistics

    st.header("⌨️ Register Multi-Sentence Behavioral Profile")

    email = st.text_input("Registered Email", key="keystroke_email")

    # Three different sentences make the behavioral profile richer than
    # training on only one fixed sentence.
    typing_sentences = [
        "Artificial Intelligence improves cybersecurity",
        "Continuous authentication protects active user sessions",
        "Machine learning detects unusual typing behavior"
    ]

    st.write("### 🧠 Multi-Sentence Typing Challenge")
    st.info(
        "Register 3 different sentences. For each sentence, provide 3 natural "
        "typing samples. The system learns your normal speed and variability "
        "across multiple texts."
    )

    # ------------------------------------------
    # INITIALIZE SESSION VARIABLES
    # ------------------------------------------

    if "typing_samples" not in st.session_state:
        st.session_state["typing_samples"] = []

    if "typing_started" not in st.session_state:
        st.session_state["typing_started"] = False

    if "typing_sentence_index" not in st.session_state:
        st.session_state["typing_sentence_index"] = 0

    # ------------------------------------------
    # CURRENT CHALLENGE
    # ------------------------------------------

    total_samples = len(st.session_state["typing_samples"])
    samples_per_sentence = 3
    total_required = len(typing_sentences) * samples_per_sentence

    current_sentence_index = min(
        total_samples // samples_per_sentence,
        len(typing_sentences) - 1
    )

    current_sentence = typing_sentences[current_sentence_index]

    st.progress(min(total_samples / total_required, 1.0))
    st.write(f"### Overall Progress: {total_samples}/{total_required}")

    for i, sentence_item in enumerate(typing_sentences):
        sentence_count = sum(
            1
            for sample in st.session_state["typing_samples"]
            if sample.get("sentence_index") == i
        )
        status = "✅" if sentence_count >= samples_per_sentence else "⬜"
        st.write(
            f"{status} Sentence {i + 1}: {sentence_count}/{samples_per_sentence} samples"
        )

    if total_samples < total_required:

        st.markdown("#### Current Sentence")
        st.code(current_sentence)

        st.caption(
            f"Sentence {current_sentence_index + 1} of {len(typing_sentences)}"
        )

        if not st.session_state["typing_started"]:

            if st.button(
                "▶️ Start Typing Sample",
                key="start_typing_sample"
            ):
                st.session_state["typing_started"] = True
                st.session_state["typing_start_time"] = time.time()

                st.success(
                    f"Sample {total_samples % samples_per_sentence + 1}/"
                    f"{samples_per_sentence} started. Type the sentence naturally."
                )
                st.rerun()

        if st.session_state["typing_started"]:

            typed_text = st.text_area(
                "Type the sentence here",
                height=120,
                key=f"typing_text_{total_samples}"
            )

            if st.button(
                "💾 Save This Sample",
                key=f"save_sample_{total_samples}"
            ):

                if email == "":
                    st.error("Please enter your registered email.")

                elif typed_text.strip() == "":
                    st.error("Please type the sentence.")

                else:
                    normalized_typed = " ".join(
                        typed_text.strip().split()
                    ).lower()

                    normalized_target = " ".join(
                        current_sentence.strip().split()
                    ).lower()

                    if normalized_typed != normalized_target:
                        st.error(
                            "❌ The typed sentence does not match the displayed "
                            "sentence. Please type it exactly and try again."
                        )
                    else:
                        duration = (
                            time.time()
                            - st.session_state["typing_start_time"]
                        )

                        speed = (
                            len(typed_text.strip())
                            / max(duration, 0.1)
                        )

                        sample = {
                            "sentence_index": current_sentence_index,
                            "sentence": current_sentence,
                            "text": typed_text,
                            "length": len(typed_text),
                            "duration": round(duration, 2),
                            "speed": round(speed, 2)
                        }

                        st.session_state["typing_samples"].append(sample)
                        st.session_state["typing_started"] = False

                        st.success(
                            f"✅ Sample {total_samples + 1}/{total_required} saved!"
                        )
                        st.rerun()

    # ------------------------------------------
    # SAVE FINAL PROFILE
    # ------------------------------------------

    if len(st.session_state["typing_samples"]) == total_required:

        samples = st.session_state["typing_samples"]

        speeds = [
            sample["speed"]
            for sample in samples
        ]

        average_speed = statistics.mean(speeds)
        min_speed = min(speeds)
        max_speed = max(speeds)

        speed_std = (
            statistics.stdev(speeds)
            if len(speeds) >= 2
            else 0.0
        )

        speed_consistency = (
            max(
                0.0,
                min(
                    100.0,
                    100.0 - ((speed_std / average_speed) * 100.0)
                )
            )
            if average_speed > 0
            else 0.0
        )

        # Per-sentence behavioral statistics.
        sentence_profiles = []

        for sentence_index, sentence_item in enumerate(typing_sentences):
            sentence_samples = [
                sample
                for sample in samples
                if sample.get("sentence_index") == sentence_index
            ]

            sentence_speeds = [
                sample["speed"]
                for sample in sentence_samples
            ]

            sentence_average = (
                statistics.mean(sentence_speeds)
                if sentence_speeds
                else 0.0
            )

            sentence_std = (
                statistics.stdev(sentence_speeds)
                if len(sentence_speeds) >= 2
                else 0.0
            )

            sentence_profiles.append({
                "sentence_index": sentence_index,
                "sentence": sentence_item,
                "samples": len(sentence_samples),
                "average_speed": round(sentence_average, 2),
                "speed_std": round(sentence_std, 2)
            })

        os.makedirs(
            "storage/typing_profiles",
            exist_ok=True
        )

        profile = {
            "email": email,
            "profile_type": "multi_sentence_behavioral",
            "sentences": typing_sentences,
            "sentence_profiles": sentence_profiles,
            "samples": samples,
            "total_samples": len(samples),
            "samples_per_sentence": samples_per_sentence,
            "average_speed": round(average_speed, 2),
            "min_speed": round(min_speed, 2),
            "max_speed": round(max_speed, 2),
            "speed_std": round(speed_std, 2),
            "speed_consistency": round(speed_consistency, 2),
            "speed": round(average_speed, 2)
        }

        path = (
            f"storage/typing_profiles/"
            f"{email}.json"
        )

        st.success("🎉 All 3 behavioral sentences have been registered!")

        st.write(
            f"**Average Typing Speed:** "
            f"{round(average_speed, 2)} characters/sec"
        )

        st.write(
            f"**Normal Speed Range:** "
            f"{round(min_speed, 2)} - "
            f"{round(max_speed, 2)} characters/sec"
        )

        st.write(
            f"**Speed Consistency:** "
            f"{round(speed_consistency, 2)}%"
        )

        st.write(
            f"**Behavioral Samples:** "
            f"{len(samples)} samples across "
            f"{len(typing_sentences)} sentences"
        )

        if st.button(
            "💾 Save Final Behavioral Profile",
            key="save_final_profile"
        ):

            if email == "":
                st.error(
                    "Please enter your registered email."
                )

            else:
                with open(path, "w") as file:
                    json.dump(
                        profile,
                        file,
                        indent=4
                    )

                st.success(
                    "✅ Personalized multi-sentence behavioral profile saved!"
                )

                st.info(
                    "The profile now contains multiple text contexts, "
                    "typing-speed variability, and per-sentence statistics."
                )

                # Reset samples after successful save.
                st.session_state["typing_samples"] = []
                st.session_state["typing_started"] = False
                st.session_state["typing_sentence_index"] = 0
                st.rerun()


# ---------------- LOGIN ---------------- #

elif page == "Login":

    import json

    st.header("🔐 Secure Login")

    email = st.text_input("Registered Email", key="login_email")

    # Load the registered typing challenge.
    login_sentences = []
    profile_path = ""

    if email.strip():
        profile_path = os.path.join(
            BASE_DIR,
            "storage",
            "typing_profiles",
            f"{email.strip()}.json"
        )

        if os.path.exists(profile_path):
            try:
                with open(profile_path, "r", encoding="utf-8") as profile_file:
                    login_profile = json.load(profile_file)

                login_sentences = login_profile.get("sentences", [])

                # Backward compatibility with the old one-sentence profile.
                if not login_sentences and login_profile.get("sentence"):
                    login_sentences = [login_profile["sentence"]]
            except Exception:
                login_sentences = []

    if login_sentences:
        sentence = st.selectbox(
            "Select the typing challenge",
            login_sentences,
            key="login_sentence_challenge"
        )
    else:
        sentence = "Artificial Intelligence improves cybersecurity"

    st.write("### Type this sentence:")
    st.code(sentence)

    typed_text = st.text_area("Type Here", key="login_typing_text")

    if st.button("🔐 Login", key="login_button"):

        if not email.strip() or not typed_text.strip():
            st.error("Please enter your email and typing sample.")
        else:
            typed_normalized = " ".join(
                typed_text.strip().split()
            ).lower()

            sentence_normalized = " ".join(
                sentence.strip().split()
            ).lower()

            if typed_normalized != sentence_normalized:
                st.error(
                    "❌ Typing challenge does not match. "
                    "Please type the displayed sentence exactly."
                )
            else:
                st.info("📷 Opening camera for face verification...")

                # Step 1: verify the registered face. This subprocess uses
                # the existing login.py implementation and does not change
                # or reset the user's registered face data.
                try:
                    result = run_face_check(email.strip())
                except Exception as exc:
                    st.error(f"❌ Could not run face recognition: {exc}")
                    result = None

                if result is not None and face_check_success(result):
                    st.success("✅ Face identity matched. Starting liveness verification...")

                    # Step 2: run liveness once, and display the returned result
                    # in Streamlit so the user can see where login is failing.
                    try:
                        # Diagnostic: call the function through its module so we
                        # can confirm which file Streamlit is actually using.
                        import authentication.face_liveness as liveness_module

                        st.caption(
                            f"Liveness module file: {liveness_module.__file__}"
                        )

                        # login.py opens and closes the same physical webcam.
                        # Give Windows/OpenCV a moment to release the device before
                        # opening it again for the anti-spoofing check.
                        time.sleep(1.5)
                        st.write("DEBUG: Starting liveness check from Streamlit")
                        live, score = liveness_module.check_liveness()
                        st.write("DEBUG: Liveness function finished")
                        st.write("DEBUG — Liveness returned:", repr((live, score)))
                        st.write("DEBUG — Liveness passed:", bool(live))
                        st.code("LIVENESS RESULT: " + repr((live, score)))

                        st.write("Raw liveness result:", repr((live, score)))
                        st.caption(
                            f"Liveness diagnostic — passed: {bool(live)}, score: {score}%"
                        )
                    except Exception as exc:
                        live, score = False, 0
                        st.error(f"Liveness verification raised an error: {exc}")

                    if not live:
                        st.error(
                            f"❌ Face liveness verification failed ({score}%). "
                            "Check the anti-spoofing window/terminal output; "
                            "the login is intentionally not granted."
                        )
                    elif verify_typing(email.strip(), typed_text):
                        st.success(
                            f"✅ Face verified + liveness passed ({score}%)."
                        )
                        st.success("✅ Multi-factor Login Successful")

                        st.session_state["logged_in"] = True
                        st.session_state["user"] = email.strip()
                        st.session_state["last_face_check_time"] = time.time()
                        st.session_state["typing_deviation"] = 0
                        st.session_state["previous_anomalies"] = 0
                        st.session_state["security_check_count"] = 0
                        st.session_state["behavior_history"] = []
                        st.session_state["monitor_start_time"] = None
                        st.session_state["last_text_length"] = 0
                        st.session_state["reauthentication_running"] = False

                        log_message = "LOGIN_SUCCESS"
                        try:
                            from authentication.logger import log_event
                            log_event(email.strip(), log_message)
                        except Exception:
                            pass

                        st.success("🔓 Access granted. You can open Secure Workspace.")
                    else:
                        st.error("❌ Behavioral typing verification failed.")
                else:
                    st.error("❌ Face verification failed — access denied.")
                    if result is not None:
                        if result.stdout:
                            st.text("Face recognition output:")
                            st.code(result.stdout)
                        if result.stderr:
                            st.text("Face recognition errors:")
                            st.code(result.stderr)

# ---------------- SECURE WORKSPACE ---------------- #



# ---------------- SECURE WORKSPACE ---------------- #







elif page == "Secure Workspace":







    import time



    import subprocess



    import sys







    from st_keyup import st_keyup







    from authentication.continuous_monitor import (



        analyze_typing,



        get_profile



    )







    from authentication.logger import log_event







    from authentication.adaptive_auth import check_risk







    from authentication.face_liveness import check_liveness











    # ============================================================



    # HEADER



    # ============================================================







    # Secure Workspace header — native Streamlit components only.
    # This prevents HTML/CSS source from ever being displayed as page text.
    with st.container(border=True):
        st.markdown("## 🛡️ Secure Workspace")
        st.caption("AI-powered continuous authentication is protecting your active session.")
        st.success("🟢 Continuous authentication is active")











    # ============================================================



    # PAGE TITLE



    # ============================================================







    st.header("🛡️ Continuous Authentication")











    # ============================================================



    # CHECK LOGIN



    # ============================================================







    # Show the final result after Streamlit reruns the page.
    reauth_notice = st.session_state.pop("reauthentication_notice", None)
    if reauth_notice:
        notice_type, notice_text = reauth_notice
        if notice_type == "success":
            st.success(notice_text)
        else:
            st.error(notice_text)

    if not st.session_state.get("logged_in", False):







        st.warning(



            "⚠️ Please login first to access the Secure Workspace."



        )







    else:







        email = st.session_state["user"]











        # ========================================================



        # LOGIN STATUS



        # ========================================================







        st.success(



            "🟢 CONTINUOUS AUTHENTICATION ACTIVE"



        )







        st.write(



            f"**Authenticated User:** {email}"



        )











        # ========================================================



        # LOAD TYPING PROFILE



        # ========================================================







        profile = get_profile(email)











        if not profile:







            st.error(



                "❌ Typing profile not found."



            )







            st.info(



                "Please register your typing pattern first."



            )







        else:







            # ====================================================



            # BASELINE SPEED



            # ====================================================







            baseline_speed = profile.get(



                "average_speed",



                profile.get("speed", 0)



            )











            if baseline_speed <= 0:







                st.error(



                    "❌ Invalid typing profile."



                )







                st.stop()











            # ====================================================



            # SESSION VARIABLES



            # ====================================================







            if "monitor_start_time" not in st.session_state:



                st.session_state["monitor_start_time"] = None







            if "last_text_length" not in st.session_state:



                st.session_state["last_text_length"] = 0







            if "typing_deviation" not in st.session_state:



                st.session_state["typing_deviation"] = 0







            if "previous_anomalies" not in st.session_state:



                st.session_state["previous_anomalies"] = 0







            if "security_check_count" not in st.session_state:



                st.session_state["security_check_count"] = 0







            if "reauthentication_running" not in st.session_state:



                st.session_state["reauthentication_running"] = False



            if "last_face_check_time" not in st.session_state:



                st.session_state["last_face_check_time"] = time.time()











            # ====================================================



            # STATUS CARDS



            # ====================================================







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



                    f"{round(baseline_speed, 2)} char/s"



                )







            with col3:







                st.metric(



                    "🟢 Monitoring",



                    "ACTIVE"



                )











            # ====================================================



            # EXPLANATION



            # ====================================================







            st.divider()







            st.subheader(



                "🛡️ Automatic Security Monitoring"



            )







            st.info(



                "The system monitors your typing behavior. "



                "If your typing speed becomes significantly "



                "different from your registered behavior, "



                "additional face authentication is triggered."



            )











            # ====================================================



            # PROTECTED WORK AREA



            # ====================================================







            st.subheader(



                "💻 Protected Work Area"



            )







            st.write(



                "Start typing below. Your typing behavior "



                "will be analyzed automatically."



            )











            # ====================================================



            # REAL-TIME KEYBOARD INPUT



            # ====================================================







            work_text = st_keyup(



                "⌨️ Type here",



                key="real_time_workspace",



                debounce=0



            )











            # ====================================================



            # CURRENT LENGTH



            # ====================================================







            current_length = len(



                work_text.strip()



            )











            if current_length > 0:







                st.caption(



                    f"Characters typed: {current_length}"



                )











            # ====================================================



            # START TIMER WHEN USER STARTS TYPING



            # ====================================================







            if current_length > 0:







                if st.session_state["monitor_start_time"] is None:







                    st.session_state[



                        "monitor_start_time"



                    ] = time.time()











            # ====================================================



            # REAL-TIME TYPING ANALYSIS



            # ====================================================







            # Recent behavioral history for this session.
            if "behavior_history" not in st.session_state:
                st.session_state["behavior_history"] = []

            MINIMUM_CHARACTERS = 15







            if (



                current_length >= MINIMUM_CHARACTERS



                and



                current_length >



                st.session_state["last_text_length"]



                and



                not st.session_state["reauthentication_running"]



            ):







                # ------------------------------------------------



                # Calculate typing duration



                # ------------------------------------------------







                start_time = st.session_state[



                    "monitor_start_time"



                ]







                if start_time is None:







                    start_time = time.time()







                    st.session_state[



                        "monitor_start_time"



                    ] = start_time











                duration = (



                    time.time()



                    - start_time



                )











                # ------------------------------------------------



                # Avoid calculating too early



                # ------------------------------------------------







                if duration >= 1:







                    result = analyze_typing(



                        email,



                        work_text,



                        duration



                    )











                    current_speed = result[



                        "current_speed"



                    ]







                    deviation = result[



                        "deviation"



                    ]











                    # ------------------------------------------------



                    # SAVE SECURITY VALUES



                    # ------------------------------------------------







                    st.session_state[



                        "typing_deviation"



                    ] = deviation







                    st.session_state[



                        "security_check_count"



                    ] += 1







                    st.session_state[



                        "last_text_length"



                    ] = current_length











                    # =================================================



                    # Save the latest behavioral measurement.
                    st.session_state["behavior_history"].append({
                        "check": st.session_state["security_check_count"],
                        "speed": round(result["current_speed"], 2),
                        "baseline": round(result["baseline_speed"], 2),
                        "deviation": round(result["deviation"], 2),
                        "confidence": round(
                            result.get("behavioral_score", 0), 2
                        ),
                        "risk": result["risk"],
                        "status": result["status"],
                    })

                    # Keep only the latest 10 checks.
                    st.session_state["behavior_history"] = (
                        st.session_state["behavior_history"][-10:]
                    )


                    # =================================================
                    # PERIODIC FACE RE-VERIFICATION
                    # =================================================
                    # The webcam is NOT kept on continuously.  While the
                    # workspace is active, the face is rechecked periodically
                    # when the user is typing.  A failed identity check ends
                    # the session immediately.
                    now = time.time()
                    last_face_check = st.session_state.get(
                        "last_face_check_time", now
                    )

                    if (
                        current_length >= MINIMUM_CHARACTERS
                        and now - last_face_check >= FACE_RECHECK_INTERVAL
                        and not st.session_state.get("reauthentication_running", False)
                        and st.session_state.get("logged_in", False)
                    ):
                        st.session_state["last_face_check_time"] = now
                        st.info("📷 Periodic identity verification: please look at the camera.")
                        periodic_face = run_face_check(email)
                        if face_check_success(periodic_face):
                            st.success("✅ Identity still verified — session continues.")
                            log_event(email, "PERIODIC_FACE_VERIFICATION_SUCCESS")
                        else:
                            log_event(email, "UNKNOWN_FACE_SESSION_TERMINATED")
                            st.session_state["logged_in"] = False
                            st.session_state["user"] = ""
                            st.session_state["reauthentication_running"] = False
                            st.error("🚨 UNKNOWN FACE DETECTED — SESSION TERMINATED")
                            if periodic_face.stdout:
                                st.code(periodic_face.stdout)
                            if periodic_face.stderr:
                                st.code(periodic_face.stderr)
                            st.stop()

                    # LIVE BEHAVIORAL ANALYSIS



                    # =================================================







                    st.subheader(



                        "📊 Live Behavioral Analysis"



                    )







                    col1, col2, col3, col4 = st.columns(4)











                    with col1:







                        st.metric(



                            "Current Speed",



                            f"{round(current_speed, 2)} char/s"



                        )











                    with col2:







                        st.metric(



                            "Baseline",



                            f"{round(baseline_speed, 2)} char/s"



                        )











                    with col3:







                        st.metric(



                            "Deviation",



                            f"{round(deviation, 2)}%"



                        )











                    with col4:







                        st.metric(



                            "Risk",



                            result["risk"]



                        )



                    # New personalized behavioral-authentication metrics.
                    behavioral_score = result.get(
                        "behavioral_score",
                        0
                    )

                    speed_consistency = result.get(
                        "speed_consistency",
                        0
                    )

                    st.markdown("#### 🧠 Personalized Behavioral Fingerprint")

                    behavior_col1, behavior_col2, behavior_col3 = st.columns(3)

                    with behavior_col1:
                        st.metric(
                            "Behavioral Confidence",
                            f"{behavioral_score:.1f}%"
                        )

                    with behavior_col2:
                        st.metric(
                            "Profile Consistency",
                            f"{speed_consistency:.1f}%"
                        )

                    with behavior_col3:
                        st.metric(
                            "Personalized Z-Score",
                            f"{result.get('z_score', 0):.2f}"
                        )

                    st.caption(
                        "The system compares the current typing speed "
                        "with the user's own registered variability, "
                        "not just a fixed threshold."
                    )

                    # ====================================================
                    # BEHAVIORAL TREND MONITORING
                    # ====================================================
                    history = st.session_state.get(
                        "behavior_history", []
                    )

                    if history:
                        st.markdown(
                            "#### 📈 Behavioral Trend Monitoring"
                        )

                        trend_col1, trend_col2, trend_col3 = st.columns(3)

                        recent_deviations = [
                            item["deviation"] for item in history
                        ]

                        with trend_col1:
                            st.metric(
                                "Recent Checks",
                                len(history)
                            )

                        with trend_col2:
                            st.metric(
                                "Average Deviation",
                                f"{sum(recent_deviations) / len(recent_deviations):.1f}%"
                            )

                        with trend_col3:
                            st.metric(
                                "Latest Risk",
                                history[-1]["risk"]
                            )

                        st.line_chart({
                            "Current Speed": [
                                item["speed"] for item in history
                            ],
                            "Baseline Speed": [
                                item["baseline"] for item in history
                            ],
                        })

                        st.caption(
                            "Recent checks show whether typing behavior "
                            "is stable or changing during the active session."
                        )












                    # =================================================



                    # NORMAL BEHAVIOR



                    # =================================================







                    if deviation <= 40:







                        st.success(



                            "🟢 NORMAL BEHAVIOR — SESSION SECURE"



                        )







                        log_event(



                            email,



                            "REAL_TIME_CHECK_NORMAL"



                        )











                    # =================================================



                    # ABNORMAL BEHAVIOR



                    # =================================================







                    else:







                        st.error(



                            "🚨 ABNORMAL TYPING BEHAVIOR DETECTED"



                        )







                        st.warning(



                            f"Typing deviation detected: "



                            f"{round(deviation, 2)}%"



                        )











                        # Increase anomaly count







                        st.session_state[



                            "previous_anomalies"



                        ] += 1











                        log_event(



                            email,



                            "REAL_TIME_TYPING_ANOMALY"



                        )











                        # =================================================



                        # ADAPTIVE RISK



                        # =================================================







                        risk_score, risk_level, reasons = check_risk(



                            True,



                            True,



                            True,



                            deviation,



                            st.session_state[



                                "previous_anomalies"



                            ]



                        )











                        st.error(



                            f"🔴 Adaptive Risk Level: "



                            f"{risk_level}"



                        )











                        st.metric(



                            "Adaptive Risk Score",



                            f"{risk_score}/100"



                        )











                        st.write(



                            "**Security Decision:**"



                        )











                        for reason in reasons:







                            st.write(



                                f"• {reason}"



                            )











                        # =================================================



                        # AUTOMATIC FACE RE-AUTHENTICATION



                        # =================================================







                        if not st.session_state[



                            "reauthentication_running"



                        ]:







                            st.session_state[



                                "reauthentication_running"



                            ] = True











                            st.warning(



                                "📷 ABNORMAL ACTIVITY DETECTED"



                            )











                            st.info(



                                "🔐 Starting automatic "



                                "face re-verification..."



                            )











                            log_event(



                                email,



                                "AUTOMATIC_REAUTHENTICATION_STARTED"



                            )











                            # =================================================



                            # OPEN CAMERA



                            # =================================================







                            with st.spinner(



                                "📷 Opening camera for "



                                "face verification..."



                            ):







                                result_camera = run_face_check(email)











                            # =================================================



                            # CHECK CAMERA RESULT



                            # =================================================







                            camera_success = face_check_success(result_camera)











                            if camera_success:







                                st.success(



                                    "✅ Face identity matched."



                                )











                                # =================================================



                                # LIVENESS



                                # =================================================







                                # login.py has just used the same webcam.
                                # Give Windows/OpenCV time to release it before
                                # opening the liveness camera.
                                time.sleep(1.5)
                                try:
                                    live, score = check_liveness()
                                except Exception as exc:
                                    live, score = False, 0
                                    st.error(f"Face liveness check error: {exc}")











                                if live:







                                    st.success(



                                        f"✅ Liveness verification "



                                        f"passed ({score}%)"



                                    )











                                    log_event(



                                        email,



                                        "REAUTHENTICATION_SUCCESS"



                                    )











                                    st.success(



                                        "🔓 Identity verified."



                                    )







                                    st.success(



                                        "🟢 SESSION CONTINUES"



                                    )











                                    # Reset security state







                                    st.session_state[



                                        "typing_deviation"



                                    ] = 0







                                    st.session_state[



                                        "previous_anomalies"



                                    ] = 0







                                    st.session_state[



                                        "last_text_length"



                                    ] = current_length







                                    st.session_state[



                                        "monitor_start_time"



                                    ] = time.time()







                                    st.session_state[
                                        "reauthentication_running"
                                    ] = False
                                    st.session_state["reauthentication_notice"] = (
                                        "success",
                                        f"✅ Re-verification successful ({score}%). "
                                        "Your session continues."
                                    )
                                    st.rerun()











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







                                    st.session_state[



                                        "reauthentication_running"



                                    ] = False











                                    st.session_state["reauthentication_notice"] = (
                                        "error",
                                        "🔒 SESSION LOCKED — face liveness verification failed. "
                                        "Please log in again."
                                    )
                                    st.rerun()











                            else:







                                st.error(



                                    "❌ Face re-verification failed."



                                )











                                # Show camera output for debugging







                                if result_camera.stdout:







                                    st.code(



                                        result_camera.stdout



                                    )











                                if result_camera.stderr:







                                    st.code(



                                        result_camera.stderr



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







                                st.session_state[



                                    "reauthentication_running"



                                ] = False











                                st.session_state["reauthentication_notice"] = (
                                    "error",
                                    "🔒 SESSION LOCKED — face identity re-verification failed. "
                                    "Please log in again."
                                )
                                st.rerun()











            # ====================================================



            # SECURITY STATUS



            # ====================================================







            st.divider()







            st.subheader(



                "📈 Security Status"



            )







            col1, col2, col3 = st.columns(3)











            with col1:







                st.metric(



                    "Security Checks",



                    st.session_state[



                        "security_check_count"



                    ]



                )











            with col2:







                st.metric(



                    "Previous Anomalies",



                    st.session_state[



                        "previous_anomalies"



                    ]



                )











            with col3:







                st.metric(



                    "Current Deviation",



                    f"{round(st.session_state['typing_deviation'], 2)}%"



                )











            # ====================================================



            # DEMO BUTTON



            # ====================================================







            st.divider()







            st.subheader(



                "🧪 Project Demonstration"



            )







            st.write(



                "Use this button if you need to demonstrate "



                "the adaptive authentication mechanism."



            )











            if st.button(



                "🚨 Simulate Abnormal User",



                key="demo_abnormal_user"



            ):







                st.error(



                    "🚨 ABNORMAL USER DETECTED"



                )











                simulated_deviation = 75











                st.session_state[



                    "typing_deviation"



                ] = simulated_deviation











                st.session_state[



                    "previous_anomalies"



                ] += 1











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











                st.warning(



                    "📷 Starting automatic "



                    "face re-verification..."



                )











                log_event(



                    email,



                    "DEMO_ABNORMAL_USER"



                )











                st.session_state[



                    "reauthentication_running"



                ] = True











                # =================================================



                # DEMO CAMERA



                # =================================================







                with st.spinner(



                    "📷 Opening camera..."



                ):







                    result_camera = run_face_check(email)











                camera_success = face_check_success(result_camera)











                if camera_success:







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



                            "DEMO_REAUTHENTICATION_SUCCESS"



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



                            "reauthentication_running"



                        ] = False











                    else:







                        st.error(



                            "❌ Liveness verification failed."



                        )







                        st.session_state[



                            "logged_in"



                        ] = False







                        st.session_state[



                            "user"



                        ] = ""







                        st.session_state[



                            "reauthentication_running"



                        ] = False











                        st.error(



                            "🔒 SESSION LOCKED"



                        )











                else:







                    st.error(



                        "❌ Face verification failed."



                    )











                    if result_camera.stdout:







                        st.code(



                            result_camera.stdout



                        )











                    if result_camera.stderr:







                        st.code(



                            result_camera.stderr



                        )











                    st.session_state[



                        "logged_in"



                    ] = False







                    st.session_state[



                        "user"



                    ] = ""







                    st.session_state[



                        "reauthentication_running"



                    ] = False



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



    # Logout is handled from the fixed sidebar control above.
