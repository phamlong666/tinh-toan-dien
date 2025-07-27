# app.py – Phiên bản đầy đủ: Tính toán điện + Chuyển đổi + Bảo vệ + Công thức điện

# Mắt Nâu – Đội quản lý Điện lực khu vực Định Hóa

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
main_menu = st.sidebar.radio("", ["Trang chủ", "Tính toán điện", "Chuyển đổi đơn vị", "Công thức điện"])

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

def latex_to_simple_text(latex_str):
    """Converts a subset of LaTeX formulas to a simpler text format for PDF."""
    # Split by common separators if multiple formulas are combined
    parts = []
    if "hoặc" in latex_str:
        parts = latex_str.split("hoặc")
    elif "\n" in latex_str:
        parts = latex_str.split("\n")
    else:
        parts = [latex_str]

    simplified_parts = []
    for part in parts:
        simple_str = part.replace(r"\(", "").replace(r"\)", "").strip()
        
        # Replace common LaTeX commands with readable text/symbols
        simple_str = simple_str.replace(r"\cdot", "*")
        simple_str = simple_str.replace(r"\sqrt{3}", "sqrt(3)")
        simple_str = simple_str.replace(r"\cos\varphi", "cos(phi)")
        simple_str = simple_str.replace(r"\Delta U", "Delta U")
        simple_str = simple_str.replace(r"\text{(1 pha)}", "(1 pha)")
        simple_str = simple_str.replace(r"\text{(3 pha)}", "(3 pha)")
        simple_str = simple_str.replace(r"n_{song song}", "n_song_song")
        simple_str = simple_str.replace(r"R_{don\_vi}", "R_don_vi")
        simple_str = simple_str.replace(r"P_{tt}", "P_tt")
        simple_str = simple_str.replace(r"L_{max}", "L_max")
        simple_str = simple_str.replace(r"\rho", "rho")

        # Handle powers like R^2, X^2, I^2
        simple_str = simple_str.replace("R^2", "R^2")
        simple_str = simple_str.replace("X^2", "X^2")
        simple_str = simple_str.replace("I^2", "I^2")

        # Handle fractions: \frac{numerator}{denominator}
        while r"\frac" in simple_str:
            start_frac = simple_str.find(r"\frac")
            num_start = simple_str.find("{", start_frac) + 1
            num_end = simple_str.find("}", num_start)
            numerator = simple_str[num_start:num_end]

            den_start = simple_str.find("{", num_end + 1) + 1
            den_end = simple_str.find("}", den_start)
            denominator = simple_str[den_start:den_end]
            
            simple_str = simple_str[:start_frac] + f"({numerator})/({denominator})" + simple_str[den_end+1:]

        # Handle square roots: \sqrt{expression}
        while r"\sqrt" in simple_str:
            start_sqrt = simple_str.find(r"\sqrt")
            expr_start = simple_str.find("{", start_sqrt) + 1
            expr_end = simple_str.find("}", expr_start)
            expression = simple_str[expr_start:expr_end]
            simple_str = simple_str[:start_sqrt] + f"sqrt({expression})" + simple_str[expr_end+1:]
        
        simplified_parts.append(simple_str.strip())
    
    return " ; ".join(simplified_parts) # Join with a semicolon for readability


