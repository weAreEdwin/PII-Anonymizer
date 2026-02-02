"""
Export Service - Generate exports in different formats
"""
from io import BytesIO
from typing import Dict, Any
from datetime import datetime
import json

# For PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# For DOCX generation
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH


class ExportService:
    """Service for exporting anonymized documents and mappings"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
    
    async def export_as_pdf(
        self,
        anonymized_text: str,
        filename: str,
        session_id: str,
        metadata: Dict[str, Any] = None
    ) -> BytesIO:
        """
        Export anonymized document as PDF
        
        Args:
            anonymized_text: The anonymized document text
            filename: Original filename
            session_id: Session identifier
            metadata: Additional metadata to include
            
        Returns:
            BytesIO: PDF file in memory
        """
        buffer = BytesIO()
        
        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Add title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor='darkblue',
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        elements.append(Paragraph("Anonymized Document", title_style))
        elements.append(Spacer(1, 12))
        
        # Add metadata
        if metadata:
            meta_style = self.styles['Normal']
            elements.append(Paragraph(f"<b>Original Filename:</b> {filename}", meta_style))
            elements.append(Paragraph(f"<b>Session ID:</b> {session_id}", meta_style))
            elements.append(Paragraph(
                f"<b>Export Date:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
                meta_style
            ))
            if metadata.get('pii_count'):
                elements.append(Paragraph(
                    f"<b>PII Items Detected:</b> {metadata['pii_count']}",
                    meta_style
                ))
            elements.append(Spacer(1, 20))
        
        # Add separator
        elements.append(Paragraph("<hr/>", self.styles['Normal']))
        elements.append(Spacer(1, 20))
        
        # Add anonymized content
        content_style = ParagraphStyle(
            'Content',
            parent=self.styles['Normal'],
            fontSize=11,
            leading=14,
            spaceAfter=10
        )
        
        # Split text into paragraphs and add each
        paragraphs = anonymized_text.split('\n')
        for para in paragraphs:
            if para.strip():
                # Escape XML special characters
                para = para.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                elements.append(Paragraph(para, content_style))
            else:
                elements.append(Spacer(1, 12))
        
        # Build PDF
        doc.build(elements)
        
        # Get the value of the BytesIO buffer
        buffer.seek(0)
        return buffer
    
    async def export_as_docx(
        self,
        anonymized_text: str,
        filename: str,
        session_id: str,
        metadata: Dict[str, Any] = None
    ) -> BytesIO:
        """
        Export anonymized document as DOCX
        
        Args:
            anonymized_text: The anonymized document text
            filename: Original filename
            session_id: Session identifier
            metadata: Additional metadata to include
            
        Returns:
            BytesIO: DOCX file in memory
        """
        buffer = BytesIO()
        
        # Create document
        document = Document()
        
        # Add title
        title = document.add_heading('Anonymized Document', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Add metadata
        if metadata:
            document.add_paragraph()
            meta_para = document.add_paragraph()
            meta_para.add_run('Original Filename: ').bold = True
            meta_para.add_run(filename)
            
            meta_para = document.add_paragraph()
            meta_para.add_run('Session ID: ').bold = True
            meta_para.add_run(session_id)
            
            meta_para = document.add_paragraph()
            meta_para.add_run('Export Date: ').bold = True
            meta_para.add_run(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'))
            
            if metadata.get('pii_count'):
                meta_para = document.add_paragraph()
                meta_para.add_run('PII Items Detected: ').bold = True
                meta_para.add_run(str(metadata['pii_count']))
            
            document.add_paragraph('_' * 80)
            document.add_paragraph()
        
        # Add anonymized content
        paragraphs = anonymized_text.split('\n')
        for para in paragraphs:
            if para.strip():
                p = document.add_paragraph(para)
                p.style.font.size = Pt(11)
            else:
                document.add_paragraph()
        
        # Save to buffer
        document.save(buffer)
        buffer.seek(0)
        return buffer
    
    async def export_mapping_as_json(
        self,
        pii_mappings: list,
        session_id: str,
        filename: str,
        metadata: Dict[str, Any] = None
    ) -> BytesIO:
        """
        Export PII mapping as JSON
        
        Args:
            pii_mappings: List of PII mapping dictionaries
            session_id: Session identifier
            filename: Original filename
            metadata: Additional metadata
            
        Returns:
            BytesIO: JSON file in memory
        """
        buffer = BytesIO()
        
        # Prepare export data
        export_data = {
            "session_id": session_id,
            "original_filename": filename,
            "export_timestamp": datetime.utcnow().isoformat(),
            "total_pii_detected": len(pii_mappings),
            "metadata": metadata or {},
            "pii_mappings": pii_mappings
        }
        
        # Write JSON
        json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
        buffer.write(json_str.encode('utf-8'))
        buffer.seek(0)
        
        return buffer
    
    async def export_as_txt(
        self,
        anonymized_text: str,
        filename: str,
        session_id: str,
        metadata: Dict[str, Any] = None
    ) -> BytesIO:
        """
        Export anonymized document as plain text
        
        Args:
            anonymized_text: The anonymized document text
            filename: Original filename
            session_id: Session identifier
            metadata: Additional metadata
            
        Returns:
            BytesIO: TXT file in memory
        """
        buffer = BytesIO()
        
        # Add header
        header = f"""
========================================
ANONYMIZED DOCUMENT
========================================

Original Filename: {filename}
Session ID: {session_id}
Export Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
"""
        
        if metadata and metadata.get('pii_count'):
            header += f"PII Items Detected: {metadata['pii_count']}\n"
        
        header += "\n" + "="*80 + "\n\n"
        
        # Combine header and content
        content = header + anonymized_text
        
        # Write to buffer
        buffer.write(content.encode('utf-8'))
        buffer.seek(0)
        
        return buffer
