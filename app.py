
import streamlit as st
import math

st.set_page_config(page_title="Tính Toán Điện", layout="centered")
st.title("🔌 Tính Toán Điện – EVNNPC")

menu = st.sidebar.selectbox("📂 Chọn chức năng", [
    "Trang chủ",
    "Tính dòng điện (I)",
    "Tính công suất (P)",
    "Tính sụt áp (ΔU)",
    "Chọn tiết diện dây dẫn",
    "Chiều dài dây tối đa (ΔU%)",
    "Tính điện trở – kháng – trở kháng",
    "Tính tổn thất công suất trên dây",
    "Chọn thiết bị bảo vệ (CB)"
])

if menu == "Trang chủ":
    st.markdown("### 👋 Chào mừng đến với ứng dụng Tính Toán Điện")
    st.markdown("Ứng dụng này giúp bạn tính toán nhanh các thông số kỹ thuật điện phổ biến trong ngành điện lực.")
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

elif menu == "Tính sụt áp (ΔU)":
    st.subheader("📉 Tính sụt áp trên đường dây")
    I = st.number_input("Dòng điện I (A):", min_value=0.0)
    R = st.number_input("Điện trở R (Ω):", min_value=0.0)
    L = st.number_input("Chiều dài dây (m):", min_value=0.0)
    Udrop = I * R * (L / 1000) * 2
    if st.button("Tính sụt áp"):
        st.success(f"🔻 Sụt áp ΔU ≈ {Udrop:.2f} V")

elif menu == "Chọn tiết diện dây dẫn":
    st.subheader("🧵 Tính tiết diện dây theo mật độ dòng điện")
    I = st.number_input("Dòng điện I (A):", min_value=0.0)
    J = st.number_input("Mật độ dòng điện J (A/mm²):", min_value=1.0, value=4.0)
    S = I / J
    if st.button("Tính tiết diện"):
        st.success(f"🔹 Tiết diện tối thiểu S = {S:.2f} mm²")

elif menu == "Chiều dài dây tối đa (ΔU%)":
    st.subheader("📏 Tính chiều dài dây tối đa theo % sụt áp")
    U = st.number_input("Điện áp danh định (V):", min_value=0.0)
    I = st.number_input("Dòng điện (A):", min_value=0.0)
    R = st.number_input("Điện trở dây dẫn (Ω/km):", min_value=0.0)
    deltaU_percent = st.number_input("Giới hạn ΔU (%):", min_value=0.0, max_value=100.0, value=5.0)
    Lmax = (U * deltaU_percent / 100) / (2 * I * R) * 1000
    if st.button("Tính chiều dài tối đa"):
        st.success(f"📏 Chiều dài dây tối đa ≈ {Lmax:.1f} m")

elif menu == "Tính điện trở – kháng – trở kháng":
    st.subheader("🧲 Tính R, X và Z của dây")
    R = st.number_input("Điện trở R (Ω):", min_value=0.0)
    X = st.number_input("Điện kháng X (Ω):", min_value=0.0)
    Z = math.sqrt(R**2 + X**2)
    if st.button("Tính trở kháng Z"):
        st.success(f"🔹 Trở kháng Z ≈ {Z:.2f} Ω")

elif menu == "Tính tổn thất công suất trên dây":
    st.subheader("🔥 Tổn thất công suất (Ptt) trên dây dẫn")
    I = st.number_input("Dòng điện I (A):", min_value=0.0)
    R = st.number_input("Điện trở R (Ω):", min_value=0.0)
    Ptt = I**2 * R
    if st.button("Tính tổn thất"):
        st.success(f"🔥 Tổn thất công suất ≈ {Ptt:.2f} W")

elif menu == "Chọn thiết bị bảo vệ (CB)":
    st.subheader("🛡️ Chọn thiết bị bảo vệ (CB, MCCB)")
    Itt = st.number_input("Dòng tải (A):", min_value=0.0)
    he_so = st.slider("Hệ số an toàn:", 1.0, 2.0, 1.25, step=0.05)
    In = Itt * he_so
    if st.button("Tính In CB"):
        st.success(f"🔌 Dòng định mức CB nên chọn ≥ {In:.0f} A")
