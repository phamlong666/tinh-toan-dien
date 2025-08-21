import matplotlib.pyplot as plt
from reportlab.platypus import Image as RLImage
import io
import numpy as np

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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as ReportLabImage
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
    font_name = 'DejaVuSans'
    font_name_bold = 'DejaVuSans-Bold'
except Exception:
    st.warning("⚠️ Không tìm thấy font 'DejaVuSans.ttf' hoặc 'DejaVuSans-Bold.ttf'. PDF có thể không hiển thị tiếng Việt đúng cách. Vui lòng đảm bảo các file font này nằm cùng thư mục với app.py hoặc sử dụng font mặc định của ReportLab.")
    font_name = 'Helvetica'
    font_name_bold = 'Helvetica-Bold'


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
main_menu = st.sidebar.radio("", ["Trang chủ", "Tính toán điện", "Chuyển đổi đơn vị", "Công thức điện", "📋 BẢNG LIỆT KÊ CÔNG SUẤT CÁC THIẾT BỊ SỬ DỤNG ĐIỆN"])

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
        # Changed font size from 17 to 15 to prevent text overflow
        styles.add(ParagraphStyle(name='TitleStyle', fontName='DejaVuSans-Bold', fontSize=15, alignment=1, spaceAfter=10)) 
        styles.add(ParagraphStyle(name='Heading2Style', fontName='DejaVuSans-Bold', fontSize=14, spaceAfter=5)) 
        styles.add(ParagraphStyle(name='NormalStyle', fontName='DejaVuSans', fontSize=12, spaceAfter=4)) 
        styles.add(ParagraphStyle(name='TableCellStyle', fontName='DejaVuSans', fontSize=11, alignment=0, leading=13)) # Increased font size and leading
        styles.add(ParagraphStyle(name='TableCellBoldStyle', fontName='DejaVuSans-Bold', fontSize=11, alignment=0, leading=13)) # Increased font size and leading
    except KeyError:
        styles.add(ParagraphStyle(name='TitleStyle', fontName='Helvetica-Bold', fontSize=15, alignment=1, spaceAfter=10)) # Changed font size here too
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
        formula_img = ReportLabImage(formula_img_buf, width=5.0*inch, height=0.7*inch) # Adjusted image size
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
        ('FONTNAME', (0,0), (0,-1), font_name_bold),
        ('FONTNAME', (1,0), (1,-1), font_name),
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
        ('FONTNAME', (0,0), (0,-1), font_name_bold),
        ('FONTNAME', (1,0), (1,-1), font_name),
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
        ('FONTNAME', (0,0), (-1,-1), font_name),
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
    
