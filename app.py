
import streamlit as st
import math

st.set_page_config(page_title="Tính Toán Điện", layout="centered")

st.title("🔌 Tính Toán Điện – Bản thử nghiệm")

menu = st.sidebar.selectbox("📂 Chọn chức năng", [
    "Trang chủ",
    "Tính dòng điện (I)",
    "Tính công suất (P)",
])

if menu == "Trang chủ":
    st.markdown("### 👋 Chào mừng đến với ứng dụng Tính Toán Điện")
    st.markdown("Ứng dụng này giúp bạn thực hiện nhanh các phép tính kỹ thuật điện phổ biến.")
    st.markdown("Chọn chức năng từ menu bên trái để bắt đầu.")

elif menu == "Tính dòng điện (I)":
    st.subheader("⚡ Tính dòng điện theo công suất")
    pha = st.radio("Loại điện:", ["1 pha", "3 pha"])
    P = st.number_input("Nhập công suất P (kW):", min_value=0.0)
    U = st.number_input("Nhập điện áp U (V):", min_value=0.0)
    cos_phi = st.slider("Hệ số cosφ:", 0.1, 1.0, 0.8, step=0.01)

    if st.button("Tính dòng điện"):
        if pha == "1 pha":
            I = P * 1000 / (U * cos_phi)
        else:
            I = P * 1000 / (math.sqrt(3) * U * cos_phi)
        st.success(f"🔹 Dòng điện I ≈ {I:.2f} A")

elif menu == "Tính công suất (P)":
    st.subheader("🔋 Tính công suất từ dòng điện")
    pha = st.radio("Loại điện:", ["1 pha", "3 pha"], key="p2")
    I = st.number_input("Nhập dòng điện I (A):", min_value=0.0)
    U = st.number_input("Nhập điện áp U (V):", min_value=0.0, key="u2")
    cos_phi = st.slider("Hệ số cosφ:", 0.1, 1.0, 0.8, step=0.01, key="c2")

    if st.button("Tính công suất"):
        if pha == "1 pha":
            P = U * I * cos_phi / 1000
        else:
            P = math.sqrt(3) * U * I * cos_phi / 1000
        st.success(f"🔹 Công suất P ≈ {P:.2f} kW")
