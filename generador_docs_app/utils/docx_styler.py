
import re
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL, WD_ROW_HEIGHT_RULE
from docx.oxml.shared import OxmlElement, qn
from docx.table import Table
from docx.text.paragraph import Paragraph

class DocxStyler:
    def __init__(self, config):
        """
        config: dict with keys from document_styles table.
        We will try to use config values for Colors/Fonts where possible,
        but fallback to script defaults for structure.
        """
        self.config = config

        # Map config colors to constants or default
        self.HEADER_FILL = self.config.get('table_header_fill') or self.config.get('header_fill', 'E2E8F0')
        if not self.HEADER_FILL: self.HEADER_FILL = 'E2E8F0'
        self.HEADER_FILL = self.HEADER_FILL.strip().lstrip('#').upper()

        self.CODE_FILL = self.config.get('header_code_fill', '0F4C81')
        if not self.CODE_FILL: self.CODE_FILL = '0F4C81'
        self.CODE_FILL = self.CODE_FILL.strip().lstrip('#').upper()

        self.BODY_FONT = self.config.get('body_font_family', 'Calibri')
        self.TITLE_FONT = self.config.get('title_font_family', 'Calibri') 
        # Note: User request implies "Formata Light" and "Formata Medium" are desired.
        # If DB has others, we honor DB but structure remains.

    # =========================
    # Helpers generales
    # =========================
    def cm_to_twips(self, cm: float) -> int:
        return int(round(cm * 567))

    def _length_cm(self, length):
        try:
            return length.cm
        except Exception:
            return float(length) / 567.0

    def get_page_setup(self, doc):
        sec = doc.sections[0]
        w_cm = self._length_cm(sec.page_width)
        h_cm = self._length_cm(sec.page_height)
        orient_h = w_cm > h_cm
        long_side = max(w_cm, h_cm)
        if abs(long_side - 27.94) <= 0.3:
            size = "letter"
        elif abs(long_side - 35.56) <= 0.3:
            size = "legal"
        else:
            size = "other"
        return orient_h, size

    def _hex_to_rgb(self, hex_str):
        if not hex_str: return (0, 0, 0)
        hex_str = hex_str.strip().lstrip('#')
        if len(hex_str) != 6: return (0, 0, 0)
        return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
    
    # =========================
    # SISTEMA DE SOMBREADO BLINDADO (CRÍTICO)
    # =========================
    def shade_cell_robust(self, cell, hex_fill="D9D9D9"):
        """
        Sistema de sombreado ULTRA-ROBUSTO que elimina TODOS los elementos
        que pueden causar que Word ignore el color y aplique negro automático.
        """
        hex_fill = (hex_fill or "").strip().lstrip("#").upper()

        # Normalizar hex de 3 a 6 caracteres
        if len(hex_fill) == 3:
            hex_fill = "".join(ch * 2 for ch in hex_fill)

        # Validar formato hexadecimal
        if not re.fullmatch(r"[0-9A-F]{6}", hex_fill):
            hex_fill = "D9D9D9"

        tc = cell._tc
        tcPr = tc.get_or_add_tcPr()

        # PASO 1: ELIMINAR TODOS LOS SOMBREADOS PREVIOS
        for shd_old in list(tcPr.findall(qn("w:shd"))):
            tcPr.remove(shd_old)

        # PASO 2: CREAR NUEVO ELEMENTO DE SOMBREADO
        shd = OxmlElement("w:shd")

        # PASO 3: CONFIGURACIÓN EXPLÍCITA Y MÍNIMA
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), hex_fill)

        # PASO 4: ELIMINAR ATRIBUTOS DE TEMA QUE CAUSAN COLOR NEGRO
        atributos_tema = [
            "w:themeFill", "w:themeFillTint", "w:themeFillShade",
            "w:themeColor", "w:themeTint", "w:themeShade"
        ]

        for att in atributos_tema:
            full = qn(att)
            if full in shd.attrib:
                del shd.attrib[full]

        # PASO 5: INSERTAR AL INICIO DE tcPr (orden importante)
        tcPr.insert(0, shd)

    def get_cell_fill_hex(self, cell):
        try:
            tcPr = cell._tc.tcPr
            if tcPr is None:
                return None
            shd = tcPr.find(qn("w:shd"))
            if shd is None:
                return None
            fill = shd.get(qn("w:fill"))
            return fill.upper() if fill else None
        except Exception:
            return None

    def clear_cell_shading(self, cell):
        tcPr = cell._element.find(qn("w:tcPr"))
        if tcPr is None:
            return
        for shd in list(tcPr.findall(qn("w:shd"))):
            tcPr.remove(shd)

    def clear_row_shading(self, row):
        try:
            trPr = row._tr.trPr
            if trPr is None:
                return
            for shd_old in list(trPr.findall(qn("w:shd"))):
                trPr.remove(shd_old)
        except Exception:
            pass

    # =========================
    # Celdas: limpiar / márgenes / tipografía
    # =========================
    def clear_cell(self, cell):
        tc = cell._element
        for child in list(tc):
            if child.tag in (qn("w:p"), qn("w:tbl")):
                tc.remove(child)

    def set_cell_margins(self, cell, top=0, left=0, bottom=0, right=0):
        tc = cell._element
        tcPr = tc.get_or_add_tcPr()
        tcMar = tcPr.find(qn("w:tcMar"))
        if tcMar is None:
            tcMar = OxmlElement("w:tcMar")
            tcPr.append(tcMar)
        for side in ("top", "left", "bottom", "right"):
            el = tcMar.find(qn(f"w:{side}"))
            if el is None:
                el = OxmlElement(f"w:{side}")
                tcMar.append(el)
            el.set(qn("w:w"), "0")
            el.set(qn("w:type"), "dxa")

    def format_cell_paragraphs_fonts(self, cell, font_name, size_pt, rgb_tuple, bold=False, center=True, line=1.0):
        for p in cell.paragraphs:
            pf = p.paragraph_format
            pf.first_line_indent = Cm(0)
            pf.left_indent = Cm(0)
            pf.right_indent = Cm(0)
            pf.space_before = Pt(0)
            pf.space_after = Pt(0)
            pf.line_spacing = line
            if center:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:
                r.font.bold = bool(bold)
                r.font.name = font_name
                r.font.size = Pt(size_pt)
                r.font.color.rgb = RGBColor(*rgb_tuple)

    # =========================
    # XML helpers tabla: ancho fijo + grid + celdas
    # =========================
    def set_tbl_pr_fixed_width(self, tbl_element, total_twips: int):
        tblPr = tbl_element.tblPr
        if tblPr is None:
            tblPr = OxmlElement("w:tblPr")
            tbl_element.insert(0, tblPr)

        tblW = tblPr.find(qn("w:tblW"))
        if tblW is None:
            tblW = OxmlElement("w:tblW")
            tblPr.append(tblW)
        tblW.set(qn("w:w"), str(total_twips))
        tblW.set(qn("w:type"), "dxa")

        tblLayout = tblPr.find(qn("w:tblLayout"))
        if tblLayout is None:
            tblLayout = OxmlElement("w:tblLayout")
            tblPr.append(tblLayout)
        tblLayout.set(qn("w:type"), "fixed")

    def set_tbl_grid(self, tbl_element, col_widths_twips):
        tblGrid = tbl_element.tblGrid
        if tblGrid is None:
            tblGrid = OxmlElement("w:tblGrid")
            tbl_element.insert(1, tblGrid)
        else:
            for gc in list(tblGrid):
                tblGrid.remove(gc)
        for w in col_widths_twips:
            gridCol = OxmlElement("w:gridCol")
            gridCol.set(qn("w:w"), str(w))
            tblGrid.append(gridCol)

    def set_cell_width_twips(self, cell, width_twips: int):
        tc = cell._element
        tcPr = tc.get_or_add_tcPr()
        tcW = tcPr.find(qn("w:tcW"))
        if tcW is None:
            tcW = OxmlElement("w:tcW")
            tcPr.append(tcW)
        tcW.set(qn("w:w"), str(width_twips))
        tcW.set(qn("w:type"), "dxa")

    def merge_h(self, table, row, col_left, col_right):
        try:
            a = table.cell(row, col_left)
            b = table.cell(row, col_right)
            if a._tc is b._tc:
                return a
            a.merge(b)
            return a
        except: return None

    def merge_v(self, table, col, row_top=0, row_bottom=1):
        try:
            top = table.cell(row_top, col)
            bottom = table.cell(row_bottom, col)
            if top._tc is bottom._tc:
                return top
            top.merge(bottom)
            return top
        except: return None
        
    # ==========================================
    # HEADER LOGIC
    # ==========================================
    
    def estilizar_celda_codigo_header(self, tabla):
        cel = tabla.cell(0, 0)
        self.shade_cell_robust(cel, hex_fill=self.CODE_FILL)
        self.format_cell_paragraphs_fonts(
            cel,
            "Formata Medium", # Force Medium per user script
            14,
            (255, 255, 255),
            bold=False,
            center=True,
            line=1.0
        )

    def estilizar_celda_titulo_header(self, tabla):
        cel = tabla.cell(0, 2)
        texto = "\n".join(p.text for p in cel.paragraphs).strip()
        # Title case simple map
        texto = texto.lower()
        texto = texto[0].upper() + texto[1:] if len(texto) > 1 else texto.upper()
        
        self.clear_cell(cel)
        self.set_cell_margins(cel, 0, 0, 0, 0)
        p = cel.add_paragraph(texto)
        pf = p.paragraph_format
        pf.line_spacing = 1.0
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        title_rgb = self._hex_to_rgb(self.config.get('title_font_color', '#429591'))
        
        for r in p.runs:
            r.font.name = "Formata Medium"
            r.font.size = Pt(14)
            r.font.bold = False
            r.font.color.rgb = RGBColor(*title_rgb)

    def configurar_paginacion_header(self, tabla):
        if len(tabla.rows) < 2 or len(tabla.columns) < 2: return
        cel = tabla.cell(1, 1)
        self.clear_cell(cel)
        p = cel.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        style_name = "KL_Paginacion" # Should ensure style exists or just run direct formatting
        
        # Short version: Just Field Codes
        def _add_run_text(txt):
            r = p.add_run(txt)
            r.font.name = "Formata Medium"
            r.font.size = Pt(8)
            r.font.color.rgb = RGBColor(88,89,91)
            
        def _add_fld(instr):
             # Simpler fldSimple if possible, but user script used complex. Let's try simple text for reliability or just Page x of y
             # User script used complex fldChar. We will replicate minimally or skip complex logic for brevity if acceptable.
             # Let's try to just insert Text "Página X de Y" as placeholder if we can't easily do fldChar here.
             # Actually, let's copy the robust fldChar logic.
             r = OxmlElement('w:r')
             fld = OxmlElement('w:fldChar')
             fld.set(qn('w:fldCharType'), 'begin')
             r.append(fld)
             p._p.append(r)
             
             r = OxmlElement('w:r')
             instr_t = OxmlElement('w:instrText')
             instr_t.set(qn('xml:space'), 'preserve')
             instr_t.text = instr
             r.append(instr_t)
             p._p.append(r)

             r = OxmlElement('w:r')
             fld = OxmlElement('w:fldChar')
             fld.set(qn('w:fldCharType'), 'end')
             r.append(fld)
             p._p.append(r)

        _add_run_text("Página ")
        _add_fld("PAGE")
        _add_run_text(" de ")
        _add_fld("NUMPAGES")

    def verificar_o_insertar_tabla_encabezado(self, doc):
        sec = doc.sections[0]
        header = sec.header
        orient_h, size = self.get_page_setup(doc)

        c3_cm = 16.0 # Default letter vertical approx
        if not orient_h: c3_cm = 9.5
        elif size == "legal": c3_cm = 21.0
        
        col_cm = [2.0, 2.5, c3_cm, 4.0]
        col_tw = [self.cm_to_twips(x) for x in col_cm]
        total_tw = sum(col_tw)

        if not header.tables:
            tabla = header.add_table(rows=2, cols=4)
        else:
            tabla = header.tables[0]
            # Ensure dims
            while len(tabla.rows) < 2: tabla.add_row()
            while len(tabla.columns) < 4: tabla.add_column(Cm(1))
        
        tabla.alignment = WD_TABLE_ALIGNMENT.CENTER
        self.set_tbl_pr_fixed_width(tabla._element, total_tw)
        self.set_tbl_grid(tabla._element, col_tw)

        # Base formatting
        for row in tabla.rows:
            row.height_rule = WD_ROW_HEIGHT_RULE.EXACTLY
            row.height = Cm(0.8)
            for cell in row.cells:
                cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
                self.set_cell_margins(cell, 0,0,0,0)
                # Default Font
                self.format_cell_paragraphs_fonts(cell, "Formata Light", 10, (88,89,91))
        
        # Merges
        self.merge_h(tabla, 0, 0, 1)
        self.merge_v(tabla, 2, 0, 1)
        self.merge_v(tabla, 3, 0, 1)
        
        # Specifics
        self.estilizar_celda_codigo_header(tabla)
        self.estilizar_celda_titulo_header(tabla)
        self.configurar_paginacion_header(tabla)
        
        # Paginacion cells defaults (Row 2, Col 0&1)
        self.format_cell_paragraphs_fonts(tabla.cell(1,0), "Formata Medium", 8, (88,89,91))
        self.format_cell_paragraphs_fonts(tabla.cell(1,1), "Formata Medium", 8, (88,89,91))
        
        return tabla

    # ==========================================
    # BODY & TABLES LOGIC
    # ==========================================

    def _norm(self, txt):
        if not txt: return ""
        s = txt.strip().lower()
        if s.endswith(":"): s = s[:-1].strip()
        trans = str.maketrans("áéíóú", "aeiou")
        s = s.translate(trans)
        return " ".join(s.split())

    def _es_titulo(self, texto):
        _TITULOS_BASE = [
            "objetivo", "alcance", "periodicidad", "responsables",
            "normativas y politicas", "normativa y politicas", "normatividad y politicas",
            "definiciones", "descripcion de actividades", "documentos y registros relacionados",
            "lista de anexos", "control de version", "elaboracion, revision y aprobacion", 
            "modificacion, revision y aprobacion"
        ]
        s = self._norm(texto)
        if not s: return False
        if s in _TITULOS_BASE: return True
        for t in _TITULOS_BASE:
            if s.startswith(t + " "): return True
        s_sin_num = re.sub(r"^[0-9]+(\.[0-9]+)*[\)\.]?\s*", "", s)
        if not s_sin_num: return False
        if s_sin_num in _TITULOS_BASE: return True
        if any(s_sin_num.startswith(t + " ") for t in _TITULOS_BASE): return True
        return False
        
    def shade_row_cells(self, tabla, row_idx, cols=None, hex_fill=None):
        if hex_fill is None: hex_fill = self.HEADER_FILL
        if row_idx >= len(tabla.rows): return
        row = tabla.rows[row_idx]
        self.clear_row_shading(row)
        rng = range(len(row.cells)) if cols is None else cols
        for c in rng:
            if c < len(row.cells):
                self.shade_cell_robust(row.cells[c], hex_fill)

    def apply_table_widths_cm(self, tabla, widths_cm):
        col_tw = [self.cm_to_twips(w) for w in widths_cm]
        self.set_tbl_pr_fixed_width(tabla._element, sum(col_tw))
        self.set_tbl_grid(tabla._element, col_tw)
        for c in range(min(len(widths_cm), len(tabla.columns))):
            wtw = col_tw[c]
            for row in tabla.rows:
                self.set_cell_width_twips(row.cells[c], wtw)

    def set_header_titles(self, tabla, titles, font="Formata Medium", size_pt=10, color=(88,89,91)):
        if len(tabla.rows) == 0: tabla.add_row()
        row0 = tabla.rows[0]
        for i, txt in enumerate(titles):
            if i >= len(row0.cells): break
            cell = row0.cells[i]
            self.clear_cell(cell)
            p = cell.add_paragraph(txt)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            self.format_cell_paragraphs_fonts(cell, font, size_pt, color, center=True)

    def _iter_doc_blocks(self, doc):
        body = doc.element.body
        for child in body.iterchildren():
            tag = child.tag
            if tag.endswith("}p"): yield Paragraph(child, doc)
            elif tag.endswith("}tbl"): yield Table(child, doc)

    def find_next_table_after_title(self, doc, title_variants):
        wanted = set(self._norm(t) for t in title_variants)
        blocks = list(self._iter_doc_blocks(doc))
        for i, blk in enumerate(blocks):
            if isinstance(blk, Paragraph) and self._norm(blk.text) in wanted:
                for j in range(i + 1, len(blocks)):
                    nb = blk = blocks[j]
                    if isinstance(nb, Table): return nb
                    if isinstance(nb, Paragraph) and self._es_titulo(nb.text): return None
        return None

    # ==========================================
    # MAIN LOGIC
    # ==========================================

    def process_procedure(self, doc_path, output_path):
        doc = Document(doc_path)

        # Configs
        title_rgb = self._hex_to_rgb(self.config.get('title_font_color', '#429591'))
        body_rgb = self._hex_to_rgb(self.config.get('body_font_color', '#58595B')) # Default gray

        # 1. Page Setup
        for sec in doc.sections:
            sec.top_margin = Cm(self.config['margin_top'])
            sec.bottom_margin = Cm(self.config['margin_bottom'])
            sec.left_margin = Cm(self.config['margin_left'])
            sec.right_margin = Cm(self.config['margin_right'])
            sec.header_distance = Cm(1.5 if sec.page_width > sec.page_height else 1.0)
            sec.footer_distance = Cm(1.0)

        # 2. Header
        self.verificar_o_insertar_tabla_encabezado(doc)

        # 3. Typography (Paragraphs)
        for p in doc.paragraphs:
            if self._es_titulo(p.text):
                self.format_cell_paragraphs_fonts(type('obj', (object,), {'paragraphs': [p]}), 
                                                self.TITLE_FONT, 12, title_rgb, bold=False, center=False)
                # Force All Caps manually for titles if desired
                for r in p.runs: r.font.all_caps = True
            else:
                self.format_cell_paragraphs_fonts(type('obj', (object,), {'paragraphs': [p]}), 
                                                self.BODY_FONT, 12, body_rgb, bold=False, center=False, line=1.15)

        # 4. Typography (Tables General)
        for t in doc.tables:
            if t._element.getparent().tag.endswith('hdr'): continue
            for r_idx, row in enumerate(t.rows):
                for cell in row.cells:
                     # General Procedure Styles: Header Medium 10, Body Light 9
                     font = "Formata Medium" if r_idx == 0 else "Formata Light"
                     size = 10 if r_idx == 0 else 9
                     self.format_cell_paragraphs_fonts(cell, font, size, body_rgb, center=False, line=1.15)

        # 5. Specific Tables
        # Actividades
        t = self.find_next_table_after_title(doc, ["descripcion de actividades"])
        if t:
            self.apply_table_widths_cm(t, [1.0, 3.6, 9.6, 3.8])
            self.set_header_titles(t, ["No.", "Responsable", "Actividad(descripción)", "Registros relacionados"])
            self.shade_row_cells(t, 0, hex_fill=self.HEADER_FILL)
        
        # Doc Relacionados
        t = self.find_next_table_after_title(doc, ["documentos y registros relacionados"])
        if t:
            self.apply_table_widths_cm(t, [3.6, 11.5, 2.9])
            self.set_header_titles(t, ["Tipo", "Nombre", "Código"])
            self.shade_row_cells(t, 0, hex_fill=self.HEADER_FILL)

        # Anexos
        t = self.find_next_table_after_title(doc, ["lista de anexos"])
        if t:
            self.apply_table_widths_cm(t, [1.0, 5.5, 11.5])
            self.set_header_titles(t, ["No.", "Nombre del documento", "Código"])
            self.shade_row_cells(t, 0, hex_fill=self.HEADER_FILL)

        # Control Version
        t = self.find_next_table_after_title(doc, ["control de version", "control de versión"])
        if t:
            self.apply_table_widths_cm(t, [1.0, 14.8, 2.2])
            self.set_header_titles(t, ["No.", "Identificación del cambio", "Fecha"])
            self.shade_row_cells(t, 0, hex_fill=self.HEADER_FILL)

        # Aprobaciones
        t = self.find_next_table_after_title(doc, ["elaboracion, revision y aprobacion", "aprobaciones"])
        if t:
            self.apply_table_widths_cm(t, [2.1, 5.3, 5.3, 5.3])
            while len(t.rows) < 4: t.add_row()
            self.set_header_titles(t, ["", "Modificó", "Revisó", "Aprobó"])
            self.shade_row_cells(t, 0, cols=range(1, 4), hex_fill=self.HEADER_FILL)
            for r in range(1, len(t.rows)):
                self.shade_cell_robust(t.cell(r,0), self.HEADER_FILL)

        # 6. Final Shading Pass (Critical)
        for t in doc.tables:
            if t._element.getparent().tag.endswith('hdr'): continue
            # If not Aprobaciones (heuristic check)
            if len(t.rows) > 0 and len(t.rows[0].cells) > 0:
                 # Check if code cell
                 c0 = t.cell(0,0)
                 if self.get_cell_fill_hex(c0) == self.CODE_FILL: continue
                 
                 # Apply generically to header row if simple table
                 # (Logic: if specific table handled above, it already has shading, but this ensures generic tables also get it)
                 # We must be careful not to overwrite specific styles if they differ.
                 # The user script applies it to ALL tables generically at end.
                 
                 # Check if Aprobaciones-like
                 c1_txt = self._norm(t.row_cells(0)[1].text) if len(t.columns) > 1 else ""
                 if "modifico" in c1_txt: continue # Skip detailed reprocessing
                 
                 self.shade_row_cells(t, 0, hex_fill=self.HEADER_FILL)

        doc.save(output_path)
        return output_path

    # ==========================================
    # LOGICA FORMATOS (Legacy/Simple Port)
    # ==========================================
    def process_format(self, doc_path, output_path):
        # Re-use robust header logic, but keep body simple as requested?
        # User only prioritized Procedimiento logic in prompt.
        # We will apply Header Fix + Margins + Simple text standardization.
        doc = Document(doc_path)
        
        for sec in doc.sections:
             sec.top_margin = Cm(self.config['margin_top'])
             sec.bottom_margin = Cm(self.config['margin_bottom'])
             sec.left_margin = Cm(self.config['margin_left'])
             sec.right_margin = Cm(self.config['margin_right'])
        
        # Header Table Fix
        self.verificar_o_insertar_tabla_encabezado(doc)
        
        # General formatting
        body_rgb = self._hex_to_rgb(self.config.get('body_font_color', '#58595B'))
        for p in doc.paragraphs:
            self.format_cell_paragraphs_fonts(type('obj', (object,), {'paragraphs': [p]}), 
                                            self.BODY_FONT, 10, body_rgb, center=False)

        doc.save(output_path)
        return output_path