# Hàm tạo PDF cho bảng liệt kê thiết bị
def create_equipment_list_pdf(df_export, don_vi, dia_chi, dia_diem, so_dien_thoai):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            topMargin=0.5 * inch, bottomMargin=0.5 * inch,
                            leftMargin=0.5 * inch, rightMargin=0.5 * inch)
    styles = getSampleStyleSheet()
    
    # Check if custom fonts are available, otherwise fallback
    try:
        font_name = 'DejaVuSans'
        font_name_bold = 'DejaVuSans-Bold'
    except:
        font_name = 'Helvetica'
        font_name_bold = 'Helvetica-Bold'
        
    styles.add(ParagraphStyle(name='VietnameseTitle', fontName=font_name_bold, fontSize=14, alignment=1, spaceAfter=12))
    styles.add(ParagraphStyle(name='VietnameseNormal', fontName=font_name, fontSize=10, alignment=0))
    styles.add(ParagraphStyle(name='VietnameseTableHeader', fontName=font_name_bold, fontSize=8, alignment=1, textColor=colors.white))
    styles.add(ParagraphStyle(name='VietnameseTableCell', fontName=font_name, fontSize=8, alignment=1))
    
    elements = []
    
    elements.append(Paragraph("BẢNG LIỆT KÊ CÔNG SUẤT CÁC THIẾT BỊ SỬ DỤNG ĐIỆN", styles['VietnameseTitle']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Đơn vị: {don_vi}", styles['VietnameseNormal']))
    elements.append(Paragraph(f"Địa chỉ: {dia_chi}", styles['VietnameseNormal']))
    elements.append(Paragraph(f"Địa điểm: {dia_diem}", styles['VietnameseNormal']))
    elements.append(Paragraph(f"Số điện thoại: {so_dien_thoai}", styles['VietnameseNormal']))
    elements.append(Spacer(1, 12))
    
    header = [Paragraph(col, styles['VietnameseTableHeader']) for col in df_export.columns.tolist()]
    data = [[Paragraph(str(item), styles['VietnameseTableCell']) for item in row] for row in df_export.values.tolist()]
    
    table_data = [header] + data
    t = Table(table_data, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('ALIGN', (0,0), (-1,-1), "CENTER"),
        ('VALIGN', (0,0), (-1,-1), "MIDDLE"),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('BOX', (0,0), (-1,-1), 1, colors.black),
        ('FONTNAME', (0,0), (-1,0), font_name_bold),
        ('FONTNAME', (0,1), (-1,-1), font_name),
    ]))
    
    elements.append(t)
    doc.build(elements)
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
        
        **Mục đích:** Tính toán công suất tiêu thụ của một thiết bị hoặc một hệ thống.
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
            U_p = st.number_input("Điện áp U (V):", min_value=0.0, key="U_p")
        with col2:
            I_p = st.number_input("Dòng điện I (A):", min_value=0.0, key="I_p")
            cos_phi_p = st.slider("Hệ số cosφ:", 0.1, 1.0, 0.8, key="cos_phi_p")

        if st.button("Tính công suất", key="btn_calc_p"):
            P_result = 0.0
            if pha_p == "1 pha":
                P_result = U_p * I_p * cos_phi_p
            elif pha_p == "3 pha":
                P_result = math.sqrt(3) * U_p * I_p * cos_phi_p
            st.success(f"Công suất P ≈ {P_result:.2f} W ({P_result/1000:.2f} kW)")

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
                "Điện áp U": f"{U_p} V",
                "Dòng điện I": f"{I_p} A",
                "Hệ số cosφ": cos_phi_p
            }
            output_results = {
                "Công suất P": f"{P_result:.2f} W ({P_result/1000:.2f} kW)"
            }

            formula_latex = r"P = U \cdot I \cdot \cos\varphi \quad \text{(1 pha)} \quad \text{hoặc} \quad P = \sqrt{3} \cdot U \cdot I \cdot \cos\varphi \quad \text{(3 pha)}"
            formula_explanation = "Công thức tính công suất thực của một hệ thống điện, phụ thuộc vào điện áp, dòng điện và hệ số công suất."

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
        st.latex(r"S = U \cdot I \quad \text{(1 pha)}")
        st.latex(r"S = \sqrt{3} \cdot U \cdot I \quad \text{(3 pha)}")
        st.markdown("""
        **Giải thích các thành phần:**
        - \( S \): Công suất biểu kiến (VA hoặc kVA)
        - \( U \): Điện áp (V)
        - \( I \): Dòng điện (A)
        
        **Mục đích:** Tính toán tổng công suất của một tải, bao gồm cả công suất thực và công suất phản kháng.
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
        
        col1, col2 = st.columns(2)
        with col1:
            pha_s = st.radio("Loại điện:", ["1 pha", "3 pha"], key="pha_s")
            U_s = st.number_input("Điện áp U (V):", min_value=0.0, key="U_s")
        with col2:
            I_s = st.number_input("Dòng điện I (A):", min_value=0.0, key="I_s")

        if st.button("Tính công suất biểu kiến", key="btn_calc_s"):
            S_result = 0.0
            if pha_s == "1 pha":
                S_result = U_s * I_s
            elif pha_s == "3 pha":
                S_result = math.sqrt(3) * U_s * I_s
            st.success(f"Công suất biểu kiến S ≈ {S_result:.2f} VA ({S_result/1000:.2f} kVA)")

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
                "Điện áp U": f"{U_s} V",
                "Dòng điện I": f"{I_s} A",
            }
            output_results = {
                "Công suất biểu kiến S": f"{S_result:.2f} VA ({S_result/1000:.2f} kVA)"
            }
            formula_latex = r"S = U \cdot I \quad \text{(1 pha)} \quad \text{hoặc} \quad S = \sqrt{3} \cdot U \cdot I \quad \text{(3 pha)}"
            formula_explanation = "Công thức tính công suất biểu kiến, là tích của điện áp và dòng điện."
            pdf_bytes = create_pdf("CÔNG SUẤT BIỂU KIẾN", formula_latex, formula_explanation, input_params, output_results, calculator_info, customer_info)
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
        st.latex(r"Q = U \cdot I \cdot \sin\varphi \quad \text{(1 pha)}")
        st.latex(r"Q = \sqrt{3} \cdot U \cdot I \cdot \sin\varphi \quad \text{(3 pha)}")
        st.markdown("""
        **Giải thích các thành phần:**
        - \( Q \): Công suất phản kháng (VAR hoặc kVAR)
        - \( U \): Điện áp (V)
        - \( I \): Dòng điện (A)
        - \( \sin\varphi \): Sin của góc lệch pha giữa điện áp và dòng điện
        
        **Mục đích:** Tính toán công suất phản kháng cần thiết để cung cấp cho các thiết bị có tính chất cảm kháng như động cơ, máy biến áp.
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
        
        col1, col2 = st.columns(2)
        with col1:
            pha_q = st.radio("Loại điện:", ["1 pha", "3 pha"], key="pha_q")
            U_q = st.number_input("Điện áp U (V):", min_value=0.0, key="U_q")
        with col2:
            I_q = st.number_input("Dòng điện I (A):", min_value=0.0, key="I_q")
            cos_phi_q = st.slider("Hệ số cosφ:", 0.1, 1.0, 0.8, key="cos_phi_q")
            sin_phi_q = math.sqrt(1 - cos_phi_q**2)
            st.info(f"sinφ ≈ {sin_phi_q:.2f}")

        if st.button("Tính công suất phản kháng", key="btn_calc_q"):
            Q_result = 0.0
            if pha_q == "1 pha":
                Q_result = U_q * I_q * sin_phi_q
            elif pha_q == "3 pha":
                Q_result = math.sqrt(3) * U_q * I_q * sin_phi_q
            st.success(f"Công suất phản kháng Q ≈ {Q_result:.2f} VAR ({Q_result/1000:.2f} kVAR)")

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
            input_params = {
                "Loại điện": pha_q,
                "Điện áp U": f"{U_q} V",
                "Dòng điện I": f"{I_q} A",
                "Hệ số cosφ": cos_phi_q
            }
            output_results = {
                "Công suất phản kháng Q": f"{Q_result:.2f} VAR ({Q_result/1000:.2f} kVAR)"
            }
            formula_latex = r"Q = U \cdot I \cdot \sin\varphi \quad \text{(1 pha)} \quad \text{hoặc} \quad Q = \sqrt{3} \cdot U \cdot I \cdot \sin\varphi \quad \text{(3 pha)}"
            formula_explanation = "Công thức tính công suất phản kháng, là tích của điện áp, dòng điện và sin của góc lệch pha."
            pdf_bytes = create_pdf("CÔNG SUẤT PHẢN KHÁNG", formula_latex, formula_explanation, input_params, output_results, calculator_info, customer_info)
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
    
    elif sub_menu_tinh_toan == "Tính sụt áp (ΔU)":
        st.header("⚡ Tính sụt áp (ΔU)")
        st.latex(r"\Delta U = \frac{2 \cdot P \cdot L}{\gamma \cdot S} \quad \text{(1 pha)}")
        st.latex(r"\Delta U = \frac{P \cdot L}{\gamma \cdot S} \quad \text{(3 pha)}")
        st.markdown("""
        **Giải thích các thành phần:**
        - \( \Delta U \): Sụt áp (V)
        - \( P \): Công suất tải (kW)
        - \( L \): Chiều dài đường dây (m)
        - \( \gamma \): Độ dẫn điện của vật liệu dây dẫn (\(56\) cho Đồng, \(35\) cho Nhôm)
        - \( S \): Tiết diện dây dẫn (mm²)
        
        **Mục đích:** Đảm bảo điện áp tại điểm cuối đường dây không bị sụt giảm quá mức cho phép, giúp thiết bị hoạt động ổn định.
        """, unsafe_allow_html=True)
        st.subheader("Thông tin Người tính toán")
        calculator_name_u = st.text_input("Họ và tên:", value="Hà Thị Lê", key="calc_name_u")
        calculator_title_u = st.text_input("Chức danh:", value="Tổ trưởng tổ KDDV", key="calc_title_u")
        calculator_phone_u = st.text_input("Số điện thoại:", value="0978578777", key="calc_phone_u")

        st.subheader("Thông tin Khách hàng")
        customer_name_u = st.text_input("Tên khách hàng:", value="Phạm Hồng Long", key="cust_name_u")
        customer_address_u = st.text_input("Địa chỉ:", value="xã Định Hóa, tỉnh Thái Nguyên", key="cust_address_u")
        customer_phone_u = st.text_input("Số điện thoại khách hàng:", value="0968552888", key="cust_phone_u")
        
        current_date_u = datetime.now().strftime("Ngày %d tháng %m năm %Y")
        st.markdown(f"**Thời gian lập phiếu:** {current_date_u}")

        col1, col2 = st.columns(2)
        with col1:
            pha_u = st.radio("Loại điện:", ["1 pha", "3 pha"], key="pha_u")
            P_u = st.number_input("Công suất P (kW):", min_value=0.0, key="P_u")
            L_u = st.number_input("Chiều dài L (m):", min_value=0.0, key="L_u")
        with col2:
            material_u = st.radio("Vật liệu dây dẫn:", ["Đồng", "Nhôm"], key="material_u")
            S_u = st.number_input("Tiết diện S (mm²):", min_value=0.0, key="S_u")
        
        gamma_u = 56 if material_u == "Đồng" else 35

        if st.button("Tính sụt áp", key="btn_calc_u"):
            delta_u = 0.0
            if gamma_u != 0 and S_u != 0:
                if pha_u == "1 pha":
                    delta_u = (2 * P_u * 1000 * L_u) / (gamma_u * S_u)
                elif pha_u == "3 pha":
                    delta_u = (P_u * 1000 * L_u) / (gamma_u * S_u)
            st.success(f"Sụt áp ΔU ≈ {delta_u:.2f} V")
            st.info(f"Độ dẫn điện γ của {material_u}: {gamma_u}")

            calculator_info = {
                'name': calculator_name_u,
                'title': calculator_title_u,
                'phone': calculator_phone_u
            }
            customer_info = {
                'name': customer_name_u,
                'address': customer_address_u,
                'phone': customer_phone_u
            }
            input_params = {
                "Loại điện": pha_u,
                "Công suất P": f"{P_u} kW",
                "Chiều dài L": f"{L_u} m",
                "Vật liệu dây dẫn": material_u,
                "Tiết diện S": f"{S_u} mm²"
            }
            output_results = {
                "Sụt áp ΔU": f"{delta_u:.2f} V"
            }
            formula_latex = r"\Delta U = \frac{2 \cdot P \cdot L}{\gamma \cdot S} \quad \text{(1 pha)} \quad \text{hoặc} \quad \Delta U = \frac{P \cdot L}{\gamma \cdot S} \quad \text{(3 pha)}"
            formula_explanation = "Công thức tính sụt áp trên đường dây, phụ thuộc vào công suất, chiều dài, độ dẫn điện của vật liệu và tiết diện dây."
            
            pdf_bytes = create_pdf("SỤT ÁP", formula_latex, formula_explanation, input_params, output_results, calculator_info, customer_info)
            st.session_state['pdf_bytes_u'] = pdf_bytes
            st.session_state['pdf_filename_u'] = f"Phieu_tinh_sut_ap_{datetime.now().strftime('%Y%m%d')}.pdf"

        if 'pdf_bytes_u' in st.session_state and st.session_state['pdf_bytes_u']:
            st.markdown("---")
            st.subheader("Tùy chọn xuất phiếu sụt áp")
            col_pdf1_u, col_pdf2_u = st.columns(2)
            with col_pdf1_u:
                st.download_button(
                    label="Xuất PDF",
                    data=st.session_state['pdf_bytes_u'],
                    file_name=st.session_state['pdf_filename_u'],
                    mime="application/pdf",
                    key="download_u_pdf"
                )
            with col_pdf2_u:
                pdf_base64_u = base64.b64encode(st.session_state['pdf_bytes_u']).decode('utf-8')
                st.markdown(
                    f"""
                    <a href="data:application/pdf;base64,{pdf_base64_u}" target="_blank" style="text-decoration: none;">
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

    elif sub_menu_tinh_toan == "Chọn tiết diện dây dẫn":
        st.header("⚡ Chọn tiết diện dây dẫn")
        st.markdown("""
        **Mục đích:** Dựa trên dòng điện tính toán, lựa chọn tiết diện dây dẫn phù hợp để đảm bảo an toàn và hiệu quả.
        
        **Cách sử dụng:**
        1. Nhập thông tin.
        2. Bấm nút "Chọn tiết diện".
        3. Ứng dụng sẽ tự động tra bảng và đưa ra khuyến nghị.
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            I_choose = st.number_input("Dòng điện tính toán I (A):", min_value=0.0, key="I_choose")
            material_choose = st.radio("Vật liệu dây dẫn:", ["Đồng", "Nhôm"], key="material_choose")
        with col2:
            installation_type = st.radio("Loại lắp đặt:", ["Đi nổi (Trong không khí)", "Trong ống"], key="install_type")

        # Select the correct data based on material and installation type
        data_to_use = {}
        if material_choose == "Đồng":
            if copper_cable_data:
                data_to_use = copper_cable_data['in_air'] if installation_type == "Đi nổi (Trong không khí)" else copper_cable_data['in_conduit']
        elif material_choose == "Nhôm":
            if aluminum_cable_data:
                data_to_use = aluminum_cable_data['in_air'] if installation_type == "Đi nổi (Trong không khí)" else aluminum_cable_data['in_conduit']

        if st.button("Chọn tiết diện", key="btn_choose_s"):
            if not data_to_use:
                st.warning("⚠️ Không có dữ liệu bảng tra. Vui lòng kiểm tra lại file Excel.")
            else:
                found_size = None
                for size, capacity in data_to_use.items():
                    if I_choose <= capacity:
                        found_size = size
                        break
                
                if found_size:
                    st.success(f"Khuyến nghị: Chọn dây có tiết diện S = {found_size} mm² (Khả năng chịu tải: {data_to_use[found_size]} A)")
                else:
                    max_capacity_size = max(data_to_use, key=data_to_use.get)
                    max_capacity = data_to_use[max_capacity_size]
                    st.warning(f"Không tìm thấy tiết diện phù hợp. Dòng điện {I_choose} A vượt quá khả năng chịu tải của tiết diện lớn nhất trong bảng ({max_capacity_size} mm² - {max_capacity} A).")
    
    elif sub_menu_tinh_toan == "Chiều dài dây tối đa (ΔU%)":
        st.header("⚡ Chiều dài dây tối đa (ΔU%)")
        st.latex(r"L_{max} = \frac{U_{dm}^2 \cdot \Delta U\%}{100 \cdot P \cdot 2} \quad \text{(1 pha)}")
        st.latex(r"L_{max} = \frac{U_{dm}^2 \cdot \Delta U\%}{100 \cdot P} \quad \text{(3 pha)}")
        st.markdown("""
        **Giải thích các thành phần:**
        - \( L_{max} \): Chiều dài tối đa (m)
        - \( U_{dm} \): Điện áp định mức (V)
        - \( \Delta U\% \): Phần trăm sụt áp cho phép (%)
        - \( P \): Công suất tải (kW)
        - \( 2 \): Hệ số cho mạch 1 pha (đi và về)
        
        **Mục đích:** Xác định chiều dài tối đa của đường dây để sụt áp không vượt quá giới hạn cho phép.
        """, unsafe_allow_html=True)
        st.subheader("Thông tin Người tính toán")
        calculator_name_l = st.text_input("Họ và tên:", value="Hà Thị Lê", key="calc_name_l")
        calculator_title_l = st.text_input("Chức danh:", value="Tổ trưởng tổ KDDV", key="calc_title_l")
        calculator_phone_l = st.text_input("Số điện thoại:", value="0978578777", key="calc_phone_l")

        st.subheader("Thông tin Khách hàng")
        customer_name_l = st.text_input("Tên khách hàng:", value="Phạm Hồng Long", key="cust_name_l")
        customer_address_l = st.text_input("Địa chỉ:", value="xã Định Hóa, tỉnh Thái Nguyên", key="cust_address_l")
        customer_phone_l = st.text_input("Số điện thoại khách hàng:", value="0968552888", key="cust_phone_l")
        
        current_date_l = datetime.now().strftime("Ngày %d tháng %m năm %Y")
        st.markdown(f"**Thời gian lập phiếu:** {current_date_l}")

        col1, col2 = st.columns(2)
        with col1:
            pha_l = st.radio("Loại điện:", ["1 pha", "3 pha"], key="pha_l")
            U_dm_l = st.number_input("Điện áp định mức Uđm (V):", min_value=0.0, key="U_dm_l")
            delta_U_percent_l = st.number_input("Sụt áp cho phép ΔU% (%):", min_value=0.0, key="delta_U_percent_l")
        with col2:
            P_l = st.number_input("Công suất P (kW):", min_value=0.0, key="P_l")

        if st.button("Tính chiều dài tối đa", key="btn_calc_l"):
            L_max = 0.0
            if P_l != 0:
                if pha_l == "1 pha":
                    L_max = (U_dm_l**2 * delta_U_percent_l) / (100 * P_l * 2)
                elif pha_l == "3 pha":
                    L_max = (U_dm_l**2 * delta_U_percent_l) / (100 * P_l)
            st.success(f"Chiều dài dây tối đa Lmax ≈ {L_max:.2f} m")

            calculator_info = {
                'name': calculator_name_l,
                'title': calculator_title_l,
                'phone': calculator_phone_l
            }
            customer_info = {
                'name': customer_name_l,
                'address': customer_address_l,
                'phone': customer_phone_l
            }
            input_params = {
                "Loại điện": pha_l,
                "Điện áp định mức Uđm": f"{U_dm_l} V",
                "Sụt áp cho phép ΔU%": f"{delta_U_percent_l} %",
                "Công suất P": f"{P_l} kW"
            }
            output_results = {
                "Chiều dài dây tối đa Lmax": f"{L_max:.2f} m"
            }
            formula_latex = r"L_{max} = \frac{U_{dm}^2 \cdot \Delta U\%}{100 \cdot P \cdot 2} \quad \text{(1 pha)} \quad \text{hoặc} \quad L_{max} = \frac{U_{dm}^2 \cdot \Delta U\%}{100 \cdot P} \quad \text{(3 pha)}"
            formula_explanation = "Công thức tính chiều dài tối đa của đường dây để sụt áp không vượt quá giới hạn cho phép."
            
            pdf_bytes = create_pdf("CHIỀU DÀI TỐI ĐA", formula_latex, formula_explanation, input_params, output_results, calculator_info, customer_info)
            st.session_state['pdf_bytes_l'] = pdf_bytes
            st.session_state['pdf_filename_l'] = f"Phieu_tinh_chieu_dai_toi_da_{datetime.now().strftime('%Y%m%d')}.pdf"

        if 'pdf_bytes_l' in st.session_state and st.session_state['pdf_bytes_l']:
            st.markdown("---")
            st.subheader("Tùy chọn xuất phiếu chiều dài tối đa")
            col_pdf1_l, col_pdf2_l = st.columns(2)
            with col_pdf1_l:
                st.download_button(
                    label="Xuất PDF",
                    data=st.session_state['pdf_bytes_l'],
                    file_name=st.session_state['pdf_filename_l'],
                    mime="application/pdf",
                    key="download_l_pdf"
                )
            with col_pdf2_l:
                pdf_base64_l = base64.b64encode(st.session_state['pdf_bytes_l']).decode('utf-8')
                st.markdown(
                    f"""
                    <a href="data:application/pdf;base64,{pdf_base64_l}" target="_blank" style="text-decoration: none;">
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
        st.latex(r"Z = \sqrt{R^2 + (X_L - X_C)^2}")
        st.markdown("""
        **Giải thích các thành phần:**
        - \( Z \): Tổng trở (Ω)
        - \( R \): Điện trở thuần (Ω)
        - \( X_L \): Cảm kháng (Ω)
        - \( X_C \): Dung kháng (Ω)
        
        **Mục đích:** Tính toán các thông số của mạch điện xoay chiều.
        """, unsafe_allow_html=True)
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

        R_z = st.number_input("Điện trở thuần R (Ω):", min_value=0.0, key="R_z")
        X_L_z = st.number_input("Cảm kháng XL (Ω):", min_value=0.0, key="X_L_z")
        X_C_z = st.number_input("Dung kháng XC (Ω):", min_value=0.0, key="X_C_z")

        if st.button("Tính tổng trở", key="btn_calc_z"):
            Z_result = math.sqrt(R_z**2 + (X_L_z - X_C_z)**2)
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
                "Cảm kháng XL": f"{X_L_z} Ω",
                "Dung kháng XC": f"{X_C_z} Ω"
            }
            output_results = {
                "Tổng trở Z": f"{Z_result:.2f} Ω"
            }
            formula_latex = r"Z = \sqrt{R^2 + (X_L - X_C)^2}"
            formula_explanation = "Công thức tính tổng trở của mạch điện xoay chiều."
            
            pdf_bytes = create_pdf("TỔNG TRỞ", formula_latex, formula_explanation, input_params, output_results, calculator_info, customer_info)
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
        st.latex(r"\Delta P = \frac{P^2 \cdot \rho \cdot L}{U^2 \cdot S \cdot \cos^2\varphi}")
        st.markdown("""
        **Giải thích các thành phần:**
        - \( \Delta P \): Tổn thất công suất (kW)
        - \( P \): Công suất tải (kW)
        - \( \rho \): Điện trở suất của vật liệu dây dẫn (Ω·mm²/m)
        - \( L \): Chiều dài đường dây (m)
        - \( U \): Điện áp (V)
        - \( S \): Tiết diện dây dẫn (mm²)
        - \( \cos\varphi \): Hệ số công suất
        
        **Mục đích:** Đánh giá hiệu suất truyền tải điện và lựa chọn dây dẫn phù hợp.
        """, unsafe_allow_html=True)
        st.subheader("Thông tin Người tính toán")
        calculator_name_p_loss = st.text_input("Họ và tên:", value="Hà Thị Lê", key="calc_name_p_loss")
        calculator_title_p_loss = st.text_input("Chức danh:", value="Tổ trưởng tổ KDDV", key="calc_title_p_loss")
        calculator_phone_p_loss = st.text_input("Số điện thoại:", value="0978578777", key="calc_phone_p_loss")

        st.subheader("Thông tin Khách hàng")
        customer_name_p_loss = st.text_input("Tên khách hàng:", value="Phạm Hồng Long", key="cust_name_p_loss")
        customer_address_p_loss = st.text_input("Địa chỉ:", value="xã Định Hóa, tỉnh Thái Nguyên", key="cust_address_p_loss")
        customer_phone_p_loss = st.text_input("Số điện thoại khách hàng:", value="0968552888", key="cust_phone_p_loss")
        
        current_date_p_loss = datetime.now().strftime("Ngày %d tháng %m năm %Y")
        st.markdown(f"**Thời gian lập phiếu:** {current_date_p_loss}")

        col1, col2 = st.columns(2)
        with col1:
            P_p_loss = st.number_input("Công suất P (kW):", min_value=0.0, key="P_p_loss")
            U_p_loss = st.number_input("Điện áp U (V):", min_value=0.0, key="U_p_loss")
            S_p_loss = st.number_input("Tiết diện S (mm²):", min_value=0.0, key="S_p_loss")
        with col2:
            material_p_loss = st.radio("Vật liệu dây dẫn:", ["Đồng", "Nhôm"], key="material_p_loss")
            L_p_loss = st.number_input("Chiều dài L (m):", min_value=0.0, key="L_p_loss")
            cos_phi_p_loss = st.slider("Hệ số cosφ:", 0.1, 1.0, 0.8, key="cos_phi_p_loss")
        
        rho_p_loss = 0.01786 if material_p_loss == "Đồng" else 0.0286
        st.info(f"Điện trở suất ρ của {material_p_loss}: {rho_p_loss}")

        if st.button("Tính tổn thất công suất", key="btn_calc_p_loss"):
            delta_P = 0.0
            if U_p_loss != 0 and S_p_loss != 0 and cos_phi_p_loss != 0:
                delta_P = (P_p_loss * 1000)**2 * rho_p_loss * L_p_loss / (U_p_loss**2 * S_p_loss * cos_phi_p_loss**2) / 1000
            st.success(f"Tổn thất công suất ΔP ≈ {delta_P:.2f} kW")

            calculator_info = {
                'name': calculator_name_p_loss,
                'title': calculator_title_p_loss,
                'phone': calculator_phone_p_loss
            }
            customer_info = {
                'name': customer_name_p_loss,
                'address': customer_address_p_loss,
                'phone': customer_phone_p_loss
            }
            input_params = {
                "Công suất P": f"{P_p_loss} kW",
                "Điện áp U": f"{U_p_loss} V",
                "Tiết diện S": f"{S_p_loss} mm²",
                "Vật liệu dây dẫn": material_p_loss,
                "Chiều dài L": f"{L_p_loss} m",
                "Hệ số cosφ": cos_phi_p_loss
            }
            output_results = {
                "Tổn thất công suất ΔP": f"{delta_P:.2f} kW"
            }
            formula_latex = r"\Delta P = \frac{P^2 \cdot \rho \cdot L}{U^2 \cdot S \cdot \cos^2\varphi}"
            formula_explanation = "Công thức tính tổn thất công suất trên đường dây truyền tải."

            pdf_bytes = create_pdf("TỔN THẤT CÔNG SUẤT", formula_latex, formula_explanation, input_params, output_results, calculator_info, customer_info)
            st.session_state['pdf_bytes_p_loss'] = pdf_bytes
            st.session_state['pdf_filename_p_loss'] = f"Phieu_tinh_ton_that_cong_suat_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        if 'pdf_bytes_p_loss' in st.session_state and st.session_state['pdf_bytes_p_loss']:
            st.markdown("---")
            st.subheader("Tùy chọn xuất phiếu tổn thất công suất")
            col_pdf1_p_loss, col_pdf2_p_loss = st.columns(2)
            with col_pdf1_p_loss:
                st.download_button(
                    label="Xuất PDF",
                    data=st.session_state['pdf_bytes_p_loss'],
                    file_name=st.session_state['pdf_filename_p_loss'],
                    mime="application/pdf",
                    key="download_p_loss_pdf"
                )
            with col_pdf2_p_loss:
                pdf_base64_p_loss = base64.b64encode(st.session_state['pdf_bytes_p_loss']).decode('utf-8')
                st.markdown(
                    f"""
                    <a href="data:application/pdf;base64,{pdf_base64_p_loss}" target="_blank" style="text-decoration: none;">
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
    
    elif sub_menu_tinh_toan == "Tính công suất cosφ":
        st.header("⚡ Tính công suất cosφ")
        st.latex(r"\cos\varphi = \frac{P}{S}")
        st.markdown("""
        **Giải thích các thành phần:**
        - \( \cos\varphi \): Hệ số công suất
        - \( P \): Công suất thực (W hoặc kW)
        - \( S \): Công suất biểu kiến (VA hoặc kVA)
        
        **Mục đích:** Xác định hệ số công suất của hệ thống, giúp cải thiện hiệu quả sử dụng điện.
        """, unsafe_allow_html=True)
        st.subheader("Thông tin Người tính toán")
        calculator_name_cos = st.text_input("Họ và tên:", value="Hà Thị Lê", key="calc_name_cos")
        calculator_title_cos = st.text_input("Chức danh:", value="Tổ trưởng tổ KDDV", key="calc_title_cos")
        calculator_phone_cos = st.text_input("Số điện thoại:", value="0978578777", key="calc_phone_cos")

        st.subheader("Thông tin Khách hàng")
        customer_name_cos = st.text_input("Tên khách hàng:", value="Phạm Hồng Long", key="cust_name_cos")
        customer_address_cos = st.text_input("Địa chỉ:", value="xã Định Hóa, tỉnh Thái Nguyên", key="cust_address_cos")
        customer_phone_cos = st.text_input("Số điện thoại khách hàng:", value="0968552888", key="cust_phone_cos")
        
        current_date_cos = datetime.now().strftime("Ngày %d tháng %m năm %Y")
        st.markdown(f"**Thời gian lập phiếu:** {current_date_cos}")

        P_cos = st.number_input("Công suất P (kW):", min_value=0.0, key="P_cos")
        S_cos = st.number_input("Công suất biểu kiến S (kVA):", min_value=0.0, key="S_cos")
        
        if st.button("Tính cosφ", key="btn_calc_cos"):
            cos_phi_result = 0.0
            if S_cos != 0:
                cos_phi_result = P_cos / S_cos
            st.success(f"Hệ số công suất cosφ ≈ {cos_phi_result:.2f}")

            calculator_info = {
                'name': calculator_name_cos,
                'title': calculator_title_cos,
                'phone': calculator_phone_cos
            }
            customer_info = {
                'name': customer_name_cos,
                'address': customer_address_cos,
                'phone': customer_phone_cos
            }
            input_params = {
                "Công suất P": f"{P_cos} kW",
                "Công suất biểu kiến S": f"{S_cos} kVA"
            }
            output_results = {
                "Hệ số công suất cosφ": f"{cos_phi_result:.2f}"
            }
            formula_latex = r"\cos\varphi = \frac{P}{S}"
            formula_explanation = "Công thức tính hệ số công suất, là tỷ lệ giữa công suất thực và công suất biểu kiến."
            
            pdf_bytes = create_pdf("HỆ SỐ CÔNG SUẤT", formula_latex, formula_explanation, input_params, output_results, calculator_info, customer_info)
            st.session_state['pdf_bytes_cos'] = pdf_bytes
            st.session_state['pdf_filename_cos'] = f"Phieu_tinh_cos_phi_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        if 'pdf_bytes_cos' in st.session_state and st.session_state['pdf_bytes_cos']:
            st.markdown("---")
            st.subheader("Tùy chọn xuất phiếu hệ số công suất")
            col_pdf1_cos, col_pdf2_cos = st.columns(2)
            with col_pdf1_cos:
                st.download_button(
                    label="Xuất PDF",
                    data=st.session_state['pdf_bytes_cos'],
                    file_name=st.session_state['pdf_filename_cos'],
                    mime="application/pdf",
                    key="download_cos_pdf"
                )
            with col_pdf2_cos:
                pdf_base64_cos = base64.b64encode(st.session_state['pdf_bytes_cos']).decode('utf-8')
                st.markdown(
                    f"""
                    <a href="data:application/pdf;base64,{pdf_base64_cos}" target="_blank" style="text-decoration: none;">
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
        st.header("⚡ Chọn thiết bị bảo vệ (Áptomat)")
        st.markdown("""
        **Mục đích:** Dựa trên dòng điện tính toán, lựa chọn thiết bị bảo vệ (áptomat) phù hợp để bảo vệ an toàn cho hệ thống điện.
        
        **Cách sử dụng:**
        1. Nhập dòng điện tính toán (Itt).
        2. Bấm nút "Chọn áptomat".
        3. Ứng dụng sẽ tra bảng áptomat thông dụng và đưa ra khuyến nghị.
        """, unsafe_allow_html=True)

        I_tt = st.number_input("Dòng điện tính toán Itt (A):", min_value=0.0, key="I_tt")
        
        if st.button("Chọn áptomat", key="btn_choose_aptomat"):
            aptomat_table = {
                6: "Áptomat 6A",
                10: "Áptomat 10A",
                16: "Áptomat 16A",
                20: "Áptomat 20A",
                25: "Áptomat 25A",
                32: "Áptomat 32A",
                40: "Áptomat 40A",
                50: "Áptomat 50A",
                63: "Áptomat 63A",
                80: "Áptomat 80A",
                100: "Áptomat 100A",
            }
            
            found_aptomat = None
            for rated_current in sorted(aptomat_table.keys()):
                # I_tt <= I_rated
                if I_tt <= rated_current:
                    found_aptomat = aptomat_table[rated_current]
                    break

            if found_aptomat:
                st.success(f"Khuyến nghị: Chọn {found_aptomat}")
            else:
                st.warning("Không tìm thấy áptomat phù hợp trong bảng. Dòng điện tính toán vượt quá giới hạn của bảng.")

elif main_menu == "Chuyển đổi đơn vị":
    st.header("🔄 Chuyển đổi đơn vị")
    unit_conversion_menu = st.sidebar.selectbox("Chọn loại chuyển đổi:", [
        "Từ kW sang kVA",
        "Từ kVA sang kW",
        "Từ kW sang HP",
        "Từ HP sang kW"
    ])
    
    if unit_conversion_menu == "Từ kW sang kVA":
        st.subheader("Từ kW sang kVA")
        P_kw = st.number_input("Nhập công suất P (kW):", min_value=0.0, key="P_kw")
        cos_phi_conv = st.slider("Hệ số cosφ:", 0.1, 1.0, 0.8, key="cos_phi_conv")
        if st.button("Chuyển đổi", key="btn_kw_kva"):
            if cos_phi_conv != 0:
                S_kva = P_kw / cos_phi_conv
                st.success(f"Công suất biểu kiến S ≈ {S_kva:.2f} kVA")
            else:
                st.error("Hệ số cosφ không thể bằng 0.")

    elif unit_conversion_menu == "Từ kVA sang kW":
        st.subheader("Từ kVA sang kW")
        S_kva = st.number_input("Nhập công suất biểu kiến S (kVA):", min_value=0.0, key="S_kva")
        cos_phi_conv = st.slider("Hệ số cosφ:", 0.1, 1.0, 0.8, key="cos_phi_conv_2")
        if st.button("Chuyển đổi", key="btn_kva_kw"):
            P_kw = S_kva * cos_phi_conv
            st.success(f"Công suất P ≈ {P_kw:.2f} kW")

    elif unit_conversion_menu == "Từ kW sang HP":
        st.subheader("Từ kW sang HP")
        P_kw_hp = st.number_input("Nhập công suất P (kW):", min_value=0.0, key="P_kw_hp")
        if st.button("Chuyển đổi", key="btn_kw_hp"):
            hp = P_kw_hp * 1.341
            st.success(f"Công suất HP ≈ {hp:.2f} HP")
    
    elif unit_conversion_menu == "Từ HP sang kW":
        st.subheader("Từ HP sang kW")
        HP_kw = st.number_input("Nhập công suất HP (HP):", min_value=0.0, key="HP_kw")
        if st.button("Chuyển đổi", key="btn_hp_kw"):
            kw = HP_kw / 1.341
            st.success(f"Công suất kW ≈ {kw:.2f} kW")


elif main_menu == "Công thức điện":
    st.header("✍️ Các công thức điện cơ bản")
    st.markdown("""
    Tổng hợp các công thức thường dùng trong ngành điện.
    """)
    
    st.markdown("### Định luật Ohm")
    st.latex(r"U = I \cdot R")
    st.markdown("""
    - \( U \): Điện áp (V)
    - \( I \): Dòng điện (A)
    - \( R \): Điện trở (Ω)
    """)
    
    st.markdown("### Công suất 1 pha")
    st.latex(r"P = U \cdot I \cdot \cos\varphi")
    st.markdown("""
    - \( P \): Công suất thực (W)
    - \( U \): Điện áp (V)
    - \( I \): Dòng điện (A)
    - \( \cos\varphi \): Hệ số công suất
    """)
    
    st.markdown("### Công suất 3 pha")
    st.latex(r"P = \sqrt{3} \cdot U \cdot I \cdot \cos\varphi")
    st.markdown("""
    - \( P \): Công suất thực (W)
    - \( U \): Điện áp dây (V)
    - \( I \): Dòng điện pha (A)
    - \( \cos\varphi \): Hệ số công suất
    """)
    
    st.markdown("### Sụt áp")
    st.latex(r"\Delta U = \frac{2 \cdot P \cdot L}{\gamma \cdot S} \quad \text{(1 pha)}")
    st.latex(r"\Delta U = \frac{P \cdot L}{\gamma \cdot S} \quad \text{(3 pha)}")
    st.markdown("""
    - \( \Delta U \): Sụt áp (V)
    - \( P \): Công suất (W)
    - \( L \): Chiều dài đường dây (m)
    - \( \gamma \): Độ dẫn điện (m/Ω·mm²)
    - \( S \): Tiết diện dây dẫn (mm²)
    """)
    
elif main_menu == "📋 BẢNG LIỆT KÊ CÔNG SUẤT CÁC THIẾT BỊ SỬ DỤNG ĐIỆN":
    # Di chuyển toàn bộ logic tạo và hiển thị bảng vào đây
    st.header("📋 BẢNG LIỆT KÊ CÔNG SUẤT CÁC THIẾT BỊ SỬ DỤNG ĐIỆN")
    
    # Check if a list of devices exists in the session state
    if 'devices' not in st.session_state:
        st.session_state['devices'] = []
    
    # Input form for customer info
    with st.expander("📝 Nhập thông tin khách hàng"):
        don_vi = st.text_input("Đơn vị:", value="Mắt Nâu", key="don_vi")
        dia_chi = st.text_input("Địa chỉ:", value="Định Hóa, Thái Nguyên", key="dia_chi")
        dia_diem = st.text_input("Địa điểm:", value="Định Hóa", key="dia_diem")
        so_dien_thoai = st.text_input("Số điện thoại:", value="0978578777", key="so_dien_thoai")

    st.markdown("---")
    
    # Input form for adding a new device
    st.subheader("➕ Thêm thiết bị")
    with st.form("add_device_form"):
        ten_thiet_bi = st.text_input("Tên thiết bị:", key="ten_thiet_bi")
        cong_suat_danh_dinh = st.number_input("Công suất định mức (W):", min_value=0.0, key="cong_suat_danh_dinh")
        so_luong = st.number_input("Số lượng:", min_value=1, step=1, key="so_luong")
        he_so_sd = st.slider("Hệ số sử dụng (cosφ):", 0.1, 1.0, 0.8, key="he_so_sd")
        
        col_form1, col_form2 = st.columns(2)
        with col_form1:
            add_button = st.form_submit_button("Thêm thiết bị", type="primary")
        with col_form2:
            clear_form = st.form_submit_button("Xóa nội dung")

        if add_button:
            if ten_thiet_bi:
                total_power = cong_suat_danh_dinh * so_luong
                st.session_state.devices.append({
                    "Tên thiết bị": ten_thiet_bi,
                    "Số lượng": so_luong,
                    "Công suất định mức (W)": cong_suat_danh_dinh,
                    "Tổng công suất (W)": total_power,
                    "Hệ số sử dụng": he_so_sd,
                    "Tổng công suất tính toán (W)": total_power * he_so_sd
                })
                st.success(f"Đã thêm thiết bị: {ten_thiet_bi}")
            else:
                st.error("Vui lòng nhập tên thiết bị.")
        
        if clear_form:
            st.session_state.ten_thiet_bi = ""
            st.session_state.cong_suat_danh_dinh = 0.0
            st.session_state.so_luong = 1
            st.session_state.he_so_sd = 0.8
            st.success("Đã xóa nội dung biểu mẫu.")
    
    st.markdown("---")

    # Display the equipment list
    st.subheader("📋 Danh sách thiết bị đã nhập")
    if not st.session_state.devices:
        st.info("Chưa có thiết bị nào được thêm.")
    else:
        df_devices = pd.DataFrame(st.session_state.devices)
        st.dataframe(df_devices, use_container_width=True)
        
        col_list1, col_list2 = st.columns(2)
        with col_list1:
            if st.button("Xóa tất cả thiết bị", key="clear_all_devices"):
                st.session_state.devices = []
                st.success("Đã xóa tất cả thiết bị khỏi danh sách.")
                st.experimental_rerun()
        with col_list2:
            if st.button("Tạo PDF Bảng liệt kê", key="create_pdf_table"):
                try:
                    df_export = df_devices.rename(columns={
                        "Công suất định mức (W)": "Công suất định mức (W)",
                        "Tổng công suất (W)": "Tổng công suất (W)",
                        "Hệ số sử dụng": "Hệ số sử dụng",
                        "Tổng công suất tính toán (W)": "Tổng công suất tính toán (W)"
                    })
                    
                    # Create the PDF and store it in session state
                    pdf_bytes_table = create_equipment_list_pdf(df_export, don_vi, dia_chi, dia_diem, so_dien_thoai)
                    st.session_state['pdf_bytes_table'] = pdf_bytes_table
                    st.session_state['pdf_filename_table'] = f"Bang_liet_ke_{datetime.now().strftime('%Y%m%d')}.pdf"
                    st.success("Đã tạo PDF thành công! Vui lòng chọn tùy chọn xuất file bên dưới.")
                except Exception as e:
                    st.error(f"Đã xảy ra lỗi khi tạo PDF: {e}")

        # Display PDF options after PDF is created
        if 'pdf_bytes_table' in st.session_state and st.session_state['pdf_bytes_table']:
            st.markdown("---")
            st.subheader("Tùy chọn xuất PDF")
            col_pdf1_table, col_pdf2_table = st.columns(2)
            with col_pdf1_table:
                st.download_button(
                    label="Xuất PDF",
                    data=st.session_state['pdf_bytes_table'],
                    file_name=st.session_state['pdf_filename_table'],
                    mime="application/pdf",
                    key="download_table_pdf"
                )
            with col_pdf2_table:
                pdf_base64_table = base64.b64encode(st.session_state['pdf_bytes_table']).decode('utf-8')
                st.markdown(
                    f"""
                    <a href="data:application/pdf;base64,{pdf_base64_table}" target="_blank" style="text-decoration: none;">
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
                        ">Xem PDF</button>
                    </a>
                    """,
                    unsafe_allow_html=True
                )
            st.info("Nhấn 'Xem PDF' để mở file trong tab mới. Nếu không mở, vui lòng sử dụng nút 'Xuất PDF'.")
