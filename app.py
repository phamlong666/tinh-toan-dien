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
main_menu = st.sidebar.radio("", [
    "Trang chủ",
    "Tính toán điện",
    "Chuyển đổi đơn vị",
    "Công thức điện",
    "📋 BẢNG LIỆT KÊ CÔNG SUẤT CÁC THIẾT BỊ SỬ DỤNG ĐIỆN" # <--- Thêm dòng này
])

# Xử lý các lựa chọn từ menu chính
if main_menu == "Trang chủ":
    st.markdown("""
    <h3 style='text-align: center;'>👋 Chào mừng đến với ứng dụng Tính Toán Điện</h3>
    <p style='text-align: center;'>Ứng dụng giúp tính nhanh các thông số kỹ thuật điện và hỗ trợ lựa chọn thiết bị phù hợp.</p>
    """, unsafe_allow_html=True)

# ... (các khối lệnh elif khác cho "Tính toán điện", "Chuyển đổi đơn vị", "Công thức điện")

elif main_menu == "📋 BẢNG LIỆT KÊ CÔNG SUẤT CÁC THIẾT BỊ SỬ DỤNG ĐIỆN": # <--- Thêm khối lệnh này
    st.header("📋 Bảng liệt kê công suất các thiết bị")
    
    # ... (Toàn bộ code xử lý bảng liệt kê của bạn ở đây)
    # Bao gồm các phần:
    # st.subheader("Thông tin chung")
    # ...
    # if st.button("Thêm thiết bị", key="add_device"):
    # ...
    # if st.button("Tạo PDF Bảng Liệt Kê", key="create_pdf_btn"):
    # ...
    # ...

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
                            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                            Xem Phiếu
                        </button>
                    </a>
                    """,
                    unsafe_allow_html=True
                )
    
    # ... (Các chức năng tính toán điện khác)
    elif sub_menu_tinh_toan == "Tính công suất (P)":
        st.header("⚡ Tính công suất (P)")
        st.latex(r"P = \frac{I \cdot U \cdot \cos\varphi}{1000} \quad \text{(1 pha)}")
        st.latex(r"P = \frac{\sqrt{3} \cdot I \cdot U \cdot \cos\varphi}{1000} \quad \text{(3 pha)}")
        st.markdown("""
        **Giải thích các thành phần:**
        - \( P \): Công suất tác dụng (kW)
        - \( I \): Dòng điện (A)
        - \( U \): Điện áp (V)
        - \( \cos\varphi \): Hệ số công suất
        
        **Mục đích:** Tính toán công suất tiêu thụ thực tế của tải điện.
        """, unsafe_allow_html=True)
        
        st.subheader("Thông tin Người tính toán")
        calculator_name_p = st.text_input("Họ và tên:", value="Hà Thị Lê", key="calc_name_p")
        calculator_title_p = st.text_input("Chức danh:", value="Tổ trưởng tổ KDDV", key="calc_title_p")
        calculator_phone_p = st.text_input("Số điện thoại:", value="0978578777", key="calc_phone_p")

        st.subheader("Thông tin Khách hàng")
        customer_name_p = st.text_input("Tên khách hàng:", value="Phạm Hồng Long", key="cust_name_p")
        customer_address_p = st.text_input("Địa chỉ:", value="xã Định Hóa, tỉnh Thái Nguyên", key="cust_address_p")
        customer_phone_p = st.text_input("Số điện thoại khách hàng:", value="0968552888", key="cust_phone_p")

        col1, col2 = st.columns(2)
        with col1:
            pha_p = st.radio("Loại điện:", ["1 pha", "3 pha"], key="pha_p")
            I_p = st.number_input("Dòng điện I (A):", min_value=0.0, key="I_p")
        with col2:
            U_p = st.number_input("Điện áp U (V):", min_value=0.0, key="U_p")
            cos_phi_p = st.slider("Hệ số cosφ:", 0.1, 1.0, 0.8, key="cos_phi_p")

        if st.button("Tính công suất", key="btn_calc_p"):
            P_result = 0.0
            if pha_p == "1 pha":
                P_result = I_p * U_p * cos_phi_p / 1000
            elif pha_p == "3 pha":
                P_result = math.sqrt(3) * I_p * U_p * cos_phi_p / 1000
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
            formula_latex = r"P = \frac{I \cdot U \cdot \cos\varphi}{1000} \quad \text{hoặc} \quad P = \frac{\sqrt{3} \cdot I \cdot U \cdot \cos\varphi}{1000}"
            formula_explanation = "Công thức tính công suất dựa trên dòng điện, điện áp và hệ số công suất cho hệ thống 1 pha hoặc 3 pha."
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
                            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                            Xem Phiếu
                        </button>
                    </a>
                    """,
                    unsafe_allow_html=True
                )
    
    # ... (Các chức năng tính toán điện khác)
    elif sub_menu_tinh_toan == "Tính công suất biểu kiến (S)":
        st.header("⚡ Tính công suất biểu kiến (S)")
        st.latex(r"S = I \cdot U \quad \text{(1 pha)}")
        st.latex(r"S = \sqrt{3} \cdot I \cdot U \quad \text{(3 pha)}")
        st.markdown("""
        **Giải thích các thành phần:**
        - \( S \): Công suất biểu kiến (kVA)
        - \( I \): Dòng điện (A)
        - \( U \): Điện áp (V)
        
        **Mục đích:** Tính toán công suất biểu kiến của tải điện, bao gồm cả công suất tác dụng và công suất phản kháng.
        """, unsafe_allow_html=True)

        st.subheader("Thông tin Người tính toán")
        calculator_name_s = st.text_input("Họ và tên:", value="Hà Thị Lê", key="calc_name_s")
        calculator_title_s = st.text_input("Chức danh:", value="Tổ trưởng tổ KDDV", key="calc_title_s")
        calculator_phone_s = st.text_input("Số điện thoại:", value="0978578777", key="calc_phone_s")

        st.subheader("Thông tin Khách hàng")
        customer_name_s = st.text_input("Tên khách hàng:", value="Phạm Hồng Long", key="cust_name_s")
        customer_address_s = st.text_input("Địa chỉ:", value="xã Định Hóa, tỉnh Thái Nguyên", key="cust_address_s")
        customer_phone_s = st.text_input("Số điện thoại khách hàng:", value="0968552888", key="cust_phone_s")
        
        col1, col2 = st.columns(2)
        with col1:
            pha_s = st.radio("Loại điện:", ["1 pha", "3 pha"], key="pha_s")
            I_s = st.number_input("Dòng điện I (A):", min_value=0.0, key="I_s")
        with col2:
            U_s = st.number_input("Điện áp U (V):", min_value=0.0, key="U_s")

        if st.button("Tính công suất biểu kiến", key="btn_calc_s"):
            S_result = 0.0
            if pha_s == "1 pha":
                S_result = I_s * U_s / 1000
            elif pha_s == "3 pha":
                S_result = math.sqrt(3) * I_s * U_s / 1000
            st.success(f"Công suất biểu kiến S ≈ {S_result:.2f} kVA")
            
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
                "Dòng điện I": f"{I_s} A",
                "Điện áp U": f"{U_s} V"
            }
            output_results = {
                "Công suất biểu kiến S": f"{S_result:.2f} kVA"
            }
            formula_latex = r"S = I \cdot U \quad \text{hoặc} \quad S = \sqrt{3} \cdot I \cdot U"
            formula_explanation = "Công thức tính công suất biểu kiến dựa trên dòng điện và điện áp cho hệ thống 1 pha hoặc 3 pha."
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
                            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                            Xem Phiếu
                        </button>
                    </a>
                    """,
                    unsafe_allow_html=True
                )
    
    # ... (Các chức năng tính toán điện khác)
    elif sub_menu_tinh_toan == "Tính công suất phản kháng (Q)":
        st.header("⚡ Tính công suất phản kháng (Q)")
        st.latex(r"Q = \frac{P \cdot \tan\varphi}{1000} \quad \text{(1 pha và 3 pha)}")
        st.markdown("""
        **Giải thích các thành phần:**
        - \( Q \): Công suất phản kháng (kVAR)
        - \( P \): Công suất tác dụng (kW)
        - \( \tan\varphi \): Tang của góc lệch pha
        
        **Mục đích:** Tính toán công suất phản kháng để lựa chọn thiết bị bù công suất phản kháng phù hợp, giúp cải thiện hệ số công suất.
        """, unsafe_allow_html=True)

        st.subheader("Thông tin Người tính toán")
        calculator_name_q = st.text_input("Họ và tên:", value="Hà Thị Lê", key="calc_name_q")
        calculator_title_q = st.text_input("Chức danh:", value="Tổ trưởng tổ KDDV", key="calc_title_q")
        calculator_phone_q = st.text_input("Số điện thoại:", value="0978578777", key="calc_phone_q")

        st.subheader("Thông tin Khách hàng")
        customer_name_q = st.text_input("Tên khách hàng:", value="Phạm Hồng Long", key="cust_name_q")
        customer_address_q = st.text_input("Địa chỉ:", value="xã Định Hóa, tỉnh Thái Nguyên", key="cust_address_q")
        customer_phone_q = st.text_input("Số điện thoại khách hàng:", value="0968552888", key="cust_phone_q")
        
        col1, col2 = st.columns(2)
        with col1:
            P_q = st.number_input("Công suất P (kW):", min_value=0.0, key="P_q")
        with col2:
            cos_phi_q = st.slider("Hệ số cosφ:", 0.1, 1.0, 0.8, key="cos_phi_q")
        
        if st.button("Tính công suất phản kháng", key="btn_calc_q"):
            Q_result = 0.0
            if cos_phi_q > 0 and cos_phi_q <= 1:
                sin_phi = math.sqrt(1 - cos_phi_q**2)
                tan_phi = sin_phi / cos_phi_q if cos_phi_q != 0 else 0
                Q_result = P_q * tan_phi
            st.success(f"Công suất phản kháng Q ≈ {Q_result:.2f} kVAR")
            
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
                "Công suất P": f"{P_q} kW",
                "Hệ số cosφ": cos_phi_q
            }
            output_results = {
                "Công suất phản kháng Q": f"{Q_result:.2f} kVAR"
            }
            formula_latex = r"Q = P \cdot \tan\varphi"
            formula_explanation = "Công thức tính công suất phản kháng dựa trên công suất tác dụng và hệ số công suất."
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
                            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                            Xem Phiếu
                        </button>
                    </a>
                    """,
                    unsafe_allow_html=True
                )
    
    # ... (Các chức năng tính toán điện khác)
    elif sub_menu_tinh_toan == "Tính sụt áp (ΔU)":
        st.header("⚡ Tính sụt áp (ΔU)")
        st.markdown(r"Công thức tính sụt áp cho đường dây tải điện:")
        st.latex(r"\Delta U = \frac{I \cdot (R \cdot \cos\varphi + X_L \cdot \sin\varphi)}{1000} \quad \text{(1 pha)}")
        st.latex(r"\Delta U = \frac{\sqrt{3} \cdot I \cdot (R \cdot \cos\varphi + X_L \cdot \sin\varphi)}{1000} \quad \text{(3 pha)}")
        st.markdown("""
        **Giải thích các thành phần:**
        - \( \Delta U \): Sụt áp (V)
        - \( I \): Dòng điện (A)
        - \( R \): Điện trở đường dây (Ohm)
        - \( X_L \): Điện kháng đường dây (Ohm)
        - \( \cos\varphi \): Hệ số công suất
        - \( \sin\varphi \): Sin của góc lệch pha
        
        **Mục đích:** Đánh giá tổn thất điện áp trên đường dây, đảm bảo điện áp tại điểm cuối đủ cho thiết bị hoạt động.
        """, unsafe_allow_html=True)
        
        st.subheader("Thông tin Người tính toán")
        calculator_name_du = st.text_input("Họ và tên:", value="Hà Thị Lê", key="calc_name_du")
        calculator_title_du = st.text_input("Chức danh:", value="Tổ trưởng tổ KDDV", key="calc_title_du")
        calculator_phone_du = st.text_input("Số điện thoại:", value="0978578777", key="calc_phone_du")

        st.subheader("Thông tin Khách hàng")
        customer_name_du = st.text_input("Tên khách hàng:", value="Phạm Hồng Long", key="cust_name_du")
        customer_address_du = st.text_input("Địa chỉ:", value="xã Định Hóa, tỉnh Thái Nguyên", key="cust_address_du")
        customer_phone_du = st.text_input("Số điện thoại khách hàng:", value="0968552888", key="cust_phone_du")
        
        col1, col2 = st.columns(2)
        with col1:
            pha_du = st.radio("Loại điện:", ["1 pha", "3 pha"], key="pha_du")
            I_du = st.number_input("Dòng điện I (A):", min_value=0.0, key="I_du")
            R_du = st.number_input("Điện trở đường dây R (Ω):", min_value=0.0, key="R_du")
        with col2:
            U_du = st.number_input("Điện áp ban đầu U (V):", min_value=0.0, key="U_du")
            cos_phi_du = st.slider("Hệ số cosφ:", 0.1, 1.0, 0.8, key="cos_phi_du")
            X_du = st.number_input("Điện kháng đường dây X_L (Ω):", min_value=0.0, key="X_du")

        if st.button("Tính sụt áp", key="btn_calc_du"):
            delta_U = 0.0
            if cos_phi_du > 0 and cos_phi_du <= 1:
                sin_phi = math.sqrt(1 - cos_phi_du**2)
                if pha_du == "1 pha":
                    delta_U = I_du * (R_du * cos_phi_du + X_du * sin_phi)
                elif pha_du == "3 pha":
                    delta_U = math.sqrt(3) * I_du * (R_du * cos_phi_du + X_du * sin_phi)
            
            U_end = U_du - delta_U
            
            st.success(f"Sụt áp ΔU ≈ {delta_U:.2f} V")
            st.info(f"Điện áp tại cuối đường dây ≈ {U_end:.2f} V")
            
            calculator_info = {
                'name': calculator_name_du,
                'title': calculator_title_du,
                'phone': calculator_phone_du
            }
            customer_info = {
                'name': customer_name_du,
                'address': customer_address_du,
                'phone': customer_phone_du
            }
            input_params = {
                "Loại điện": pha_du,
                "Dòng điện I": f"{I_du} A",
                "Điện áp ban đầu U": f"{U_du} V",
                "Điện trở R": f"{R_du} Ω",
                "Điện kháng X_L": f"{X_du} Ω",
                "Hệ số cosφ": cos_phi_du
            }
            output_results = {
                "Sụt áp ΔU": f"{delta_U:.2f} V",
                "Điện áp cuối đường dây": f"{U_end:.2f} V"
            }
            formula_latex = r"\Delta U = I \cdot (R \cos\varphi + X_L \sin\varphi) \quad \text{hoặc} \quad \Delta U = \sqrt{3} \cdot I \cdot (R \cos\varphi + X_L \sin\varphi)"
            formula_explanation = "Công thức tính sụt áp dựa trên dòng điện, điện trở, điện kháng, và hệ số công suất của hệ thống 1 pha hoặc 3 pha."
            pdf_bytes = create_pdf("SỤT ÁP", formula_latex, formula_explanation, input_params, output_results, calculator_info, customer_info)
            st.session_state['pdf_bytes_du'] = pdf_bytes
            st.session_state['pdf_filename_du'] = f"Phieu_tinh_sut_ap_{datetime.now().strftime('%Y%m%d')}.pdf"

        if 'pdf_bytes_du' in st.session_state and st.session_state['pdf_bytes_du']:
            st.markdown("---")
            st.subheader("Tùy chọn xuất phiếu sụt áp")
            col_pdf1_du, col_pdf2_du = st.columns(2)
            with col_pdf1_du:
                st.download_button(
                    label="Xuất PDF",
                    data=st.session_state['pdf_bytes_du'],
                    file_name=st.session_state['pdf_filename_du'],
                    mime="application/pdf",
                    key="download_du_pdf"
                )
            with col_pdf2_du:
                pdf_base64_du = base64.b64encode(st.session_state['pdf_bytes_du']).decode('utf-8')
                st.markdown(
                    f"""
                    <a href="data:application/pdf;base64,{pdf_base64_du}" target="_blank" style="text-decoration: none;">
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
                            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                            Xem Phiếu
                        </button>
                    </a>
                    """,
                    unsafe_allow_html=True
                )
    
    # ... (Các chức năng tính toán điện khác)
    elif sub_menu_tinh_toan == "Chọn tiết diện dây dẫn":
        st.header("⚡ Chọn tiết diện dây dẫn")
        st.markdown("""
        Ứng dụng giúp bạn chọn tiết diện dây dẫn phù hợp dựa trên dòng điện I thực tế và loại vật liệu (đồng hoặc nhôm).
        **Lưu ý:** Dữ liệu tra cứu được lấy từ bảng tra tiêu chuẩn của Cadivi.
        """, unsafe_allow_html=True)
        
        st.subheader("Thông tin Người tính toán")
        calculator_name_td = st.text_input("Họ và tên:", value="Hà Thị Lê", key="calc_name_td")
        calculator_title_td = st.text_input("Chức danh:", value="Tổ trưởng tổ KDDV", key="calc_title_td")
        calculator_phone_td = st.text_input("Số điện thoại:", value="0978578777", key="calc_phone_td")

        st.subheader("Thông tin Khách hàng")
        customer_name_td = st.text_input("Tên khách hàng:", value="Phạm Hồng Long", key="cust_name_td")
        customer_address_td = st.text_input("Địa chỉ:", value="xã Định Hóa, tỉnh Thái Nguyên", key="cust_address_td")
        customer_phone_td = st.text_input("Số điện thoại khách hàng:", value="0968552888", key="cust_phone_td")
        
        col1, col2 = st.columns(2)
        with col1:
            I_td = st.number_input("Dòng điện I thực tế (A):", min_value=0.0, key="I_td")
        with col2:
            material = st.radio("Vật liệu dây:", ["Đồng", "Nhôm"], key="material_td")

        installation_method = st.radio(
            "Phương pháp lắp đặt:",
            ["Đi trong không khí", "Đi trong ống"],
            help="Chọn phương pháp lắp đặt để có kết quả chính xác nhất dựa trên bảng tra."
        )

        if st.button("Chọn tiết diện", key="btn_calc_td"):
            if I_td <= 0:
                st.warning("⚠️ Vui lòng nhập dòng điện I > 0 để tính toán.")
            else:
                data_source = None
                if material == "Đồng":
                    data_source = copper_cable_data
                elif material == "Nhôm":
                    data_source = aluminum_cable_data
                
                if not data_source:
                    st.error("❌ Không thể tra cứu dữ liệu. Vui lòng kiểm tra lại file dữ liệu hoặc lỗi đã được báo cáo phía trên.")
                else:
                    capacities = data_source['in_air'] if installation_method == "Đi trong không khí" else data_source['in_conduit']
                    
                    selected_size = "Không tìm thấy"
                    safe_capacity = 0
                    
                    # Sort capacities by cross-section in ascending order
                    sorted_capacities = sorted(capacities.items())
                    
                    for size, capacity in sorted_capacities:
                        if I_td <= capacity:
                            selected_size = f"{size} mm²"
                            safe_capacity = capacity
                            break

                    if selected_size == "Không tìm thấy":
                        # If current is higher than any value in the table, recommend the highest
                        highest_size, highest_capacity = sorted_capacities[-1]
                        st.warning(
                            f"⚠️ Dòng điện I = {I_td:.2f} A vượt quá khả năng chịu tải của các loại dây có sẵn trong bảng tra ({highest_capacity} A). "
                            f"Vui lòng cân nhắc chọn dây có tiết diện lớn hơn {highest_size} mm² hoặc sử dụng nhiều dây song song."
                        )
                        selected_size = "Không tìm thấy trong bảng tra"
                    else:
                        st.success(
                            f"Tiết diện dây dẫn phù hợp với dòng điện {I_td:.2f} A là: **{selected_size}**"
                            f" (Khả năng chịu tải: {safe_capacity:.2f} A)"
                        )

                    calculator_info = {
                        'name': calculator_name_td,
                        'title': calculator_title_td,
                        'phone': calculator_phone_td
                    }
                    customer_info = {
                        'name': customer_name_td,
                        'address': customer_address_td,
                        'phone': customer_phone_td
                    }
                    input_params = {
                        "Dòng điện I thực tế": f"{I_td:.2f} A",
                        "Vật liệu dây": material,
                        "Phương pháp lắp đặt": installation_method
                    }
                    output_results = {
                        "Tiết diện dây dẫn phù hợp": selected_size,
                        "Khả năng chịu tải của dây": f"{safe_capacity} A" if selected_size != "Không tìm thấy trong bảng tra" else "N/A"
                    }
                    formula_latex = "" # This calculation is based on a lookup table, not a formula
                    formula_explanation = "Kết quả được tra cứu từ bảng tiêu chuẩn của Cadivi dựa trên dòng điện thực tế và phương pháp lắp đặt."
                    pdf_bytes = create_pdf("CHỌN TIẾT DIỆN DÂY DẪN", formula_latex, formula_explanation, input_params, output_results, calculator_info, customer_info)
                    st.session_state['pdf_bytes_td'] = pdf_bytes
                    st.session_state['pdf_filename_td'] = f"Phieu_chon_tiet_dien_{datetime.now().strftime('%Y%m%d')}.pdf"

        if 'pdf_bytes_td' in st.session_state and st.session_state['pdf_bytes_td']:
            st.markdown("---")
            st.subheader("Tùy chọn xuất phiếu chọn tiết diện")
            col_pdf1_td, col_pdf2_td = st.columns(2)
            with col_pdf1_td:
                st.download_button(
                    label="Xuất PDF",
                    data=st.session_state['pdf_bytes_td'],
                    file_name=st.session_state['pdf_filename_td'],
                    mime="application/pdf",
                    key="download_td_pdf"
                )
            with col_pdf2_td:
                pdf_base64_td = base64.b64encode(st.session_state['pdf_bytes_td']).decode('utf-8')
                st.markdown(
                    f"""
                    <a href="data:application/pdf;base64,{pdf_base64_td}" target="_blank" style="text-decoration: none;">
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
                            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                            Xem Phiếu
                        </button>
                    </a>
                    """,
                    unsafe_allow_html=True
                )
    
    # ... (Các chức năng tính toán điện khác)
    elif sub_menu_tinh_toan == "Chiều dài dây tối đa (ΔU%)":
        st.header("⚡ Tính chiều dài dây tối đa")
        st.markdown(r"Công thức tính chiều dài tối đa của dây dẫn dựa trên phần trăm sụt áp cho phép:")
        st.latex(r"L_{max} = \frac{\Delta U_{max} \cdot 1000}{I \cdot (R_0 \cdot \cos\varphi + X_{L0} \cdot \sin\varphi)} \quad \text{(1 pha)}")
        st.latex(r"L_{max} = \frac{\Delta U_{max} \cdot 1000}{\sqrt{3} \cdot I \cdot (R_0 \cdot \cos\varphi + X_{L0} \cdot \sin\varphi)} \quad \text{(3 pha)}")
        st.markdown("""
        **Giải thích các thành phần:**
        - \( L_{max} \): Chiều dài tối đa (m)
        - \( \Delta U_{max} \): Sụt áp tối đa cho phép (V)
        - \( I \): Dòng điện (A)
        - \( R_0 \): Điện trở suất (Ohm/km)
        - \( X_{L0} \): Điện kháng suất (Ohm/km)
        
        **Mục đích:** Xác định chiều dài tối đa của đường dây để đảm bảo sụt áp không vượt quá mức cho phép, thường là dưới 5% điện áp định mức.
        """, unsafe_allow_html=True)

        st.subheader("Thông tin Người tính toán")
        calculator_name_cd = st.text_input("Họ và tên:", value="Hà Thị Lê", key="calc_name_cd")
        calculator_title_cd = st.text_input("Chức danh:", value="Tổ trưởng tổ KDDV", key="calc_title_cd")
        calculator_phone_cd = st.text_input("Số điện thoại:", value="0978578777", key="calc_phone_cd")

        st.subheader("Thông tin Khách hàng")
        customer_name_cd = st.text_input("Tên khách hàng:", value="Phạm Hồng Long", key="cust_name_cd")
        customer_address_cd = st.text_input("Địa chỉ:", value="xã Định Hóa, tỉnh Thái Nguyên", key="cust_address_cd")
        customer_phone_cd = st.text_input("Số điện thoại khách hàng:", value="0968552888", key="cust_phone_cd")
        
        col1, col2 = st.columns(2)
        with col1:
            pha_cd = st.radio("Loại điện:", ["1 pha", "3 pha"], key="pha_cd")
            I_cd = st.number_input("Dòng điện I (A):", min_value=0.0, key="I_cd")
            R0_cd = st.number_input("Điện trở suất R₀ (Ω/km):", min_value=0.0, key="R0_cd")
            U_rate_cd = st.number_input("Điện áp định mức Uđm (V):", min_value=0.0, key="U_rate_cd")
        with col2:
            cos_phi_cd = st.slider("Hệ số cosφ:", 0.1, 1.0, 0.8, key="cos_phi_cd")
            X0_cd = st.number_input("Điện kháng suất X₀ (Ω/km):", min_value=0.0, key="X0_cd")
            delta_U_percent_cd = st.slider("Phần trăm sụt áp cho phép ΔU%:", 0.0, 10.0, 5.0, help="Sụt áp tối đa cho phép, thường là 5%.", key="delta_U_percent_cd")
        
        if st.button("Tính chiều dài tối đa", key="btn_calc_cd"):
            L_max = 0.0
            if U_rate_cd > 0 and I_cd > 0:
                delta_U_max = (delta_U_percent_cd / 100) * U_rate_cd
                sin_phi = math.sqrt(1 - cos_phi_cd**2)
                
                denominator = (R0_cd * cos_phi_cd + X0_cd * sin_phi)
                if denominator != 0:
                    if pha_cd == "1 pha":
                        L_max = (delta_U_max * 1000) / (I_cd * denominator)
                    elif pha_cd == "3 pha":
                        L_max = (delta_U_max * 1000) / (math.sqrt(3) * I_cd * denominator)
            
            st.success(f"Chiều dài dây tối đa Lₘₐₓ ≈ {L_max:.2f} m")
            
            calculator_info = {
                'name': calculator_name_cd,
                'title': calculator_title_cd,
                'phone': calculator_phone_cd
            }
            customer_info = {
                'name': customer_name_cd,
                'address': customer_address_cd,
                'phone': customer_phone_cd
            }
            input_params = {
                "Loại điện": pha_cd,
                "Dòng điện I": f"{I_cd} A",
                "Điện áp định mức Uđm": f"{U_rate_cd} V",
                "Điện trở suất R₀": f"{R0_cd} Ω/km",
                "Điện kháng suất X₀": f"{X0_cd} Ω/km",
                "Hệ số cosφ": cos_phi_cd,
                "Phần trăm sụt áp cho phép ΔU%": f"{delta_U_percent_cd} %"
            }
            output_results = {
                "Sụt áp tối đa cho phép ΔUₘₐₓ": f"{delta_U_max:.2f} V",
                "Chiều dài dây tối đa Lₘₐₓ": f"{L_max:.2f} m"
            }
            formula_latex = r"L_{max} = \frac{\Delta U_{max}}{I (R_0 \cos\varphi + X_{L0} \sin\varphi)} \quad \text{hoặc} \quad L_{max} = \frac{\Delta U_{max}}{\sqrt{3} I (R_0 \cos\varphi + X_{L0} \sin\varphi)}"
            formula_explanation = "Công thức tính chiều dài tối đa của đường dây để đảm bảo sụt áp không vượt quá mức cho phép, thường là dưới 5% điện áp định mức."
            pdf_bytes = create_pdf("CHIỀU DÀI DÂY TỐI ĐA", formula_latex, formula_explanation, input_params, output_results, calculator_info, customer_info)
            st.session_state['pdf_bytes_cd'] = pdf_bytes
            st.session_state['pdf_filename_cd'] = f"Phieu_chieu_dai_day_toi_da_{datetime.now().strftime('%Y%m%d')}.pdf"

        if 'pdf_bytes_cd' in st.session_state and st.session_state['pdf_bytes_cd']:
            st.markdown("---")
            st.subheader("Tùy chọn xuất phiếu chiều dài tối đa")
            col_pdf1_cd, col_pdf2_cd = st.columns(2)
            with col_pdf1_cd:
                st.download_button(
                    label="Xuất PDF",
                    data=st.session_state['pdf_bytes_cd'],
                    file_name=st.session_state['pdf_filename_cd'],
                    mime="application/pdf",
                    key="download_cd_pdf"
                )
            with col_pdf2_cd:
                pdf_base64_cd = base64.b64encode(st.session_state['pdf_bytes_cd']).decode('utf-8')
                st.markdown(
                    f"""
                    <a href="data:application/pdf;base64,{pdf_base64_cd}" target="_blank" style="text-decoration: none;">
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
                            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                            Xem Phiếu
                        </button>
                    </a>
                    """,
                    unsafe_allow_html=True
                )
    
    # ... (Các chức năng tính toán điện khác)
    elif sub_menu_tinh_toan == "Tính điện trở – kháng – trở kháng":
        st.header("⚡ Tính điện trở – kháng – trở kháng")
        st.markdown(r"Công thức:")
        st.latex(r"Z = \sqrt{R^2 + (X_L - X_C)^2}")
        st.latex(r"R_{total} = R_{dây} + R_{phụ tải}")
        st.markdown("""
        **Giải thích các thành phần:**
        - \( Z \): Trở kháng (Ohm)
        - \( R \): Điện trở (Ohm)
        - \( X_L \): Điện kháng cảm (Ohm)
        - \( X_C \): Điện kháng dung (Ohm)
        
        **Mục đích:** Phân tích tổng trở của mạch để hiểu rõ hơn về ảnh hưởng của các thành phần điện trở, điện cảm, điện dung.
        """, unsafe_allow_html=True)

        st.subheader("Thông tin Người tính toán")
        calculator_name_z = st.text_input("Họ và tên:", value="Hà Thị Lê", key="calc_name_z")
        calculator_title_z = st.text_input("Chức danh:", value="Tổ trưởng tổ KDDV", key="calc_title_z")
        calculator_phone_z = st.text_input("Số điện thoại:", value="0978578777", key="calc_phone_z")

        st.subheader("Thông tin Khách hàng")
        customer_name_z = st.text_input("Tên khách hàng:", value="Phạm Hồng Long", key="cust_name_z")
        customer_address_z = st.text_input("Địa chỉ:", value="xã Định Hóa, tỉnh Thái Nguyên", key="cust_address_z")
        customer_phone_z = st.text_input("Số điện thoại khách hàng:", value="0968552888", key="cust_phone_z")
        
        col1, col2 = st.columns(2)
        with col1:
            R_z = st.number_input("Điện trở R (Ω):", min_value=0.0, key="R_z")
            XL_z = st.number_input("Điện kháng cảm X_L (Ω):", min_value=0.0, key="XL_z")
        with col2:
            XC_z = st.number_input("Điện kháng dung X_C (Ω):", min_value=0.0, key="XC_z")

        if st.button("Tính trở kháng", key="btn_calc_z"):
            Z_result = math.sqrt(R_z**2 + (XL_z - XC_z)**2)
            st.success(f"Trở kháng Z ≈ {Z_result:.2f} Ω")
            
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
                "Điện kháng cảm X_L": f"{XL_z} Ω",
                "Điện kháng dung X_C": f"{XC_z} Ω"
            }
            output_results = {
                "Trở kháng Z": f"{Z_result:.2f} Ω"
            }
            formula_latex = r"Z = \sqrt{R^2 + (X_L - X_C)^2}"
            formula_explanation = "Công thức tính trở kháng của một mạch RLC nối tiếp."
            pdf_bytes = create_pdf("ĐIỆN TRỞ – KHÁNG – TRỞ KHÁNG", formula_latex, formula_explanation, input_params, output_results, calculator_info, customer_info)
            st.session_state['pdf_bytes_z'] = pdf_bytes
            st.session_state['pdf_filename_z'] = f"Phieu_tinh_tro_khang_{datetime.now().strftime('%Y%m%d')}.pdf"

        if 'pdf_bytes_z' in st.session_state and st.session_state['pdf_bytes_z']:
            st.markdown("---")
            st.subheader("Tùy chọn xuất phiếu trở kháng")
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
                            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                            Xem Phiếu
                        </button>
                    </a>
                    """,
                    unsafe_allow_html=True
                )
    
    # ... (Các chức năng tính toán điện khác)
    elif sub_menu_tinh_toan == "Tính tổn thất công suất trên dây":
        st.header("⚡ Tính tổn thất công suất trên dây")
        st.markdown(r"Công thức tính tổn thất công suất trên đường dây:")
        st.latex(r"\Delta P = I^2 \cdot R")
        st.markdown("""
        **Giải thích các thành phần:**
        - \( \Delta P \): Tổn thất công suất (W)
        - \( I \): Dòng điện (A)
        - \( R \): Điện trở đường dây (Ohm)
        
        **Mục đích:** Đánh giá năng lượng bị tiêu hao trên đường dây, giúp lựa chọn dây dẫn có điện trở thấp để giảm tổn thất.
        """, unsafe_allow_html=True)
        
        st.subheader("Thông tin Người tính toán")
        calculator_name_dp = st.text_input("Họ và tên:", value="Hà Thị Lê", key="calc_name_dp")
        calculator_title_dp = st.text_input("Chức danh:", value="Tổ trưởng tổ KDDV", key="calc_title_dp")
        calculator_phone_dp = st.text_input("Số điện thoại:", value="0978578777", key="calc_phone_dp")

        st.subheader("Thông tin Khách hàng")
        customer_name_dp = st.text_input("Tên khách hàng:", value="Phạm Hồng Long", key="cust_name_dp")
        customer_address_dp = st.text_input("Địa chỉ:", value="xã Định Hóa, tỉnh Thái Nguyên", key="cust_address_dp")
        customer_phone_dp = st.text_input("Số điện thoại khách hàng:", value="0968552888", key="cust_phone_dp")
        
        col1, col2 = st.columns(2)
        with col1:
            I_dp = st.number_input("Dòng điện I (A):", min_value=0.0, key="I_dp")
        with col2:
            R_dp = st.number_input("Điện trở đường dây R (Ω):", min_value=0.0, key="R_dp")

        if st.button("Tính tổn thất công suất", key="btn_calc_dp"):
            delta_P = I_dp**2 * R_dp
            st.success(f"Tổn thất công suất ΔP ≈ {delta_P:.2f} W")
            
            calculator_info = {
                'name': calculator_name_dp,
                'title': calculator_title_dp,
                'phone': calculator_phone_dp
            }
            customer_info = {
                'name': customer_name_dp,
                'address': customer_address_dp,
                'phone': customer_phone_dp
            }
            input_params = {
                "Dòng điện I": f"{I_dp} A",
                "Điện trở đường dây R": f"{R_dp} Ω"
            }
            output_results = {
                "Tổn thất công suất ΔP": f"{delta_P:.2f} W"
            }
            formula_latex = r"\Delta P = I^2 \cdot R"
            formula_explanation = "Công thức tính tổn thất công suất do hiệu ứng Joule trên đường dây."
            pdf_bytes = create_pdf("TỔN THẤT CÔNG SUẤT", formula_latex, formula_explanation, input_params, output_results, calculator_info, customer_info)
            st.session_state['pdf_bytes_dp'] = pdf_bytes
            st.session_state['pdf_filename_dp'] = f"Phieu_tinh_ton_that_cong_suat_{datetime.now().strftime('%Y%m%d')}.pdf"

        if 'pdf_bytes_dp' in st.session_state and st.session_state['pdf_bytes_dp']:
            st.markdown("---")
            st.subheader("Tùy chọn xuất phiếu tổn thất công suất")
            col_pdf1_dp, col_pdf2_dp = st.columns(2)
            with col_pdf1_dp:
                st.download_button(
                    label="Xuất PDF",
                    data=st.session_state['pdf_bytes_dp'],
                    file_name=st.session_state['pdf_filename_dp'],
                    mime="application/pdf",
                    key="download_dp_pdf"
                )
            with col_pdf2_dp:
                pdf_base64_dp = base64.b64encode(st.session_state['pdf_bytes_dp']).decode('utf-8')
                st.markdown(
                    f"""
                    <a href="data:application/pdf;base64,{pdf_base64_dp}" target="_blank" style="text-decoration: none;">
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
                            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                            Xem Phiếu
                        </button>
                    </a>
                    """,
                    unsafe_allow_html=True
                )
    
    # ... (Các chức năng tính toán điện khác)
    elif sub_menu_tinh_toan == "Tính công suất cosφ":
        st.header("⚡ Tính hệ số công suất cosφ")
        st.markdown(r"Công thức tính cosφ từ các thông số đã biết:")
        st.latex(r"\cos\varphi = \frac{P}{S}")
        st.latex(r"\tan\varphi = \frac{Q}{P}")
        st.latex(r"S^2 = P^2 + Q^2")
        st.markdown("""
        **Giải thích các thành phần:**
        - \( \cos\varphi \): Hệ số công suất
        - \( P \): Công suất tác dụng (kW)
        - \( Q \): Công suất phản kháng (kVAR)
        - \( S \): Công suất biểu kiến (kVA)
        
        **Mục đích:** Tính toán hệ số công suất của tải điện, giúp đánh giá hiệu quả sử dụng năng lượng điện.
        """, unsafe_allow_html=True)
        
        st.subheader("Thông tin Người tính toán")
        calculator_name_cosphi = st.text_input("Họ và tên:", value="Hà Thị Lê", key="calc_name_cosphi")
        calculator_title_cosphi = st.text_input("Chức danh:", value="Tổ trưởng tổ KDDV", key="calc_title_cosphi")
        calculator_phone_cosphi = st.text_input("Số điện thoại:", value="0978578777", key="calc_phone_cosphi")

        st.subheader("Thông tin Khách hàng")
        customer_name_cosphi = st.text_input("Tên khách hàng:", value="Phạm Hồng Long", key="cust_name_cosphi")
        customer_address_cosphi = st.text_input("Địa chỉ:", value="xã Định Hóa, tỉnh Thái Nguyên", key="cust_address_cosphi")
        customer_phone_cosphi = st.text_input("Số điện thoại khách hàng:", value="0968552888", key="cust_phone_cosphi")
        
        col1, col2 = st.columns(2)
        with col1:
            P_cosphi = st.number_input("Công suất tác dụng P (kW):", min_value=0.0, key="P_cosphi")
        with col2:
            S_cosphi = st.number_input("Công suất biểu kiến S (kVA):", min_value=0.0, key="S_cosphi")
            
        if st.button("Tính cosφ", key="btn_calc_cosphi"):
            cosphi_result = 0.0
            if S_cosphi > 0:
                cosphi_result = P_cosphi / S_cosphi
            
            if cosphi_result > 1:
                st.warning("⚠️ Kết quả cosφ không hợp lệ. Vui lòng kiểm tra lại giá trị P và S.")
            else:
                st.success(f"Hệ số công suất cosφ ≈ {cosphi_result:.2f}")
            
            calculator_info = {
                'name': calculator_name_cosphi,
                'title': calculator_title_cosphi,
                'phone': calculator_phone_cosphi
            }
            customer_info = {
                'name': customer_name_cosphi,
                'address': customer_address_cosphi,
                'phone': customer_phone_cosphi
            }
            input_params = {
                "Công suất tác dụng P": f"{P_cosphi} kW",
                "Công suất biểu kiến S": f"{S_cosphi} kVA"
            }
            output_results = {
                "Hệ số công suất cosφ": f"{cosphi_result:.2f}"
            }
            formula_latex = r"\cos\varphi = \frac{P}{S}"
            formula_explanation = "Công thức tính hệ số công suất dựa trên tỷ lệ giữa công suất tác dụng và công suất biểu kiến."
            pdf_bytes = create_pdf("HỆ SỐ CÔNG SUẤT COSφ", formula_latex, formula_explanation, input_params, output_results, calculator_info, customer_info)
            st.session_state['pdf_bytes_cosphi'] = pdf_bytes
            st.session_state['pdf_filename_cosphi'] = f"Phieu_tinh_cosphi_{datetime.now().strftime('%Y%m%d')}.pdf"

        if 'pdf_bytes_cosphi' in st.session_state and st.session_state['pdf_bytes_cosphi']:
            st.markdown("---")
            st.subheader("Tùy chọn xuất phiếu cosφ")
            col_pdf1_cosphi, col_pdf2_cosphi = st.columns(2)
            with col_pdf1_cosphi:
                st.download_button(
                    label="Xuất PDF",
                    data=st.session_state['pdf_bytes_cosphi'],
                    file_name=st.session_state['pdf_filename_cosphi'],
                    mime="application/pdf",
                    key="download_cosphi_pdf"
                )
            with col_pdf2_cosphi:
                pdf_base64_cosphi = base64.b64encode(st.session_state['pdf_bytes_cosphi']).decode('utf-8')
                st.markdown(
                    f"""
                    <a href="data:application/pdf;base64,{pdf_base64_cosphi}" target="_blank" style="text-decoration: none;">
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
                            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                            Xem Phiếu
                        </button>
                    </a>
                    """,
                    unsafe_allow_html=True
                )
    
    # ... (Các chức năng tính toán điện khác)
    elif sub_menu_tinh_toan == "Chọn thiết bị bảo vệ":
        st.header("⚡ Chọn thiết bị bảo vệ (Áp tô mát – CB)")
        st.markdown(r"Công thức tính dòng điện định mức cho CB:")
        st.latex(r"I_{cb} \geq I_{tt} / K_{mt}")
        st.markdown("""
        **Giải thích các thành phần:**
        - \( I_{cb} \): Dòng điện định mức của CB (A)
        - \( I_{tt} \): Dòng điện thực tế của phụ tải (A)
        - \( K_{mt} \): Hệ số môi trường (thường là 0.8)
        
        **Mục đích:** Lựa chọn Áp tô mát (Circuit Breaker - CB) có dòng định mức phù hợp để bảo vệ an toàn cho hệ thống điện.
        """, unsafe_allow_html=True)
        
        st.subheader("Thông tin Người tính toán")
        calculator_name_cb = st.text_input("Họ và tên:", value="Hà Thị Lê", key="calc_name_cb")
        calculator_title_cb = st.text_input("Chức danh:", value="Tổ trưởng tổ KDDV", key="calc_title_cb")
        calculator_phone_cb = st.text_input("Số điện thoại:", value="0978578777", key="calc_phone_cb")

        st.subheader("Thông tin Khách hàng")
        customer_name_cb = st.text_input("Tên khách hàng:", value="Phạm Hồng Long", key="cust_name_cb")
        customer_address_cb = st.text_input("Địa chỉ:", value="xã Định Hóa, tỉnh Thái Nguyên", key="cust_address_cb")
        customer_phone_cb = st.text_input("Số điện thoại khách hàng:", value="0968552888", key="cust_phone_cb")
        
        col1, col2 = st.columns(2)
        with col1:
            I_tt = st.number_input("Dòng điện thực tế Itt (A):", min_value=0.0, key="I_tt")
        with col2:
            K_mt = st.number_input("Hệ số môi trường Kmt:", min_value=0.0, max_value=1.0, value=0.8, step=0.05, key="K_mt")

        if st.button("Chọn CB", key="btn_calc_cb"):
            I_cb = 0.0
            if K_mt > 0:
                I_cb = I_tt / K_mt
            
            st.success(f"Dòng điện định mức tối thiểu cho CB là: **{I_cb:.2f} A**")
            st.info("💡 Bạn nên chọn loại CB có dòng định mức lớn hơn hoặc bằng giá trị này.")
            
            calculator_info = {
                'name': calculator_name_cb,
                'title': calculator_title_cb,
                'phone': calculator_phone_cb
            }
            customer_info = {
                'name': customer_name_cb,
                'address': customer_address_cb,
                'phone': customer_phone_cb
            }
            input_params = {
                "Dòng điện thực tế Itt": f"{I_tt} A",
                "Hệ số môi trường Kmt": K_mt
            }
            output_results = {
                "Dòng điện định mức CB tối thiểu": f"{I_cb:.2f} A"
            }
            formula_latex = r"I_{cb} \geq I_{tt} / K_{mt}"
            formula_explanation = "Công thức lựa chọn CB dựa trên dòng điện thực tế và hệ số môi trường."
            pdf_bytes = create_pdf("CHỌN THIẾT BỊ BẢO VỆ", formula_latex, formula_explanation, input_params, output_results, calculator_info, customer_info)
            st.session_state['pdf_bytes_cb'] = pdf_bytes
            st.session_state['pdf_filename_cb'] = f"Phieu_chon_cb_{datetime.now().strftime('%Y%m%d')}.pdf"

        if 'pdf_bytes_cb' in st.session_state and st.session_state['pdf_bytes_cb']:
            st.markdown("---")
            st.subheader("Tùy chọn xuất phiếu chọn CB")
            col_pdf1_cb, col_pdf2_cb = st.columns(2)
            with col_pdf1_cb:
                st.download_button(
                    label="Xuất PDF",
                    data=st.session_state['pdf_bytes_cb'],
                    file_name=st.session_state['pdf_filename_cb'],
                    mime="application/pdf",
                    key="download_cb_pdf"
                )
            with col_pdf2_cb:
                pdf_base64_cb = base64.b64encode(st.session_state['pdf_bytes_cb']).decode('utf-8')
                st.markdown(
                    f"""
                    <a href="data:application/pdf;base64,{pdf_base64_cb}" target="_blank" style="text-decoration: none;">
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
                            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                            Xem Phiếu
                        </button>
                    </a>
                    """,
                    unsafe_allow_html=True
                )
    
    # ... (Các chức năng tính toán điện khác)
    elif sub_menu_tinh_toan == "Chuyển đổi đơn vị":
        st.header("🔄 Chuyển đổi đơn vị")
        
        # Hàm chuyển đổi đơn vị
        def convert_units(value, unit_from, unit_to):
            conversions = {
                'V': {'mV': 1000, 'kV': 0.001},
                'mV': {'V': 0.001, 'kV': 0.000001},
                'kV': {'V': 1000, 'mV': 1000000},
                'A': {'mA': 1000, 'kA': 0.001},
                'mA': {'A': 0.001, 'kA': 0.000001},
                'kA': {'A': 1000, 'mA': 1000000},
                'W': {'kW': 0.001, 'MW': 0.000001},
                'kW': {'W': 1000, 'MW': 0.001},
                'MW': {'W': 1000000, 'kW': 1000},
                'kVA': {'MVA': 0.001},
                'MVA': {'kVA': 1000},
                'kVAR': {'MVAR': 0.001},
                'MVAR': {'kVAR': 1000},
                'Ω': {'mΩ': 1000, 'kΩ': 0.001},
                'mΩ': {'Ω': 0.001, 'kΩ': 0.000001},
                'kΩ': {'Ω': 1000, 'mΩ': 1000000},
                'mm²': {'cm²': 0.01},
                'cm²': {'mm²': 100},
                'm': {'km': 0.001},
                'km': {'m': 1000}
            }
            if unit_from == unit_to:
                return value
            elif unit_from in conversions and unit_to in conversions[unit_from]:
                return value * conversions[unit_from][unit_to]
            else:
                return None

        # Giao diện chuyển đổi đơn vị
        st.subheader("Chuyển đổi điện áp")
        col_v1, col_v2, col_v3 = st.columns(3)
        with col_v1:
            value_v = st.number_input("Giá trị", key="value_v")
        with col_v2:
            unit_from_v = st.selectbox("Từ đơn vị", ["V", "mV", "kV"], key="unit_from_v")
        with col_v3:
            unit_to_v = st.selectbox("Sang đơn vị", ["V", "mV", "kV"], key="unit_to_v")
        if st.button("Chuyển đổi", key="convert_v"):
            result = convert_units(value_v, unit_from_v, unit_to_v)
            if result is not None:
                st.success(f"{value_v} {unit_from_v} = {result:.6f} {unit_to_v}")
            else:
                st.error("❌ Không thể chuyển đổi đơn vị này.")

        st.markdown("---")
        st.subheader("Chuyển đổi dòng điện")
        col_a1, col_a2, col_a3 = st.columns(3)
        with col_a1:
            value_a = st.number_input("Giá trị", key="value_a", value=0.0)
        with col_a2:
            unit_from_a = st.selectbox("Từ đơn vị", ["A", "mA", "kA"], key="unit_from_a")
        with col_a3:
            unit_to_a = st.selectbox("Sang đơn vị", ["A", "mA", "kA"], key="unit_to_a")
        if st.button("Chuyển đổi ", key="convert_a"):
            result = convert_units(value_a, unit_from_a, unit_to_a)
            if result is not None:
                st.success(f"{value_a} {unit_from_a} = {result:.6f} {unit_to_a}")
            else:
                st.error("❌ Không thể chuyển đổi đơn vị này.")

        st.markdown("---")
        st.subheader("Chuyển đổi công suất")
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            value_p = st.number_input("Giá trị", key="value_p", value=0.0)
        with col_p2:
            unit_from_p = st.selectbox("Từ đơn vị", ["W", "kW", "MW"], key="unit_from_p")
        with col_p3:
            unit_to_p = st.selectbox("Sang đơn vị", ["W", "kW", "MW"], key="unit_to_p")
        if st.button("Chuyển đổi  ", key="convert_p"):
            result = convert_units(value_p, unit_from_p, unit_to_p)
            if result is not None:
                st.success(f"{value_p} {unit_from_p} = {result:.6f} {unit_to_p}")
            else:
                st.error("❌ Không thể chuyển đổi đơn vị này.")

        st.markdown("---")
        st.subheader("Chuyển đổi trở kháng")
        col_o1, col_o2, col_o3 = st.columns(3)
        with col_o1:
            value_o = st.number_input("Giá trị", key="value_o", value=0.0)
        with col_o2:
            unit_from_o = st.selectbox("Từ đơn vị", ["Ω", "mΩ", "kΩ"], key="unit_from_o")
        with col_o3:
            unit_to_o = st.selectbox("Sang đơn vị", ["Ω", "mΩ", "kΩ"], key="unit_to_o")
        if st.button("Chuyển đổi   ", key="convert_o"):
            result = convert_units(value_o, unit_from_o, unit_to_o)
            if result is not None:
                st.success(f"{value_o} {unit_from_o} = {result:.6f} {unit_to_o}")
            else:
                st.error("❌ Không thể chuyển đổi đơn vị này.")
        
        st.markdown("---")
        st.subheader("Chuyển đổi diện tích")
        col_area1, col_area2, col_area3 = st.columns(3)
        with col_area1:
            value_area = st.number_input("Giá trị", key="value_area", value=0.0)
        with col_area2:
            unit_from_area = st.selectbox("Từ đơn vị", ["mm²", "cm²"], key="unit_from_area")
        with col_area3:
            unit_to_area = st.selectbox("Sang đơn vị", ["mm²", "cm²"], key="unit_to_area")
        if st.button("Chuyển đổi    ", key="convert_area"):
            result = convert_units(value_area, unit_from_area, unit_to_area)
            if result is not None:
                st.success(f"{value_area} {unit_from_area} = {result:.6f} {unit_to_area}")
            else:
                st.error("❌ Không thể chuyển đổi đơn vị này.")

        st.markdown("---")
        st.subheader("Chuyển đổi chiều dài")
        col_len1, col_len2, col_len3 = st.columns(3)
        with col_len1:
            value_len = st.number_input("Giá trị", key="value_len", value=0.0)
        with col_len2:
            unit_from_len = st.selectbox("Từ đơn vị", ["m", "km"], key="unit_from_len")
        with col_len3:
            unit_to_len = st.selectbox("Sang đơn vị", ["m", "km"], key="unit_to_len")
        if st.button("Chuyển đổi     ", key="convert_len"):
            result = convert_units(value_len, unit_from_len, unit_to_len)
            if result is not None:
                st.success(f"{value_len} {unit_from_len} = {result:.6f} {unit_to_len}")
            else:
                st.error("❌ Không thể chuyển đổi đơn vị này.")
    
    # ... (Các chức năng tính toán điện khác)
    elif sub_menu_tinh_toan == "Công thức điện":
        st.header("➗ Công thức điện")
        
        formula_choice = st.selectbox("Chọn nhóm công thức:", [
            "Công thức chung",
            "Định luật Ohm",
            "Công suất và năng lượng",
            "Mạch điện",
            "Điện áp và dòng điện"
        ])

        if formula_choice == "Công thức chung":
            st.markdown("""
            **Công suất (Power):**
            - $P = U \cdot I \cdot \cos\varphi$ (mạch 1 pha)
            - $P = \sqrt{3} \cdot U \cdot I \cdot \cos\varphi$ (mạch 3 pha)
            
            **Dòng điện (Current):**
            - $I = P / (U \cdot \cos\varphi)$ (mạch 1 pha)
            - $I = P / (\sqrt{3} \cdot U \cdot \cos\varphi)$ (mạch 3 pha)
            
            **Công suất biểu kiến (Apparent Power):**
            - $S = U \cdot I$ (mạch 1 pha)
            - $S = \sqrt{3} \cdot U \cdot I$ (mạch 3 pha)
            
            **Công suất phản kháng (Reactive Power):**
            - $Q = P \cdot \tan\varphi$
            
            **Mối quan hệ:**
            - $S^2 = P^2 + Q^2$
            
            """, unsafe_allow_html=True)
            
        elif formula_choice == "Định luật Ohm":
            st.markdown("""
            **Định luật Ohm:**
            - $U = I \cdot R$
            - $I = U / R$
            - $R = U / I$
            
            **Điện trở tương đương:**
            - Nối tiếp: $R_{td} = R_1 + R_2 + ...$
            - Song song: $1/R_{td} = 1/R_1 + 1/R_2 + ...$
            """, unsafe_allow_html=True)
            
        elif formula_choice == "Công suất và năng lượng":
            st.markdown("""
            **Công suất:**
            - $P = U \cdot I$ (DC)
            - $P = R \cdot I^2$
            - $P = U^2 / R$
            
            **Năng lượng điện tiêu thụ:**
            - $A = P \cdot t$
            """, unsafe_allow_html=True)

        elif formula_choice == "Mạch điện":
            st.markdown("""
            **Điện trở (Resistance):**
            - $R = \rho \cdot L / A$
            
            **Trở kháng (Impedance):**
            - $Z = \sqrt{R^2 + (X_L - X_C)^2}$
            
            **Điện kháng cảm (Inductive Reactance):**
            - $X_L = 2 \cdot \pi \cdot f \cdot L$
            
            **Điện kháng dung (Capacitive Reactance):**
            - $X_C = 1 / (2 \cdot \pi \cdot f \cdot C)$
            
            """, unsafe_allow_html=True)
            
        elif formula_choice == "Điện áp và dòng điện":
            st.markdown("""
            **Mạch nối tiếp:**
            - Dòng điện: $I_{td} = I_1 = I_2 = ...$
            - Điện áp: $U_{td} = U_1 + U_2 + ...$
            
            **Mạch song song:**
            - Dòng điện: $I_{td} = I_1 + I_2 + ...$
            - Điện áp: $U_{td} = U_1 = U_2 = ...$
            
            """, unsafe_allow_html=True)

elif main_menu == "Chuyển đổi đơn vị":
    st.header("🔄 Chuyển đổi đơn vị")
    
    # Hàm chuyển đổi đơn vị
    def convert_units(value, unit_from, unit_to):
        conversions = {
            'V': {'mV': 1000, 'kV': 0.001},
            'mV': {'V': 0.001, 'kV': 0.000001},
            'kV': {'V': 1000, 'mV': 1000000},
            'A': {'mA': 1000, 'kA': 0.001},
            'mA': {'A': 0.001, 'kA': 0.000001},
            'kA': {'A': 1000, 'mA': 1000000},
            'W': {'kW': 0.001, 'MW': 0.000001},
            'kW': {'W': 1000, 'MW': 0.001},
            'MW': {'W': 1000000, 'kW': 1000},
            'kVA': {'MVA': 0.001},
            'MVA': {'kVA': 1000},
            'kVAR': {'MVAR': 0.001},
            'MVAR': {'kVAR': 1000},
            'Ω': {'mΩ': 1000, 'kΩ': 0.001},
            'mΩ': {'Ω': 0.001, 'kΩ': 0.000001},
            'kΩ': {'Ω': 1000, 'mΩ': 1000000},
            'mm²': {'cm²': 0.01},
            'cm²': {'mm²': 100},
            'm': {'km': 0.001},
            'km': {'m': 1000}
        }
        if unit_from == unit_to:
            return value
        elif unit_from in conversions and unit_to in conversions[unit_from]:
            return value * conversions[unit_from][unit_to]
        else:
            return None

    # Giao diện chuyển đổi đơn vị
    st.subheader("Chuyển đổi điện áp")
    col_v1, col_v2, col_v3 = st.columns(3)
    with col_v1:
        value_v = st.number_input("Giá trị", key="value_v_2")
    with col_v2:
        unit_from_v = st.selectbox("Từ đơn vị", ["V", "mV", "kV"], key="unit_from_v_2")
    with col_v3:
        unit_to_v = st.selectbox("Sang đơn vị", ["V", "mV", "kV"], key="unit_to_v_2")
    if st.button("Chuyển đổi", key="convert_v_2"):
        result = convert_units(value_v, unit_from_v, unit_to_v)
        if result is not None:
            st.success(f"{value_v} {unit_from_v} = {result:.6f} {unit_to_v}")
        else:
            st.error("❌ Không thể chuyển đổi đơn vị này.")

    st.markdown("---")
    st.subheader("Chuyển đổi dòng điện")
    col_a1, col_a2, col_a3 = st.columns(3)
    with col_a1:
        value_a = st.number_input("Giá trị", key="value_a_2", value=0.0)
    with col_a2:
        unit_from_a = st.selectbox("Từ đơn vị", ["A", "mA", "kA"], key="unit_from_a_2")
    with col_a3:
        unit_to_a = st.selectbox("Sang đơn vị", ["A", "mA", "kA"], key="unit_to_a_2")
    if st.button("Chuyển đổi ", key="convert_a_2"):
        result = convert_units(value_a, unit_from_a, unit_to_a)
        if result is not None:
            st.success(f"{value_a} {unit_from_a} = {result:.6f} {unit_to_a}")
        else:
            st.error("❌ Không thể chuyển đổi đơn vị này.")

    st.markdown("---")
    st.subheader("Chuyển đổi công suất")
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        value_p = st.number_input("Giá trị", key="value_p_2", value=0.0)
    with col_p2:
        unit_from_p = st.selectbox("Từ đơn vị", ["W", "kW", "MW"], key="unit_from_p_2")
    with col_p3:
        unit_to_p = st.selectbox("Sang đơn vị", ["W", "kW", "MW"], key="unit_to_p_2")
    if st.button("Chuyển đổi  ", key="convert_p_2"):
        result = convert_units(value_p, unit_from_p, unit_to_p)
        if result is not None:
            st.success(f"{value_p} {unit_from_p} = {result:.6f} {unit_to_p}")
        else:
            st.error("❌ Không thể chuyển đổi đơn vị này.")

    st.markdown("---")
    st.subheader("Chuyển đổi trở kháng")
    col_o1, col_o2, col_o3 = st.columns(3)
    with col_o1:
        value_o = st.number_input("Giá trị", key="value_o_2", value=0.0)
    with col_o2:
        unit_from_o = st.selectbox("Từ đơn vị", ["Ω", "mΩ", "kΩ"], key="unit_from_o_2")
    with col_o3:
        unit_to_o = st.selectbox("Sang đơn vị", ["Ω", "mΩ", "kΩ"], key="unit_to_o_2")
    if st.button("Chuyển đổi   ", key="convert_o_2"):
        result = convert_units(value_o, unit_from_o, unit_to_o)
        if result is not None:
            st.success(f"{value_o} {unit_from_o} = {result:.6f} {unit_to_o}")
        else:
            st.error("❌ Không thể chuyển đổi đơn vị này.")
    
    st.markdown("---")
    st.subheader("Chuyển đổi diện tích")
    col_area1, col_area2, col_area3 = st.columns(3)
    with col_area1:
        value_area = st.number_input("Giá trị", key="value_area_2", value=0.0)
    with col_area2:
        unit_from_area = st.selectbox("Từ đơn vị", ["mm²", "cm²"], key="unit_from_area_2")
    with col_area3:
        unit_to_area = st.selectbox("Sang đơn vị", ["mm²", "cm²"], key="unit_to_area_2")
    if st.button("Chuyển đổi    ", key="convert_area_2"):
        result = convert_units(value_area, unit_from_area, unit_to_area)
        if result is not None:
            st.success(f"{value_area} {unit_from_area} = {result:.6f} {unit_to_area}")
        else:
            st.error("❌ Không thể chuyển đổi đơn vị này.")

    st.markdown("---")
    st.subheader("Chuyển đổi chiều dài")
    col_len1, col_len2, col_len3 = st.columns(3)
    with col_len1:
        value_len = st.number_input("Giá trị", key="value_len_2", value=0.0)
    with col_len2:
        unit_from_len = st.selectbox("Từ đơn vị", ["m", "km"], key="unit_from_len_2")
    with col_len3:
        unit_to_len = st.selectbox("Sang đơn vị", ["m", "km"], key="unit_to_len_2")
    if st.button("Chuyển đổi     ", key="convert_len_2"):
        result = convert_units(value_len, unit_from_len, unit_to_len)
        if result is not None:
            st.success(f"{value_len} {unit_from_len} = {result:.6f} {unit_to_len}")
        else:
            st.error("❌ Không thể chuyển đổi đơn vị này.")
            
elif main_menu == "Công thức điện":
    st.header("➗ Công thức điện")
    
    formula_choice = st.selectbox("Chọn nhóm công thức:", [
        "Công thức chung",
        "Định luật Ohm",
        "Công suất và năng lượng",
        "Mạch điện",
        "Điện áp và dòng điện"
    ])

    if formula_choice == "Công thức chung":
        st.markdown("""
        **Công suất (Power):**
        - $P = U \cdot I \cdot \cos\varphi$ (mạch 1 pha)
        - $P = \sqrt{3} \cdot U \cdot I \cdot \cos\varphi$ (mạch 3 pha)
        
        **Dòng điện (Current):**
        - $I = P / (U \cdot \cos\varphi)$ (mạch 1 pha)
        - $I = P / (\sqrt{3} \cdot U \cdot \cos\varphi)$ (mạch 3 pha)
        
        **Công suất biểu kiến (Apparent Power):**
        - $S = U \cdot I$ (mạch 1 pha)
        - $S = \sqrt{3} \cdot U \cdot I$ (mạch 3 pha)
        
        **Công suất phản kháng (Reactive Power):**
        - $Q = P \cdot \tan\varphi$
        
        **Mối quan hệ:**
        - $S^2 = P^2 + Q^2$
        
        """, unsafe_allow_html=True)
        
    elif formula_choice == "Định luật Ohm":
        st.markdown("""
        **Định luật Ohm:**
        - $U = I \cdot R$
        - $I = U / R$
        - $R = U / I$
        
        **Điện trở tương đương:**
        - Nối tiếp: $R_{td} = R_1 + R_2 + ...$
        - Song song: $1/R_{td} = 1/R_1 + 1/R_2 + ...$
        """, unsafe_allow_html=True)
        
    elif formula_choice == "Công suất và năng lượng":
        st.markdown("""
        **Công suất:**
        - $P = U \cdot I$ (DC)
        - $P = R \cdot I^2$
        - $P = U^2 / R$
        
        **Năng lượng điện tiêu thụ:**
        - $A = P \cdot t$
        """, unsafe_allow_html=True)

    elif formula_choice == "Mạch điện":
        st.markdown("""
        **Điện trở (Resistance):**
        - $R = \rho \cdot L / A$
        
        **Trở kháng (Impedance):**
        - $Z = \sqrt{R^2 + (X_L - X_C)^2}$
        
        **Điện kháng cảm (Inductive Reactance):**
        - $X_L = 2 \cdot \pi \cdot f \cdot L$
        
        **Điện kháng dung (Capacitive Reactance):**
        - $X_C = 1 / (2 \cdot \pi \cdot f \cdot C)$
        
        """, unsafe_allow_html=True)
        
    elif formula_choice == "Điện áp và dòng điện":
        st.markdown("""
        **Mạch nối tiếp:**
        - Dòng điện: $I_{td} = I_1 = I_2 = ...$
        - Điện áp: $U_{td} = U_1 + U_2 + ...$
        
        **Mạch song song:**
        - Dòng điện: $I_{td} = I_1 + I_2 + ...$
        - Điện áp: $U_{td} = U_1 = U_2 = ...$
        
        """, unsafe_allow_html=True)

# Lỗi đã sửa: Dùng main_menu thay vì choice
elif main_menu == "📋 BẢNG LIỆT KÊ CÔNG SUẤT CÁC THIẾT BỊ SỬ DỤNG ĐIỆN": # <--- Sửa lỗi ở đây
    st.header("📋 Bảng liệt kê công suất các thiết bị")

    # Mắt Nâu – Đội quản lý Điện lực khu vực Định Hóa
    # Bảng liệt kê công suất các thiết bị sử dụng điện
    # File name: app.py
    
    # Hàm để hiển thị và quản lý bảng
    def show_device_list():
        st.subheader("Thông tin chung")
        # Sử dụng st.session_state để lưu trữ thông tin
        if "customer_info" not in st.session_state:
            st.session_state.customer_info = {
                "don_vi": "Phạm Hồng Long",
                "dia_chi": "xã Định Hóa, tỉnh Thái Nguyên",
                "dia_diem": "tổ 14",
                "so_dien_thoai": "0968552888"
            }
        
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.customer_info["don_vi"] = st.text_input("Đơn vị (khách hàng):", value=st.session_state.customer_info["don_vi"], key="don_vi")
            st.session_state.customer_info["dia_chi"] = st.text_input("Địa chỉ:", value=st.session_state.customer_info["dia_chi"], key="dia_chi")
        with col2:
            st.session_state.customer_info["dia_diem"] = st.text_input("Địa điểm:", value=st.session_state.customer_info["dia_diem"], key="dia_diem")
            st.session_state.customer_info["so_dien_thoai"] = st.text_input("Số điện thoại:", value=st.session_state.customer_info["so_dien_thoai"], key="so_dien_thoai")

        st.markdown("---")
        st.subheader("Thêm thiết bị mới")
        
        # Lưu trữ danh sách thiết bị trong st.session_state
        if "device_list" not in st.session_state:
            st.session_state.device_list = []
        
        col_new1, col_new2, col_new3, col_new4 = st.columns(4)
        with col_new1:
            ten_thiet_bi = st.text_input("Tên thiết bị:", key="new_device_name")
        with col_new2:
            cong_suat = st.number_input("Công suất (kW):", min_value=0.0, key="new_device_power")
        with col_new3:
            so_luong = st.number_input("Số lượng:", min_value=1, step=1, key="new_device_quantity")
        with col_new4:
            thoi_gian = st.number_input("TGSD TB (giờ/ngày):", min_value=0.0, max_value=24.0, key="new_device_time")
            
        if st.button("Thêm thiết bị", key="add_device"):
            if ten_thiet_bi and cong_suat > 0 and so_luong > 0:
                st.session_state.device_list.append({
                    "Tên thiết bị": ten_thiet_bi,
                    "Công suất (kW)": cong_suat,
                    "Số lượng": so_luong,
                    "TGSD TB (giờ/ngày)": thoi_gian,
                    "Tổng công suất (kW)": cong_suat * so_luong
                })
                st.success(f"Đã thêm thiết bị '{ten_thiet_bi}'")
                
        # Hiển thị bảng dữ liệu
        if st.session_state.device_list:
            df_device_list = pd.DataFrame(st.session_state.device_list)
            df_device_list.index = df_device_list.index + 1
            st.markdown("---")
            st.subheader("Danh sách các thiết bị đã thêm")
            st.dataframe(df_device_list)
            
            # Tính tổng công suất và hiển thị
            total_power_sum = df_device_list["Tổng công suất (kW)"].sum()
            total_daily_energy = sum(d["Tổng công suất (kW)"] * d["TGSD TB (giờ/ngày)"] for d in st.session_state.device_list)
            
            st.markdown(f"**Tổng công suất lắp đặt:** **{total_power_sum:.2f} kW**")
            st.markdown(f"**Tổng điện năng tiêu thụ hàng ngày (tạm tính):** **{total_daily_energy:.2f} kWh**")
            
            # Nút tạo PDF
            st.markdown("---")
            st.subheader("Tạo PDF từ bảng liệt kê")
            
            if st.button("Tạo PDF Bảng Liệt Kê", key="create_pdf_btn"):
                pdf_bytes = create_device_list_pdf(df_device_list, st.session_state.customer_info)
                st.session_state['pdf_bytes_list'] = pdf_bytes
                st.session_state['pdf_filename_list'] = f"Bang_liet_ke_cong_suat_{datetime.now().strftime('%Y%m%d')}.pdf"

            if 'pdf_bytes_list' in st.session_state and st.session_state['pdf_bytes_list']:
                col_pdf1, col_pdf2 = st.columns(2)
                with col_pdf1:
                    st.download_button(
                        label="Xuất PDF",
                        data=st.session_state['pdf_bytes_list'],
                        file_name=st.session_state['pdf_filename_list'],
                        mime="application/pdf",
                        key="download_list_pdf"
                    )
                with col_pdf2:
                    pdf_base64_list = base64.b64encode(st.session_state['pdf_bytes_list']).decode('utf-8')
                    st.markdown(
                        f"""
                        <a href="data:application/pdf;base64,{pdf_base64_list}" target="_blank" style="text-decoration: none;">
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
                                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                                Xem Phiếu
                            </button>
                        </a>
                        """,
                        unsafe_allow_html=True
                    )
        
    # Hàm tạo PDF cho bảng liệt kê
    def create_device_list_pdf(df, customer_info):
        from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()

        try:
            styles.add(ParagraphStyle(name='TitleStyle', fontName='DejaVuSans-Bold', fontSize=15, alignment=1, spaceAfter=12))
            styles.add(ParagraphStyle(name='Heading2Style', fontName='DejaVuSans-Bold', fontSize=14, spaceAfter=5))
            styles.add(ParagraphStyle(name='NormalStyle', fontName='DejaVuSans', fontSize=12, spaceAfter=4))
            styles.add(ParagraphStyle(name='TableCellStyle', fontName='DejaVuSans', fontSize=10, alignment=0, leading=12))
            styles.add(ParagraphStyle(name='TableCellBoldStyle', fontName='DejaVuSans-Bold', fontSize=10, alignment=0, leading=12))
            
            # Tạo các style cho bảng
            styles.add(ParagraphStyle(name='TableHeaderStyle', fontName='DejaVuSans-Bold', fontSize=10, alignment=1, textColor=colors.whitesmoke, leading=12))
            styles.add(ParagraphStyle(name='TableDataStyle', fontName='DejaVuSans', fontSize=10, alignment=1, leading=12))
            styles.add(ParagraphStyle(name='TableTotalStyle', fontName='DejaVuSans-Bold', fontSize=10, alignment=2, leading=12))
            
        except KeyError:
            styles.add(ParagraphStyle(name='TitleStyle', fontName='Helvetica-Bold', fontSize=15, alignment=1, spaceAfter=12))
            styles.add(ParagraphStyle(name='Heading2Style', fontName='Helvetica-Bold', fontSize=14, spaceAfter=5))
            styles.add(ParagraphStyle(name='NormalStyle', fontName='Helvetica', fontSize=12, spaceAfter=4))
            styles.add(ParagraphStyle(name='TableCellStyle', fontName='Helvetica', fontSize=10, alignment=0, leading=12))
            styles.add(ParagraphStyle(name='TableCellBoldStyle', fontName='Helvetica-Bold', fontSize=10, alignment=0, leading=12))
            
            # Tạo các style cho bảng
            styles.add(ParagraphStyle(name='TableHeaderStyle', fontName='Helvetica-Bold', fontSize=10, alignment=1, textColor=colors.whitesmoke, leading=12))
            styles.add(ParagraphStyle(name='TableDataStyle', fontName='Helvetica', fontSize=10, alignment=1, leading=12))
            styles.add(ParagraphStyle(name='TableTotalStyle', fontName='Helvetica-Bold', fontSize=10, alignment=2, leading=12))


        # Tiêu đề
        elements.append(Paragraph("<para align=center><b>BẢNG LIỆT KÊ CÔNG SUẤT CÁC THIẾT BỊ SỬ DỤNG ĐIỆN</b></para>", styles["TitleStyle"]))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"Đơn vị (khách hàng): {customer_info['don_vi']}", styles["NormalStyle"]))
        elements.append(Paragraph(f"Địa chỉ: {customer_info['dia_chi']}", styles["NormalStyle"]))
        elements.append(Paragraph(f"Địa điểm: {customer_info['dia_diem']}", styles["NormalStyle"]))
        elements.append(Paragraph(f"Số điện thoại: {customer_info['so_dien_thoai']}", styles["NormalStyle"]))
        elements.append(Spacer(1, 12))

        # Bảng PDF
        # Thêm cột STT
        df_display = df.reset_index(drop=False)
        df_display.columns = ["STT"] + list(df.columns)
        df_display["STT"] = df_display["STT"].astype(str)
        
        table_data = [
            [Paragraph(col, styles["TableHeaderStyle"]) for col in df_display.columns.to_list()]
        ] + [
            [Paragraph(str(cell), styles["TableDataStyle"]) for cell in row] for row in df_display.values.tolist()
        ]
        
        # Thêm hàng tổng cộng
        total_power_sum = df_display["Tổng công suất (kW)"].sum()
        total_daily_energy = sum(d["Tổng công suất (kW)"] * d["TGSD TB (giờ/ngày)"] for d in st.session_state.device_list)
        
        table_data.append([
            Paragraph("<b>Tổng cộng</b>", styles["TableTotalStyle"]),
            "", "", "",
            Paragraph(f"<b>{total_power_sum:.2f} kW</b>", styles["TableTotalStyle"])
        ])
        
        col_widths = [0.5*inch, 2*inch, 1*inch, 1*inch, 1.5*inch, 1.5*inch]
        t = Table(table_data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BOX", (0, 0), (-1, -1), 1, colors.black),
            ("LEFTPADDING", (0,0), (-1,-1), 2),
            ("RIGHTPADDING", (0,0), (-1,-1), 2),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
            ("TOPPADDING", (0,0), (-1,-1), 4),
            ("SPAN", (0,-1), (3,-1)) # Gộp ô cho dòng tổng cộng
        ]))
        elements.append(t)
        
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"<b>Tổng công suất lắp đặt:</b> **{total_power_sum:.2f} kW**", styles["NormalStyle"]))
        elements.append(Paragraph(f"<b>Tổng điện năng tiêu thụ hàng ngày (tạm tính):</b> **{total_daily_energy:.2f} kWh**", styles["NormalStyle"]))
        elements.append(Spacer(1, 24))

        # Chữ ký
        signature_data = [
            [Paragraph("<b>ĐƠN VỊ TƯ VẤN THIẾT KẾ</b>", styles['TableCellBoldStyle']), Paragraph("<b>KHÁCH HÀNG</b>", styles['TableCellBoldStyle'])],
            [Paragraph("(Ký, ghi rõ họ tên)", styles['TableCellStyle']), Paragraph("(Ký, ghi rõ họ tên)", styles['TableCellStyle'])],
            [Spacer(1, 0.6 * inch), Spacer(1, 0.6 * inch)],
            [Paragraph(f"<b>{st.session_state.get('calculator_name_td', 'Hà Thị Lê')}</b>", styles['TableCellBoldStyle']), Paragraph(f"<b>{customer_info['don_vi']}</b>", styles['TableCellBoldStyle'])]
        ]
        signature_table = Table(signature_data, colWidths=[3*inch, 3*inch])
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,-1), 'DejaVuSans' if 'DejaVuSans' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 11),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('TOPPADDING', (0,0), (-1,-1), 2),
        ]))
        elements.append(signature_table)

        doc.build(elements)
        pdf_bytes = pdf_buffer.getvalue()
        pdf_buffer.close()
        return pdf_bytes
        
    show_device_list()
