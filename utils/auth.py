"""
সহজ password-gate। Manager page গুলোর (upload/delete/edit করতে পারে এমন)
শুরুতে require_admin() কল করলেই হবে — password ঠিক না হওয়া পর্যন্ত বাকি
page এর কোড রান হবে না।

একবার সঠিক password দিলে সেই browser session এ (সব page জুড়ে) admin থেকে
যাবে, বার বার password দিতে হবে না।
"""

import streamlit as st


def is_admin():
    return st.session_state.get("is_admin", False)


def require_admin():
    if is_admin():
        with st.sidebar:
            st.success("🔓 Admin মোড")
            if st.button("Logout"):
                st.session_state["is_admin"] = False
                st.rerun()
        return

    st.warning("🔒 এই page শুধু Admin এর জন্য — normal user রা শুধু দেখতে/practice করতে পারবে।")
    admin_password = st.secrets.get("ADMIN_PASSWORD")

    if not admin_password:
        st.error(
            "⚠️ ADMIN_PASSWORD Streamlit secrets এ সেট করা নেই। "
            "Settings → Secrets এ গিয়ে ADMIN_PASSWORD যোগ করো, নাহলে কেউ এই page ব্যবহার করতে পারবে না।"
        )
        st.stop()

    pwd = st.text_input("Admin Password দাও", type="password")
    if st.button("🔓 Login"):
        if pwd == admin_password:
            st.session_state["is_admin"] = True
            st.rerun()
        else:
            st.error("ভুল password")
    st.stop()
