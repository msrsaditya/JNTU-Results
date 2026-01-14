import fitz
import pdfplumber
import pandas as pd
import re
import os
import sys
from datetime import datetime
INPUT_PDF_FILE = "JNTU IT.pdf"
OUTPUT_DIRECTORY = "Extraction_Output"
PHOTOS_DIRECTORY = os.path.join(OUTPUT_DIRECTORY, "Student_Photos")
OUTPUT_CSV_FILE = os.path.join(OUTPUT_DIRECTORY, "Results.csv")
if not os.path.exists(PHOTOS_DIRECTORY):
    os.makedirs(PHOTOS_DIRECTORY)
def sanitize_address_text(address_text):
    if not address_text:
        return "-"
    address_text = address_text.replace('\n', ' ').strip()
    if not address_text:
        return "-"
    address_text = re.sub(r'Valid up to\s+[A-Za-z]+\s+\d{4}', '', address_text, flags=re.IGNORECASE)
    address_text = address_text.replace("PRINCIPAL", "").strip()
    address_text = re.sub(r'\s+', ' ', address_text).strip()
    return address_text if address_text else "-"
def format_date_string(date_string):
    if not date_string:
        return "-"
    try:
        date_object = datetime.strptime(date_string, "%m/%d/%Y")
        return date_object.strftime("%d-%m-%Y")
    except ValueError:
        return "-"
def extract_student_data(pdf_source_path):
    print(f"Starting extraction for: {pdf_source_path}")
    try:
        pdf_image_doc = fitz.open(pdf_source_path)
    except Exception as e:
        print(f"Error opening PDF: {e}")
        sys.exit(1)
    extracted_records = []
    with pdfplumber.open(pdf_source_path) as pdf_text_doc:
        print(f"Processing {len(pdf_text_doc.pages)} pages...")
        for page_index, page_content in enumerate(pdf_text_doc.pages):
            raw_text = page_content.extract_text(x_tolerance=6)
            if not raw_text:
                continue
            roll_no_match = re.search(r'Roll No:\s*([A-Z0-9]+)', raw_text)
            roll_number = roll_no_match.group(1).strip() if roll_no_match else f"UNKNOWN_{page_index+1}"
            name_match = re.search(r'Phone:.*?08922-277911\s+(.*?)\s+Course:', raw_text, re.DOTALL)
            student_name = name_match.group(1).replace('\n', ' ').strip() if name_match else "-"
            course_match = re.search(r'Course:\s*(.*?)(?=\s*Blood Group|\s*DOB|\n)', raw_text, re.IGNORECASE)
            course_name = course_match.group(1).strip() if course_match else "-"
            blood_group_match = re.search(r'Blood Group:\s*(.*?)(?=\s*DOB:|$)', raw_text, re.IGNORECASE)
            blood_group = blood_group_match.group(1).strip() if blood_group_match else "-"
            if "DOB" in blood_group or not blood_group:
                blood_group = "-"
            dob_match = re.search(r'DOB:\s*(\d{1,2}/\d{1,2}/\d{4})', raw_text)
            raw_dob = dob_match.group(1).strip() if dob_match else ""
            formatted_dob = format_date_string(raw_dob)
            phone_match = re.search(r'Ph\.No\.:\s*([\d\s-]{10,})', raw_text)
            phone_number = "-"
            if phone_match:
                digits_only = re.sub(r'\D', '', phone_match.group(1))
                if len(digits_only) >= 10:
                    phone_number = digits_only
            address_match = re.search(r'PRINCIPAL\s+(.*?)\s+Ph\.No\.:', raw_text, re.DOTALL)
            raw_address = address_match.group(1) if address_match else ""
            cleaned_address = sanitize_address_text(raw_address)
            extracted_records.append({
                "Roll No": roll_number,
                "Name": student_name,
                "Course": course_name,
                "Blood Group": blood_group,
                "DOB": formatted_dob,
                "Phone": phone_number,
                "Address": cleaned_address
            })
            try:
                page_image_container = pdf_image_doc[page_index]
                image_list = page_image_container.get_images(full=True)
                if image_list:
                    best_image = None
                    max_pixel_area = 0
                    for img_info in image_list:
                        xref_id = img_info[0]
                        base_image = pdf_image_doc.extract_image(xref_id)
                        image_width = base_image["width"]
                        image_height = base_image["height"]
                        image_area = image_width * image_height
                        aspect_ratio = image_width / image_height
                        if image_area > 5000 and 0.6 < aspect_ratio < 1.5:
                            if image_area > max_pixel_area:
                                max_pixel_area = image_area
                                best_image = base_image
                    if best_image:
                        image_file_name = f"{roll_number}.{best_image['ext']}"
                        image_save_path = os.path.join(PHOTOS_DIRECTORY, image_file_name)
                        with open(image_save_path, "wb") as img_file:
                            img_file.write(best_image["image"])
            except Exception:
                pass
    return extracted_records
if __name__ == "__main__":
    student_data = extract_student_data(INPUT_PDF_FILE)
    dataframe = pd.DataFrame(student_data)
    dataframe = dataframe.fillna("-")
    dataframe.to_csv(OUTPUT_CSV_FILE, index=False)
    print("-" * 30)
    print(f"SUCCESS! Data saved to: {OUTPUT_CSV_FILE}")
