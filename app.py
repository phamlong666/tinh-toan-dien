# app.py – Phiên bản đầy đủ: Tính toán điện + Chuyển đổi + Bảo vệ + Công thức điện
# Mắt Nâu – Đội quản lý Điện lực khu vực Định Hóa

import streamlit as st
import math
from PIL import Image

# Thiết lập cấu hình trang
st.set_page_config(page_title="Tính Toán Điện – Đội quản lý Điện lực khu vực Định Hóa", page_icon="⚡", layout="wide")

# Tiêu đề chính của ứng dụng
st.markdown("""
<h1 style='text-align: center;'>⚡ Tính Toán Điện – <span style='color:red;'>Đội Quản lý Điện lực khu vực Định Hóa</span></h1>
""", unsafe_allow_html=True)

# Sidebar – chọn chức năng chính
st.sidebar.subheader("📂 Chọn chức năng")
main_menu = st.sidebar.selectbox("", ["Trang chủ", "Tính toán điện", "Công cụ bổ trợ"])

# Xử lý các lựa chọn từ menu chính
if main_menu == "Trang chủ":
    st.markdown("""
    <h3 style='text-align: center;'>👋 Chào mừng đến với ứng dụng Tính Toán Điện</h3>
    <p style='text-align: center;'>Ứng dụng giúp tính nhanh các thông số kỹ thuật điện và hỗ trợ lựa chọn thiết bị phù hợp.</p>
    """, unsafe_allow_html=True)

elif main_menu == "Tính toán điện":
    # Menu con cho các chức năng tính toán điện
    sub_menu_tinh_toan = st.sidebar.selectbox("Chọn loại tính toán:", [
        "Tính dòng điện (I)",
        "Tính công suất (P)",
        "Tính sụt áp (ΔU)",
        "Chọn tiết diện dây dẫn",
        "Chiều dài dây tối đa (ΔU%)",
        "Tính điện trở – kháng – trở kháng",
        "Tính tổn thất công suất trên dây",
        "Chọn thiết bị bảo vệ"
    ])

    # Hiển thị nội dung dựa trên lựa chọn menu con
    if sub_menu_tinh_toan == "Tính dòng điện (I)":
        st.header("⚡ Tính dòng điện (I)")
        pha = st.radio("Loại điện:", ["1 pha", "3 pha"])
        P = st.number_input("Công suất P (kW):", min_value=0.0)
        U = st.number_input("Điện áp U (V):", min_value=0.0)
        cos_phi = st.slider("Hệ số cosφ:", 0.1, 1.0, 0.8)
        if st.button("Tính dòng điện"):
            I = P * 1000 / (U * cos_phi) if pha == "1 pha" else P * 1000 / (math.sqrt(3) * U * cos_phi)
            st.success(f"Dòng điện I ≈ {I:.2f} A")

    elif sub_menu_tinh_toan == "Tính công suất (P)":
        st.header("⚡ Tính công suất (P)")
        pha = st.radio("Loại điện:", ["1 pha", "3 pha"], key="p2")
        I = st.number_input("Dòng điện I (A):", min_value=0.0)
        U = st.number_input("Điện áp U (V):", min_value=0.0, key="u2")
        cos_phi = st.slider("Hệ số cosφ:", 0.1, 1.0, 0.8, key="c2")
        if st.button("Tính công suất"):
            P = U * I * cos_phi / 1000 if pha == "1 pha" else math.sqrt(3) * U * I * cos_phi / 1000
            st.success(f"Công suất P ≈ {P:.2f} kW")

    elif sub_menu_tinh_toan == "Tính sụt áp (ΔU)":
        st.header("⚡ Tính sụt áp (ΔU)")
        I = st.number_input("Dòng điện I (A):", min_value=0.0)
        rho = st.selectbox("Chất liệu dây dẫn", ["Đồng", "Nhôm"])
        S = st.number_input("Tiết diện dây dẫn (mm²):", min_value=0.1)
        L = st.number_input("Chiều dài dây (m):", min_value=0.0)
        rho_value = 0.0175 if rho == "Đồng" else 0.028
        R = rho_value * (2 * L) / S
        Udrop = I * R
        if st.button("Tính sụt áp"):
            st.success(f"Sụt áp ΔU ≈ {Udrop:.2f} V")

    elif sub_menu_tinh_toan == "Chọn tiết diện dây dẫn":
        st.header("⚡ Chọn tiết diện dây dẫn")
        I = st.number_input("Dòng điện I (A):", min_value=0.0)
        J = st.number_input("Mật độ dòng điện J (A/mm²):", min_value=1.0, value=4.0)
        S = I / J
        if st.button("Tính tiết diện"):
            st.success(f"Tiết diện S tối thiểu ≈ {S:.2f} mm²")

    elif sub_menu_tinh_toan == "Chiều dài dây tối đa (ΔU%)":
        st.header("⚡ Chiều dài dây tối đa (ΔU%)")
        U = st.number_input("Điện áp danh định (V):", min_value=0.0)
        I = st.number_input("Dòng điện (A):", min_value=0.0)
        R = st.number_input("R đơn vị (Ω/km):", min_value=0.0)
        deltaU_percent = st.number_input("Giới hạn ΔU (%):", value=5.0)
        Lmax = (U * deltaU_percent / 100) / (2 * I * R) * 1000
        if st.button("Tính chiều dài tối đa"):
            st.success(f"Chiều dài dây tối đa ≈ {Lmax:.1f} m")

    elif sub_menu_tinh_toan == "Tính điện trở – kháng – trở kháng":
        st.header("⚡ Tính điện trở – kháng – trở kháng")
        R = st.number_input("Điện trở R (Ω):", min_value=0.0)
        X = st.number_input("Điện kháng X (Ω):", min_value=0.0)
        Z = math.sqrt(R**2 + X**2)
        if st.button("Tính Z"):
            st.success(f"Tổng trở Z ≈ {Z:.2f} Ω")

    elif sub_menu_tinh_toan == "Tính tổn thất công suất trên dây":
        st.header("⚡ Tính tổn thất công suất trên dây")
        I = st.number_input("Dòng điện I (A):", min_value=0.0)
        R = st.number_input("Điện trở R (Ω):", min_value=0.0)
        Ptt = I**2 * R
        if st.button("Tính tổn thất"):
            st.success(f"Ptt ≈ {Ptt:.2f} W")

    elif sub_menu_tinh_toan == "Chọn thiết bị bảo vệ":
        st.header("🔌 Tính thiết bị bảo vệ (CB/MCCB)")
        # Phân loại thiết bị
        nhom = st.selectbox("Chọn nhóm thiết bị", ["Chọn nhóm", "Trung thế", "Hạ thế", "Hộ gia đình"])

        if nhom == "Chọn nhóm":
            st.warning("Vui lòng chọn nhóm thiết bị.")
        else:
            Itt = st.number_input("Dòng tải (A):", min_value=0.0, step=0.01, format="%.2f")
            he_so = st.slider("Hệ số an toàn:", 1.0, 2.0, 1.25, 0.05)
            In = Itt * he_so
            if st.button("Tính In CB"):
                st.success(f"Nên chọn CB có In ≥ {In:.0f} A")

