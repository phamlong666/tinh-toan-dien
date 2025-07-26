# app.py – Phiên bản đầy đủ: Tính toán điện + Chuyển đổi + Bảo vệ + Công thức ngược
# Mắt Nâu – EVNNPC Điện lực Định Hóa

import streamlit as st
import math
from PIL import Image
import pandas as pd
import io
from datetime import datetime
import base64 # Import thư viện base64 để mã hóa PDF cho nút xem phiếu

# Import các thành phần từ ReportLab để tạo PDF
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Đăng ký font hỗ trợ tiếng Việt (ví dụ: DejaVuSans, cần có sẵn trong môi trường)
# Hoặc bạn có thể sử dụng một font khác có sẵn trên hệ thống hoặc cung cấp file .ttf
try:
    pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', 'DejaVuSans-Bold.ttf'))
except Exception:
    st.warning("⚠️ Không tìm thấy font 'DejaVuSans.ttf' hoặc 'DejaVuSans-Bold.ttf'. PDF có thể không hiển thị tiếng Việt đúng cách. Vui lòng đảm bảo các file font này nằm cùng thư mục với app.py hoặc sử dụng font mặc định của ReportLab.")
    # Fallback to default fonts if custom font is not found
    pass


# Lưu ý: Để đọc file Excel (.xlsx), thư viện 'openpyxl' là bắt buộc.
# Nếu gặp lỗi liên quan đến 'openpyxl', vui lòng cài đặt bằng lệnh sau trong terminal:
# pip install openpyxl
# hoặc
# conda install openpyxl

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

# Hàm để tải dữ liệu bảng tra từ file Excel
@st.cache_data # Sử dụng cache để không phải đọc lại file mỗi lần tương tác
def load_cable_data(copper_file_path, aluminum_file_path):
    copper_data = {}
    aluminum_data = {}
    
    # Hàm trợ giúp để đọc từng file Excel và xử lý lỗi
    def read_excel_file(file_path, material_type):
        try:
            df = pd.read_excel(file_path)
            
            # Kiểm tra số lượng cột tối thiểu
            if df.shape[1] < 3:
                st.error(f"❌ Lỗi cấu trúc file Excel {material_type}: File '{file_path}' cần ít nhất 3 cột (Tiết diện, Khả năng chịu tải không khí, Khả năng chịu tải trong ống).")
                return {}
            
            # Kiểm tra dữ liệu cột Tiết diện và Khả năng chịu tải có phải là số không
            col_sizes = df.iloc[:, 0]
            col_capacities_in_air = df.iloc[:, 1] # Cột thứ 2: Khả năng chịu tải trong không khí
            col_capacities_in_conduit = df.iloc[:, 2] # Cột thứ 3: Khả năng chịu tải đi trong ống

            if not pd.api.types.is_numeric_dtype(col_sizes) or \
               not pd.api.types.is_numeric_dtype(col_capacities_in_air) or \
               not pd.api.types.is_numeric_dtype(col_capacities_in_conduit):
                st.error(f"❌ Lỗi dữ liệu file Excel {material_type}: Cột tiết diện (cột 1), cột khả năng chịu tải không khí (cột 2) hoặc cột khả năng chịu tải trong ống (cột 3) trong file '{file_path}' chứa dữ liệu không phải số. Vui lòng kiểm tra lại.")
                return {}

            # Trả về dictionary chứa cả hai loại khả năng chịu tải
            return {
                'in_air': dict(zip(col_sizes, col_capacities_in_air)),
                'in_conduit': dict(zip(col_sizes, col_capacities_in_conduit))
            }
        except FileNotFoundError:
            st.error(f"❌ Không tìm thấy file Excel '{file_path}' cho dây {material_type}. Vui lòng đảm bảo file nằm cùng thư mục với app.py.")
            return {}
        except Exception as e:
            if "No module named 'openpyxl'" in str(e) or "Missing optional dependency 'openpyxl'" in str(e):
                st.error(f"❌ Lỗi: Thiếu thư viện 'openpyxl' để đọc file Excel dây {material_type}. Vui lòng cài đặt bằng lệnh: `pip install openpyxl`")
            else:
                st.error(f"❌ Có lỗi xảy ra khi đọc file Excel dây {material_type}: {e}. Vui lòng kiểm tra định dạng file và cấu trúc cột.")
            return {}

    copper_data = read_excel_file(copper_file_path, "Đồng")
    aluminum_data = read_excel_file(aluminum_file_path, "Nhôm")
        
    return copper_data, aluminum_data

