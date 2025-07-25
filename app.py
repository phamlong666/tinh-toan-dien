# app.py – Phiên bản đầy đủ: Tính toán điện + Chuyển đổi + Bảo vệ + Công thức ngược
# Mắt Nâu – EVNNPC Điện lực Định Hóa

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
# Sử dụng st.radio để tạo các nút lựa chọn riêng biệt
main_menu = st.sidebar.radio("", ["Trang chủ", "Tính toán điện", "Chuyển đổi đơn vị", "Công thức ngược"])

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

        st.latex(r"S = \frac{2 \cdot \rho \cdot L \cdot I}{U \cdot (\Delta U\% / 100)}")
        st.markdown("""
        **Giải thích các thành phần:**
        - \( S \): Tiết diện dây dẫn cần chọn (mm²)  
        - \( \rho \): Điện trở suất của vật liệu dây (Ω·mm²/m)  
        - \( L \): Chiều dài dây dẫn 1 chiều (m)  
        - \( I \): Dòng điện tải (A)  
        - \( U \): Điện áp danh định (V)  
        - \( \Delta U\% \): Sụt áp cho phép (%)  

        **Mục đích:**  
        Tính tiết diện dây dẫn phù hợp với công suất tải, chiều dài và điều kiện sụt áp cho phép.  
        Giúp chọn dây dẫn đúng kỹ thuật và đảm bảo an toàn vận hành.
        """, unsafe_allow_html=True)

        pha = st.radio("Loại điện:", ["1 pha", "3 pha"])
        P = st.number_input("Công suất tải (kW):", min_value=0.0)
        U = st.number_input("Điện áp danh định (V):", min_value=0.0, value=220.0)
        cos_phi = st.slider("Hệ số công suất cosφ:", 0.1, 1.0, 0.85)
        L = st.number_input("Chiều dài dây dẫn (m):", min_value=0.0)
        deltaU_percent = st.number_input("Sụt áp cho phép (%):", min_value=1.0, value=4.0)
        material = st.selectbox("Chất liệu dây dẫn:", ["Đồng", "Nhôm"])

        if st.button("Tính tiết diện"):
            I = P * 1000 / (U * cos_phi) if pha == "1 pha" else P * 1000 / (math.sqrt(3) * U * cos_phi)
            rho = 0.0175 if material == "Đồng" else 0.028
            deltaU = U * deltaU_percent / 100
            S = (2 * rho * L * I) / deltaU
            standard_sizes = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240]
            closest_standard = min(standard_sizes, key=lambda x: abs(x - S))
            st.success(f"Tiết diện S tính được ≈ {S:.2f} mm²")
            st.info(f"👉 Gợi ý chọn tiết diện chuẩn thương mại: **{closest_standard} mm²**")

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

        nhom = st.selectbox("Chọn nhóm thiết bị", ["Chọn nhóm", "Trung thế (cấp 22–110kV)", "Hạ thế (phía 0.4kV)", "Hộ gia đình"])

        if nhom == "Chọn nhóm":
            st.warning("Vui lòng chọn nhóm thiết bị.")

        elif nhom == "Trung thế (cấp 22–110kV)":
            st.subheader("⚙️ Tính dòng điện trung thế (tham khảo)")
            cap_dien_ap = st.selectbox("Cấp điện áp trung thế:", ["110 kV", "35 kV", "22 kV", "10 kV"])
            cong_suat = st.selectbox("Công suất MBA (kVA):", [50, 75, 100, 160, 180, 250, 320, 400, 560, 1000])
            U = 110000 if cap_dien_ap == "110 kV" else 35000 if cap_dien_ap == "35 kV" else 22000 if cap_dien_ap == "22 kV" else 10000
            I = cong_suat * 1000 / (math.sqrt(3) * U)
            he_so = st.slider("Hệ số an toàn:", 1.0, 2.0, 1.25, 0.05)
            In = I * he_so

            st.latex(r"I = rac{S 	imes 1000}{\sqrt{3} 	imes U}")
            st.markdown("""
            **Trong đó**:
            - \( S \): Công suất MBA (kVA)
            - \( U \): Cấp điện áp (V)
            - \( I \): Dòng điện định mức (A)

            **Mục đích**: Tính dòng điện để chọn thiết bị bảo vệ trung thế phù hợp.
            """, unsafe_allow_html=True)

            st.success(f"Dòng điện I ≈ {I:.2f} A → Nên chọn CB có In ≥ {In:.0f} A")

        elif nhom == "Hạ thế (phía 0.4kV)":
            st.subheader("⚙️ Tính dòng điện phía hạ áp 0.4kV")
            cong_suat = st.selectbox("Công suất MBA (kVA):", [50, 75, 100, 160, 180, 250, 320, 400, 560, 1000])
            U = 400
            I = cong_suat * 1000 / (math.sqrt(3) * U)
            he_so = st.slider("Hệ số an toàn:", 1.0, 2.0, 1.25, 0.05)
            In = I * he_so

            st.latex(r"I = rac{S 	imes 1000}{\sqrt{3} 	imes 400}")
            st.markdown("""
            **Trong đó**:
            - \( S \): Công suất MBA (kVA)
            - \( U = 400 \) V: Điện áp hạ áp
            - \( I \): Dòng điện định mức phía hạ áp

            **Mục đích**: Tính dòng điện phía hạ áp để lựa chọn CB/AB phù hợp lắp đặt tại tủ tổng.
            """, unsafe_allow_html=True)

            st.success(f"Dòng điện I ≈ {I:.2f} A → Nên chọn CB có In ≥ {In:.0f} A")
elif main_menu == "Chuyển đổi đơn vị":
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

elif main_menu == "Công thức ngược":
    st.header("📐 Tính toán theo công thức ngược")
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