elif main_menu == "Công cụ bổ trợ":
    # Menu con cho các công cụ bổ trợ
    sub_menu_cong_cu = st.sidebar.selectbox("Chọn công cụ:", [
        "Chuyển đổi đơn vị",
        "Công thức điện"
    ])

    # Hiển thị nội dung dựa trên lựa chọn menu con
    if sub_menu_cong_cu == "Chuyển đổi đơn vị":
        st.header("🔄 Chuyển đổi đơn vị")
        chon = st.selectbox("Chuyển đổi loại:", ["BTU ➜ kW", "HP ➜ kW", "kVA ➜ kW"])
        value = st.number_input("Giá trị cần chuyển đổi:", min_value=0.0)
        if chon == "BTU ➜ kW":
            result = value / 3412.14
        elif chon == "HP ➜ kW":
            result = value * 0.7457
        elif chon == "kVA ➜ kW":
            cos = st.slider("Hệ số cosφ:", 0.1, 1.0, 0.8, key="cosva")
            result = value * cos
        else:
            result = 0 # Default value if no conversion type is selected
        if st.button("Chuyển đổi"):
            st.success(f"Kết quả: ≈ {result:.2f} kW")

    elif sub_menu_cong_cu == "Công thức điện":
        st.header("📐 Tính toán theo công thức điện")
        cong_thuc = st.selectbox("Tính ngược theo:", ["ΔU & I → R", "Ptt & I → R", "ΔU & R → I", "Ptt & R → I"])
        if cong_thuc == "ΔU & I → R":
            u = st.number_input("ΔU (V):")
            i = st.number_input("I (A):")
            r = u / i if i != 0 else 0
            if st.button("Tính R"):
                st.success(f"R ≈ {r:.3f} Ω")
        elif cong_thuc == "Ptt & I → R":
            ptt = st.number_input("Ptt (W):")
            i = st.number_input("I (A):")
            r = ptt / (i**2) if i != 0 else 0
            if st.button("Tính R"):
                st.success(f"R ≈ {r:.3f} Ω")
        elif cong_thuc == "ΔU & R → I":
            u = st.number_input("ΔU (V):")
            r = st.number_input("R (Ω):")
            i = u / r if r != 0 else 0
            if st.button("Tính I"):
                st.success(f"I ≈ {i:.3f} A")
        elif cong_thuc == "Ptt & R → I":
            ptt = st.number_input("Ptt (W):")
            r = st.number_input("R (Ω):")
            i = math.sqrt(ptt / r) if r != 0 else 0
            if st.button("Tính I"):
                st.success(f"I ≈ {i:.3f} A")