# Hàm tạo PDF chung
def create_pdf(title, formula_latex_str, formula_explanation, input_params, output_results, calculator_info, customer_info):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            topMargin=0.75 * inch,
                            bottomMargin=0.75 * inch)
    styles = getSampleStyleSheet()

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

    story.append(Paragraph(f"<b>PHIẾU TÍNH TOÁN {title.upper()}</b>", styles['TitleStyle']))
    story.append(Spacer(1, 0.2 * inch))

    # Thông tin chung
    story.append(Paragraph("<b>1. THÔNG TIN CHUNG</b>", styles['Heading2Style']))
    story.append(Paragraph(f"<b>Người tính toán:</b> {calculator_info['name']}", styles['NormalStyle']))
    story.append(Paragraph(f"<b>Chức danh:</b> {calculator_info['title']}", styles['NormalStyle']))
    story.append(Paragraph(f"<b>Điện thoại:</b> {calculator_info['phone']}", styles['NormalStyle']))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(f"<b>Khách hàng:</b> {customer_info['name']}", styles['NormalStyle']))
    story.append(Paragraph(f"<b>Địa chỉ:</b> {customer_info['address']}", styles['NormalStyle']))
    story.append(Paragraph(f"<b>Điện thoại khách hàng:</b> {customer_info['phone']}", styles['NormalStyle']))
    story.append(Paragraph(f"<b>Thời gian lập phiếu:</b> {datetime.now().strftime('Ngày %d tháng %m năm %Y')}", styles['NormalStyle']))
    story.append(Spacer(1, 0.2 * inch))

    # Công thức và giải thích
    story.append(Paragraph("<b>2. CÔNG THỨC VÀ GIẢI THÍCH</b>", styles['Heading2Style']))
    # Display the raw LaTeX string
    story.append(Paragraph(f"<b>Công thức (LaTeX):</b> {formula_latex_str}", styles['NormalStyle']))
    # Display the simplified readable version
    formula_readable_str = latex_to_simple_text(formula_latex_str)
    story.append(Paragraph(f"<b>Công thức (Đơn giản):</b> {formula_readable_str}", styles['NormalStyle']))
    story.append(Paragraph(f"<b>Giải thích:</b> {formula_explanation}", styles['NormalStyle']))
    story.append(Spacer(1, 0.2 * inch))

    # Thông số đầu vào
    story.append(Paragraph("<b>3. THÔNG SỐ ĐẦU VÀO</b>", styles['Heading2Style']))
    input_table_data = []
    for label, value in input_params.items():
        input_table_data.append([f"<b>{label}:</b>", str(value)])
    input_table = Table(input_table_data, colWidths=[2.5*inch, 3*inch])
    input_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (0,-1), 'DejaVuSans-Bold' if 'DejaVuSans-Bold' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold'),
        ('FONTNAME', (1,0), (1,-1), 'DejaVuSans' if 'DejaVuSans' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
    ]))
    story.append(input_table)
    story.append(Spacer(1, 0.2 * inch))

    # Kết quả tính toán
    story.append(Paragraph("<b>4. KẾT QUẢ TÍNH TOÁN</b>", styles['Heading2Style']))
    output_table_data = []
    for label, value in output_results.items():
        output_table_data.append([f"<b>{label}:</b>", str(value)])
    output_table = Table(output_table_data, colWidths=[3*inch, 2.5*inch])
    output_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (0,-1), 'DejaVuSans-Bold' if 'DejaVuSans-Bold' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold'),
        ('FONTNAME', (1,0), (1,-1), 'DejaVuSans' if 'DejaVuSans' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
    ]))
    story.append(output_table)
    story.append(Spacer(1, 0.5 * inch))
    
    # Chữ ký
    signature_data = [
        [Paragraph("<b>NGƯỜI TÍNH TOÁN</b>", styles['TableCellBoldStyle']), Paragraph("<b>KHÁCH HÀNG</b>", styles['TableCellBoldStyle'])],
        [Paragraph("(Ký, ghi rõ họ tên)", styles['TableCellStyle']), Paragraph("(Ký, ghi rõ họ tên)", styles['TableCellStyle'])],
        [Spacer(1, 0.8 * inch), Spacer(1, 0.8 * inch)],
        [Paragraph(f"<b>{calculator_info['name']}</b>", styles['TableCellBoldStyle']), Paragraph(f"<b>{customer_info['name']}</b>", styles['TableCellBoldStyle'])]
    ]
    signature_table = Table(signature_data, colWidths=[2.75*inch, 2.75*inch])
    signature_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,-1), 'DejaVuSans' if 'DejaVuSans' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(signature_table)
    story.append(Spacer(1, 0.2 * inch))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

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
        # LaTeX for UI
        st.latex(r"I = \frac{P \cdot 1000}{U \cdot \cos\varphi} \quad \text{(1 pha)}")
        st.latex(r"I = \frac{P \cdot 1000}{\sqrt{3} \cdot U \cdot \cos\varphi} \quad \text{(3 pha)}")
        st.markdown("""
        **Giải thích các thành phần:**
        - \( I \): Dòng điện (A)
        - \( P \): Công suất tải (kW)
        - \( U \): Điện áp (V)
        - \( \cos\varphi \): Hệ số công suất
        
        **Mục đích:** Tính toán dòng điện chạy trong mạch để lựa chọn dây dẫn và thiết bị bảo vệ phù hợp.
        """, unsafe_allow_html=True)

        st.subheader("Thông tin Người tính toán")
        calculator_name_i = st.text_input("Họ và tên:", value="Hà Thị Lê", key="calc_name_i")
        calculator_title_i = st.text_input("Chức danh:", value="Tổ trưởng tổ KDDV", key="calc_title_i")
        calculator_phone_i = st.text_input("Số điện thoại:", value="0978578777", key="calc_phone_i")

        st.subheader("Thông tin Khách hàng")
        customer_name_i = st.text_input("Tên khách hàng:", value="Phạm Hồng Long", key="cust_name_i")
        customer_address_i = st.text_input("Địa chỉ:", value="xã Định Hóa, tỉnh Thái Nguyên", key="cust_address_i")
        customer_phone_i = st.text_input("Số điện thoại khách hàng:", value="0968552888", key="cust_phone_i")
        
        current_date_i = datetime.now().strftime("Ngày %d tháng %m năm %Y")
        st.markdown(f"**Thời gian lập phiếu:** {current_date_i}")

        col1, col2 = st.columns(2)
        with col1:
            pha_i = st.radio("Loại điện:", ["1 pha", "3 pha"], key="pha_i")
            P_i = st.number_input("Công suất P (kW):", min_value=0.0, key="P_i")
        with col2:
            U_i = st.number_input("Điện áp U (V):", min_value=0.0, key="U_i")
            cos_phi_i = st.slider("Hệ số cosφ:", 0.1, 1.0, 0.8, key="cos_phi_i")
        
        if st.button("Tính dòng điện", key="btn_calc_i"):
            I_result = 0.0
            if U_i != 0 and cos_phi_i != 0:
                if pha_i == "1 pha":
                    I_result = P_i * 1000 / (U_i * cos_phi_i)
                elif pha_i == "3 pha":
                    I_result = P_i * 1000 / (math.sqrt(3) * U_i * cos_phi_i)
            st.success(f"Dòng điện I ≈ {I_result:.2f} A")

            calculator_info = {
                'name': calculator_name_i,
                'title': calculator_title_i,
                'phone': calculator_phone_i
            }
            customer_info = {
                'name': customer_name_i,
                'address': customer_address_i,
                'phone': customer_phone_i
            }
            input_params = {
                "Loại điện": pha_i,
                "Công suất P": f"{P_i} kW",
                "Điện áp U": f"{U_i} V",
                "Hệ số cosφ": cos_phi_i
            }
            output_results = {
                "Dòng điện I": f"{I_result:.2f} A"
            }
            # Combine LaTeX strings for PDF
            formula_latex_str_i_pdf = (
                r"1 pha: \(I = \frac{P \cdot 1000}{U \cdot \cos\varphi}\) "
                r"hoặc 3 pha: \(I = \frac{P \cdot 1000}{\sqrt{3} \cdot U \cdot \cos\varphi}\)"
            )
            formula_explanation_i = "Công thức tính dòng điện dựa trên công suất, điện áp và hệ số công suất cho hệ thống 1 pha hoặc 3 pha."

            pdf_bytes = create_pdf("DÒNG ĐIỆN", formula_latex_str_i_pdf, formula_explanation_i, input_params, output_results, calculator_info, customer_info)
            st.session_state['pdf_bytes_i'] = pdf_bytes
            st.session_state['pdf_filename_i'] = f"Phieu_tinh_dong_dien_{datetime.now().strftime('%Y%m%d')}.pdf"

        if 'pdf_bytes_i' in st.session_state and st.session_state['pdf_bytes_i']:
            st.markdown("---")
            st.subheader("Tùy chọn xuất phiếu dòng điện")
            col_pdf1_i, col_pdf2_i = st.columns(2)
            with col_pdf1_i:
                st.download_button(
                    label="Xuất PDF",
                    data=st.session_state['pdf_bytes_i'],
                    file_name=st.session_state['pdf_filename_i'],
                    mime="application/pdf",
                    key="download_i_pdf"
                )
            with col_pdf2_i:
                pdf_base64_i = base64.b64encode(st.session_state['pdf_bytes_i']).decode('utf-8')
                st.markdown(
                    f"""
                    <a href="data:application/pdf;base64,{pdf_base64_i}" target="_blank" style="text-decoration: none;">
                        <button style="
                            background-color: #007bff;
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

    elif sub_menu_tinh_toan == "Tính công suất (P)":
        st.header("⚡ Tính công suất (P)")
        # LaTeX for UI
        st.latex(r"P = U \cdot I \cdot \cos\varphi \quad \text{(1 pha)}")
        st.latex(r"P = \sqrt{3} \cdot U \cdot I \cdot \cos\varphi \quad \text{(3 pha)}")
        st.markdown("""
        **Giải thích các thành phần:**
        - \( P \): Công suất (W hoặc kW)
        - \( U \): Điện áp (V)
        - \( I \): Dòng điện (A)
        - \( \cos\varphi \): Hệ số công suất
        
        **Mục đích:** Tính toán công suất tiêu thụ hoặc công suất của nguồn điện dựa trên điện áp, dòng điện và hệ số công suất.
        """, unsafe_allow_html=True)

        st.subheader("Thông tin Người tính toán")
        calculator_name_p = st.text_input("Họ và tên:", value="Hà Thị Lê", key="calc_name_p")
        calculator_title_p = st.text_input("Chức danh:", value="Tổ trưởng tổ KDDV", key="calc_title_p")
        calculator_phone_p = st.text_input("Số điện thoại:", value="0978578777", key="calc_phone_p")

        st.subheader("Thông tin Khách hàng")
        customer_name_p = st.text_input("Tên khách hàng:", value="Phạm Hồng Long", key="cust_name_p")
        customer_address_p = st.text_input("Địa chỉ:", value="xã Định Hóa, tỉnh Thái Nguyên", key="cust_address_p")
        customer_phone_p = st.text_input("Số điện thoại khách hàng:", value="0968552888", key="cust_phone_p")
        
        current_date_p = datetime.now().strftime("Ngày %d tháng %m năm %Y")
        st.markdown(f"**Thời gian lập phiếu:** {current_date_p}")

        col1, col2 = st.columns(2)
        with col1:
            pha_p = st.radio("Loại điện:", ["1 pha", "3 pha"], key="pha_p")
            I_p = st.number_input("Dòng điện I (A):", min_value=0.0, key="I_p")
        with col2:
            U_p = st.number_input("Điện áp U (V):", min_value=0.0, key="U_p")
            cos_phi_p = st.slider("Hệ số cosφ:", 0.1, 1.0, 0.8, key="cos_phi_p")
        
        if st.button("Tính công suất", key="btn_calc_p"):
            P_result = 0.0
            if U_p != 0 and I_p != 0 and cos_phi_p != 0:
                if pha_p == "1 pha":
                    P_result = U_p * I_p * cos_phi_p / 1000
                elif pha_p == "3 pha":
                    P_result = math.sqrt(3) * U_p * I_p * cos_phi_p / 1000
            st.success(f"Công suất P ≈ {P_result:.2f} kW")

            calculator_info = {
                'name': calculator_name_p,
                'title': calculator_title_p,
                'phone': calculator_phone_p
            }
            customer_info = {
                'name': customer_name_p,
                'address': customer_address_p,
                'phone': customer_phone_p
            }
            input_params = {
                "Loại điện": pha_p,
                "Dòng điện I": f"{I_p} A",
                "Điện áp U": f"{U_p} V",
                "Hệ số cosφ": cos_phi_p
            }
            output_results = {
                "Công suất P": f"{P_result:.2f} kW"
            }
            # Combine LaTeX strings for PDF
            formula_latex_str_p_pdf = (
                r"1 pha: \(P = U \cdot I \cdot \cos\varphi\) "
                r"hoặc 3 pha: \(P = \sqrt{3} \cdot U \cdot I \cdot \cos\varphi\)"
            )
            formula_explanation_p = "Công thức tính công suất tiêu thụ hoặc công suất của nguồn điện dựa trên điện áp, dòng điện và hệ số công suất."

            pdf_bytes = create_pdf("CÔNG SUẤT", formula_latex_str_p_pdf, formula_explanation_p, input_params, output_results, calculator_info, customer_info)
            st.session_state['pdf_bytes_p'] = pdf_bytes
            st.session_state['pdf_filename_p'] = f"Phieu_tinh_cong_suat_{datetime.now().strftime('%Y%m%d')}.pdf"

        if 'pdf_bytes_p' in st.session_state and st.session_state['pdf_bytes_p']:
            st.markdown("---")
            st.subheader("Tùy chọn xuất phiếu công suất")
            col_pdf1_p, col_pdf2_p = st.columns(2)
            with col_pdf1_p:
                st.download_button(
                    label="Xuất PDF",
                    data=st.session_state['pdf_bytes_p'],
                    file_name=st.session_state['pdf_filename_p'],
                    mime="application/pdf",
                    key="download_p_pdf"
                )
            with col_pdf2_p:
                pdf_base64_p = base64.b64encode(st.session_state['pdf_bytes_p']).decode('utf-8')
                st.markdown(
                    f"""
                    <a href="data:application/pdf;base64,{pdf_base64_p}" target="_blank" style="text-decoration: none;">
                        <button style="
                            background-color: #007bff;
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

    elif sub_menu_tinh_toan == "Tính sụt áp (ΔU)":
        st.header("⚡ Tính sụt áp (ΔU)")
        formula_latex_str_sd = r"\Delta U = \frac{k \cdot L \cdot P}{S \cdot U \cdot \cos\varphi \cdot n_{song song}}"
        st.latex(formula_latex_str_sd)
        formula_explanation_sd = """
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
        """
        st.markdown(formula_explanation_sd, unsafe_allow_html=True)

        # Thêm các trường nhập liệu mới cho Người tính toán
        st.subheader("Thông tin Người tính toán")
        calculator_name_sd = st.text_input("Họ và tên:", value="Hà Thị Lê", key="calc_name_sd")
        calculator_title_sd = st.text_input("Chức danh:", value="Tổ trưởng tổ KDDV", key="calc_title_sd")
        calculator_phone_sd = st.text_input("Số điện thoại:", value="0978578777", key="calc_phone_sd")

        # Thêm các trường nhập liệu mới cho Khách hàng
        st.subheader("Thông tin Khách hàng")
        customer_name_sd = st.text_input("Tên khách hàng:", value="Phạm Hồng Long", key="cust_name_sd")
        customer_address_sd = st.text_input("Địa chỉ:", value="xã Định Hóa, tỉnh Thái Nguyên", key="cust_address_sd")
        customer_phone_sd = st.text_input("Số điện thoại khách hàng:", value="0968552888", key="cust_phone_sd")
        
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

            calculator_info = {
                'name': calculator_name_sd,
                'title': calculator_title_sd,
                'phone': calculator_phone_sd
            }
            customer_info = {
                'name': customer_name_sd,
                'address': customer_address_sd,
                'phone': customer_phone_sd
            }
            input_params = {
                "Loại dòng điện": current_type_sd,
                "Điện áp (U)": f"{U_sd} V",
                "Công suất tải (P)": f"{P_sd} kW",
                "Hệ số công suất (cosφ)": cos_phi_sd,
                "Chất liệu dây dẫn": material_sd,
                "Tiết diện dây dẫn (S)": f"{S_sd} mm²",
                "Chiều dài tuyến (L)": f"{L_sd} m",
                "Số dây dẫn song song/pha": n_parallel_sd
            }
            output_results = {
                "Dòng điện tính toán (I)": f"{I_sd:.2f} A",
                "Sụt áp ΔU": f"{deltaU_sd:.3f} V",
                "Sụt áp ΔU%": f"{deltaU_percent_sd:.2f} %",
                "Điện áp tại tải": f"{U_at_load_sd:.3f} V"
            }
            
            pdf_bytes_sd = create_pdf("SỤT ÁP DÂY CÁP ĐIỆN", formula_latex_str_sd, formula_explanation_sd, input_params, output_results, calculator_info, customer_info)
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
        
    elif sub_menu_tinh_toan == "Chọn tiết diện dây dẫn":
        st.header("⚡ Chọn tiết diện dây dẫn")

        formula_latex_str_s = r"S = \frac{2 \cdot \rho \cdot L \cdot I}{U \cdot (\Delta U\% / 100)}"
        st.latex(formula_latex_str_s)
        formula_explanation_s = """
        **Giải thích các thành phần:**
        - \( S \): Tiết diện dây dẫn cần chọn (mm²)  
        - \( \rho \): Điện trở suất của vật liệu dây (Ω·mm²/m)  
        - \( L \): Chiều dài dây dẫn 1 chiều (m)  
        - \( I \): Dòng điện tải (A)  
        - \( U \): Điện áp danh định (V)  
        - \( \Delta U\% \): Sụt áp cho phép (%)  

        **Mục đích:** Tính tiết diện dây dẫn phù hợp với công suất tải, chiều dài và điều kiện sụt áp cho phép.  
        Giúp chọn dây dẫn đúng kỹ thuật và đảm bảo an toàn vận hành.
        """
        st.markdown(formula_explanation_s, unsafe_allow_html=True)

        # Thêm các trường nhập liệu mới cho Người tính toán
        st.subheader("Thông tin Người tính toán")
        calculator_name_s = st.text_input("Họ và tên:", value="Hà Thị Lê", key="calc_name_s")
        calculator_title_s = st.text_input("Chức danh:", value="Tổ trưởng tổ KDDV", key="calc_title_s")
        calculator_phone_s = st.text_input("Số điện thoại:", value="0978578777", key="calc_phone_s")

        # Thêm các trường nhập liệu mới cho Khách hàng
        st.subheader("Thông tin Khách hàng")
        customer_name_s = st.text_input("Tên khách hàng:", value="Phạm Hồng Long", key="cust_name_s")
        customer_address_s = st.text_input("Địa chỉ:", value="xã Định Hóa,tỉnh Thái Nguyên", key="cust_address_s")
        customer_phone_s = st.text_input("Số điện thoại khách hàng:", value="0968552888", key="cust_phone_s")
        
        # Lấy thời gian thực (chỉ ngày, tháng, năm)
        current_date_s = datetime.now().strftime("Ngày %d tháng %m năm %Y")
        st.markdown(f"**Thời gian lập phiếu:** {current_date_s}")

        pha_s = st.radio("Loại điện:", ["1 pha", "3 pha"], key="pha_s")
        P_s = st.number_input("Công suất tải (kW):", min_value=0.0, key="P_s")
        U_s = st.number_input("Điện áp danh định (V):", min_value=0.0, value=220.0, key="U_s")
        cos_phi_s = st.slider("Hệ số công suất cosφ:", 0.1, 1.0, 0.85, key="cos_phi_s")
        L_s = st.number_input("Chiều dài dây dẫn (m):", min_value=0.0, key="L_s")
        deltaU_percent_s = st.number_input("Sụt áp cho phép (%):", min_value=1.0, value=4.0, key="deltaU_percent_s")
        material_s = st.selectbox("Chất liệu dây dẫn:", ["Đồng", "Nhôm"], key="material_s")
        
        # Thêm lựa chọn phương pháp lắp đặt
        installation_method_s = st.radio(
            "Phương pháp lắp đặt:", 
            ["Trong không khí (25°C)", "Trong ống (25°C)"],
            help="Chọn phương pháp lắp đặt để xác định khả năng chịu tải của dây dẫn.",
            key="installation_method_s"
        )

        # Nút tính toán
        if st.button("Tính tiết diện", key="btn_calc_s"):
            # Tính dòng điện I
            I_s = P_s * 1000 / (U_s * cos_phi_s) if U_s != 0 and cos_phi_s != 0 else 0 # Tránh chia cho 0
            if pha_s == "3 pha":
                I_s = P_s * 1000 / (math.sqrt(3) * U_s * cos_phi_s) if U_s != 0 and cos_phi_s != 0 else 0
            
            # Điện trở suất
            rho_s = 0.0175 if material_s == "Đồng" else 0.028
            
            # Sụt áp cho phép (ΔU)
            deltaU_s = U_s * deltaU_percent_s / 100
            
            # Tính tiết diện S (dựa trên sụt áp)
            S_result = (2 * rho_s * L_s * I_s) / deltaU_s if deltaU_s != 0 else 0 # Tránh chia cho 0

            # Hiển thị dòng điện tính toán được
            st.info(f"⚡ Dòng điện tính toán được I ≈ {I_s:.2f} A")
            st.success(f"🔢 Tiết diện S tối thiểu theo sụt áp ≈ {S_result:.2f} mm²")

            # Chọn bảng khả năng chịu tải phù hợp từ dữ liệu Excel đã tải
            if material_s == "Đồng":
                selected_cable_data = copper_cable_data
            else: # material == "Nhôm"
                selected_cable_data = aluminum_cable_data

            # Kiểm tra nếu dữ liệu bảng tra rỗng (do lỗi đọc file Excel)
            suggested_size = None
            if not selected_cable_data:
                st.error("❌ Không thể gợi ý tiết diện do không đọc được dữ liệu bảng tra từ file Excel. Vui lòng kiểm tra các lỗi đọc file Excel phía trên.")
            else:
                # Chọn loại khả năng chịu tải dựa trên phương pháp lắp đặt
                if installation_method_s == "Trong không khí (25°C)":
                    current_capacities = selected_cable_data.get('in_air', {})
                else: # "Trong ống (25°C)"
                    current_capacities = selected_cable_data.get('in_conduit', {})

                if not current_capacities:
                    st.error(f"❌ Không có dữ liệu khả năng chịu tải cho phương pháp '{installation_method_s}' của dây {material_s}. Vui lòng kiểm tra lại file Excel.")
                else:
                    # Tìm tiết diện chuẩn nhỏ nhất thỏa mãn cả sụt áp và khả năng chịu tải
                    available_sizes = sorted(current_capacities.keys())

                    for size in available_sizes:
                        # Kiểm tra cả hai điều kiện: tiết diện đủ lớn theo sụt áp VÀ khả năng chịu tải đủ lớn theo dòng điện
                        capacity = current_capacities.get(size, 0)
                        if isinstance(capacity, (int, float)) and size >= S_result and capacity >= I_s:
                            suggested_size = size
                            break # Đã tìm thấy tiết diện nhỏ nhất phù hợp, thoát vòng lặp

                    if suggested_size:
                        st.info(f"👉 Gợi ý chọn tiết diện chuẩn thương mại CADIVI: **{suggested_size} mm²**")
                    else:
                        st.error("❌ Không có tiết diện thương mại phù hợp với các điều kiện đã nhập. Vui lòng kiểm tra lại thông số hoặc cân nhắc sử dụng dây có tiết diện lớn hơn.")

            # --- Bắt đầu phần tạo và xuất PDF ---
            calculator_info = {
                'name': calculator_name_s,
                'title': calculator_title_s,
                'phone': calculator_phone_s
            }
            customer_info = {
                'name': customer_name_s,
                'address': customer_address_s,
                'phone': customer_phone_s
            }
            input_params = {
                "Loại điện": pha_s,
                "Công suất tải (P)": f"{P_s} kW",
                "Điện áp danh định (U)": f"{U_s} V",
                "Hệ số công suất (cosφ)": cos_phi_s,
                "Chiều dài dây dẫn (L)": f"{L_s} m",
                "Sụt áp cho phép (ΔU%)": f"{deltaU_percent_s} %",
                "Chất liệu dây dẫn": material_s,
                "Phương pháp lắp đặt": installation_method_s
            }
            output_results = {
                "Dòng điện tính toán (I)": f"{I_s:.2f} A",
                "Tiết diện S tối thiểu theo sụt áp": f"{S_result:.2f} mm²",
                "Gợi ý tiết diện chuẩn CADIVI": f"{suggested_size} mm²" if suggested_size else "Không có"
            }
            
            pdf_bytes = create_pdf("LỰA CHỌN DÂY CÁP ĐIỆN", formula_latex_str_s, formula_explanation_s, input_params, output_results, calculator_info, customer_info)
            st.session_state['pdf_bytes_s'] = pdf_bytes
            st.session_state['pdf_filename_s'] = f"Phieu_tinh_toan_day_cap_dien_{datetime.now().strftime('%Y%m%d')}.pdf"

            # --- Các nút PDF riêng biệt ---
        if 'pdf_bytes_s' in st.session_state and st.session_state['pdf_bytes_s']:
            st.markdown("---") # Đường phân cách
            st.subheader("Tùy chọn xuất phiếu")
            col_pdf1, col_pdf2 = st.columns(2)
            with col_pdf1:
                st.download_button(
                    label="Xuất PDF",
                    data=st.session_state['pdf_bytes_s'],
                    file_name=st.session_state['pdf_filename_s'],
                    mime="application/pdf",
                    help="Tải về phiếu tính toán dưới dạng PDF",
                    key="download_s_pdf"
                )
            with col_pdf2:
                # Nút "Xem phiếu" sẽ mở PDF trong tab mới
                pdf_base64 = base64.b64encode(st.session_state['pdf_bytes_s']).decode('utf-8')
                
                # Sử dụng st.markdown với thẻ <a> để mở trong tab mới mà không tải xuống
                # Lưu ý: Hành vi này có thể khác nhau tùy trình duyệt và cài đặt bảo mật
                st.markdown(
                    f"""
                    <a href="data:application/pdf;base64,{pdf_base64}" target="_blank" style="text-decoration: none;">
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

            # Hiển thị bảng tra CADIVI cho dây Đồng (vẫn dùng ảnh vì trực quan)
            st.markdown("📘 **Tham khảo bảng tra tiết diện dây dẫn của hãng CADIVI (Dây Đồng):**")
            try:
                # Đảm bảo file 'cadivi_cho bảng tra dây đồng.jpg' nằm cùng thư mục với app.py
                with open("cadivi_cho bảng tra dây đồng.jpg", "rb") as f:
                    st.image(f.read(), caption="Bảng tra dây dẫn CADIVI (Dây Đồng)", use_container_width=True)
            except FileNotFoundError:
                st.warning("⚠️ Không tìm thấy file ảnh 'cadivi_cho bảng tra dây đồng.jpg'. Vui lòng đảm bảo ảnh nằm cùng thư mục với file app.py.")
            except Exception as e:
                st.error(f"❌ Có lỗi xảy ra khi tải ảnh dây đồng: {e}")

            # Hiển thị bảng tra CADIVI cho dây Nhôm (vẫn dùng ảnh vì trực quan)
            st.markdown("📘 **Tham khảo bảng tra tiết diện dây dẫn của hãng CADIVI (Dây Nhôm):**")
            try:
                # Đảm bảo file 'cadivi_cho bảng tra dây nhôm.jpg' nằm cùng thư mục với app.py
                with open("cadivi_cho bảng tra dây nhôm.jpg", "rb") as f:
                    st.image(f.read(), caption="Bảng tra dây dẫn CADIVI (Dây Nhôm)", use_container_width=True)
            except FileNotFoundError:
                st.warning("⚠️ Không tìm thấy file ảnh 'cadivi_cho bảng tra dây nhôm.jpg'. Vui lòng đảm bảo ảnh nằm cùng thư mục với file app.py.")
            except Exception as e:
                st.error(f"❌ Có lỗi xảy ra khi tải ảnh dây nhôm: {e}")
        
    elif sub_menu_tinh_toan == "Chiều dài dây tối đa (ΔU%)":
        st.header("⚡ Chiều dài dây tối đa (ΔU%)")
        formula_latex_str_lmax = r"L_{max} = \frac{U \cdot (\Delta U\% / 100)}{2 \cdot I \cdot R_{don\_vi}} \cdot 1000"
        st.latex(formula_latex_str_lmax)
        formula_explanation_lmax = """
        **Giải thích các thành phần:**
        - \( L_{max} \): Chiều dài dây tối đa (m)
        - \( U \): Điện áp danh định (V)
        - \( \Delta U\% \): Giới hạn sụt áp cho phép (%)
        - \( I \): Dòng điện (A)
        - \( R_{don\_vi} \): Điện trở đơn vị của dây (Ω/km)
        
        **Mục đích:** Xác định chiều dài tối đa của dây dẫn để đảm bảo sụt áp không vượt quá giới hạn cho phép, duy trì chất lượng điện năng.
        """
        st.markdown(formula_explanation_lmax, unsafe_allow_html=True)

        st.subheader("Thông tin Người tính toán")
        calculator_name_lmax = st.text_input("Họ và tên:", value="Hà Thị Lê", key="calc_name_lmax")
        calculator_title_lmax = st.text_input("Chức danh:", value="Tổ trưởng tổ KDDV", key="calc_title_lmax")
        calculator_phone_lmax = st.text_input("Số điện thoại:", value="0978578777", key="calc_phone_lmax")

        st.subheader("Thông tin Khách hàng")
        customer_name_lmax = st.text_input("Tên khách hàng:", value="Phạm Hồng Long", key="cust_name_lmax")
        customer_address_lmax = st.text_input("Địa chỉ:", value="xã Định Hóa, tỉnh Thái Nguyên", key="cust_address_lmax")
        customer_phone_lmax = st.text_input("Số điện thoại khách hàng:", value="0968552888", key="cust_phone_lmax")
        
        current_date_lmax = datetime.now().strftime("Ngày %d tháng %m năm %Y")
        st.markdown(f"**Thời gian lập phiếu:** {current_date_lmax}")

        col1, col2 = st.columns(2)
        with col1:
            U_lmax = st.number_input("Điện áp danh định (V):", min_value=0.0, key="U_lmax")
            I_lmax = st.number_input("Dòng điện (A):", min_value=0.0, key="I_lmax")
        with col2:
            R_lmax = st.number_input("R đơn vị (Ω/km):", min_value=0.0, key="R_lmax")
            deltaU_percent_lmax = st.number_input("Giới hạn ΔU (%):", value=5.0, key="deltaU_percent_lmax")
        
        if st.button("Tính chiều dài tối đa", key="btn_calc_lmax"):
            Lmax_result = 0.0
            if I_lmax != 0 and R_lmax != 0:
                Lmax_result = (U_lmax * deltaU_percent_lmax / 100) / (2 * I_lmax * R_lmax) * 1000
            st.success(f"Chiều dài dây tối đa ≈ {Lmax_result:.1f} m")

            calculator_info = {
                'name': calculator_name_lmax,
                'title': calculator_title_lmax,
                'phone': calculator_phone_lmax
            }
            customer_info = {
                'name': customer_name_lmax,
                'address': customer_address_lmax,
                'phone': customer_phone_lmax
            }
            input_params = {
                "Điện áp danh định (U)": f"{U_lmax} V",
                "Dòng điện (I)": f"{I_lmax} A",
                "Điện trở đơn vị (R)": f"{R_lmax} Ω/km",
                "Giới hạn ΔU (%)": f"{deltaU_percent_lmax} %"
            }
            output_results = {
                "Chiều dài dây tối đa": f"{Lmax_result:.1f} m"
            }
            
            pdf_bytes = create_pdf("CHIỀU DÀI DÂY TỐI ĐA", formula_latex_str_lmax, formula_explanation_lmax, input_params, output_results, calculator_info, customer_info)
            st.session_state['pdf_bytes_lmax'] = pdf_bytes
            st.session_state['pdf_filename_lmax'] = f"Phieu_tinh_chieu_dai_toi_da_{datetime.now().strftime('%Y%m%d')}.pdf"

        if 'pdf_bytes_lmax' in st.session_state and st.session_state['pdf_bytes_lmax']:
            st.markdown("---")
            st.subheader("Tùy chọn xuất phiếu chiều dài dây tối đa")
            col_pdf1_lmax, col_pdf2_lmax = st.columns(2)
            with col_pdf1_lmax:
                st.download_button(
                    label="Xuất PDF",
                    data=st.session_state['pdf_bytes_lmax'],
                    file_name=st.session_state['pdf_filename_lmax'],
                    mime="application/pdf",
                    key="download_lmax_pdf"
                )
            with col_pdf2_lmax:
                pdf_base64_lmax = base64.b64encode(st.session_state['pdf_bytes_lmax']).decode('utf-8')
                st.markdown(
                    f"""
                    <a href="data:application/pdf;base64,{pdf_base64_lmax}" target="_blank" style="text-decoration: none;">
                        <button style="
                            background-color: #007bff;
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

    elif sub_menu_tinh_toan == "Tính điện trở – kháng – trở kháng":
        st.header("⚡ Tính điện trở – kháng – trở kháng")
        formula_latex_str_z = r"Z = \sqrt{R^2 + X^2}"
        st.latex(formula_latex_str_z)
        formula_explanation_z = """
        **Giải thích các thành phần:**
        - \( Z \): Tổng trở (Ω)
        - \( R \): Điện trở (Ω)
        - \( X \): Điện kháng (Ω)
        
        **Mục đích:** Tính toán tổng trở của mạch điện xoay chiều, cần thiết cho việc phân tích mạch và tính toán dòng điện, sụt áp.
        """
        st.markdown(formula_explanation_z, unsafe_allow_html=True)

        st.subheader("Thông tin Người tính toán")
        calculator_name_z = st.text_input("Họ và tên:", value="Hà Thị Lê", key="calc_name_z")
        calculator_title_z = st.text_input("Chức danh:", value="Tổ trưởng tổ KDDV", key="calc_title_z")
        calculator_phone_z = st.text_input("Số điện thoại:", value="0978578777", key="calc_phone_z")

        st.subheader("Thông tin Khách hàng")
        customer_name_z = st.text_input("Tên khách hàng:", value="Phạm Hồng Long", key="cust_name_z")
        customer_address_z = st.text_input("Địa chỉ:", value="xã Định Hóa, tỉnh Thái Nguyên", key="cust_address_z")
        customer_phone_z = st.text_input("Số điện thoại khách hàng:", value="0968552888", key="cust_phone_z")
        
        current_date_z = datetime.now().strftime("Ngày %d tháng %m năm %Y")
        st.markdown(f"**Thời gian lập phiếu:** {current_date_z}")

        col1, col2 = st.columns(2)
        with col1:
            R_z = st.number_input("Điện trở R (Ω):", min_value=0.0, key="R_z")
        with col2:
            X_z = st.number_input("Điện kháng X (Ω):", min_value=0.0, key="X_z")
        
        if st.button("Tính Z", key="btn_calc_z"):
            Z_result = math.sqrt(R_z**2 + X_z**2)
            st.success(f"Tổng trở Z ≈ {Z_result:.2f} Ω")

            calculator_info = {
                'name': calculator_name_z,
                'title': calculator_title_z,
                'phone': calculator_phone_z
            }
            customer_info = {
                'name': customer_name_z,
                'address': customer_address_z,
                'phone': customer_phone_z
            }
            input_params = {
                "Điện trở R": f"{R_z} Ω",
                "Điện kháng X": f"{X_z} Ω"
            }
            output_results = {
                "Tổng trở Z": f"{Z_result:.2f} Ω"
            }
            
            pdf_bytes = create_pdf("ĐIỆN TRỞ – KHÁNG – TRỞ KHÁNG", formula_latex_str_z, formula_explanation_z, input_params, output_results, calculator_info, customer_info)
            st.session_state['pdf_bytes_z'] = pdf_bytes
            st.session_state['pdf_filename_z'] = f"Phieu_tinh_tong_tro_{datetime.now().strftime('%Y%m%d')}.pdf"

        if 'pdf_bytes_z' in st.session_state and st.session_state['pdf_bytes_z']:
            st.markdown("---")
            st.subheader("Tùy chọn xuất phiếu tổng trở")
            col_pdf1_z, col_pdf2_z = st.columns(2)
            with col_pdf1_z:
                st.download_button(
                    label="Xuất PDF",
                    data=st.session_state['pdf_bytes_z'],
                    file_name=st.session_state['pdf_filename_z'],
                    mime="application/pdf",
                    key="download_z_pdf"
                )
            with col_pdf2_z:
                pdf_base64_z = base64.b64encode(st.session_state['pdf_bytes_z']).decode('utf-8')
                st.markdown(
                    f"""
                    <a href="data:application/pdf;base64,{pdf_base64_z}" target="_blank" style="text-decoration: none;">
                        <button style="
                            background-color: #007bff;
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

    elif sub_menu_tinh_toan == "Tính tổn thất công suất trên dây":
        st.header("⚡ Tính tổn thất công suất trên dây")
        formula_latex_str_ptt = r"P_{tt} = I^2 \cdot R"
        st.latex(formula_latex_str_ptt)
        formula_explanation_ptt = """
        **Giải thích các thành phần:**
        - \( P_{tt} \): Tổn thất công suất (W)
        - \( I \): Dòng điện (A)
        - \( R \): Điện trở của dây (Ω)
        
        **Mục đích:** Tính toán công suất bị hao phí trên đường dây truyền tải, giúp đánh giá hiệu quả truyền tải và tối ưu hóa hệ thống.
        """
        st.markdown(formula_explanation_ptt, unsafe_allow_html=True)

        st.subheader("Thông tin Người tính toán")
        calculator_name_ptt = st.text_input("Họ và tên:", value="Hà Thị Lê", key="calc_name_ptt")
        calculator_title_ptt = st.text_input("Chức danh:", value="Tổ trưởng tổ KDDV", key="calc_title_ptt")
        calculator_phone_ptt = st.text_input("Số điện thoại:", value="0978578777", key="calc_phone_ptt")

        st.subheader("Thông tin Khách hàng")
        customer_name_ptt = st.text_input("Tên khách hàng:", value="Phạm Hồng Long", key="cust_name_ptt")
        customer_address_ptt = st.text_input("Địa chỉ:", value="xã Định Hóa, tỉnh Thái Nguyên", key="cust_address_ptt")
        customer_phone_ptt = st.text_input("Số điện thoại khách hàng:", value="0968552888", key="cust_phone_ptt")
        
        current_date_ptt = datetime.now().strftime("Ngày %d tháng %m năm %Y")
        st.markdown(f"**Thời gian lập phiếu:** {current_date_ptt}")

        col1, col2 = st.columns(2)
        with col1:
            I_ptt = st.number_input("Dòng điện I (A):", min_value=0.0, key="I_ptt")
        with col2:
            R_ptt = st.number_input("Điện trở R (Ω):", min_value=0.0, key="R_ptt")
        
        if st.button("Tính tổn thất", key="btn_calc_ptt"):
            Ptt_result = I_ptt**2 * R_ptt
            st.success(f"Ptt ≈ {Ptt_result:.2f} W")

            calculator_info = {
                'name': calculator_name_ptt,
                'title': calculator_title_ptt,
                'phone': calculator_phone_ptt
            }
            customer_info = {
                'name': customer_name_ptt,
                'address': customer_address_ptt,
                'phone': customer_phone_ptt
            }
            input_params = {
                "Dòng điện I": f"{I_ptt} A",
                "Điện trở R": f"{R_ptt} Ω"
            }
            output_results = {
                "Tổn thất công suất Ptt": f"{Ptt_result:.2f} W"
            }
            
            pdf_bytes = create_pdf("TỔN THẤT CÔNG SUẤT TRÊN DÂY", formula_latex_str_ptt, formula_explanation_ptt, input_params, output_results, calculator_info, customer_info)
            st.session_state['pdf_bytes_ptt'] = pdf_bytes
            st.session_state['pdf_filename_ptt'] = f"Phieu_tinh_ton_that_cong_suat_{datetime.now().strftime('%Y%m%d')}.pdf"

        if 'pdf_bytes_ptt' in st.session_state and st.session_state['pdf_bytes_ptt']:
            st.markdown("---")
            st.subheader("Tùy chọn xuất phiếu tổn thất công suất")
            col_pdf1_ptt, col_pdf2_ptt = st.columns(2)
            with col_pdf1_ptt:
                st.download_button(
                    label="Xuất PDF",
                    data=st.session_state['pdf_bytes_ptt'],
                    file_name=st.session_state['pdf_filename_ptt'],
                    mime="application/pdf",
                    key="download_ptt_pdf"
                )
            with col_pdf2_ptt:
                pdf_base64_ptt = base64.b64encode(st.session_state['pdf_bytes_ptt']).decode('utf-8')
                st.markdown(
                    f"""
                    <a href="data:application/pdf;base64,{pdf_base64_ptt}" target="_blank" style="text-decoration: none;">
                        <button style="
                            background-color: #007bff;
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

elif main_menu == "Công thức điện":
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

