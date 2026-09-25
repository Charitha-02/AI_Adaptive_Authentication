import streamlit as st
import sqlite3

st.set_page_config(page_title="User Registration", page_icon="🔐")

st.title("🔐 AI Adaptive Authentication")
st.subheader("User Registration")

name = st.text_input("Full Name")
email = st.text_input("Email")
password = st.text_input("Password", type="password")
confirm = st.text_input("Confirm Password", type="password")


if st.button("Register"):

    if name == "" or email == "" or password == "":
        st.error("Please fill all fields.")

    elif password != confirm:
        st.error("Passwords do not match.")

    else:

        conn = sqlite3.connect("database/users.db")
        cursor = conn.cursor()

        try:

            cursor.execute("""
            INSERT INTO users(name,email,password)
            VALUES(?,?,?)
            """,(name,email,password))

            conn.commit()

            st.success("Registration Successful!")

        except:

            st.error("Email already exists!")

        conn.close()