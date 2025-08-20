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
import pandas as pd
import openpyxl

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

            st.markdown("---")
            st.subheader("Kết quả:")
            st.info(f"Dòng điện I = **{I_result:.2f}** A")

            # Tạo thông tin cho PDF
            customer_info = {
                "name": customer_name_i,
                "address": customer_address_i,
                "phone": customer_phone_i
            }
            calculator_info = {
                "name": calculator_name_i,
                "title": calculator_title_i,
                "phone": calculator_phone_i
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
            formula_latex = r"I = \frac{P \cdot 1000}{U \cdot \cos\varphi} \quad (1 \text{ pha});\quad I = \frac{P \cdot 1000}{\sqrt{3} \cdot U \cdot \cos\varphi} \quad (3 \text{ pha})"
            formula_explanation = "Công thức tính toán dòng điện (I) dựa trên công suất (P), điện áp (U) và hệ số công suất (cosφ)."
            
            pdf_bytes = create_pdf("DÒNG ĐIỆN", formula_latex, formula_explanation, input_params, output_results, calculator_info, customer_info)
            st.session_state['pdf_bytes_i'] = pdf_bytes
            st.session_state['pdf_filename_i'] = f"Phieu_tinh_I_{datetime.now().strftime('%Y%m%d')}.pdf"

        if 'pdf_bytes_i' in st.session_state and st.session_state['pdf_bytes_i']:
            st.markdown("---")
            col_pdf1, col_pdf2 = st.columns(2)
            with col_pdf1:
                st.download_button(label="Xuất PDF", data=st.session_state['pdf_bytes_i'], file_name=st.session_state['pdf_filename_i'], mime="application/pdf", key="download_i_pdf")
            with col_pdf2:
                pdf_base64_i = base64.b64encode(st.session_state['pdf_bytes_i']).decode('utf-8')
                st.markdown(f"""
                <a href="data:application/pdf;base64,{pdf_base64_i}" target="_blank">
                    <button style="background-color: #f0f2f6; border: 1px solid #d3d3d3; color: #333; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px; cursor: pointer;">
                        Xem Phiếu PDF
                    </button>
                </a>
                """, unsafe_allow_html=True)
                
    elif sub_menu_tinh_toan == "Tính công suất (P)":
        st.header("💡 Tính công suất (P)")
        st.latex(r"P = \frac{U \cdot I \cdot \cos\varphi}{1000} \quad \text{(1 pha)}")
        st.latex(r"P = \frac{\sqrt{3} \cdot U \cdot I \cdot \cos\varphi}{1000} \quad \text{(3 pha)}")
        st.markdown("""
        **Giải thích các thành phần:**
        - \( P \): Công suất tải (kW)
        - \( U \): Điện áp (V)
        - \( I \): Dòng điện (A)
        - \( \cos\varphi \): Hệ số công suất
        
        **Mục đích:** Tính toán công suất tiêu thụ của một tải dựa trên dòng điện, điện áp và hệ số công suất.
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
            if pha_p == "1 pha":
                P_result = U_p * I_p * cos_phi_p / 1000
            elif pha_p == "3 pha":
                P_result = math.sqrt(3) * U_p * I_p * cos_phi_p / 1000
            
            st.markdown("---")
            st.subheader("Kết quả:")
            st.info(f"Công suất P = **{P_result:.2f}** kW")
            
            # Tạo thông tin cho PDF
            customer_info = {
                "name": customer_name_p,
                "address": customer_address_p,
                "phone": customer_phone_p
            }
            calculator_info = {
                "name": calculator_name_p,
                "title": calculator_title_p,
                "phone": calculator_phone_p
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
            formula_latex = r"P = \frac{U \cdot I \cdot \cos\varphi}{1000} \quad (1 \text{ pha}); \quad P = \frac{\sqrt{3} \cdot U \cdot I \cdot \cos\varphi}{1000} \quad (3 \text{ pha})"
            formula_explanation = "Công thức tính toán công suất (P) dựa trên điện áp (U), dòng điện (I) và hệ số công suất (cosφ)."
            
            pdf_bytes = create_pdf("CÔNG SUẤT", formula_latex, formula_explanation, input_params, output_results, calculator_info, customer_info)
            st.session_state['pdf_bytes_p'] = pdf_bytes
            st.session_state['pdf_filename_p'] = f"Phieu_tinh_P_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        if 'pdf_bytes_p' in st.session_state and st.session_state['pdf_bytes_p']:
            st.markdown("---")
            col_pdf1, col_pdf2 = st.columns(2)
            with col_pdf1:
                st.download_button(label="Xuất PDF", data=st.session_state['pdf_bytes_p'], file_name=st.session_state['pdf_filename_p'], mime="application/pdf", key="download_p_pdf")
            with col_pdf2:
                pdf_base64_p = base64.b64encode(st.session_state['pdf_bytes_p']).decode('utf-8')
                st.markdown(f"""
                <a href="data:application/pdf;base64,{pdf_base64_p}" target="_blank">
                    <button style="background-color: #f0f2f6; border: 1px solid #d3d3d3; color: #333; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px; cursor: pointer;">
                        Xem Phiếu PDF
                    </button>
                </a>
                """, unsafe_allow_html=True)
                
    elif sub_menu_tinh_toan == "Tính công suất biểu kiến (S)":
        st.header("🧲 Tính công suất biểu kiến (S)")
        st.latex(r"S = \frac{P}{\cos\varphi} \quad \text{(1 pha)}")
        st.latex(r"S = \frac{\sqrt{3} \cdot U \cdot I}{1000} \quad \text{(3 pha)}")
        st.markdown("""
        **Giải thích các thành phần:**
        - \( S \): Công suất biểu kiến (kVA)
        - \( P \): Công suất tác dụng (kW)
        - \( U \): Điện áp (V)
        - \( I \): Dòng điện (A)
        - \( \cos\varphi \): Hệ số công suất
        
        **Mục đích:** Tính toán công suất biểu kiến của tải để lựa chọn máy biến áp hoặc nguồn điện phù hợp.
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

        calculation_type_s = st.radio("Chọn cách tính:", ["Từ P và cosφ", "Từ U và I"], key="calc_type_s")
        
        if calculation_type_s == "Từ P và cosφ":
            col1, col2 = st.columns(2)
            with col1:
                P_s = st.number_input("Công suất P (kW):", min_value=0.0, key="P_s")
            with col2:
                cos_phi_s = st.slider("Hệ số cosφ:", 0.1, 1.0, 0.8, key="cos_phi_s")
            
            if st.button("Tính công suất biểu kiến", key="btn_calc_s_p"):
                S_result = 0.0
                if cos_phi_s != 0:
                    S_result = P_s / cos_phi_s
                
                st.markdown("---")
                st.subheader("Kết quả:")
                st.info(f"Công suất biểu kiến S = **{S_result:.2f}** kVA")
                
                # Tạo thông tin cho PDF
                customer_info = {
                    "name": customer_name_s,
                    "address": customer_address_s,
                    "phone": customer_phone_s
                }
                calculator_info = {
                    "name": calculator_name_s,
                    "title": calculator_title_s,
                    "phone": calculator_phone_s
                }
                input_params = {
                    "Công suất P": f"{P_s} kW",
                    "Hệ số cosφ": cos_phi_s
                }
                output_results = {
                    "Công suất biểu kiến S": f"{S_result:.2f} kVA"
                }
                formula_latex = r"S = \frac{P}{\cos\varphi}"
                formula_explanation = "Công thức tính toán công suất biểu kiến (S) dựa trên công suất tác dụng (P) và hệ số công suất (cosφ)."
                
                pdf_bytes = create_pdf("CÔNG SUẤT BIỂU KIẾN (TỪ P & cosφ)", formula_latex, formula_explanation, input_params, output_results, calculator_info, customer_info)
                st.session_state['pdf_bytes_s_p'] = pdf_bytes
                st.session_state['pdf_filename_s_p'] = f"Phieu_tinh_S_tu_P_cosφ_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        else: # Từ U và I
            col1, col2 = st.columns(2)
            with col1:
                pha_s = st.radio("Loại điện:", ["1 pha", "3 pha"], key="pha_s_ui")
                U_s = st.number_input("Điện áp U (V):", min_value=0.0, key="U_s")
            with col2:
                I_s = st.number_input("Dòng điện I (A):", min_value=0.0, key="I_s")
            
            if st.button("Tính công suất biểu kiến", key="btn_calc_s_ui"):
                S_result = 0.0
                if pha_s == "1 pha":
                    S_result = U_s * I_s / 1000
                elif pha_s == "3 pha":
                    S_result = math.sqrt(3) * U_s * I_s / 1000
                
                st.markdown("---")
                st.subheader("Kết quả:")
                st.info(f"Công suất biểu kiến S = **{S_result:.2f}** kVA")
                
                # Tạo thông tin cho PDF
                customer_info = {
                    "name": customer_name_s,
                    "address": customer_address_s,
                    "phone": customer_phone_s
                }
                calculator_info = {
                    "name": calculator_name_s,
                    "title": calculator_title_s,
                    "phone": calculator_phone_s
                }
                input_params = {
                    "Loại điện": pha_s,
                    "Điện áp U": f"{U_s} V",
                    "Dòng điện I": f"{I_s} A"
                }
                output_results = {
                    "Công suất biểu kiến S": f"{S_result:.2f} kVA"
                }
                formula_latex = r"S = \frac{U \cdot I}{1000} \quad (1 \text{ pha}); \quad S = \frac{\sqrt{3} \cdot U \cdot I}{1000} \quad (3 \text{ pha})"
                formula_explanation = "Công thức tính toán công suất biểu kiến (S) dựa trên điện áp (U) và dòng điện (I)."
                
                pdf_bytes = create_pdf("CÔNG SUẤT BIỂU KIẾN (TỪ U & I)", formula_latex, formula_explanation, input_params, output_results, calculator_info, customer_info)
                st.session_state['pdf_bytes_s_ui'] = pdf_bytes
                st.session_state['pdf_filename_s_ui'] = f"Phieu_tinh_S_tu_U_I_{datetime.now().strftime('%Y%m%d')}.pdf"
                
        if 'pdf_bytes_s_p' in st.session_state and st.session_state['pdf_bytes_s_p']:
            st.markdown("---")
            col_pdf1, col_pdf2 = st.columns(2)
            with col_pdf1:
                st.download_button(label="Xuất PDF", data=st.session_state['pdf_bytes_s_p'], file_name=st.session_state['pdf_filename_s_p'], mime="application/pdf", key="download_s_p_pdf")
            with col_pdf2:
                pdf_base64_sp = base64.b64encode(st.session_state['pdf_bytes_s_p']).decode('utf-8')
                st.markdown(f"""
                <a href="data:application/pdf;base64,{pdf_base64_sp}" target="_blank">
                    <button style="background-color: #f0f2f6; border: 1px solid #d3d3d3; color: #333; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px; cursor: pointer;">
                        Xem Phiếu PDF
                    </button>
                </a>
                """, unsafe_allow_html=True)
                
        if 'pdf_bytes_s_ui' in st.session_state and st.session_state['pdf_bytes_s_ui']:
            st.markdown("---")
            col_pdf1, col_pdf2 = st.columns(2)
            with col_pdf1:
                st.download_button(label="Xuất PDF", data=st.session_state['pdf_bytes_s_ui'], file_name=st.session_state['pdf_filename_s_ui'], mime="application/pdf", key="download_s_ui_pdf")
            with col_pdf2:
                pdf_base64_sui = base64.b64encode(st.session_state['pdf_bytes_s_ui']).decode('utf-8')
                st.markdown(f"""
                <a href="data:application/pdf;base64,{pdf_base64_sui}" target="_blank">
                    <button style="background-color: #f0f2f6; border: 1px solid #d3d3d3; color: #333; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px; cursor: pointer;">
                        Xem Phiếu PDF
                    </button>
                </a>
                """, unsafe_allow_html=True)
                
    elif sub_menu_tinh_toan == "Tính công suất phản kháng (Q)":
        st.header("⚖️ Tính công suất phản kháng (Q)")
        st.latex(r"Q = \frac{P}{\tan\varphi}")
        st.latex(r"Q = \frac{\sqrt{3} \cdot U \cdot I \cdot \sin\varphi}{1000}")
        st.markdown("""
        **Giải thích các thành phần:**
        - \( Q \): Công suất phản kháng (kVAr)
        - \( P \): Công suất tác dụng (kW)
        - \( U \): Điện áp (V)
        - \( I \): Dòng điện (A)
        - \( \cos\varphi \): Hệ số công suất
        
        **Mục đích:** Tính toán công suất phản kháng để lựa chọn tụ bù phù hợp nhằm nâng cao hệ số công suất.
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
        
        calculation_type_q = st.radio("Chọn cách tính:", ["Từ P và cosφ", "Từ P, U và I"], key="calc_type_q")
        
        if calculation_type_q == "Từ P và cosφ":
            col1, col2 = st.columns(2)
            with col1:
                P_q_tan = st.number_input("Công suất P (kW):", min_value=0.0, key="P_q_tan")
            with col2:
                cos_phi_q_tan = st.slider("Hệ số cosφ:", 0.1, 1.0, 0.8, key="cos_phi_q_tan")
            
            if st.button("Tính công suất phản kháng", key="btn_calc_q_tan"):
                Q_result = 0.0
                if cos_phi_q_tan > 0:
                    tan_phi_q = math.sqrt(1 / (cos_phi_q_tan**2) - 1)
                    Q_result = P_q_tan * tan_phi_q
                
                st.markdown("---")
                st.subheader("Kết quả:")
                st.info(f"Công suất phản kháng Q = **{Q_result:.2f}** kVAr")
                
                # Tạo thông tin cho PDF
                customer_info = {
                    "name": customer_name_q,
                    "address": customer_address_q,
                    "phone": customer_phone_q
                }
                calculator_info = {
                    "name": calculator_name_q,
                    "title": calculator_title_q,
                    "phone": calculator_phone_q
                }
                input_params = {
                    "Công suất P": f"{P_q_tan} kW",
                    "Hệ số cosφ": cos_phi_q_tan
                }
                output_results = {
                    "Công suất phản kháng Q": f"{Q_result:.2f} kVAr"
                }
                formula_latex = r"Q = P \cdot \tan\varphi = P \cdot \sqrt{\frac{1}{\cos^2\varphi}-1}"
                formula_explanation = "Công thức tính toán công suất phản kháng (Q) dựa trên công suất tác dụng (P) và hệ số công suất (cosφ)."
                
                pdf_bytes = create_pdf("CÔNG SUẤT PHẢN KHÁNG (TỪ P & cosφ)", formula_latex, formula_explanation, input_params, output_results, calculator_info, customer_info)
                st.session_state['pdf_bytes_q_tan'] = pdf_bytes
                st.session_state['pdf_filename_q_tan'] = f"Phieu_tinh_Q_tu_P_cosφ_{datetime.now().strftime('%Y%m%d')}.pdf"

        else: # Từ P, U, và I
            col1, col2 = st.columns(2)
            with col1:
                P_q_sin = st.number_input("Công suất P (kW):", min_value=0.0, key="P_q_sin")
                I_q_sin = st.number_input("Dòng điện I (A):", min_value=0.0, key="I_q_sin")
            with col2:
                U_q_sin = st.number_input("Điện áp U (V):", min_value=0.0, key="U_q_sin")
                pha_q_sin = st.radio("Loại điện:", ["1 pha", "3 pha"], key="pha_q_sin")
            
            if st.button("Tính công suất phản kháng", key="btn_calc_q_sin"):
                Q_result = 0.0
                if U_q_sin != 0 and I_q_sin != 0:
                    S_q_sin = U_q_sin * I_q_sin / 1000 if pha_q_sin == "1 pha" else math.sqrt(3) * U_q_sin * I_q_sin / 1000
                    P_q_sin_val = P_q_sin
                    if S_q_sin > 0 and S_q_sin >= P_q_sin_val:
                        Q_result = math.sqrt(S_q_sin**2 - P_q_sin_val**2)
                    else:
                        st.warning("⚠️ Công suất tác dụng (P) không thể lớn hơn công suất biểu kiến (S). Vui lòng kiểm tra lại các giá trị đầu vào.")
                        Q_result = "N/A"
                
                if Q_result != "N/A":
                    st.markdown("---")
                    st.subheader("Kết quả:")
                    st.info(f"Công suất phản kháng Q = **{Q_result:.2f}** kVAr")
                    
                    # Tạo thông tin cho PDF
                    customer_info = {
                        "name": customer_name_q,
                        "address": customer_address_q,
                        "phone": customer_phone_q
                    }
                    calculator_info = {
                        "name": calculator_name_q,
                        "title": calculator_title_q,
                        "phone": calculator_phone_q
                    }
                    input_params = {
                        "Loại điện": pha_q_sin,
                        "Công suất P": f"{P_q_sin} kW",
                        "Điện áp U": f"{U_q_sin} V",
                        "Dòng điện I": f"{I_q_sin} A"
                    }
                    output_results = {
                        "Công suất phản kháng Q": f"{Q_result:.2f} kVAr"
                    }
                    formula_latex = r"S^2 = P^2 + Q^2 \implies Q = \sqrt{S^2 - P^2}"
                    formula_explanation = "Công thức tính toán công suất phản kháng (Q) dựa trên công suất biểu kiến (S) và công suất tác dụng (P)."
                    
                    pdf_bytes = create_pdf("CÔNG SUẤT PHẢN KHÁNG (TỪ S & P)", formula_latex, formula_explanation, input_params, output_results, calculator_info, customer_info)
                    st.session_state['pdf_bytes_q_sin'] = pdf_bytes
                    st.session_state['pdf_filename_q_sin'] = f"Phieu_tinh_Q_tu_S_P_{datetime.now().strftime('%Y%m%d')}.pdf"

        if 'pdf_bytes_q_tan' in st.session_state and st.session_state['pdf_bytes_q_tan']:
            st.markdown("---")
            col_pdf1, col_pdf2 = st.columns(2)
            with col_pdf1:
                st.download_button(label="Xuất PDF", data=st.session_state['pdf_bytes_q_tan'], file_name=st.session_state['pdf_filename_q_tan'], mime="application/pdf", key="download_q_tan_pdf")
            with col_pdf2:
                pdf_base64_qt = base64.b64encode(st.session_state['pdf_bytes_q_tan']).decode('utf-8')
                st.markdown(f"""
                <a href="data:application/pdf;base64,{pdf_base64_qt}" target="_blank">
                    <button style="background-color: #f0f2f6; border: 1px solid #d3d3d3; color: #333; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px; cursor: pointer;">
                        Xem Phiếu PDF
                    </button>
                </a>
                """, unsafe_allow_html=True)
                
        if 'pdf_bytes_q_sin' in st.session_state and st.session_state['pdf_bytes_q_sin']:
            st.markdown("---")
            col_pdf1, col_pdf2 = st.columns(2)
            with col_pdf1:
                st.download_button(label="Xuất PDF", data=st.session_state['pdf_bytes_q_sin'], file_name=st.session_state['pdf_filename_q_sin'], mime="application/pdf", key="download_q_sin_pdf")
            with col_pdf2:
                pdf_base64_qs = base64.b64encode(st.session_state['pdf_bytes_q_sin']).decode('utf-8')
                st.markdown(f"""
                <a href="data:application/pdf;base64,{pdf_base64_qs}" target="_blank">
                    <button style="background-color: #f0f2f6; border: 1px solid #d3d3d3; color: #333; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px; cursor: pointer;">
                        Xem Phiếu PDF
                    </button>
                </a>
                """, unsafe_allow_html=True)

    elif sub_menu_tinh_toan == "Tính sụt áp (ΔU)":
        st.header("📉 Tính sụt áp (ΔU)")
        st.markdown("""
        **Công thức tính sụt áp:**
        - **Đối với đường dây 1 pha:** $ΔU = \frac{2 \cdot I \cdot (R_0 \cdot L \cdot \cos\varphi + X_0 \cdot L \cdot \sin\varphi)}{1000} \text{ (V)}$
        - **Đối với đường dây 3 pha:** $ΔU = \frac{\sqrt{3} \cdot I \cdot (R_0 \cdot L \cdot \cos\varphi + X_0 \cdot L \cdot \sin\varphi)}{1000} \text{ (V)}$
        
        **Giải thích các thành phần:**
        - \( ΔU \): Sụt áp (V)
        - \( I \): Dòng điện (A)
        - \( R_0 \): Điện trở trên 1km dây dẫn ($Ω/km$)
        - \( X_0 \): Điện kháng trên 1km dây dẫn ($Ω/km$)
        - \( L \): Chiều dài đường dây (m)
        - \( \cos\varphi \): Hệ số công suất
        
        **Mục đích:** Tính toán sụt áp trên đường dây để đảm bảo điện áp cuối nguồn không vượt quá giới hạn cho phép.
        """, unsafe_allow_html=True)

        st.subheader("Thông tin Người tính toán")
        calculator_name_du = st.text_input("Họ và tên:", value="Hà Thị Lê", key="calc_name_du")
        calculator_title_du = st.text_input("Chức danh:", value="Tổ trưởng tổ KDDV", key="calc_title_du")
        calculator_phone_du = st.text_input("Số điện thoại:", value="0978578777", key="calc_phone_du")

        st.subheader("Thông tin Khách hàng")
        customer_name_du = st.text_input("Tên khách hàng:", value="Phạm Hồng Long", key="cust_name_du")
        customer_address_du = st.text_input("Địa chỉ:", value="xã Định Hóa, tỉnh Thái Nguyên", key="cust_address_du")
        customer_phone_du = st.text_input("Số điện thoại khách hàng:", value="0968552888", key="cust_phone_du")
        
        current_date_du = datetime.now().strftime("Ngày %d tháng %m năm %Y")
        st.markdown(f"**Thời gian lập phiếu:** {current_date_du}")

        col1, col2 = st.columns(2)
        with col1:
            pha_du = st.radio("Loại điện:", ["1 pha", "3 pha"], key="pha_du")
            I_du = st.number_input("Dòng điện I (A):", min_value=0.0, key="I_du")
            R0_du = st.number_input("Điện trở R0 (Ω/km):", min_value=0.0, key="R0_du", format="%.5f")
        with col2:
            L_du = st.number_input("Chiều dài đường dây L (m):", min_value=0.0, key="L_du")
            X0_du = st.number_input("Điện kháng X0 (Ω/km):", min_value=0.0, key="X0_du", format="%.5f")
            cos_phi_du = st.slider("Hệ số cosφ:", 0.1, 1.0, 0.8, key="cos_phi_du")

        if st.button("Tính sụt áp", key="btn_calc_du"):
            delta_U_result = 0.0
            sin_phi_du = math.sqrt(1 - cos_phi_du**2)
            # Chuyển đổi L từ mét sang km
            L_du_km = L_du / 1000
            
            if pha_du == "1 pha":
                delta_U_result = 2 * I_du * (R0_du * L_du_km * cos_phi_du + X0_du * L_du_km * sin_phi_du)
            elif pha_du == "3 pha":
                delta_U_result = math.sqrt(3) * I_du * (R0_du * L_du_km * cos_phi_du + X0_du * L_du_km * sin_phi_du)

            st.markdown("---")
            st.subheader("Kết quả:")
            st.info(f"Sụt áp ΔU = **{delta_U_result:.2f}** V")
            st.info(f"Phần trăm sụt áp ΔU% = **{(delta_U_result / (U_du if pha_du == '1 pha' else U_du * math.sqrt(3)) * 100):.2f}** %")
            
            # Tạo thông tin cho PDF
            customer_info = {
                "name": customer_name_du,
                "address": customer_address_du,
                "phone": customer_phone_du
            }
            calculator_info = {
                "name": calculator_name_du,
                "title": calculator_title_du,
                "phone": calculator_phone_du
            }
            input_params = {
                "Loại điện": pha_du,
                "Dòng điện I": f"{I_du} A",
                "Chiều dài L": f"{L_du} m",
                "Điện trở R0": f"{R0_du} Ω/km",
                "Điện kháng X0": f"{X0_du} Ω/km",
                "Hệ số cosφ": cos_phi_du
            }
            output_results = {
                "Sụt áp ΔU": f"{delta_U_result:.2f} V"
            }
            formula_latex = r"\Delta U = 2 \cdot I \cdot (R_0 \cdot L \cdot \cos\varphi + X_0 \cdot L \cdot \sin\varphi) \quad (1 \text{ pha}); \quad \Delta U = \sqrt{3} \cdot I \cdot (R_0 \cdot L \cdot \cos\varphi + X_0 \cdot L \cdot \sin\varphi) \quad (3 \text{ pha})"
            formula_explanation = "Công thức tính toán sụt áp (ΔU) trên đường dây."
            
            pdf_bytes = create_pdf("SỤT ÁP", formula_latex, formula_explanation, input_params, output_results, calculator_info, customer_info)
            st.session_state['pdf_bytes_du'] = pdf_bytes
            st.session_state['pdf_filename_du'] = f"Phieu_tinh_sut_ap_{datetime.now().strftime('%Y%m%d')}.pdf"
            
        if 'pdf_bytes_du' in st.session_state and st.session_state['pdf_bytes_du']:
            st.markdown("---")
            col_pdf1, col_pdf2 = st.columns(2)
            with col_pdf1:
                st.download_button(label="Xuất PDF", data=st.session_state['pdf_bytes_du'], file_name=st.session_state['pdf_filename_du'], mime="application/pdf", key="download_du_pdf")
            with col_pdf2:
                pdf_base64_du = base64.b64encode(st.session_state['pdf_bytes_du']).decode('utf-8')
                st.markdown(f"""
                <a href="data:application/pdf;base64,{pdf_base64_du}" target="_blank">
                    <button style="background-color: #f0f2f6; border: 1px solid #d3d3d3; color: #333; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px; cursor: pointer;">
                        Xem Phiếu PDF
                    </button>
                </a>
                """, unsafe_allow_html=True)
    
    elif sub_menu_tinh_toan == "Chọn tiết diện dây dẫn":
        st.header("📏 Chọn tiết diện dây dẫn")
        st.markdown("""
        **Mục đích:** Hỗ trợ lựa chọn tiết diện dây dẫn phù hợp với dòng điện tải, đảm bảo an toàn và hiệu quả truyền tải điện.
        """, unsafe_allow_html=True)
        
        st.subheader("Thông tin Người tính toán")
        calculator_name_td = st.text_input("Họ và tên:", value="Hà Thị Lê", key="calc_name_td")
        calculator_title_td = st.text_input("Chức danh:", value="Tổ trưởng tổ KDDV", key="calc_title_td")
        calculator_phone_td = st.text_input("Số điện thoại:", value="0978578777", key="calc_phone_td")

        st.subheader("Thông tin Khách hàng")
        customer_name_td = st.text_input("Tên khách hàng:", value="Phạm Hồng Long", key="cust_name_td")
        customer_address_td = st.text_input("Địa chỉ:", value="xã Định Hóa, tỉnh Thái Nguyên", key="cust_address_td")
        customer_phone_td = st.text_input("Số điện thoại khách hàng:", value="0968552888", key="cust_phone_td")

        current_date_td = datetime.now().strftime("Ngày %d tháng %m năm %Y")
        st.markdown(f"**Thời gian lập phiếu:** {current_date_td}")
        
        st.subheader("Tiết diện dây theo dòng điện")
        
        col1, col2 = st.columns(2)
        with col1:
            I_td = st.number_input("Dòng điện tải I (A):", min_value=0.0, key="I_td")
            vat_lieu_day = st.radio("Vật liệu dây:", ["Đồng", "Nhôm"], key="vat_lieu_day")
        with col2:
            cach_lap_dat = st.radio("Cách lắp đặt:", ["Trong không khí", "Trong ống"], key="cach_lap_dat")

        if st.button("Chọn tiết diện", key="btn_calc_td"):
            data_to_use = {}
            if vat_lieu_day == "Đồng":
                data_to_use = copper_cable_data
            elif vat_lieu_day == "Nhôm":
                data_to_use = aluminum_cable_data
            
            if not data_to_use:
                st.warning("⚠️ Không tìm thấy dữ liệu bảng tra. Vui lòng kiểm tra lại các file Excel.")
            else:
                
                capacity_dict = {}
                if cach_lap_dat == "Trong không khí":
                    capacity_dict = data_to_use.get('in_air', {})
                else:
                    capacity_dict = data_to_use.get('in_conduit', {})
                
                if not capacity_dict:
                    st.warning("⚠️ Không có dữ liệu cho cách lắp đặt này.")
                else:
                    selected_size = "Không tìm thấy"
                    for size, capacity in capacity_dict.items():
                        if I_td <= capacity:
                            selected_size = size
                            break
                    
                    st.markdown("---")
                    st.subheader("Kết quả:")
                    st.info(f"Tiết diện dây dẫn phù hợp cho dòng điện **{I_td} A** là: **{selected_size} mm²**")
                    st.warning("⚠️ Lưu ý: Kết quả chỉ mang tính tham khảo. Cần tính toán thêm sụt áp, tổn thất và các yếu tố khác để có lựa chọn chính xác.")
                    
                    # Tạo thông tin cho PDF
                    customer_info = {
                        "name": customer_name_td,
                        "address": customer_address_td,
                        "phone": customer_phone_td
                    }
                    calculator_info = {
                        "name": calculator_name_td,
                        "title": calculator_title_td,
                        "phone": calculator_phone_td
                    }
                    input_params = {
                        "Dòng điện tải I": f"{I_td} A",
                        "Vật liệu dây": vat_lieu_day,
                        "Cách lắp đặt": cach_lap_dat
                    }
                    output_results = {
                        "Tiết diện dây dẫn phù hợp": f"{selected_size} mm²"
                    }
                    formula_latex = r"\text{Tra bảng khả năng chịu tải của dây dẫn}"
                    formula_explanation = "Lựa chọn tiết diện dây dẫn dựa trên khả năng chịu tải dòng điện cho phép của dây."
                    
                    pdf_bytes = create_pdf("LỰA CHỌN TIẾT DIỆN DÂY", formula_latex, formula_explanation, input_params, output_results, calculator_info, customer_info)
                    st.session_state['pdf_bytes_td'] = pdf_bytes
                    st.session_state['pdf_filename_td'] = f"Phieu_chon_tiet_dien_{datetime.now().strftime('%Y%m%d')}.pdf"

        if 'pdf_bytes_td' in st.session_state and st.session_state['pdf_bytes_td']:
            st.markdown("---")
            col_pdf1, col_pdf2 = st.columns(2)
            with col_pdf1:
                st.download_button(label="Xuất PDF", data=st.session_state['pdf_bytes_td'], file_name=st.session_state['pdf_filename_td'], mime="application/pdf", key="download_td_pdf")
            with col_pdf2:
                pdf_base64_td = base64.b64encode(st.session_state['pdf_bytes_td']).decode('utf-8')
                st.markdown(f"""
                <a href="data:application/pdf;base64,{pdf_base64_td}" target="_blank">
                    <button style="background-color: #f0f2f6; border: 1px solid #d3d3d3; color: #333; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px; cursor: pointer;">
                        Xem Phiếu PDF
                    </button>
                </a>
                """, unsafe_allow_html=True)

    elif sub_menu_tinh_toan == "Chiều dài dây tối đa (ΔU%)":
        st.header("🛣️ Chiều dài dây tối đa")
        st.markdown("""
        **Mục đích:** Tính toán chiều dài tối đa của đường dây để đảm bảo sụt áp không vượt quá giới hạn cho phép (thường là 2-3% đối với lưới hạ áp).
        """, unsafe_allow_html=True)
        
        st.subheader("Thông tin Người tính toán")
        calculator_name_cdtd = st.text_input("Họ và tên:", value="Hà Thị Lê", key="calc_name_cdtd")
        calculator_title_cdtd = st.text_input("Chức danh:", value="Tổ trưởng tổ KDDV", key="calc_title_cdtd")
        calculator_phone_cdtd = st.text_input("Số điện thoại:", value="0978578777", key="calc_phone_cdtd")

        st.subheader("Thông tin Khách hàng")
        customer_name_cdtd = st.text_input("Tên khách hàng:", value="Phạm Hồng Long", key="cust_name_cdtd")
        customer_address_cdtd = st.text_input("Địa chỉ:", value="xã Định Hóa, tỉnh Thái Nguyên", key="cust_address_cdtd")
        customer_phone_cdtd = st.text_input("Số điện thoại khách hàng:", value="0968552888", key="cust_phone_cdtd")

        current_date_cdtd = datetime.now().strftime("Ngày %d tháng %m năm %Y")
        st.markdown(f"**Thời gian lập phiếu:** {current_date_cdtd}")
        
        col1, col2 = st.columns(2)
        with col1:
            pha_cdtd = st.radio("Loại điện:", ["1 pha", "3 pha"], key="pha_cdtd")
            I_cdtd = st.number_input("Dòng điện tải I (A):", min_value=0.0, key="I_cdtd")
            R0_cdtd = st.number_input("Điện trở R0 (Ω/km):", min_value=0.0, key="R0_cdtd", format="%.5f")
        with col2:
            U_cdtd = st.number_input("Điện áp U (V):", min_value=0.0, key="U_cdtd")
            X0_cdtd = st.number_input("Điện kháng X0 (Ω/km):", min_value=0.0, key="X0_cdtd", format="%.5f")
            cos_phi_cdtd = st.slider("Hệ số cosφ:", 0.1, 1.0, 0.8, key="cos_phi_cdtd")
            delta_U_percent_cdtd = st.number_input("Sụt áp cho phép ΔU% (%):", min_value=0.0, value=3.0, key="delta_U_percent_cdtd")

        if st.button("Tính chiều dài tối đa", key="btn_calc_cdtd"):
            max_L_result = 0.0
            if U_cdtd != 0 and I_cdtd != 0:
                U_phase_cdtd = U_cdtd if pha_cdtd == "1 pha" else U_cdtd * math.sqrt(3)
                delta_U_max = U_phase_cdtd * (delta_U_percent_cdtd / 100)
                
                sin_phi_cdtd = math.sqrt(1 - cos_phi_cdtd**2)
                
                if pha_cdtd == "1 pha":
                    mau_so = 2 * I_cdtd * (R0_cdtd * cos_phi_cdtd + X0_cdtd * sin_phi_cdtd)
                else:
                    mau_so = math.sqrt(3) * I_cdtd * (R0_cdtd * cos_phi_cdtd + X0_cdtd * sin_phi_cdtd)
                
                if mau_so != 0:
                    max_L_result = delta_U_max / mau_so
                else:
                    st.error("⚠️ Không thể tính toán. Mẫu số bằng 0. Vui lòng kiểm tra lại các thông số đầu vào.")
                    max_L_result = 0.0

            st.markdown("---")
            st.subheader("Kết quả:")
            st.info(f"Chiều dài dây tối đa L = **{max_L_result:.2f}** km")
            st.info(f"Hoặc **{max_L_result * 1000:.2f}** m")
            
            # Tạo thông tin cho PDF
            customer_info = {
                "name": customer_name_cdtd,
                "address": customer_address_cdtd,
                "phone": customer_phone_cdtd
            }
            calculator_info = {
                "name": calculator_name_cdtd,
                "title": calculator_title_cdtd,
                "phone": calculator_phone_cdtd
            }
            input_params = {
                "Loại điện": pha_cdtd,
                "Dòng điện tải I": f"{I_cdtd} A",
                "Điện áp U": f"{U_cdtd} V",
                "Điện trở R0": f"{R0_cdtd} Ω/km",
                "Điện kháng X0": f"{X0_cdtd} Ω/km",
                "Hệ số cosφ": cos_phi_cdtd,
                "Sụt áp cho phép ΔU%": f"{delta_U_percent_cdtd} %"
            }
            output_results = {
                "Chiều dài dây tối đa L": f"{max_L_result:.2f} km"
            }
            formula_latex = r"L_{max} = \frac{\Delta U_{max}}{K \cdot I \cdot (R_0 \cos\varphi + X_0 \sin\varphi)}"
            formula_explanation = "Công thức tính chiều dài dây tối đa cho phép dựa trên sụt áp tối đa cho phép."
            
            pdf_bytes = create_pdf("CHIỀU DÀI DÂY TỐI ĐA", formula_latex, formula_explanation, input_params, output_results, calculator_info, customer_info)
            st.session_state['pdf_bytes_cdtd'] = pdf_bytes
            st.session_state['pdf_filename_cdtd'] = f"Phieu_chieu_dai_day_toi_da_{datetime.now().strftime('%Y%m%d')}.pdf"

        if 'pdf_bytes_cdtd' in st.session_state and st.session_state['pdf_bytes_cdtd']:
            st.markdown("---")
            col_pdf1, col_pdf2 = st.columns(2)
            with col_pdf1:
                st.download_button(label="Xuất PDF", data=st.session_state['pdf_bytes_cdtd'], file_name=st.session_state['pdf_filename_cdtd'], mime="application/pdf", key="download_cdtd_pdf")
            with col_pdf2:
                pdf_base64_cdtd = base64.b64encode(st.session_state['pdf_bytes_cdtd']).decode('utf-8')
                st.markdown(f"""
                <a href="data:application/pdf;base64,{pdf_base64_cdtd}" target="_blank">
                    <button style="background-color: #f0f2f6; border: 1px solid #d3d3d3; color: #333; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px; cursor: pointer;">
                        Xem Phiếu PDF
                    </button>
                </a>
                """, unsafe_allow_html=True)
                
    elif sub_menu_tinh_toan == "Tính điện trở – kháng – trở kháng":
        st.header("➗ Tính điện trở – kháng – trở kháng")
        st.markdown("""
        **Mục đích:** Tính toán các thông số cơ bản của mạch điện xoay chiều.
        
        **Công thức:**
        - **Điện trở (R):** $R = \frac{\rho \cdot L}{A}$
        - **Điện cảm (L):** $L = 2 \cdot 10^{-4} \cdot L_{m} \cdot [\ln(\frac{D}{r}) + \mu_{r} \cdot \frac{1}{4}]$
        - **Điện kháng (X):** $X = 2 \cdot \pi \cdot f \cdot L$
        - **Điện dung (C):** $C = \frac{1}{2 \cdot \ln(D/r)}$
        - **Điện dung kháng (Xc):** $X_c = \frac{1}{2 \cdot \pi \cdot f \cdot C}$
        - **Trở kháng (Z):** $Z = \sqrt{R^2 + (X_L - X_C)^2}$ (cho mạch RLC)
        
        **Trong đó:**
        - \( R \): Điện trở (Ω)
        - \( \rho \): Điện trở suất vật liệu ($Ω \cdot m$)
        - \( L \): Chiều dài dây (m)
        - \( A \): Tiết diện dây dẫn ($mm^2$)
        - \( X_L \): Điện kháng cuộn dây (Ω)
        - \( X_C \): Dung kháng tụ điện (Ω)
        - \( Z \): Trở kháng (Ω)
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

        st.subheader("Tính Trở kháng Z")
        col1, col2 = st.columns(2)
        with col1:
            R_z = st.number_input("Điện trở R (Ω):", min_value=0.0, key="R_z")
            Xl_z = st.number_input("Điện kháng Xl (Ω):", min_value=0.0, key="Xl_z")
        with col2:
            Xc_z = st.number_input("Dung kháng Xc (Ω):", min_value=0.0, key="Xc_z")

        if st.button("Tính Trở kháng Z", key="btn_calc_z"):
            Z_result = math.sqrt(R_z**2 + (Xl_z - Xc_z)**2)
            
            st.markdown("---")
            st.subheader("Kết quả:")
            st.info(f"Trở kháng Z = **{Z_result:.2f}** Ω")
            
            # Tạo thông tin cho PDF
            customer_info = {
                "name": customer_name_z,
                "address": customer_address_z,
                "phone": customer_phone_z
            }
            calculator_info = {
                "name": calculator_name_z,
                "title": calculator_title_z,
                "phone": calculator_phone_z
            }
            input_params = {
                "Điện trở R": f"{R_z} Ω",
                "Điện kháng Xl": f"{Xl_z} Ω",
                "Dung kháng Xc": f"{Xc_z} Ω"
            }
            output_results = {
                "Trở kháng Z": f"{Z_result:.2f} Ω"
            }
            formula_latex = r"Z = \sqrt{R^2 + (X_L - X_C)^2}"
            formula_explanation = "Công thức tính trở kháng tổng hợp của một mạch RLC nối tiếp."
            
            pdf_bytes = create_pdf("ĐIỆN TRỞ – KHÁNG – TRỞ KHÁNG", formula_latex, formula_explanation, input_params, output_results, calculator_info, customer_info)
            st.session_state['pdf_bytes_z'] = pdf_bytes
            st.session_state['pdf_filename_z'] = f"Phieu_tinh_Z_{datetime.now().strftime('%Y%m%d')}.pdf"
            
        if 'pdf_bytes_z' in st.session_state and st.session_state['pdf_bytes_z']:
            st.markdown("---")
            col_pdf1, col_pdf2 = st.columns(2)
            with col_pdf1:
                st.download_button(label="Xuất PDF", data=st.session_state['pdf_bytes_z'], file_name=st.session_state['pdf_filename_z'], mime="application/pdf", key="download_z_pdf")
            with col_pdf2:
                pdf_base64_z = base64.b64encode(st.session_state['pdf_bytes_z']).decode('utf-8')
                st.markdown(f"""
                <a href="data:application/pdf;base64,{pdf_base64_z}" target="_blank">
                    <button style="background-color: #f0f2f6; border: 1px solid #d3d3d3; color: #333; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px; cursor: pointer;">
                        Xem Phiếu PDF
                    </button>
                </a>
                """, unsafe_allow_html=True)

    elif sub_menu_tinh_toan == "Tính tổn thất công suất trên dây":
        st.header("💡 Tính tổn thất công suất")
        st.markdown("""
        **Mục đích:** Tính toán phần công suất bị tổn thất trên đường dây do điện trở của dây dẫn.
        
        **Công thức:**
        - **Đối với 1 pha:** $ΔP = 2 \cdot I^2 \cdot R$ (kW)
        - **Đối với 3 pha:** $ΔP = 3 \cdot I^2 \cdot R$ (kW)
        
        **Trong đó:**
        - \( ΔP \): Tổn thất công suất trên đường dây (kW)
        - \( I \): Dòng điện (A)
        - \( R \): Điện trở của toàn bộ đường dây (Ω)
        
        **Lưu ý:** Điện trở của đường dây $R = \rho \cdot \frac{L}{S}$ với $\rho$ là điện trở suất ($Ω \cdot mm^2/m$), $L$ là chiều dài (m), $S$ là tiết diện ($mm^2$).
        """, unsafe_allow_html=True)
        
        st.subheader("Thông tin Người tính toán")
        calculator_name_ttcs = st.text_input("Họ và tên:", value="Hà Thị Lê", key="calc_name_ttcs")
        calculator_title_ttcs = st.text_input("Chức danh:", value="Tổ trưởng tổ KDDV", key="calc_title_ttcs")
        calculator_phone_ttcs = st.text_input("Số điện thoại:", value="0978578777", key="calc_phone_ttcs")

        st.subheader("Thông tin Khách hàng")
        customer_name_ttcs = st.text_input("Tên khách hàng:", value="Phạm Hồng Long", key="cust_name_ttcs")
        customer_address_ttcs = st.text_input("Địa chỉ:", value="xã Định Hóa, tỉnh Thái Nguyên", key="cust_address_ttcs")
        customer_phone_ttcs = st.text_input("Số điện thoại khách hàng:", value="0968552888", key="cust_phone_ttcs")

        current_date_ttcs = datetime.now().strftime("Ngày %d tháng %m năm %Y")
        st.markdown(f"**Thời gian lập phiếu:** {current_date_ttcs}")
        
        col1, col2 = st.columns(2)
        with col1:
            pha_ttcs = st.radio("Loại điện:", ["1 pha", "3 pha"], key="pha_ttcs")
            I_ttcs = st.number_input("Dòng điện I (A):", min_value=0.0, key="I_ttcs")
        with col2:
            R_ttcs = st.number_input("Điện trở R toàn bộ dây (Ω):", min_value=0.0, key="R_ttcs")

        if st.button("Tính tổn thất công suất", key="btn_calc_ttcs"):
            delta_P_result = 0.0
            if pha_ttcs == "1 pha":
                delta_P_result = 2 * (I_ttcs**2) * R_ttcs / 1000
            elif pha_ttcs == "3 pha":
                delta_P_result = 3 * (I_ttcs**2) * R_ttcs / 1000

            st.markdown("---")
            st.subheader("Kết quả:")
            st.info(f"Tổn thất công suất ΔP = **{delta_P_result:.2f}** kW")
            
            # Tạo thông tin cho PDF
            customer_info = {
                "name": customer_name_ttcs,
                "address": customer_address_ttcs,
                "phone": customer_phone_ttcs
            }
            calculator_info = {
                "name": calculator_name_ttcs,
                "title": calculator_title_ttcs,
                "phone": calculator_phone_ttcs
            }
            input_params = {
                "Loại điện": pha_ttcs,
                "Dòng điện I": f"{I_ttcs} A",
                "Điện trở R": f"{R_ttcs} Ω"
            }
            output_results = {
                "Tổn thất công suất ΔP": f"{delta_P_result:.2f} kW"
            }
            formula_latex = r"\Delta P = 2 \cdot I^2 \cdot R \quad (1 \text{ pha}); \quad \Delta P = 3 \cdot I^2 \cdot R \quad (3 \text{ pha})"
            formula_explanation = "Công thức tính tổn thất công suất trên đường dây do điện trở của dây dẫn."
            
            pdf_bytes = create_pdf("TỔN THẤT CÔNG SUẤT TRÊN DÂY", formula_latex, formula_explanation, input_params, output_results, calculator_info, customer_info)
            st.session_state['pdf_bytes_ttcs'] = pdf_bytes
            st.session_state['pdf_filename_ttcs'] = f"Phieu_tinh_ton_that_CS_{datetime.now().strftime('%Y%m%d')}.pdf"

        if 'pdf_bytes_ttcs' in st.session_state and st.session_state['pdf_bytes_ttcs']:
            st.markdown("---")
            col_pdf1, col_pdf2 = st.columns(2)
            with col_pdf1:
                st.download_button(label="Xuất PDF", data=st.session_state['pdf_bytes_ttcs'], file_name=st.session_state['pdf_filename_ttcs'], mime="application/pdf", key="download_ttcs_pdf")
            with col_pdf2:
                pdf_base64_ttcs = base64.b64encode(st.session_state['pdf_bytes_ttcs']).decode('utf-8')
                st.markdown(f"""
                <a href="data:application/pdf;base64,{pdf_base64_ttcs}" target="_blank">
                    <button style="background-color: #f0f2f6; border: 1px solid #d3d3d3; color: #333; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px; cursor: pointer;">
                        Xem Phiếu PDF
                    </button>
                </a>
                """, unsafe_allow_html=True)

    elif sub_menu_tinh_toan == "Tính công suất cosφ":
        st.header("📈 Tính công suất cosφ")
        st.markdown("""
        **Mục đích:** Hỗ trợ tính toán hệ số công suất của một tải dựa trên công suất tác dụng và công suất biểu kiến.
        
        **Công thức:**
        - $\cos\varphi = \frac{P}{S}$
        
        **Trong đó:**
        - \( \cos\varphi \): Hệ số công suất
        - \( P \): Công suất tác dụng (kW)
        - \( S \): Công suất biểu kiến (kVA)
        """, unsafe_allow_html=True)
        
        st.subheader("Thông tin Người tính toán")
        calculator_name_cosphi = st.text_input("Họ và tên:", value="Hà Thị Lê", key="calc_name_cosphi")
        calculator_title_cosphi = st.text_input("Chức danh:", value="Tổ trưởng tổ KDDV", key="calc_title_cosphi")
        calculator_phone_cosphi = st.text_input("Số điện thoại:", value="0978578777", key="calc_phone_cosphi")

        st.subheader("Thông tin Khách hàng")
        customer_name_cosphi = st.text_input("Tên khách hàng:", value="Phạm Hồng Long", key="cust_name_cosphi")
        customer_address_cosphi = st.text_input("Địa chỉ:", value="xã Định Hóa, tỉnh Thái Nguyên", key="cust_address_cosphi")
        customer_phone_cosphi = st.text_input("Số điện thoại khách hàng:", value="0968552888", key="cust_phone_cosphi")

        current_date_cosphi = datetime.now().strftime("Ngày %d tháng %m năm %Y")
        st.markdown(f"**Thời gian lập phiếu:** {current_date_cosphi}")
        
        col1, col2 = st.columns(2)
        with col1:
            P_cosphi = st.number_input("Công suất tác dụng P (kW):", min_value=0.0, key="P_cosphi")
        with col2:
            S_cosphi = st.number_input("Công suất biểu kiến S (kVA):", min_value=0.0, key="S_cosphi")

        if st.button("Tính cosφ", key="btn_calc_cosphi"):
            cos_phi_result = 0.0
            if S_cosphi != 0:
                cos_phi_result = P_cosphi / S_cosphi
            
            st.markdown("---")
            st.subheader("Kết quả:")
            st.info(f"Hệ số công suất cosφ = **{cos_phi_result:.2f}**")
            
            # Tạo thông tin cho PDF
            customer_info = {
                "name": customer_name_cosphi,
                "address": customer_address_cosphi,
                "phone": customer_phone_cosphi
            }
            calculator_info = {
                "name": calculator_name_cosphi,
                "title": calculator_title_cosphi,
                "phone": calculator_phone_cosphi
            }
            input_params = {
                "Công suất tác dụng P": f"{P_cosphi} kW",
                "Công suất biểu kiến S": f"{S_cosphi} kVA"
            }
            output_results = {
                "Hệ số công suất cosφ": f"{cos_phi_result:.2f}"
            }
            formula_latex = r"\cos\varphi = \frac{P}{S}"
            formula_explanation = "Công thức tính hệ số công suất dựa trên công suất tác dụng và công suất biểu kiến."
            
            pdf_bytes = create_pdf("HỆ SỐ CÔNG SUẤT COSφ", formula_latex, formula_explanation, input_params, output_results, calculator_info, customer_info)
            st.session_state['pdf_bytes_cosphi'] = pdf_bytes
            st.session_state['pdf_filename_cosphi'] = f"Phieu_tinh_cosφ_{datetime.now().strftime('%Y%m%d')}.pdf"

        if 'pdf_bytes_cosphi' in st.session_state and st.session_state['pdf_bytes_cosphi']:
            st.markdown("---")
            col_pdf1, col_pdf2 = st.columns(2)
            with col_pdf1:
                st.download_button(label="Xuất PDF", data=st.session_state['pdf_bytes_cosphi'], file_name=st.session_state['pdf_filename_cosphi'], mime="application/pdf", key="download_cosphi_pdf")
            with col_pdf2:
                pdf_base64_cosphi = base64.b64encode(st.session_state['pdf_bytes_cosphi']).decode('utf-8')
                st.markdown(f"""
                <a href="data:application/pdf;base64,{pdf_base64_cosphi}" target="_blank">
                    <button style="background-color: #f0f2f6; border: 1px solid #d3d3d3; color: #333; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px; cursor: pointer;">
                        Xem Phiếu PDF
                    </button>
                </a>
                """, unsafe_allow_html=True)
    
    elif sub_menu_tinh_toan == "Chọn thiết bị bảo vệ":
        st.header("🛡️ Chọn thiết bị bảo vệ")
        st.markdown("""
        **Mục đích:** Lựa chọn aptomat (CB) phù hợp với dòng điện tải, đảm bảo an toàn cho hệ thống điện.
        """, unsafe_allow_html=True)
        
        st.subheader("Thông tin Người tính toán")
        calculator_name_cb = st.text_input("Họ và tên:", value="Hà Thị Lê", key="calc_name_cb")
        calculator_title_cb = st.text_input("Chức danh:", value="Tổ trưởng tổ KDDV", key="calc_title_cb")
        calculator_phone_cb = st.text_input("Số điện thoại:", value="0978578777", key="calc_phone_cb")

        st.subheader("Thông tin Khách hàng")
        customer_name_cb = st.text_input("Tên khách hàng:", value="Phạm Hồng Long", key="cust_name_cb")
        customer_address_cb = st.text_input("Địa chỉ:", value="xã Định Hóa, tỉnh Thái Nguyên", key="cust_address_cb")
        customer_phone_cb = st.text_input("Số điện thoại khách hàng:", value="0968552888", key="cust_phone_cb")

        current_date_cb = datetime.now().strftime("Ngày %d tháng %m năm %Y")
        st.markdown(f"**Thời gian lập phiếu:** {current_date_cb}")
        
        st.subheader("Lựa chọn Aptomat (CB) theo dòng điện")
        
        col1, col2 = st.columns(2)
        with col1:
            I_cb = st.number_input("Dòng điện tải I (A):", min_value=0.0, key="I_cb")
        
        # Bảng các dòng điện định mức của CB
        cb_ratings = [1, 2, 3, 4, 6, 10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630]
        
        if st.button("Chọn CB", key="btn_calc_cb"):
            selected_cb = "Không tìm thấy"
            for rating in cb_ratings:
                if I_cb <= rating:
                    selected_cb = rating
                    break
            
            st.markdown("---")
            st.subheader("Kết quả:")
            if selected_cb != "Không tìm thấy":
                st.info(f"Dòng điện định mức CB phù hợp là **{selected_cb} A**")
            else:
                st.warning(f"⚠️ Không tìm thấy CB tiêu chuẩn nào phù hợp cho dòng điện **{I_cb} A**. Vui lòng kiểm tra lại dòng điện tải hoặc chọn CB có dòng điện định mức lớn hơn giá trị tiêu chuẩn cao nhất.")
            
            # Tạo thông tin cho PDF
            customer_info = {
                "name": customer_name_cb,
                "address": customer_address_cb,
                "phone": customer_phone_cb
            }
            calculator_info = {
                "name": calculator_name_cb,
                "title": calculator_title_cb,
                "phone": calculator_phone_cb
            }
            input_params = {
                "Dòng điện tải I": f"{I_cb} A"
            }
            output_results = {
                "Dòng điện định mức CB phù hợp": f"{selected_cb} A"
            }
            formula_latex = r"\text{Tra bảng dòng điện định mức của CB}"
            formula_explanation = "Lựa chọn aptomat phù hợp dựa trên dòng điện tải thực tế. Chọn CB có dòng định mức gần nhất và lớn hơn dòng tải."
            
            pdf_bytes = create_pdf("LỰA CHỌN THIẾT BỊ BẢO VỆ", formula_latex, formula_explanation, input_params, output_results, calculator_info, customer_info)
            st.session_state['pdf_bytes_cb'] = pdf_bytes
            st.session_state['pdf_filename_cb'] = f"Phieu_chon_CB_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        if 'pdf_bytes_cb' in st.session_state and st.session_state['pdf_bytes_cb']:
            st.markdown("---")
            col_pdf1, col_pdf2 = st.columns(2)
            with col_pdf1:
                st.download_button(label="Xuất PDF", data=st.session_state['pdf_bytes_cb'], file_name=st.session_state['pdf_filename_cb'], mime="application/pdf", key="download_cb_pdf")
            with col_pdf2:
                pdf_base64_cb = base64.b64encode(st.session_state['pdf_bytes_cb']).decode('utf-8')
                st.markdown(f"""
                <a href="data:application/pdf;base64,{pdf_base64_cb}" target="_blank">
                    <button style="background-color: #f0f2f6; border: 1px solid #d3d3d3; color: #333; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px; cursor: pointer;">
                        Xem Phiếu PDF
                    </button>
                </a>
                """, unsafe_allow_html=True)
    
    else:
        st.warning("⚠️ Chức năng này chưa được hỗ trợ.")

elif main_menu == "Chuyển đổi đơn vị":
    # Menu con cho các chức năng chuyển đổi đơn vị
    sub_menu_chuyen_doi = st.sidebar.selectbox("Chọn loại chuyển đổi:", [
        "kW <-> kVA",
        "kW <-> HP",
        "kW <-> BTU"
    ])

    # Hiển thị nội dung dựa trên lựa chọn menu con
    if sub_menu_chuyen_doi == "kW <-> kVA":
        st.header("🔄 Chuyển đổi kW sang kVA và ngược lại")
        st.markdown("""
        **Công thức:**
        - \( S = \frac{P}{\cos\varphi} \)
        - \( P = S \cdot \cos\varphi \)
        
        **Trong đó:**
        - \( S \): Công suất biểu kiến (kVA)
        - \( P \): Công suất tác dụng (kW)
        - \( \cos\varphi \): Hệ số công suất
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            P_kVA = st.number_input("Nhập Công suất P (kW):", min_value=0.0)
            cos_phi_kVA = st.slider("Hệ số cosφ:", 0.1, 1.0, 0.8)
            if st.button("Chuyển đổi kW -> kVA"):
                if cos_phi_kVA > 0:
                    S_result = P_kVA / cos_phi_kVA
                    st.success(f"Kết quả: **{P_kVA} kW = {S_result:.2f} kVA**")
                else:
                    st.error("Lỗi: Hệ số cosφ phải lớn hơn 0.")
        with col2:
            S_kW = st.number_input("Nhập Công suất S (kVA):", min_value=0.0)
            cos_phi_kW = st.slider("Hệ số cosφ:", 0.1, 1.0, 0.8, key="cos_phi_kw")
            if st.button("Chuyển đổi kVA -> kW"):
                P_result = S_kW * cos_phi_kW
                st.success(f"Kết quả: **{S_kW} kVA = {P_result:.2f} kW**")

    elif sub_menu_chuyen_doi == "kW <-> HP":
        st.header("🔄 Chuyển đổi kW sang HP và ngược lại")
        st.markdown("""
        **Quy đổi:**
        - **1 kW = 1.34102 HP**
        - **1 HP = 0.7457 kW**
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            P_HP = st.number_input("Nhập Công suất P (kW):", min_value=0.0)
            if st.button("Chuyển đổi kW -> HP"):
                HP_result = P_HP * 1.34102
                st.success(f"Kết quả: **{P_HP} kW = {HP_result:.2f} HP**")
        with col2:
            HP_kW = st.number_input("Nhập Công suất HP (HP):", min_value=0.0)
            if st.button("Chuyển đổi HP -> kW"):
                kW_result = HP_kW * 0.7457
                st.success(f"Kết quả: **{HP_kW} HP = {kW_result:.2f} kW**")

    elif sub_menu_chuyen_doi == "kW <-> BTU":
        st.header("🔄 Chuyển đổi kW sang BTU/h và ngược lại")
        st.markdown("""
        **Quy đổi:**
        - **1 kW = 3412.14 BTU/h**
        - **1 BTU/h = 0.000293 kW**
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            P_BTU = st.number_input("Nhập Công suất P (kW):", min_value=0.0)
            if st.button("Chuyển đổi kW -> BTU/h"):
                BTU_result = P_BTU * 3412.14
                st.success(f"Kết quả: **{P_BTU} kW = {BTU_result:.2f} BTU/h**")
        with col2:
            BTU_kW = st.number_input("Nhập Công suất BTU/h:", min_value=0.0)
            if st.button("Chuyển đổi BTU/h -> kW"):
                kW_result = BTU_kW * 0.000293
                st.success(f"Kết quả: **{BTU_kW} BTU/h = {kW_result:.2f} kW**")

elif main_menu == "Công thức điện":
    st.header("📚 Các công thức tính toán điện")
    st.markdown("""
    Ứng dụng này cung cấp các công cụ tính toán dựa trên các công thức phổ biến sau:
    
    ---
    ### Công thức tính dòng điện (I)
    
    - **Một pha:** $I = \frac{P}{U \cdot \cos\varphi}$
    - **Ba pha:** $I = \frac{P}{\sqrt{3} \cdot U \cdot \cos\varphi}$
    
    ---
    ### Công thức tính công suất (P)
    
    - **Một pha:** $P = U \cdot I \cdot \cos\varphi$
    - **Ba pha:** $P = \sqrt{3} \cdot U \cdot I \cdot \cos\varphi$
    
    ---
    ### Công thức tính trở kháng (Z)
    - $Z = \sqrt{R^2 + (X_L - X_C)^2}$
    
    ---
    ### Công thức tính sụt áp (ΔU)
    - **Một pha:** $ΔU = 2 \cdot I \cdot (R_0 \cdot L \cdot \cos\varphi + X_0 \cdot L \cdot \sin\varphi)$
    - **Ba pha:** $ΔU = \sqrt{3} \cdot I \cdot (R_0 \cdot L \cdot \cos\varphi + X_0 \cdot L \cdot \sin\varphi)$
    
    ---
    ### Công thức tính tổn thất công suất (ΔP)
    - **Một pha:** $ΔP = 2 \cdot I^2 \cdot R$
    - **Ba pha:** $ΔP = 3 \cdot I^2 \cdot R$
    """, unsafe_allow_html=True)
    
elif main_menu == "📋 BẢNG LIỆT KÊ CÔNG SUẤT CÁC THIẾT BỊ SỬ DỤNG ĐIỆN":
    st.subheader("BẢNG LIỆT KÊ CÔNG SUẤT CÁC THIẾT BỊ SỬ DỤNG ĐIỆN")

    # Nhập thông tin khách hàng
    don_vi = st.text_input("Đơn vị (khách hàng) sử dụng điện")
    dia_chi = st.text_input("Địa chỉ")
    dia_diem = st.text_input("Địa điểm sử dụng điện")
    so_dien_thoai = st.text_input("Số điện thoại")

    # Khởi tạo session state cho bảng thiết bị
    if "table_data" not in st.session_state:
        st.session_state.table_data = []

    # Form nhập thiết bị
    with st.form("add_device_form"):
        col1, col2 = st.columns([2,1])
        with col1:
            ten_tb = st.text_input("Tên thiết bị")
        with col2:
            so_luong = st.number_input("Số lượng", min_value=1, value=1)

        cong_suat = st.text_input("Công suất (W/BTU/HP...)")
        tg_ngay = st.number_input("Thời gian sử dụng (giờ/ngày)", min_value=0.0, value=0.0)
        tg_thang = st.number_input("Thời gian sử dụng (giờ/tháng)", min_value=0.0, value=0.0)
        tg_nam = st.number_input("Thời gian sử dụng (giờ/năm)", min_value=0.0, value=0.0)

        submitted = st.form_submit_button("➕ Thêm thiết bị")
        if submitted:
            st.session_state.table_data.append({
                "Tên thiết bị": ten_tb,
                "Số lượng": so_luong,
                "Công suất": cong_suat,
                "TG/ngày": tg_ngay,
                "TG/tháng": tg_thang,
                "TG/năm": tg_nam
            })

    if st.button("� Cập nhật bảng"):
        st.success("Bảng đã được cập nhật!")

    # Hiển thị bảng nếu có dữ liệu
    if st.session_state.table_data:
        import pandas as pd
        df = pd.DataFrame(st.session_state.table_data)
        # Thêm dòng tổng cộng
        tong = {
            "Tên thiết bị": "TỔNG CỘNG",
            "Số lượng": df["Số lượng"].sum(),
            "Công suất": "",
            "TG/ngày": df["TG/ngày"].sum(),
            "TG/tháng": df["TG/tháng"].sum(),
            "TG/năm": df["TG/năm"].sum()
        }
        df = pd.concat([df, pd.DataFrame([tong])], ignore_index=True)
        st.dataframe(df, use_container_width=True)

        # Xuất Excel
        import io
        import pandas as pd
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="BangCongSuat")
        st.download_button("💾 Xuất Excel", data=output.getvalue(),
                             file_name="BangCongSuat.xlsx",
                             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        # Xuất PDF
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet

        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()

        # Tiêu đề
        elements.append(Paragraph("<para align=center><b>BẢNG LIỆT KÊ CÔNG SUẤT CÁC THIẾT BỊ SỬ DỤNG ĐIỆN</b></para>", styles["Normal"]))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"Đơn vị (khách hàng): {don_vi}", styles["Normal"]))
        elements.append(Paragraph(f"Địa chỉ: {dia_chi}", styles["Normal"]))
        elements.append(Paragraph(f"Địa điểm: {dia_diem}", styles["Normal"]))
        elements.append(Paragraph(f"Số điện thoại: {so_dien_thoai}", styles["Normal"]))
        elements.append(Spacer(1, 12))

        # Bảng PDF
        table_data = [df.columns.to_list()] + df.astype(str).values.tolist()
        t = Table(table_data, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.grey),
            ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
            ("ALIGN", (0,0), (-1,-1), "CENTER"),
            ("GRID", (0,0), (-1,-1), 1, colors.black),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ]))
        elements.append(t)
        doc.build(elements)
        st.download_button("📄 Xuất PDF", data=pdf_buffer.getvalue(),
                             file_name="BangCongSuat.pdf", mime="application/pdf")
else:
    st.warning("⚠️ Lựa chọn không hợp lệ.")
