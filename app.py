import matplotlib.pyplot as plt

from reportlab.platypus import Image as RLImage
import matplotlib.pyplot as plt
import io

def render_latex_formula_to_image(latex_str):
    """
    Renders a LaTeX formula to a PNG image using Matplotlib.
    This image can then be embedded into the PDF.
    """
    fig, ax = plt.subplots(figsize=(5.5, 0.8)) # Adjusted figsize for better PDF fit
    ax.axis("off")
    # Use a larger fontsize for better readability in the PDF
    ax.text(0.5, 0.5, f"${latex_str}$", fontsize=18, ha='center', va='center') # Increased fontsize to 18
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.1, dpi=300) # Increased DPI for better quality
    plt.close(fig)
    buf.seek(0)
    return buf

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
    # Assuming DejaVuSans.ttf and DejaVuSans-Bold.ttf are in the same directory as app.py
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

    copper_data = read_excel_file('cadivi_dong.xlsx', "Đồng")
    aluminum_data = read_excel_file('cadivi_nhom.xlsx', "Nhôm")
        
    return copper_data, aluminum_data

# Tải dữ liệu bảng tra khi ứng dụng khởi động
copper_cable_data, aluminum_cable_data = load_cable_data(
    'cadivi_dong.xlsx',
    'cadivi_nhom.xlsx'
)

