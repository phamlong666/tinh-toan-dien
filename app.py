# app.py – Phiên bản đầy đủ: Tính toán điện + Chuyển đổi + Bảo vệ + Công thức ngược
# Mắt Nâu – EVNNPC Điện lực Định Hóa

import streamlit as st
import math
from PIL import Image
import pandas as pd
import io
from datetime import datetime

# Import các thành phần từ ReportLab để tạo PDF
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
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

        **Mục đích:** Tính tiết diện dây dẫn phù hợp với công suất tải, chiều dài và điều kiện sụt áp cho phép.  
        Giúp chọn dây dẫn đúng kỹ thuật và đảm bảo an toàn vận hành.
        """, unsafe_allow_html=True)

        # Thêm các trường nhập liệu mới cho Người tính toán
        st.subheader("Thông tin Người tính toán")
        calculator_name = st.text_input("Họ và tên:", value="Mắt Nâu")
        calculator_title = st.text_input("Chức danh:", value="Kỹ sư điện")
        calculator_phone = st.text_input("Số điện thoại:", value="0123 456 789")

        # Thêm các trường nhập liệu mới cho Khách hàng
        st.subheader("Thông tin Khách hàng")
        customer_name = st.text_input("Tên khách hàng:", value="Điện lực Định Hóa")
        customer_address = st.text_input("Địa chỉ:", value="Thị trấn Chợ Chu, Định Hóa, Thái Nguyên")
        customer_phone = st.text_input("Số điện thoại khách hàng:", value="0987 654 321")
        
        # Lấy thời gian thực
        current_time = datetime.now().strftime("%H:%M ngày %d/%m/%Y")
        st.markdown(f"**Thời gian lập phiếu:** {current_time}")

        pha = st.radio("Loại điện:", ["1 pha", "3 pha"])
        P = st.number_input("Công suất tải (kW):", min_value=0.0)
        U = st.number_input("Điện áp danh định (V):", min_value=0.0, value=220.0)
        cos_phi = st.slider("Hệ số công suất cosφ:", 0.1, 1.0, 0.85)
        L = st.number_input("Chiều dài dây dẫn (m):", min_value=0.0)
        deltaU_percent = st.number_input("Sụt áp cho phép (%):", min_value=1.0, value=4.0)
        material = st.selectbox("Chất liệu dây dẫn:", ["Đồng", "Nhôm"])
        
        # Thêm lựa chọn phương pháp lắp đặt
        installation_method = st.radio(
            "Phương pháp lắp đặt:", 
            ["Trong không khí (25°C)", "Trong ống (25°C)"],
            help="Chọn phương pháp lắp đặt để xác định khả năng chịu tải của dây dẫn."
        )

        # Nút tính toán
        if st.button("Tính tiết diện"):
            # Tính dòng điện I
            I = P * 1000 / (U * cos_phi) if U != 0 and cos_phi != 0 else 0 # Tránh chia cho 0
            if pha == "3 pha":
                I = P * 1000 / (math.sqrt(3) * U * cos_phi) if U != 0 and cos_phi != 0 else 0
            
            # Điện trở suất
            rho = 0.0175 if material == "Đồng" else 0.028
            
            # Sụt áp cho phép (ΔU)
            deltaU = U * deltaU_percent / 100
            
            # Tính tiết diện S (dựa trên sụt áp)
            S = (2 * rho * L * I) / deltaU if deltaU != 0 else 0 # Tránh chia cho 0

            # Hiển thị dòng điện tính toán được
            st.info(f"⚡ Dòng điện tính toán được I ≈ {I:.2f} A")
            st.success(f"🔢 Tiết diện S tối thiểu theo sụt áp ≈ {S:.2f} mm²")

            # Chọn bảng khả năng chịu tải phù hợp từ dữ liệu Excel đã tải
            if material == "Đồng":
                selected_cable_data = copper_cable_data
            else: # material == "Nhôm"
                selected_cable_data = aluminum_cable_data

            # Kiểm tra nếu dữ liệu bảng tra rỗng (do lỗi đọc file Excel)
            if not selected_cable_data:
                st.error("❌ Không thể gợi ý tiết diện do không đọc được dữ liệu bảng tra từ file Excel. Vui lòng kiểm tra các lỗi đọc file Excel phía trên.")
                suggested_size = None # Đảm bảo suggested_size được gán giá trị
            else:
                # Chọn loại khả năng chịu tải dựa trên phương pháp lắp đặt
                if installation_method == "Trong không khí (25°C)":
                    current_capacities = selected_cable_data.get('in_air', {})
                else: # "Trong ống (25°C)"
                    current_capacities = selected_cable_data.get('in_conduit', {})

                if not current_capacities:
                    st.error(f"❌ Không có dữ liệu khả năng chịu tải cho phương pháp '{installation_method}' của dây {material}. Vui lòng kiểm tra lại file Excel.")
                    suggested_size = None # Đảm bảo suggested_size được gán giá trị
                else:
                    # Tìm tiết diện chuẩn nhỏ nhất thỏa mãn cả sụt áp và khả năng chịu tải
                    suggested_size = None
                    # Sắp xếp các tiết diện có sẵn để tìm ra tiết diện nhỏ nhất phù hợp
                    available_sizes = sorted(current_capacities.keys())

                    for size in available_sizes:
                        # Kiểm tra cả hai điều kiện: tiết diện đủ lớn theo sụt áp VÀ khả năng chịu tải đủ lớn theo dòng điện
                        capacity = current_capacities.get(size, 0)
                        if isinstance(capacity, (int, float)) and size >= S and capacity >= I:
                            suggested_size = size
                            break # Đã tìm thấy tiết diện nhỏ nhất phù hợp, thoát vòng lặp

                    if suggested_size:
                        st.info(f"👉 Gợi ý chọn tiết diện chuẩn thương mại CADIVI: **{suggested_size} mm²**")
                    else:
                        st.error("❌ Không có tiết diện thương mại phù hợp với các điều kiện đã nhập. Vui lòng kiểm tra lại thông số hoặc cân nhắc sử dụng dây có tiết diện lớn hơn.")

            # --- Bắt đầu phần tạo và xuất PDF ---
            if suggested_size is not None: # Chỉ tạo PDF nếu có gợi ý tiết diện hợp lệ
                # Tạo một đối tượng BytesIO để lưu PDF vào bộ nhớ
                buffer = io.BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=A4)
                styles = getSampleStyleSheet()

                # Định nghĩa style cho tiếng Việt
                # Cần đảm bảo font 'DejaVuSans' và 'DejaVuSans-Bold' đã được đăng ký
                # Nếu không có font tiếng Việt, ReportLab sẽ dùng font mặc định và có thể bị lỗi hiển thị
                try:
                    styles.add(ParagraphStyle(name='TitleStyle', fontName='DejaVuSans-Bold', fontSize=16, alignment=1, spaceAfter=14))
                    styles.add(ParagraphStyle(name='Heading2Style', fontName='DejaVuSans-Bold', fontSize=12, spaceAfter=6))
                    styles.add(ParagraphStyle(name='NormalStyle', fontName='DejaVuSans', fontSize=10, spaceAfter=6))
                    styles.add(ParagraphStyle(name='TableCellStyle', fontName='DejaVuSans', fontSize=9, alignment=1))
                    styles.add(ParagraphStyle(name='TableCellBoldStyle', fontName='DejaVuSans-Bold', fontSize=9, alignment=1))
                except KeyError:
                    st.warning("⚠️ Không tìm thấy font tiếng Việt đã đăng ký. PDF sẽ sử dụng font mặc định của ReportLab, có thể không hiển thị tiếng Việt đúng cách.")
                    styles.add(ParagraphStyle(name='TitleStyle', fontName='Helvetica-Bold', fontSize=16, alignment=1, spaceAfter=14))
                    styles.add(ParagraphStyle(name='Heading2Style', fontName='Helvetica-Bold', fontSize=12, spaceAfter=6))
                    styles.add(ParagraphStyle(name='NormalStyle', fontName='Helvetica', fontSize=10, spaceAfter=6))
                    styles.add(ParagraphStyle(name='TableCellStyle', fontName='Helvetica', fontSize=9, alignment=1))
                    styles.add(ParagraphStyle(name='TableCellBoldStyle', fontName='Helvetica-Bold', fontSize=9, alignment=1))


                story = []

                # Tiêu đề phiếu
                story.append(Paragraph("<b>PHIẾU TÍNH TOÁN LỰA CHỌN DÂY CÁP ĐIỆN</b>", styles['TitleStyle']))
                story.append(Spacer(1, 0.2 * inch))

                # Thông tin chung
                story.append(Paragraph("<b>1. THÔNG TIN CHUNG</b>", styles['Heading2Style']))
                story.append(Paragraph(f"<b>Người tính toán:</b> {calculator_name}", styles['NormalStyle']))
                story.append(Paragraph(f"<b>Chức danh:</b> {calculator_title}", styles['NormalStyle']))
                story.append(Paragraph(f"<b>Điện thoại:</b> {calculator_phone}", styles['NormalStyle']))
                story.append(Spacer(1, 0.1 * inch))
                story.append(Paragraph(f"<b>Khách hàng:</b> {customer_name}", styles['NormalStyle']))
                story.append(Paragraph(f"<b>Địa chỉ:</b> {customer_address}", styles['NormalStyle']))
                story.append(Paragraph(f"<b>Điện thoại khách hàng:</b> {customer_phone}", styles['NormalStyle']))
                story.append(Paragraph(f"<b>Thời gian lập phiếu:</b> {current_time}", styles['NormalStyle']))
                story.append(Spacer(1, 0.2 * inch))

                # Thông số đầu vào
                story.append(Paragraph("<b>2. THÔNG SỐ ĐẦU VÀO</b>", styles['Heading2Style']))
                input_data = [
                    ["Loại điện:", pha],
                    ["Công suất tải (P):", f"{P} kW"],
                    ["Điện áp danh định (U):", f"{U} V"],
                    ["Hệ số công suất (cosφ):", cos_phi],
                    ["Chiều dài dây dẫn (L):", f"{L} m"],
                    ["Sụt áp cho phép (ΔU%):", f"{deltaU_percent} %"],
                    ["Chất liệu dây dẫn:", material],
                    ["Phương pháp lắp đặt:", installation_method]
                ]
                input_table = Table(input_data, colWidths=[2.5*inch, 3*inch])
                input_table.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
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
                story.append(Paragraph("<b>3. KẾT QUẢ TÍNH TOÁN VÀ GỢI Ý</b>", styles['Heading2Style']))
                output_data = [
                    ["Dòng điện tính toán (I):", f"{I:.2f} A"],
                    ["Tiết diện S tối thiểu theo sụt áp:", f"{S:.2f} mm²"],
                    ["Gợi ý tiết diện chuẩn CADIVI:", f"{suggested_size} mm²"]
                ]
                output_table = Table(output_data, colWidths=[3*inch, 2.5*inch])
                output_table.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                    ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                    ('FONTNAME', (0,0), (0,-1), 'DejaVuSans-Bold' if 'DejaVuSans-Bold' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold'),
                    ('FONTNAME', (1,0), (1,-1), 'DejaVuSans' if 'DejaVuSans' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'),
                    ('FONTSIZE', (0,0), (-1,-1), 10),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                    ('TOPPADDING', (0,0), (-1,-1), 6),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
                ]))
                story.append(output_table)
                story.append(Spacer(1, 0.2 * inch))
                
                # Chèn hình ảnh bảng tra vào PDF
                story.append(Paragraph("<b>4. BẢNG TRA THAM KHẢO</b>", styles['Heading2Style']))
                
                # Chèn bảng tra dây Đồng
                try:
                    img_copper_path = "cadivi_cho bảng tra dây đồng.jpg"
                    img_copper = Image.open(img_copper_path)
                    # Resize ảnh để vừa trang A4 (khoảng 6 inch chiều rộng)
                    aspect = img_copper.width / float(img_copper.height)
                    img_width = 6 * inch
                    img_height = img_width / aspect
                    story.append(Paragraph("<b>Bảng tra dây dẫn CADIVI (Dây Đồng):</b>", styles['NormalStyle']))
                    story.append(Image(img_copper_path, width=img_width, height=img_height))
                    story.append(Spacer(1, 0.1 * inch))
                except FileNotFoundError:
                    story.append(Paragraph(f"<i>Không tìm thấy ảnh: {img_copper_path}</i>", styles['NormalStyle']))
                except Exception as e:
                    story.append(Paragraph(f"<i>Lỗi tải ảnh dây đồng: {e}</i>", styles['NormalStyle']))

                # Chèn bảng tra dây Nhôm
                try:
                    img_aluminum_path = "cadivi_cho bảng tra dây nhôm.jpg"
                    img_aluminum = Image.open(img_aluminum_path)
                    # Resize ảnh để vừa trang A4 (khoảng 6 inch chiều rộng)
                    aspect = img_aluminum.width / float(img_aluminum.height)
                    img_width = 6 * inch
                    img_height = img_width / aspect
                    story.append(Paragraph("<b>Bảng tra dây dẫn CADIVI (Dây Nhôm):</b>", styles['NormalStyle']))
                    story.append(Image(img_aluminum_path, width=img_width, height=img_height))
                    story.append(Spacer(1, 0.1 * inch))
                except FileNotFoundError:
                    story.append(Paragraph(f"<i>Không tìm thấy ảnh: {img_aluminum_path}</i>", styles['NormalStyle']))
                except Exception as e:
                    story.append(Paragraph(f"<i>Lỗi tải ảnh dây nhôm: {e}</i>", styles['NormalStyle']))


                doc.build(story)
                pdf_bytes = buffer.getvalue()
                buffer.close()

                st.download_button(
                    label="Xuất PDF",
                    data=pdf_bytes,
                    file_name=f"Phieu_tinh_toan_day_cap_dien_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    help="Tải về phiếu tính toán dưới dạng PDF"
                )
            # --- Kết thúc phần tạo và xuất PDF ---

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