# Tải dữ liệu bảng tra khi ứng dụng khởi động
# Đảm bảo tên file Excel là chính xác và nằm cùng thư mục với app.py
# Đã đổi tên file để tránh lỗi ký tự đặc biệt/khoảng trắng
copper_cable_data, aluminum_cable_data = load_cable_data(
    'cadivi_dong.xlsx', # Tên file mới
    'cadivi_nhom.xlsx'  # Tên file mới
)


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
            I = P * 1000 / (U * cos_phi) if U != 0 and cos_phi != 0 else 0
            st.success(f"Dòng điện I ≈ {I:.2f} A")

    elif sub_menu_tinh_toan == "Tính công suất (P)":
        st.header("⚡ Tính công suất (P)")
        pha = st.radio("Loại điện:", ["1 pha", "3 pha"], key="p2")
        I = st.number_input("Dòng điện I (A):", min_value=0.0)
        U = st.number_input("Điện áp U (V):", min_value=0.0, key="u2")
        cos_phi = st.slider("Hệ số cosφ:", 0.1, 1.0, 0.8, key="c2")
        if st.button("Tính công suất"):
            P = U * I * cos_phi / 1000 if U != 0 and I != 0 and cos_phi != 0 else 0
            if pha == "3 pha":
                P = math.sqrt(3) * U * I * cos_phi / 1000
            st.success(f"Công suất P ≈ {P:.2f} kW")

    elif sub_menu_tinh_toan == "Tính sụt áp (ΔU)":
        st.header("⚡ Tính sụt áp (ΔU)")
        st.latex(r"\Delta U = \frac{k \cdot L \cdot P}{S \cdot U \cdot \cos\varphi \cdot n_{song song}}")
        st.markdown("""
        **Giải thích các thành phần:**
        - \( \Delta U \): Sụt áp (V)
        - \( k \): Hệ số phụ thuộc loại điện và điện trở suất vật liệu (Ω·mm²/m)
            - 1 pha: \( k = 2 \cdot \rho \)
            - 3 pha: \( k = \sqrt{3} \cdot \rho \)
        - \( L \): Chiều dài tuyến (m)
        - \( P \): Công suất tải (W)
        - \( S \): Tiết diện dây dẫn (mm²)
        - \( U \): Điện áp danh định (V)
        - \( \cos\varphi \): Hệ số công suất
        - \( n_{song song} \): Số dây dẫn song song trên mỗi pha
        
        **Mục đích:** Tính toán độ sụt áp trên dây dẫn để đảm bảo điện áp tại tải nằm trong giới hạn cho phép, tránh ảnh hưởng đến hoạt động của thiết bị.
        """, unsafe_allow_html=True)

        # Thêm các trường nhập liệu mới cho Người tính toán
        st.subheader("Thông tin Người tính toán")
        calculator_name_sd = st.text_input("Họ và tên:", value="Mắt Nâu", key="calc_name_sd")
        calculator_title_sd = st.text_input("Chức danh:", value="Kỹ sư điện", key="calc_title_sd")
        calculator_phone_sd = st.text_input("Số điện thoại:", value="0123 456 789", key="calc_phone_sd")

        # Thêm các trường nhập liệu mới cho Khách hàng
        st.subheader("Thông tin Khách hàng")
        customer_name_sd = st.text_input("Tên khách hàng:", value="Điện lực Định Hóa", key="cust_name_sd")
        customer_address_sd = st.text_input("Địa chỉ:", value="Thị trấn Chợ Chu, Định Hóa, Thái Nguyên", key="cust_address_sd")
        customer_phone_sd = st.text_input("Số điện thoại khách hàng:", value="0987 654 321", key="cust_phone_sd")
        
        # Lấy thời gian thực (chỉ ngày, tháng, năm)
        current_date_sd = datetime.now().strftime("Ngày %d tháng %m năm %Y")
        st.markdown(f"**Thời gian lập phiếu:** {current_date_sd}")

        col1, col2 = st.columns(2)
        with col1:
            current_type_sd = st.radio("Loại dòng điện:", ["1 pha xoay chiều", "3 pha xoay chiều"], key="current_type_sd")
            U_sd = st.number_input("Điện áp (V):", min_value=0.0, value=220.0, key="U_sd")
            P_sd = st.number_input("Công suất tải (kW):", min_value=0.0, key="P_sd")
            cos_phi_sd = st.slider("Hệ số công suất cosφ:", 0.1, 1.0, 0.85, key="cos_phi_sd")
        with col2:
            material_sd = st.selectbox("Chất liệu dây dẫn:", ["Đồng", "Nhôm"], key="material_sd")
            S_sd = st.number_input("Tiết diện dây dẫn (mm²):", min_value=0.1, value=10.0, key="S_sd")
            L_sd = st.number_input("Chiều dài tuyến (m):", min_value=0.0, value=200.0, key="L_sd")
            n_parallel_sd = st.number_input("Số dây dẫn song song/pha:", min_value=1, value=1, key="n_parallel_sd")
            
        # Nút tính toán
        if st.button("Tính sụt áp"):
            # Tính điện trở suất
            rho_sd = 0.0175 if material_sd == "Đồng" else 0.028

            # Tính dòng điện I
            I_sd = 0.0
            if U_sd != 0 and cos_phi_sd != 0:
                if current_type_sd == "1 pha xoay chiều":
                    I_sd = (P_sd * 1000) / (U_sd * cos_phi_sd)
                elif current_type_sd == "3 pha xoay chiều":
                    I_sd = (P_sd * 1000) / (math.sqrt(3) * U_sd * cos_phi_sd)
            
            # Tính sụt áp Delta U
            deltaU_sd = 0.0
            if S_sd != 0 and n_parallel_sd != 0 and U_sd != 0:
                # Tính tổng trở kháng (chỉ xét R, bỏ qua X để đơn giản)
                # R_total = rho * L / S_effective
                # S_effective = S * n_parallel
                # R_total_per_meter = rho / S_effective
                # Delta U = 2 * I * R_total_per_meter * L (for 1-phase)
                # Delta U = sqrt(3) * I * R_total_per_meter * L (for 3-phase)
                
                # Formula derived from P, U, cos_phi and rho, L, S, n_parallel
                if current_type_sd == "1 pha xoay chiều":
                    deltaU_sd = (2 * rho_sd * L_sd * I_sd) / (S_sd * n_parallel_sd)
                elif current_type_sd == "3 pha xoay chiều":
                    deltaU_sd = (math.sqrt(3) * rho_sd * L_sd * I_sd) / (S_sd * n_parallel_sd)
            
            # Tính sụt áp phần trăm
            deltaU_percent_sd = (deltaU_sd / U_sd) * 100 if U_sd != 0 else 0

            # Tính điện áp tại tải
            U_at_load_sd = U_sd - deltaU_sd

            st.info(f"⚡ Dòng điện tính toán được I ≈ {I_sd:.2f} A")
            st.success(f"⬇️ Sụt áp ΔU ≈ {deltaU_sd:.3f} V")
            st.success(f"📊 Sụt áp ΔU% ≈ {deltaU_percent_sd:.2f} %")
            st.success(f"💡 Điện áp tại tải ≈ {U_at_load_sd:.3f} V")

            # --- Bắt đầu phần tạo và xuất PDF ---
            # Tạo một đối tượng BytesIO để lưu PDF vào bộ nhớ
            # Đã điều chỉnh lề trên và lề dưới để tối ưu hóa không gian
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4,
                                    topMargin=0.75 * inch, # Giảm lề trên
                                    bottomMargin=0.75 * inch) # Giảm lề dưới
            styles = getSampleStyleSheet()

            # Định nghĩa style cho tiếng Việt
            try:
                styles.add(ParagraphStyle(name='TitleStyle', fontName='DejaVuSans-Bold', fontSize=16, alignment=1, spaceAfter=14))
                styles.add(ParagraphStyle(name='Heading2Style', fontName='DejaVuSans-Bold', fontSize=12, spaceAfter=6))
                styles.add(ParagraphStyle(name='NormalStyle', fontName='DejaVuSans', fontSize=10, spaceAfter=6))
                styles.add(ParagraphStyle(name='TableCellStyle', fontName='DejaVuSans', fontSize=9, alignment=1))
                styles.add(ParagraphStyle(name='TableCellBoldStyle', fontName='DejaVuSans-Bold', fontSize=9, alignment=1))
            except KeyError:
                styles.add(ParagraphStyle(name='TitleStyle', fontName='Helvetica-Bold', fontSize=16, alignment=1, spaceAfter=14))
                styles.add(ParagraphStyle(name='Heading2Style', fontName='Helvetica-Bold', fontSize=12, spaceAfter=6))
                styles.add(ParagraphStyle(name='NormalStyle', fontName='Helvetica', fontSize=10, spaceAfter=6))
                styles.add(ParagraphStyle(name='TableCellStyle', fontName='Helvetica', fontSize=9, alignment=1))
                styles.add(ParagraphStyle(name='TableCellBoldStyle', fontName='Helvetica-Bold', fontSize=9, alignment=1))


            story = []

            # Tiêu đề phiếu
            story.append(Paragraph("<b>PHIẾU TÍNH TOÁN SỤT ÁP DÂY CÁP ĐIỆN</b>", styles['TitleStyle']))
            story.append(Spacer(1, 0.2 * inch))

            # Thông tin chung
            story.append(Paragraph("<b>1. THÔNG TIN CHUNG</b>", styles['Heading2Style']))
            story.append(Paragraph(f"<b>Người tính toán:</b> {calculator_name_sd}", styles['NormalStyle']))
            story.append(Paragraph(f"<b>Chức danh:</b> {calculator_title_sd}", styles['NormalStyle']))
            story.append(Paragraph(f"<b>Điện thoại:</b> {calculator_phone_sd}", styles['NormalStyle']))
            story.append(Spacer(1, 0.1 * inch))
            story.append(Paragraph(f"<b>Khách hàng:</b> {customer_name_sd}", styles['NormalStyle']))
            story.append(Paragraph(f"<b>Địa chỉ:</b> {customer_address_sd}", styles['NormalStyle']))
            story.append(Paragraph(f"<b>Điện thoại khách hàng:</b> {customer_phone_sd}", styles['NormalStyle']))
            story.append(Paragraph(f"<b>Thời gian lập phiếu:</b> {current_date_sd}", styles['NormalStyle']))
            story.append(Spacer(1, 0.2 * inch))

            # Thông số đầu vào
            story.append(Paragraph("<b>2. THÔNG SỐ ĐẦU VÀO</b>", styles['Heading2Style']))
            input_data_sd = [
                ["Loại dòng điện:", current_type_sd],
                ["Điện áp (U):", f"{U_sd} V"],
                ["Công suất tải (P):", f"{P_sd} kW"],
                ["Hệ số công suất (cosφ):", cos_phi_sd],
                ["Chất liệu dây dẫn:", material_sd],
                ["Tiết diện dây dẫn (S):", f"{S_sd} mm²"],
                ["Chiều dài tuyến (L):", f"{L_sd} m"],
                ["Số dây dẫn song song/pha:", n_parallel_sd]
            ]
            input_table_sd = Table(input_data_sd, colWidths=[2.5*inch, 3*inch])
            input_table_sd.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('FONTNAME', (0,0), (0,-1), 'DejaVuSans-Bold' if 'DejaVuSans-Bold' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold'),
                ('FONTNAME', (1,0), (1,-1), 'DejaVuSans' if 'DejaVuSans' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'),
                ('FONTSIZE', (0,0), (-1,-1), 10),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ('TOPPADDING', (0,0), (-1,-1), 6),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
            ]))
            story.append(input_table_sd)
            story.append(Spacer(1, 0.2 * inch))

            # Kết quả tính toán
            story.append(Paragraph("<b>3. KẾT QUẢ TÍNH TOÁN</b>", styles['Heading2Style']))
            output_data_sd = [
                ["Dòng điện tính toán (I):", f"{I_sd:.2f} A"],
                ["Sụt áp ΔU:", f"{deltaU_sd:.3f} V"],
                ["Sụt áp ΔU%:", f"{deltaU_percent_sd:.2f} %"],
                ["Điện áp tại tải:", f"{U_at_load_sd:.3f} V"]
            ]
            output_table_sd = Table(output_data_sd, colWidths=[3*inch, 2.5*inch])
            output_table_sd.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('FONTNAME', (0,0), (0,-1), 'DejaVuSans-Bold' if 'DejaVuSans-Bold' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold'),
                ('FONTNAME', (1,0), (1,-1), 'DejaVuSans' if 'DejaVuSans' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'),
                ('FONTSIZE', (0,0), (-1,-1), 10),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ('TOPPADDING', (0,0), (-1,-1), 6),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
            ]))
            story.append(output_table_sd)
            story.append(Spacer(1, 0.5 * inch)) # Thêm khoảng trống trước chữ ký
            
            # Chữ ký
            signature_data_sd = [
                [Paragraph("<b>NGƯỜI TÍNH TOÁN</b>", styles['TableCellBoldStyle']), Paragraph("<b>KHÁCH HÀNG</b>", styles['TableCellBoldStyle'])],
                [Paragraph("(Ký, ghi rõ họ tên)", styles['TableCellStyle']), Paragraph("(Ký, ghi rõ họ tên)", styles['TableCellStyle'])],
                [Spacer(1, 0.8 * inch), Spacer(1, 0.8 * inch)], # Khoảng trống cho chữ ký
                [Paragraph(f"<b>{calculator_name_sd}</b>", styles['TableCellBoldStyle']), Paragraph(f"<b>{customer_name_sd}</b>", styles['TableCellBoldStyle'])]
            ]
            signature_table_sd = Table(signature_data_sd, colWidths=[2.75*inch, 2.75*inch])
            signature_table_sd.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTNAME', (0,0), (-1,-1), 'DejaVuSans' if 'DejaVuSans' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'),
                ('FONTSIZE', (0,0), (-1,-1), 10),
                ('BOTTOMPADDING', (0,0), (-1,-1), 2),
                ('TOPPADDING', (0,0), (-1,-1), 2),
            ]))
            story.append(signature_table_sd)
            story.append(Spacer(1, 0.2 * inch))


            doc.build(story)
            pdf_bytes_sd = buffer.getvalue()
            buffer.close()

            # Lưu PDF bytes vào session state
            st.session_state['pdf_bytes_sd'] = pdf_bytes_sd
            st.session_state['pdf_filename_sd'] = f"Phieu_tinh_sut_ap_{datetime.now().strftime('%Y%m%d')}.pdf"

        # --- Các nút PDF riêng biệt ---
        # Chỉ hiển thị các nút nếu có PDF bytes trong session state (tức là đã tính toán thành công)
        if 'pdf_bytes_sd' in st.session_state and st.session_state['pdf_bytes_sd']:
            st.markdown("---") # Đường phân cách
            st.subheader("Tùy chọn xuất phiếu sụt áp")
            col_pdf1_sd, col_pdf2_sd = st.columns(2)
            with col_pdf1_sd:
                st.download_button(
                    label="Xuất PDF",
                    data=st.session_state['pdf_bytes_sd'],
                    file_name=st.session_state['pdf_filename_sd'],
                    mime="application/pdf",
                    key="download_sd_pdf",
                    help="Tải về phiếu tính toán sụt áp dưới dạng PDF"
                )
            with col_pdf2_sd:
                # Nút "Xem phiếu" sẽ mở PDF trong tab mới
                pdf_base64_sd = base64.b64encode(st.session_state['pdf_bytes_sd']).decode('utf-8')
                
                st.markdown(
                    f"""
                    <a href="data:application/pdf;base64,{pdf_base64_sd}" target="_blank" style="text-decoration: none;">
                        <button style="
                            background-color: #007bff; /* Blue */
                            border: none;
                            color: white;
                            padding: 10px 24px;
                            text-align: center;
                            text-decoration: none;
                            display: inline-block;
                            font-size: 16px;
                            margin: 4px 2px;
                            cursor: pointer;
                            border-radius: 8px;
                        ">Xem phiếu</button>
                    </a>
                    """,
                    unsafe_allow_html=True
                )
                st.info("Nhấn 'Xem phiếu' để mở PDF trong tab mới của trình duyệt. Nếu không mở, vui lòng kiểm tra cài đặt trình duyệt hoặc sử dụng nút 'Xuất PDF'.")
        
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

            st.latex(r"I = \frac{S \times 1000}{\sqrt{3} \times U}")
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

            st.latex(r"I = \frac{S \times 1000}{\sqrt{3} \times 400}")
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
