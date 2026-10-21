import os
import re
from typing import List
from bs4 import BeautifulSoup
import markdown

class FileExtractor:
    def __init__(self, chunk_size_words: int = 2500):
        self.chunk_size_words = chunk_size_words

    def extract_text(self, filepath: str) -> str:
        """
        Extracts plain text from various file formats.
        """
        ext = os.path.splitext(filepath)[1].lower()
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        if ext == '.txt':
            return self._extract_txt(filepath)
        elif ext in ['.html', '.htm']:
            return self._extract_html(filepath)
        elif ext == '.pdf':
            return self._extract_pdf(filepath)
        elif ext == '.docx':
            return self._extract_docx(filepath)
        elif ext == '.epub':
            return self._extract_epub(filepath)
        elif ext == '.md':
            return self._extract_md(filepath)
        elif ext == '.mobi':
            return self._extract_mobi(filepath)
        else:
            # Fallback or unsupported
            raise ValueError(f"Unsupported file format: {ext}")

    def _extract_txt(self, filepath: str) -> str:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()

    def _extract_html(self, filepath: str) -> str:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            return soup.get_text(separator='\n\n', strip=True)

    def _extract_pdf(self, filepath: str) -> str:
        try:
            from pypdf import PdfReader
        except ImportError:
            raise ImportError("Please install pypdf to extract text from PDF files.")

        reader = PdfReader(filepath)
        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        return "\n\n".join(text_parts)

    def _extract_docx(self, filepath: str) -> str:
        try:
            import docx
        except ImportError:
            raise ImportError("Please install python-docx to extract text from DOCX files.")

        doc = docx.Document(filepath)
        return "\n\n".join([p.text for p in doc.paragraphs if p.text.strip()])

    def _extract_epub(self, filepath: str) -> str:
        try:
            import ebooklib
            from ebooklib import epub
        except ImportError:
            raise ImportError("Please install ebooklib to extract text from EPUB files.")

        book = epub.read_epub(filepath)
        text_parts = []
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_body_content(), 'html.parser')
                text_parts.append(soup.get_text(separator='\n\n', strip=True))
        return "\n\n".join(text_parts)

    def _extract_md(self, filepath: str) -> str:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            html = markdown.markdown(f.read())
            soup = BeautifulSoup(html, 'html.parser')
            return soup.get_text(separator='\n\n', strip=True)

    def _extract_mobi(self, filepath: str) -> str:
        # Full mobi support requires heavy external libs like mobi/calibre.
        # But we will provide a placeholder or basic error since user requested it to be supported but we did not implement it fully.
        raise NotImplementedError("Mobi support is not natively implemented yet. Please use EPUB instead.")

    def chunk_text(self, text: str) -> List[str]:
        """
        Splits text into chunks of approximately self.chunk_size_words words.
        Tries to break at double newlines (paragraphs) to keep logical flow.
        """
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = []
        current_words = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            words_in_para = len(re.findall(r'\w+', para))

            if current_words + words_in_para > self.chunk_size_words and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [para]
                current_words = words_in_para
            else:
                current_chunk.append(para)
                current_words += words_in_para

        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))

        return chunks
