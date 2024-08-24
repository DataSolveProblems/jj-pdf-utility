import os
from typing import List
from PyPDF2 import PdfMerger, PdfReader, PdfWriter

class PDFUtility:
    def merge_pdfs(self, pdf_files: List[str] , output_file: str):
        if not pdf_files:
            print('hit')
            raise FileNotFoundError('No PDF files found')
        
        try:
            # clear the merger object
            with PdfMerger() as self.merger:
                for pdf_file in pdf_files:
                    self.merger.append(pdf_file)

                with open(output_file, 'wb') as output_file:
                    self.merger.write(output_file)
                return True
        except Exception as e:
            raise Exception(f'Error merging PDFs: {e}')

    def split_pdf(self, pdf_file: str, output_dir: str, split_type: str = 'All', custom_pages: str = None):
        if not pdf_file:
            raise FileNotFoundError('No PDF file found')
        
        try:
            with open(pdf_file, 'rb') as file:
                pdf_reader = PdfReader(file)
                file_base_name = os.path.splitext(os.path.basename(pdf_file))[0]

                if split_type == 'All':
                    for page in range(len(pdf_reader.pages)):
                        pdf_writer = PdfWriter()
                        pdf_writer.add_page(pdf_reader.pages[page])
                        output_file = os.path.join(output_dir, f'{file_base_name}_page{page + 1}.pdf')
                        with open(output_file, 'wb') as output:
                            pdf_writer.write(output)

                elif split_type == 'Even':
                    for page in range(1, len(pdf_reader.pages), 2):
                        pdf_writer = PdfWriter()
                        pdf_writer.add_page(pdf_reader.pages[page])
                        output_file = os.path.join(output_dir, f'{file_base_name}_page{page + 1}.pdf')
                        with open(output_file, 'wb') as output:
                            pdf_writer.write(output)

                elif split_type == 'Odd':
                    for page in range(0, len(pdf_reader.pages), 2):
                        pdf_writer = PdfWriter()
                        pdf_writer.add_page(pdf_reader.pages[page])
                        output_file = os.path.join(output_dir, f'{file_base_name}_page{page + 1}.pdf')
                        with open(output_file, 'wb') as output:
                            pdf_writer.write(output)

                elif split_type == 'Custom':
                    pages = custom_pages.split(',')
                    for page_range in pages:
                        pdf_writer = PdfWriter()
                        if '-' in page_range:
                            start, end = map(int, page_range.split('-'))
                            for page in range(start, end + 1):
                                pdf_writer.add_page(pdf_reader.pages[page - 1])
                            output_file = os.path.join(output_dir, f'{file_base_name}_pages{start}-{end}.pdf')
                        else:
                            page = int(page_range)
                            pdf_writer.add_page(pdf_reader.pages[page - 1])
                            output_file = os.path.join(output_dir, f'{file_base_name}_page{page}.pdf')
                        
                        with open(output_file, 'wb') as output:
                            pdf_writer.write(output)
                return True
        except Exception as e:
            raise Exception(f'Error splitting PDF: {e}')
        
    def encrypt_pdf(self, pdf_file: str, password: str, output_file: str = None):
        if not pdf_file:
            raise FileNotFoundError('No PDF file found')
            
        try:
            with open(pdf_file, 'rb') as file:
                pdf_reader = PdfReader(file)
                pdf_writer = PdfWriter()
                for page in pdf_reader.pages:
                    pdf_writer.add_page(page)
                pdf_writer.encrypt(password)
                if not output_file:
                    output_file = os.path.splitext(pdf_file)[0] + '_encrypted.pdf'
                with open(output_file, 'wb') as output:
                    pdf_writer.write(output)
                return True
        except Exception as e:
            raise Exception(f'Error encrypting PDF: {e}')
        
    def decrypt_pdf(self, pdf_file: str, password: str):
        if not pdf_file:
            raise FileNotFoundError('No PDF file found')
        
        try:
            with open(pdf_file, 'rb') as file:
                pdf_reader = PdfReader(file)
                if pdf_reader.is_encrypted:
                    pdf_reader.decrypt(password)
                    pdf_writer = PdfWriter()
                    for page in pdf_reader.pages:
                        pdf_writer.add_page(page)
                    with open(pdf_file, 'wb') as output:
                        pdf_writer.write(output)
                    return True
                else:
                    raise Exception('PDF file is not encrypted')
        except Exception as e:
            raise Exception(f'Error decrypting PDF: {e}')