# Hàm tạo PDF chung
def create_pdf(title, formula_latex, formula_explanation, input_params, output_results, calculator_info, customer_info):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            topMargin=0.5 * inch, # Reduced top margin
                            bottomMargin=0.5 * inch, # Reduced bottom margin
                            leftMargin=0.75 * inch, # Standard left margin
                            rightMargin=0.75 * inch) # Standard right margin
    styles = getSampleStyleSheet()

    try:
        # Increased font sizes for better readability
        styles.add(ParagraphStyle(name='TitleStyle', fontName='DejaVuSans-Bold', fontSize=17, alignment=1, spaceAfter=10)) 
        styles.add(ParagraphStyle(name='Heading2Style', fontName='DejaVuSans-Bold', fontSize=14, spaceAfter=5)) 
        styles.add(ParagraphStyle(name='NormalStyle', fontName='DejaVuSans', fontSize=12, spaceAfter=4)) 
        styles.add(ParagraphStyle(name='TableCellStyle', fontName='DejaVuSans', fontSize=11, alignment=0, leading=13)) # Increased font size and leading
        styles.add(ParagraphStyle(name='TableCellBoldStyle', fontName='DejaVuSans-Bold', fontSize=11, alignment=0, leading=13)) # Increased font size and leading
    except KeyError:
        styles.add(ParagraphStyle(name='TitleStyle', fontName='Helvetica-Bold', fontSize=17, alignment=1, spaceAfter=10))
        styles.add(ParagraphStyle(name='Heading2Style', fontName='Helvetica-Bold', fontSize=14, spaceAfter=5))
        styles.add(ParagraphStyle(name='NormalStyle', fontName='Helvetica', fontSize=12, spaceAfter=4))
        styles.add(ParagraphStyle(name='TableCellStyle', fontName='Helvetica', fontSize=11, alignment=0, leading=13))
        styles.add(ParagraphStyle(name='TableCellBoldStyle', fontName='Helvetica-Bold', fontSize=11, alignment=0, leading=13))

    story = []

    story.append(Paragraph(f"<b>PHIẾU TÍNH TOÁN {title.upper()}</b>", styles['TitleStyle']))
    story.append(Spacer(1, 0.15 * inch)) # Reduced spacer

    # Thông tin chung
    story.append(Paragraph("<b>1. THÔNG TIN CHUNG</b>", styles['Heading2Style']))
    story.append(Paragraph(f"<b>Người tính toán:</b> {calculator_info['name']}", styles['NormalStyle']))
    story.append(Paragraph(f"<b>Chức danh:</b> {calculator_info['title']}", styles['NormalStyle']))
    story.append(Paragraph(f"<b>Điện thoại:</b> {calculator_info['phone']}", styles['NormalStyle']))
    story.append(Spacer(1, 0.05 * inch)) # Reduced spacer
    story.append(Paragraph(f"<b>Khách hàng:</b> {customer_info['name']}", styles['NormalStyle']))
    story.append(Paragraph(f"<b>Địa chỉ:</b> {customer_info['address']}", styles['NormalStyle']))
    story.append(Paragraph(f"<b>Điện thoại khách hàng:</b> {customer_info['phone']}", styles['NormalStyle']))
    story.append(Paragraph(f"<b>Thời gian lập phiếu:</b> {datetime.now().strftime('Ngày %d tháng %m năm %Y')}", styles['NormalStyle']))
    story.append(Spacer(1, 0.15 * inch)) # Reduced spacer

    # Công thức và giải thích
    story.append(Paragraph("<b>2. CÔNG THỨC VÀ GIẢI THÍCH</b>", styles['Heading2Style']))
    story.append(Paragraph("Công thức tính:", styles['NormalStyle']))
    try:
        # Tạo ảnh công thức từ matplotlib
        formula_img_buf = render_latex_formula_to_image(formula_latex)
        # Adjust image width/height to fit on A4
        formula_img = Image(formula_img_buf, width=5.0*inch, height=0.7*inch) # Adjusted image size
        story.append(formula_img)
    except Exception as e:
        story.append(Paragraph(f"(Không hiển thị được công thức LaTeX: {e})", styles['NormalStyle']))
        story.append(Paragraph(formula_latex, styles['NormalStyle']))
    story.append(Paragraph(formula_explanation, styles['NormalStyle']))
    story.append(Spacer(1, 0.15 * inch)) # Reduced spacer
    
    # Thông số đầu vào
    story.append(Paragraph("<b>3. THÔNG SỐ ĐẦU VÀO</b>", styles['Heading2Style']))
    input_table_data = []
    for label, value in input_params.items():
        input_table_data.append([Paragraph(f"<b>{label}</b>", styles['TableCellBoldStyle']), Paragraph(str(value), styles['TableCellStyle'])])
    input_table = Table(input_table_data, colWidths=[2.5*inch, 3*inch]) # Adjusted colWidths for better fit
    input_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (0,-1), 'DejaVuSans-Bold' if 'DejaVuSans-Bold' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold'),
        ('FONTNAME', (1,0), (1,-1), 'DejaVuSans' if 'DejaVuSans' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 11), # Adjusted font size
        ('BOTTOMPADDING', (0,0), (-1,-1), 4), # Reduced padding
        ('TOPPADDING', (0,0), (-1,-1), 4), # Reduced padding
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
    ]))
    story.append(input_table)
    story.append(Spacer(1, 0.15 * inch)) # Reduced spacer

    # Kết quả tính toán
    story.append(Paragraph("<b>4. KẾT QUẢ TÍNH TOÁN</b>", styles['Heading2Style']))
    output_table_data = []
    for label, value in output_results.items():
        output_table_data.append([Paragraph(f"<b>{label}</b>", styles['TableCellBoldStyle']), Paragraph(str(value), styles['TableCellStyle'])])
    output_table = Table(output_table_data, colWidths=[3*inch, 2.5*inch]) # Adjusted colWidths for better fit
    output_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (0,-1), 'DejaVuSans-Bold' if 'DejaVuSans-Bold' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold'),
        ('FONTNAME', (1,0), (1,-1), 'DejaVuSans' if 'DejaVuSans' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 11), # Adjusted font size
        ('BOTTOMPADDING', (0,0), (-1,-1), 4), # Reduced padding
        ('TOPPADDING', (0,0), (-1,-1), 4), # Reduced padding
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
    ]))
    story.append(output_table)
    story.append(Spacer(1, 0.3 * inch)) # Reduced spacer
    
    # Chữ ký
    signature_data = [
        [Paragraph("<b>NGƯỜI TÍNH TOÁN</b>", styles['TableCellBoldStyle']), Paragraph("<b>KHÁCH HÀNG</b>", styles['TableCellBoldStyle'])],
        [Paragraph("(Ký, ghi rõ họ tên)", styles['TableCellStyle']), Paragraph("(Ký, ghi rõ họ tên)", styles['TableCellStyle'])],
        [Spacer(1, 0.6 * inch), Spacer(1, 0.6 * inch)], # Reduced space for signature
        [Paragraph(f"<b>{calculator_info['name']}</b>", styles['TableCellBoldStyle']), Paragraph(f"<b>{customer_info['name']}</b>", styles['TableCellBoldStyle'])]
    ]
    signature_table = Table(signature_data, colWidths=[2.75*inch, 2.75*inch])
    signature_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,-1), 'DejaVuSans' if 'DejaVuSans' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 11), # Adjusted font size
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(signature_table)
    story.append(Spacer(1, 0.1 * inch)) # Reduced spacer

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
        "Tính công suất biểu kiến (S)", # Added new option
        "Tính công suất phản kháng (Q)", # Added new option
        "Tính sụt áp (ΔU)",
        "Chọn tiết diện dây dẫn",
        "Chiều dài dây tối đa (ΔU%)",
        "Tính điện trở – kháng – trở kháng",
        "Tính tổn thất công suất trên dây",
        "Tính công suất cosφ",
        "Chọn thiết bị bảo vệ"
    ])

    # Hiển thị nội dung dựa trên lựa chọn menu con
    if sub_menu_tinh_toan == "Tính dòng điện (I)":
        st.header("⚡ Tính dòng điện (I)")
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
            # The formula_latex needs to be a single string for MathText,
            # so combine the 1-phase and 3-phase formulas.
            # Removed \text{} and \quad for better MathText parsing in PDF
            formula_latex = r"I = \frac{P \cdot 1000}{U \cdot \cos\varphi} \quad \text{(1 pha)} \quad \text{hoặc} \quad I = \frac{P \cdot 1000}{\sqrt{3} \cdot U \cdot \cos\varphi} \quad \text{(3 pha)}"
            formula_explanation = "Công thức tính dòng điện dựa trên công suất, điện áp và hệ số công suất cho hệ thống 1 pha hoặc 3 pha."

            pdf_bytes = create_pdf("DÒNG ĐIỆN", formula_latex, formula_explanation, input_params, output_results, calculator_info, customer_info)
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
            # Combine 1-phase and 3-phase formulas for MathText
            # Removed \text{} and \quad for better MathText parsing in PDF
            formula_latex = r"P = U \cdot I \cdot \cos\varphi \quad \text{(1 pha)} \quad \text{hoặc} \quad P = \sqrt{3} \cdot U \cdot I \cdot \cos\varphi \quad \text{(3 pha)}"
            formula_explanation = "Công thức tính công suất dựa trên điện áp, dòng điện và hệ số công suất cho hệ thống 1 pha hoặc 3 pha."

            pdf_bytes = create_pdf("CÔNG SUẤT", formula_latex, formula_explanation, input_params, output_results, calculator_info, customer_info)
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

    elif sub_menu_tinh_toan == "Tính công suất biểu kiến (S)":
        st.header("⚡ Tính công suất biểu kiến (S)")
        st.latex(r"S = \sqrt{P^2 + Q^2}")
        st.latex(r"S = U \cdot I \quad \text{(1 pha)}")
        st.latex(r"S = \sqrt{3} \cdot U \cdot I \quad \text{(3 pha)}")
        st.markdown("""
        **Giải thích các thành phần:**
        - \( S \): Công suất biểu kiến (kVA)
        - \( P \): Công suất tác dụng (kW)
        - \( Q \): Công suất phản kháng (kVAR)
        - \( U \): Điện áp (V)
        - \( I \): Dòng điện (A)
        
        **Mục đích:** Tính toán tổng công suất của hệ thống điện, bao gồm cả công suất tác dụng và công suất phản kháng.
        """, unsafe_allow_html=True)

        st.subheader("Thông tin Người tính toán")
        calculator_name_s = st.text_input("Họ và tên:", value="Hà Thị Lê", key="calc_name_s")
        calculator_title_s = st.text_input("Chức danh:", value="Tổ trưởng tổ KDDV", key="calc_title_s")
        calculator_phone_s = st.text_input("Số điện thoại:", value="0978578777", key="calc_phone_s")

        st.subheader("Thông tin Khách hàng")
        customer_name_s = st.text_input("Tên khách hàng:", value="Phạm Hồng Long", key="cust_name_s")
        customer_address_s = st.text_input("Địa chỉ:", value="xã Định Hóa, tỉnh Thái Nguyên", key="cust_address_s")
        customer_phone_s = st.text_input("Số điện thoại khách hàng:", value="0968552888", key="cust_phone_s")
        
        current_date_s = datetime.now().strftime("Ngày %d tháng %m năm %Y")
        st.markdown(f"**Thời gian lập phiếu:** {current_date_s}")

        s_calc_method = st.radio(
            "Chọn phương pháp tính S:",
            ["Từ P, Q", "Từ U, I"],
            key="s_calc_method"
        )

        S_result = 0.0
        input_params_s = {}
        formula_latex_s = ""
        formula_explanation_s = ""

        if s_calc_method == "Từ P, Q":
            col1, col2 = st.columns(2)
            with col1:
                P_s_pq = st.number_input("Công suất tác dụng P (kW):", min_value=0.0, key="P_s_pq")
            with col2:
                Q_s_pq = st.number_input("Công suất phản kháng Q (kVAR):", min_value=0.0, key="Q_s_pq")
            
            if st.button("Tính S (từ P, Q)", key="btn_calc_s_pq"):
                S_result = math.sqrt(P_s_pq**2 + Q_s_pq**2)
                st.success(f"Công suất biểu kiến S ≈ {S_result:.2f} kVA")
                input_params_s = {
                    "Công suất tác dụng P": f"{P_s_pq} kW",
                    "Công suất phản kháng Q": f"{Q_s_pq} kVAR"
                }
                formula_latex_s = r"S = \sqrt{P^2 + Q^2}"
                formula_explanation_s = "Công thức tính công suất biểu kiến từ công suất tác dụng và công suất phản kháng."

        elif s_calc_method == "Từ U, I":
            col1, col2 = st.columns(2)
            with col1:
                pha_s_ui = st.radio("Loại điện:", ["1 pha", "3 pha"], key="pha_s_ui")
                U_s_ui = st.number_input("Điện áp U (V):", min_value=0.0, key="U_s_ui")
            with col2:
                I_s_ui = st.number_input("Dòng điện I (A):", min_value=0.0, key="I_s_ui")
            
            if st.button("Tính S (từ U, I)", key="btn_calc_s_ui"):
                if U_s_ui != 0 and I_s_ui != 0:
                    if pha_s_ui == "1 pha":
                        S_result = (U_s_ui * I_s_ui) / 1000
                    elif pha_s_ui == "3 pha":
                        S_result = (math.sqrt(3) * U_s_ui * I_s_ui) / 1000
                st.success(f"Công suất biểu kiến S ≈ {S_result:.2f} kVA")
                input_params_s = {
                    "Loại điện": pha_s_ui,
                    "Điện áp U": f"{U_s_ui} V",
                    "Dòng điện I": f"{I_s_ui} A"
                }
                formula_latex_s = r"S = U \cdot I \quad \text{(1 pha)} \quad \text{hoặc} \quad S = \sqrt{3} \cdot U \cdot I \quad \text{(3 pha)}"
                formula_explanation_s = "Công thức tính công suất biểu kiến từ điện áp và dòng điện cho hệ thống 1 pha hoặc 3 pha."

        if S_result != 0.0: # Only generate PDF if a calculation was performed
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
            output_results = {
                "Công suất biểu kiến S": f"{S_result:.2f} kVA"
            }

            pdf_bytes = create_pdf(f"CÔNG SUẤT BIỂU KIẾN (S) ({s_calc_method.replace('Từ ', '')})", formula_latex_s, formula_explanation_s, input_params_s, output_results, calculator_info, customer_info)
            st.session_state['pdf_bytes_s'] = pdf_bytes
            st.session_state['pdf_filename_s'] = f"Phieu_tinh_cong_suat_bieu_kien_{datetime.now().strftime('%Y%m%d')}.pdf"

        if 'pdf_bytes_s' in st.session_state and st.session_state['pdf_bytes_s']:
            st.markdown("---")
            st.subheader("Tùy chọn xuất phiếu công suất biểu kiến")
            col_pdf1_s, col_pdf2_s = st.columns(2)
            with col_pdf1_s:
                st.download_button(
                    label="Xuất PDF",
                    data=st.session_state['pdf_bytes_s'],
                    file_name=st.session_state['pdf_filename_s'],
                    mime="application/pdf",
                    key="download_s_pdf"
                )
            with col_pdf2_s:
                pdf_base64_s = base64.b64encode(st.session_state['pdf_bytes_s']).decode('utf-8')
                st.markdown(
                    f"""
                    <a href="data:application/pdf;base64,{pdf_base64_s}" target="_blank" style="text-decoration: none;">
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

    elif sub_menu_tinh_toan == "Tính công suất phản kháng (Q)":
        st.header("⚡ Tính công suất phản kháng (Q)")
        st.latex(r"Q = \sqrt{S^2 - P^2}")
        st.latex(r"Q = P \cdot \tan(\arccos(\cos\varphi))")
        st.latex(r"Q = U \cdot I \cdot \sin\varphi \quad \text{(1 pha)}")
        st.latex(r"Q = \sqrt{3} \cdot U \cdot I \cdot \sin\varphi \quad \text{(3 pha)}")
        st.markdown("""
        **Giải thích các thành phần:**
        - \( Q \): Công suất phản kháng (kVAR)
        - \( S \): Công suất biểu kiến (kVA)
        - \( P \): Công suất tác dụng (kW)
        - \( \cos\varphi \): Hệ số công suất
        - \( U \): Điện áp (V)
        - \( I \): Dòng điện (A)
        - \( \sin\varphi \): Sin của góc lệch pha
        
        **Mục đích:** Tính toán công suất phản kháng, cần thiết cho việc bù công suất phản kháng để cải thiện hệ số công suất.
        """, unsafe_allow_html=True)

        st.subheader("Thông tin Người tính toán")
        calculator_name_q = st.text_input("Họ và tên:", value="Hà Thị Lê", key="calc_name_q")
        calculator_title_q = st.text_input("Chức danh:", value="Tổ trưởng tổ KDDV", key="calc_title_q")
        calculator_phone_q = st.text_input("Số điện thoại:", value="0978578777", key="calc_phone_q")

        st.subheader("Thông tin Khách hàng")
        customer_name_q = st.text_input("Tên khách hàng:", value="Phạm Hồng Long", key="cust_name_q")
        customer_address_q = st.text_input("Địa chỉ:", value="xã Định Hóa, tỉnh Thái Nguyên", key="cust_address_q")
        customer_phone_q = st.text_input("Số điện thoại khách hàng:", value="0968552888", key="cust_phone_q")
        
        current_date_q = datetime.now().strftime("Ngày %d tháng %m năm %Y")
        st.markdown(f"**Thời gian lập phiếu:** {current_date_q}")

        q_calc_method = st.radio(
            "Chọn phương pháp tính Q:",
            ["Từ P, S", "Từ P, cosφ", "Từ U, I, sinφ"],
            key="q_calc_method"
        )

        Q_result = 0.0
        input_params_q = {}
        formula_latex_q = ""
        formula_explanation_q = ""

        if q_calc_method == "Từ P, S":
            col1, col2 = st.columns(2)
            with col1:
                P_q_ps = st.number_input("Công suất tác dụng P (kW):", min_value=0.0, key="P_q_ps")
            with col2:
                S_q_ps = st.number_input("Công suất biểu kiến S (kVA):", min_value=0.0, key="S_q_ps")
            
            if st.button("Tính Q (từ P, S)", key="btn_calc_q_ps"):
                if S_q_ps >= P_q_ps:
                    Q_result = math.sqrt(S_q_ps**2 - P_q_ps**2)
                else:
                    st.warning("Công suất biểu kiến (S) phải lớn hơn hoặc bằng Công suất tác dụng (P).")
                st.success(f"Công suất phản kháng Q ≈ {Q_result:.2f} kVAR")
                input_params_q = {
                    "Công suất tác dụng P": f"{P_q_ps} kW",
                    "Công suất biểu kiến S": f"{S_q_ps} kVA"
                }
                formula_latex_q = r"Q = \sqrt{S^2 - P^2}"
                formula_explanation_q = "Công thức tính công suất phản kháng từ công suất biểu kiến và công suất tác dụng."

        elif q_calc_method == "Từ P, cosφ":
            col1, col2 = st.columns(2)
            with col1:
                P_q_pc = st.number_input("Công suất tác dụng P (kW):", min_value=0.0, key="P_q_pc")
            with col2:
                cos_phi_q_pc = st.slider("Hệ số cosφ:", 0.001, 1.0, 0.8, key="cos_phi_q_pc") # Min value > 0 to avoid division by zero
            
            if st.button("Tính Q (từ P, cosφ)", key="btn_calc_q_pc"):
                if cos_phi_q_pc > 0:
                    # Calculate tan(phi)
                    tan_phi = math.sqrt(1 / (cos_phi_q_pc**2) - 1)
                    Q_result = P_q_pc * tan_phi
                else:
                    Q_result = 0 # If cosphi is 0, Q is undefined or infinite for P>0
                st.success(f"Công suất phản kháng Q ≈ {Q_result:.2f} kVAR")
                input_params_q = {
                    "Công suất tác dụng P": f"{P_q_pc} kW",
                    "Hệ số cosφ": cos_phi_q_pc
                }
                formula_latex_q = r"Q = P \cdot \tan(\arccos(\cos\varphi))"
                formula_explanation_q = "Công thức tính công suất phản kháng từ công suất tác dụng và hệ số công suất."

        elif q_calc_method == "Từ U, I, sinφ":
            col1, col2 = st.columns(2)
            with col1:
                pha_q_uis = st.radio("Loại điện:", ["1 pha", "3 pha"], key="pha_q_uis")
                U_q_uis = st.number_input("Điện áp U (V):", min_value=0.0, key="U_q_uis")
            with col2:
                I_q_uis = st.number_input("Dòng điện I (A):", min_value=0.0, key="I_q_uis")
                sin_phi_q_uis = st.slider("Hệ số sinφ:", 0.0, 1.0, 0.6, key="sin_phi_q_uis") # sin(arccos(0.8)) approx 0.6
            
            if st.button("Tính Q (từ U, I, sinφ)", key="btn_calc_q_uis"):
                if U_q_uis != 0 and I_q_uis != 0:
                    if pha_q_uis == "1 pha":
                        Q_result = (U_q_uis * I_q_uis * sin_phi_q_uis) / 1000
                    elif pha_q_uis == "3 pha":
                        Q_result = (math.sqrt(3) * U_q_uis * I_q_uis * sin_phi_q_uis) / 1000
                st.success(f"Công suất phản kháng Q ≈ {Q_result:.2f} kVAR")
                input_params_q = {
                    "Loại điện": pha_q_uis,
                    "Điện áp U": f"{U_q_uis} V",
                    "Dòng điện I": f"{I_q_uis} A",
                    "Hệ số sinφ": sin_phi_q_uis
                }
                formula_latex_q = r"Q = U \cdot I \cdot \sin\varphi \quad \text{(1 pha)} \quad \text{hoặc} \quad Q = \sqrt{3} \cdot U \cdot I \cdot \sin\varphi \quad \text{(3 pha)}"
                formula_explanation_q = "Công thức tính công suất phản kháng từ điện áp, dòng điện và sin của góc lệch pha."

        if Q_result != 0.0: # Only generate PDF if a calculation was performed
            calculator_info = {
                'name': calculator_name_q,
                'title': calculator_title_q,
                'phone': calculator_phone_q
            }
            customer_info = {
                'name': customer_name_q,
                'address': customer_address_q,
                'phone': customer_phone_q
            }
            output_results = {
                "Công suất phản kháng Q": f"{Q_result:.2f} kVAR"
            }

            pdf_bytes = create_pdf(f"CÔNG SUẤT PHẢN KHÁNG (Q) ({q_calc_method.replace('Từ ', '')})", formula_latex_q, formula_explanation_q, input_params_q, output_results, calculator_info, customer_info)
            st.session_state['pdf_bytes_q'] = pdf_bytes
            st.session_state['pdf_filename_q'] = f"Phieu_tinh_cong_suat_phan_khang_{datetime.now().strftime('%Y%m%d')}.pdf"

        if 'pdf_bytes_q' in st.session_state and st.session_state['pdf_bytes_q']:
            st.markdown("---")
            st.subheader("Tùy chọn xuất phiếu công suất phản kháng")
            col_pdf1_q, col_pdf2_q = st.columns(2)
            with col_pdf1_q:
                st.download_button(
                    label="Xuất PDF",
                    data=st.session_state['pdf_bytes_q'],
                    file_name=st.session_state['pdf_filename_q'],
                    mime="application/pdf",
                    key="download_q_pdf"
                )
            with col_pdf2_q:
                pdf_base64_q = base64.b64encode(st.session_state['pdf_bytes_q']).decode('utf-8')
                st.markdown(
                    f"""
                    <a href="data:application/pdf;base64,{pdf_base64_q}" target="_blank" style="text-decoration: none;">
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

    # Thêm thông tin người tính toán và khách hàng
    st.subheader("Thông tin Người tính toán")
    calculator_name_ct = st.text_input("Họ và tên:", value="Hà Thị Lê", key="calc_name_ct")
    calculator_title_ct = st.text_input("Chức danh:", value="Tổ trưởng tổ KDDV", key="calc_title_ct")
    calculator_phone_ct = st.text_input("Số điện thoại:", value="0978578777", key="calc_phone_ct")

    st.subheader("Thông tin Khách hàng")
    customer_name_ct = st.text_input("Tên khách hàng:", value="Phạm Hồng Long", key="cust_name_ct")
    customer_address_ct = st.text_input("Địa chỉ:", value="xã Định Hóa, tỉnh Thái Nguyên", key="cust_address_ct")
    customer_phone_ct = st.text_input("Số điện thoại khách hàng:", value="0968552888", key="cust_phone_ct")
    
    current_date_ct = datetime.now().strftime("Ngày %d tháng %m năm %Y")
    st.markdown(f"**Thời gian lập phiếu:** {current_date_ct}")

    if cong_thuc == "ΔU & I → R":
        st.latex(r"R = \frac{\Delta U}{I}")
        st.markdown("""
        **Giải thích các thành phần:**
        - \( R \): Điện trở (Ω)
        - \( \Delta U \): Sụt áp (V)
        - \( I \): Dòng điện (A)
        
        **Mục đích:** Tính toán điện trở của một đoạn mạch khi biết sụt áp và dòng điện.
        """, unsafe_allow_html=True)
        u = st.number_input("ΔU (V):", min_value=0.0, key="du_i_r_u")
        i = st.number_input("I (A):", min_value=0.0, key="du_i_r_i")
        r = u / i if i != 0 else 0
        if st.button("Tính R", key="btn_calc_du_i_r"):
            st.success(f"R ≈ {r:.3f} Ω")
            calculator_info = {
                'name': calculator_name_ct,
                'title': calculator_title_ct,
                'phone': calculator_phone_ct
            }
            customer_info = {
                'name': customer_name_ct,
                'address': customer_address_ct,
                'phone': customer_phone_ct
            }
            input_params = {
                "Sụt áp ΔU": f"{u} V",
                "Dòng điện I": f"{i} A"
            }
            output_results = {
                "Điện trở R": f"{r:.3f} Ω"
            }
            formula_latex = r"R = \frac{\Delta U}{I}"
            formula_explanation = "Công thức tính điện trở từ sụt áp và dòng điện."
            pdf_bytes = create_pdf("ĐIỆN TRỞ (TỪ ΔU & I)", formula_latex, formula_explanation, input_params, output_results, calculator_info, customer_info)
            st.session_state['pdf_bytes_du_i_r'] = pdf_bytes
            st.session_state['pdf_filename_du_i_r'] = f"Phieu_tinh_R_tu_DU_I_{datetime.now().strftime('%Y%m%d')}.pdf"
        if 'pdf_bytes_du_i_r' in st.session_state and st.session_state['pdf_bytes_du_i_r']:
            st.markdown("---")
            col_pdf1_du_i_r, col_pdf2_du_i_r = st.columns(2)
            with col_pdf1_du_i_r:
                st.download_button(label="Xuất PDF", data=st.session_state['pdf_bytes_du_i_r'], file_name=st.session_state['pdf_filename_du_i_r'], mime="application/pdf", key="download_du_i_r_pdf")
            with col_pdf2_du_i_r:
                pdf_base64_du_i_r = base64.b64encode(st.session_state['pdf_bytes_du_i_r']).decode('utf-8')
                st.markdown(f"""<a href="data:application/pdf;base64,{pdf_base64_du_i_r}" target="_blank" style="text-decoration: none;"><button style="background-color: #007bff;border: none;color: white;padding: 10px 24px;text-align: center;text-decoration: none;display: inline-block;font-size: 16px;margin: 4px 2px;cursor: pointer;border-radius: 8px;">Xem phiếu</button></a>""", unsafe_allow_html=True)
                st.info("Nhấn 'Xem phiếu' để mở PDF trong tab mới của trình duyệt. Nếu không mở, vui lòng kiểm tra cài đặt trình duyệt hoặc sử dụng nút 'Xuất PDF'.")

    elif cong_thuc == "Ptt & I → R":
        st.latex(r"R = \frac{P_{tt}}{I^2}")
        st.markdown("""
        **Giải thích các thành phần:**
        - \( R \): Điện trở (Ω)
        - \( P_{tt} \): Tổn thất công suất (W)
        - \( I \): Dòng điện (A)
        
        **Mục đích:** Tính toán điện trở của một đoạn mạch khi biết tổn thất công suất và dòng điện.
        """, unsafe_allow_html=True)
        ptt = st.number_input("Ptt (W):", min_value=0.0, key="ptt_i_r_ptt")
        i = st.number_input("I (A):", min_value=0.0, key="ptt_i_r_i")
        r = ptt / (i**2) if i != 0 else 0
        if st.button("Tính R", key="btn_calc_ptt_i_r"):
            st.success(f"R ≈ {r:.3f} Ω")
            calculator_info = {
                'name': calculator_name_ct,
                'title': calculator_title_ct,
                'phone': calculator_phone_ct
            }
            customer_info = {
                'name': customer_name_ct,
                'address': customer_address_ct,
                'phone': customer_phone_ct
            }
            input_params = {
                "Tổn thất công suất Ptt": f"{ptt} W",
                "Dòng điện I": f"{i} A"
            }
            output_results = {
                "Điện trở R": f"{r:.3f} Ω"
            }
            formula_latex = r"R = \frac{P_{tt}}{I^2}"
            formula_explanation = "Công thức tính điện trở từ tổn thất công suất và dòng điện."
            pdf_bytes = create_pdf("ĐIỆN TRỞ (TỪ Ptt & I)", formula_latex, formula_explanation, input_params, output_results, calculator_info, customer_info)
            st.session_state['pdf_bytes_ptt_i_r'] = pdf_bytes
            st.session_state['pdf_filename_ptt_i_r'] = f"Phieu_tinh_R_tu_Ptt_I_{datetime.now().strftime('%Y%m%d')}.pdf"
        if 'pdf_bytes_ptt_i_r' in st.session_state and st.session_state['pdf_bytes_ptt_i_r']:
            st.markdown("---")
            col_pdf1_ptt_i_r, col_pdf2_ptt_i_r = st.columns(2)
            with col_pdf1_ptt_i_r:
                st.download_button(label="Xuất PDF", data=st.session_state['pdf_bytes_ptt_i_r'], file_name=st.session_state['pdf_filename_ptt_i_r'], mime="application/pdf", key="download_ptt_i_r_pdf")
            with col_pdf2_ptt_i_r:
                pdf_base64_ptt_i_r = base64.b64encode(st.session_state['pdf_bytes_ptt_i_r']).decode('utf-8')
                st.markdown(f"""<a href="data:application/pdf;base64,{pdf_base64_ptt_i_r}" target="_blank" style="text-decoration: none;"><button style="background-color: #007bff;border: none;color: white;padding: 10px 24px;text-align: center;text-decoration: none;display: inline-block;font-size: 16px;margin: 4px 2px;cursor: pointer;border-radius: 8px;">Xem phiếu</button></a>""", unsafe_allow_html=True)
                st.info("Nhấn 'Xem phiếu' để mở PDF trong tab mới của trình duyệt. Nếu không mở, vui lòng kiểm tra cài đặt trình duyệt hoặc sử dụng nút 'Xuất PDF'.")

    elif cong_thuc == "ΔU & R → I":
        st.latex(r"I = \frac{\Delta U}{R}")
        st.markdown("""
        **Giải thích các thành phần:**
        - \( I \): Dòng điện (A)
        - \( \Delta U \): Sụt áp (V)
        - \( R \): Điện trở (Ω)
        
        **Mục đích:** Tính toán dòng điện trong một đoạn mạch khi biết sụt áp và điện trở.
        """, unsafe_allow_html=True)
        u = st.number_input("ΔU (V):", min_value=0.0, key="du_r_i_u")
        r = st.number_input("R (Ω):", min_value=0.0, key="du_r_i_r")
        i = u / r if r != 0 else 0
        if st.button("Tính I", key="btn_calc_du_r_i"):
            st.success(f"I ≈ {i:.3f} A")
            calculator_info = {
                'name': calculator_name_ct,
                'title': calculator_title_ct,
                'phone': calculator_phone_ct
            }
            customer_info = {
                'name': customer_name_ct,
                'address': customer_address_ct,
                'phone': customer_phone_ct
            }
            input_params = {
                "Sụt áp ΔU": f"{u} V",
                "Điện trở R": f"{r} Ω"
            }
            output_results = {
                "Dòng điện I": f"{i:.3f} A"
            }
            formula_latex = r"I = \frac{\Delta U}{R}"
            formula_explanation = "Công thức tính dòng điện từ sụt áp và điện trở."
            pdf_bytes = create_pdf("DÒNG ĐIỆN (TỪ ΔU & R)", formula_latex, formula_explanation, input_params, output_results, calculator_info, customer_info)
            st.session_state['pdf_bytes_du_r_i'] = pdf_bytes
            st.session_state['pdf_filename_du_r_i'] = f"Phieu_tinh_I_tu_DU_R_{datetime.now().strftime('%Y%m%d')}.pdf"
        if 'pdf_bytes_du_r_i' in st.session_state and st.session_state['pdf_bytes_du_r_i']:
            st.markdown("---")
            col_pdf1_du_r_i, col_pdf2_du_r_i = st.columns(2)
            with col_pdf1_du_r_i:
                st.download_button(label="Xuất PDF", data=st.session_state['pdf_bytes_du_r_i'], file_name=st.session_state['pdf_filename_du_r_i'], mime="application/pdf", key="download_du_r_i_pdf")
            with col_pdf2_du_r_i:
                pdf_base64_du_r_i = base64.b64encode(st.session_state['pdf_bytes_du_r_i']).decode('utf-8')
                st.markdown(f"""<a href="data:application/pdf;base64,{pdf_base64_du_i_r}" target="_blank" style="text-decoration: none;"><button style="background-color: #007bff;border: none;color: white;padding: 10px 24px;text-align: center;text-decoration: none;display: inline-block;font-size: 16px;margin: 4px 2px;cursor: pointer;border-radius: 8px;">Xem phiếu</button></a>""", unsafe_allow_html=True)
                st.info("Nhấn 'Xem phiếu' để mở PDF trong tab mới của trình duyệt. Nếu không mở, vui lòng kiểm tra cài đặt trình duyệt hoặc sử dụng nút 'Xuất PDF'.")

    elif cong_thuc == "Ptt & R → I":
        st.latex(r"I = \sqrt{\frac{P_{tt}}{R}}")
        st.markdown("""
        **Giải thích các thành phần:**
        - \( I \): Dòng điện (A)
        - \( P_{tt} \): Tổn thất công suất (W)
        - \( R \): Điện trở (Ω)
        
        **Mục đích:** Tính toán dòng điện trong một đoạn mạch khi biết tổn thất công suất và điện trở.
        """, unsafe_allow_html=True)
        ptt = st.number_input("Ptt (W):", min_value=0.0, key="ptt_r_i_ptt")
        r = st.number_input("R (Ω):", min_value=0.0, key="ptt_r_i_r")
        i = math.sqrt(ptt / r) if r != 0 and ptt >= 0 else 0 # Ensure ptt is non-negative for sqrt
        if st.button("Tính I", key="btn_calc_ptt_r_i"):
            st.success(f"I ≈ {i:.3f} A")
            calculator_info = {
                'name': calculator_name_ct,
                'title': calculator_title_ct,
                'phone': calculator_phone_ct
            }
            customer_info = {
                'name': customer_name_ct,
                'address': customer_address_ct,
                'phone': customer_phone_ct
            }
            input_params = {
                "Tổn thất công suất Ptt": f"{ptt} W",
                "Điện trở R": f"{r} Ω"
            }
            output_results = {
                "Dòng điện I": f"{i:.3f} A"
            }
            formula_latex = r"I = \sqrt{\frac{P_{tt}}{R}}"
            formula_explanation = "Công thức tính dòng điện từ tổn thất công suất và điện trở."
            pdf_bytes = create_pdf("DÒNG ĐIỆN (TỪ Ptt & R)", formula_latex, formula_explanation, input_params, output_results, calculator_info, customer_info)
            st.session_state['pdf_bytes_ptt_r_i'] = pdf_bytes
            st.session_state['pdf_filename_ptt_r_i'] = f"Phieu_tinh_I_tu_Ptt_R_{datetime.now().strftime('%Y%m%d')}.pdf"
        if 'pdf_bytes_ptt_r_i' in st.session_state and st.session_state['pdf_bytes_ptt_r_i']:
            st.markdown("---")
            col_pdf1_ptt_r_i, col_pdf2_ptt_r_i = st.columns(2)
            with col_pdf1_ptt_r_i:
                st.download_button(label="Xuất PDF", data=st.session_state['pdf_bytes_ptt_r_i'], file_name=st.session_state['pdf_filename_ptt_r_i'], mime="application/pdf", key="download_ptt_r_i_pdf")
            with col_pdf2_ptt_r_i:
                pdf_base64_ptt_r_i = base64.b64encode(st.session_state['pdf_bytes_ptt_r_i']).decode('utf-8')
                st.markdown(f"""<a href="data:application/pdf;base64,{pdf_base64_ptt_r_i}" target="_blank" style="text-decoration: none;"><button style="background-color: #007bff;border: none;color: white;padding: 10px 24px;text-align: center;text-decoration: none;display: inline-block;font-size: 16px;margin: 4px 2px;cursor: pointer;border-radius: 8px;">Xem phiếu</button></a>""", unsafe_allow_html=True)
                st.info("Nhấn 'Xem phiếu' để mở PDF trong tab mới của trình duyệt. Nếu không mở, vui lòng kiểm tra cài đặt trình duyệt hoặc sử dụng nút 'Xuất PDF'.")
