"""
Formateador Específico para FORMATOS (Tipografía Arial, etc.)
Lógica separada para "Estandarizador de Formatos".
"""

import os
import io
import re
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.shared import OxmlElement
from docx.oxml.ns import qn

class FormatFormatter:
    @staticmethod
    def _hex_to_rgb(hex_str):
        if not hex_str: return (45, 55, 72)
        h = hex_str.strip().lstrip('#')
        if len(h) == 3: h = ''.join(ch * 2 for ch in h)
        if len(h) != 6: return (45, 55, 72)
        try:
            return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
        except ValueError:
            return (45, 55, 72)

    def __init__(self, config=None):
        self.config = config or {}
        self.FONT_NAME = self.config.get('body_font_family') or "Calibri"
        if self.config.get('body_font_color'):
            self.COLOR_INSTITUCIONAL_RGB = self._hex_to_rgb(self.config['body_font_color'])
            self.COLOR_INSTITUCIONAL_HEX = self.config['body_font_color'].strip().lstrip('#').upper()
        if self.config.get('table_header_fill'):
            self.COLOR_TEXTO_CC_HEX = self.config['table_header_fill'].strip().lstrip('#').upper()
        self.MARGIN_TOP = float(self.config.get('margin_top', 2.5))
        self.MARGIN_BOTTOM = float(self.config.get('margin_bottom', 2.5))
        self.MARGIN_LEFT = float(self.config.get('margin_left', 2.5))
        self.MARGIN_RIGHT = float(self.config.get('margin_right', 2.5))

    # ---------------------------- Configuración de colores ----------------------------
    COLOR_INSTITUCIONAL_RGB = (45, 55, 72)
    COLOR_INSTITUCIONAL_HEX = "2D3748"
    COLOR_TEXTO_BLANCO = RGBColor(255, 255, 255)
    COLOR_TEXTO_CC_HEX = "E2E8F0"

    # ---------------------------- Utilidades ------------------------------------
    UPPER_ES = set("ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜÑ")
    LOWER_ES = set("abcdefghijklmnopqrstuvwxyzáéíóúüñ")
    LETTERS_ES = UPPER_ES | LOWER_ES

    def _is_letter_es(self, ch: str) -> bool:
        return ch in self.LETTERS_ES

    def _is_upper_es(self, ch: str) -> bool:
        return ch in self.UPPER_ES

    def _is_all_upper_es(self, word: str) -> bool:
        return all((c in self.UPPER_ES) for c in word if self._is_letter_es(c)) and any(self._is_letter_es(c) for c in word)

    def _is_title_case_es(self, word: str) -> bool:
        if not word:
            return False
        letters = [c for c in word if self._is_letter_es(c)]
        if not letters:
            return False
        if letters[0] not in self.UPPER_ES:
            return False
        return all((c not in self.UPPER_ES) for c in letters[1:])

    # ---------------------------- Helpers XML ---------------------------
    _THEME_COLOR_ATTRS = (qn('w:themeColor'), qn('w:themeTint'), qn('w:themeShade'))

    def _ensure_rPr(self, r_elem):
        rPr = r_elem.find(qn('w:rPr'))
        if rPr is None:
            rPr = OxmlElement('w:rPr')
            r_elem.insert(0, rPr)
        return rPr

    def _set_run_font(self, rPr, font_name="Calibri", half_points="20"):
        rFonts = rPr.find(qn('w:rFonts'))
        if rFonts is None:
            rFonts = OxmlElement('w:rFonts')
            rPr.append(rFonts)
        rFonts.set(qn('w:ascii'), font_name)
        rFonts.set(qn('w:hAnsi'), font_name)
        rFonts.set(qn('w:eastAsia'), font_name)
        rFonts.set(qn('w:cs'), font_name)

        for tag in ('w:sz', 'w:szCs'):
            el = rPr.find(qn(tag))
            if el is None:
                el = OxmlElement(tag)
                rPr.append(el)
            el.set(qn('w:val'), str(half_points))

    def _force_run_color(self, rPr, color_hex: str):
        color_hex = (color_hex or "").strip().lstrip("#").upper()

        color_el = rPr.find(qn('w:color'))
        if color_el is None:
            color_el = OxmlElement('w:color')
            rPr.append(color_el)

        for attr in self._THEME_COLOR_ATTRS:
            if attr in color_el.attrib:
                del color_el.attrib[attr]

        color_el.set(qn('w:val'), color_hex)

    # ---------------------------- 1) Formato general ---------------------------------
    def aplicar_margenes_y_formato_general(self, doc: Document):
        for section in doc.sections:
            section.top_margin = Cm(getattr(self, "MARGIN_TOP", 2.5))
            section.bottom_margin = Cm(getattr(self, "MARGIN_BOTTOM", 2.5))
            section.left_margin = Cm(getattr(self, "MARGIN_LEFT", 2.5))
            section.right_margin = Cm(getattr(self, "MARGIN_RIGHT", 2.5))

        def _apply_runs(paragraphs):
            for p in paragraphs:
                for run in p.runs:
                    run.font.name = getattr(self, "FONT_NAME", "Calibri")
                    run.font.size = Pt(10)
                    run.font.color.rgb = RGBColor(*self.COLOR_INSTITUCIONAL_RGB)

        _apply_runs(doc.paragraphs)

        for table in doc.tables:
            if 'hdr' in table._element.getparent().tag:
                continue
            for row in table.rows:
                for cell in row.cells:
                    _apply_runs(cell.paragraphs)

        for section in doc.sections:
            _apply_runs(section.header.paragraphs)
            _apply_runs(section.footer.paragraphs)

    # ---------------------------- 2) Content Controls --------------------------------
    def aplicar_formato_content_controls(self, doc: Document):
        count = 0
        def _process(root):
            nonlocal count
            for sdt in root.findall('.//' + qn('w:sdt')):
                for r in sdt.findall('.//' + qn('w:r')):
                    rPr = self._ensure_rPr(r)
                    self._set_run_font(rPr, getattr(self, "FONT_NAME", "Calibri"), "20")          # 10pt
                    self._force_run_color(rPr, self.COLOR_TEXTO_CC_HEX)  # D9D9D9
                    count += 1

        _process(doc.element.body)
        for section in doc.sections:
            _process(section.header._element)
            _process(section.footer._element)
        return count

    # ---------------------------- 3) Minúsculas tras ":" -----------------------------
    def _procesar_parrafo_minusculas(self, p):
        runs = p.runs
        def _get_char(rid, cid):
            if rid >= len(runs): return None
            t = runs[rid].text
            if cid >= len(t): return None
            return t[cid]

        for i, run in enumerate(runs):
            for idx, ch in enumerate(run.text):
                if ch != ":":
                    continue

                rj, cj = i, idx + 1
                nxt = None
                while True:
                    c = _get_char(rj, cj)
                    if c is None:
                        rj += 1
                        cj = 0
                        if rj >= len(runs): break
                        continue
                    if c in (" ", "\t", "\u00A0"):
                        cj += 1
                        continue
                    nxt = c
                    break

                if nxt is None or (not self._is_letter_es(nxt)) or (not self._is_upper_es(nxt)):
                    continue

                rk, ck = rj, cj
                word = ""
                while True:
                    c2 = _get_char(rk, ck)
                    if c2 is None or (not self._is_letter_es(c2)):
                        break
                    word += c2
                    ck += 1
                    if ck >= len(runs[rk].text):
                        rk += 1
                        ck = 0
                        if rk >= len(runs):
                            break

                if len(word) <= 3 and self._is_all_upper_es(word):
                    continue
                if self._is_title_case_es(word):
                    continue

                target_run = runs[rj]
                s = target_run.text
                target_run.text = s[:cj] + s[cj].lower() + s[cj+1:]

    def aplicar_minusculas_despues_de_dos_puntos(self, doc: Document):
        for p in doc.paragraphs:
            self._procesar_parrafo_minusculas(p)
        for t in doc.tables:
            if 'hdr' in t._element.getparent().tag:
                continue
            for row in t.rows:
                for cell in row.cells:
                    for p in cell.paragraphs:
                        self._procesar_parrafo_minusculas(p)
        for sec in doc.sections:
            for p in sec.header.paragraphs:
                self._procesar_parrafo_minusculas(p)
            for p in sec.footer.paragraphs:
                self._procesar_parrafo_minusculas(p)

    # ---------------------------- 4) Sombreado robusto -------------------------------
    def shade_cell_robust(self, cell, hex_color: str):
        tc = cell._element
        tcPr = tc.get_or_add_tcPr()
        for shd_elem in tcPr.findall(qn('w:shd')):
            tcPr.remove(shd_elem)
        shd = OxmlElement('w:shd')
        shd.set(qn('w:val'), 'clear')
        shd.set(qn('w:color'), 'auto')
        shd.set(qn('w:fill'), (hex_color or "").strip().lstrip("#").upper())
        for attr in ['w:themeFill', 'w:themeFillTint', 'w:themeFillShade', 'w:themeColor', 'w:themeTint', 'w:themeShade']:
            qname = qn(attr)
            if qname in shd.attrib:
                del shd.attrib[qname]
        tcPr.insert(0, shd)

    # ---------------------------- 5) Ajuste de ancho (twips) --------------------------
    def set_tbl_pr_fixed_width(self, tbl_element, total_twips: int):
        tblPr = tbl_element.tblPr
        if tblPr is None:
            tblPr = OxmlElement('w:tblPr')
            tbl_element.insert(0, tblPr)
        tblW = tblPr.find(qn('w:tblW'))
        if tblW is None:
            tblW = OxmlElement('w:tblW')
            tblPr.append(tblW)
        tblW.set(qn('w:w'), str(total_twips))
        tblW.set(qn('w:type'), 'dxa')

        tblLayout = tblPr.find(qn('w:tblLayout'))
        if tblLayout is None or tblLayout.get(qn('w:type')) != 'fixed':
            if tblLayout is not None:
                tblPr.remove(tblLayout)
            tblLayout = OxmlElement('w:tblLayout')
            tblLayout.set(qn('w:type'), 'fixed')
            tblPr.append(tblLayout)
        tblInd = tblPr.find(qn('w:tblInd'))
        if tblInd is not None:
            tblPr.remove(tblInd)

    def set_tbl_grid(self, tbl_element, col_widths_twips):
        tblGrid = tbl_element.tblGrid
        if tblGrid is None:
            tblGrid = OxmlElement('w:tblGrid')
            tbl_element.insert(1, tblGrid)
        else:
            for gc in list(tblGrid):
                tblGrid.remove(gc)
        for w in col_widths_twips:
            gridCol = OxmlElement('w:gridCol')
            gridCol.set(qn('w:w'), str(w))
            tblGrid.append(gridCol)

    def set_cell_width_twips(self, cell, width_twips: int):
        tc = cell._element
        tcPr = tc.find(qn('w:tcPr'))
        if tcPr is None:
            tcPr = OxmlElement('w:tcPr')
            tc.append(tcPr)
        tcW = tcPr.find(qn('w:tcW'))
        if tcW is None:
            tcW = OxmlElement('w:tcW')
            tcPr.append(tcW)
        tcW.set(qn('w:w'), str(width_twips))
        tcW.set(qn('w:type'), 'dxa')

    # ---------------------------- 6) Encabezado + Paginación --------------------------
    def format_cell_paragraphs(self, cell, bold=True, size_pt=None, color=None, center=True):
        for p in cell.paragraphs:
            if center:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in p.runs:
                run.font.name = getattr(self, "FONT_NAME", "Calibri")
                run.font.bold = bold
                if size_pt is not None:
                    run.font.size = Pt(size_pt)
                if color is not None:
                    run.font.color.rgb = color

    def reset_page_x_de_y(self, cell):
        for p in list(cell.paragraphs):
            p._element.getparent().remove(p._element)
        p = cell.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER

        def add_text(txt):
            r = p.add_run(txt)
            r.font.name = getattr(self, "FONT_NAME", "Calibri")
            r.font.size = Pt(8)
            r.font.bold = True
            r.font.color.rgb = RGBColor(*self.COLOR_INSTITUCIONAL_RGB)

        def add_field(code):
            r = p.add_run()
            r.font.name = getattr(self, "FONT_NAME", "Calibri")
            r.font.size = Pt(8)
            r.font.bold = True
            r.font.color.rgb = RGBColor(*self.COLOR_INSTITUCIONAL_RGB)
            b = OxmlElement('w:fldChar'); b.set(qn('w:fldCharType'), 'begin')
            it = OxmlElement('w:instrText'); it.set(qn('xml:space'), 'preserve'); it.text = f" {code} "
            s = OxmlElement('w:fldChar'); s.set(qn('w:fldCharType'), 'separate')
            e = OxmlElement('w:fldChar'); e.set(qn('w:fldCharType'), 'end')
            r._r.append(b); r._r.append(it); r._r.append(s)
            t = OxmlElement('w:t'); t.text = "1"
            r._r.append(t)
            r._r.append(e)

        add_text("Página ")
        add_field("PAGE")
        add_text(" de ")
        add_field("NUMPAGES")

    def verificar_y_corregir_tabla_encabezado(self, doc):
        if not doc.sections:
            return
        header = doc.sections[0].header
        
        # Si no existe tabla, crear una por defecto 2x4
        if not header.tables:
            tabla = header.add_table(rows=2, cols=4)
        else:
            tabla = header.tables[0]
        
        tabla.alignment = WD_TABLE_ALIGNMENT.CENTER
        
        col_widths_twips = [int(Cm(2).twips), int(Cm(2.5).twips), int(Cm(9.5).twips), int(Cm(4).twips)]
        try:
            self.set_tbl_pr_fixed_width(tabla._tbl, sum(col_widths_twips))
            self.set_tbl_grid(tabla._tbl, col_widths_twips)
            for col_idx, w in enumerate(col_widths_twips):
                for row in tabla.rows:
                    self.set_cell_width_twips(row.cells[col_idx], w)
        except Exception:
            pass

        cel_codigo = None
        cel_titulo = None
        cel_izq_paginacion = None
        try: cel_codigo = tabla.cell(0, 0)
        except: pass
        try: cel_titulo = tabla.cell(0, 2)
        except: pass
        try: cel_izq_paginacion = tabla.cell(1, 0)
        except: pass

        if cel_codigo is not None:
            self.shade_cell_robust(cel_codigo, self.COLOR_INSTITUCIONAL_HEX)
            self.format_cell_paragraphs(cel_codigo, bold=True, size_pt=14, color=self.COLOR_TEXTO_BLANCO, center=True)

        if cel_titulo is not None:
            self.format_cell_paragraphs(cel_titulo, bold=True, size_pt=14, color=RGBColor(*self.COLOR_INSTITUCIONAL_RGB), center=True)

        if cel_izq_paginacion is not None:
            self.format_cell_paragraphs(cel_izq_paginacion, bold=True, size_pt=8, color=RGBColor(*self.COLOR_INSTITUCIONAL_RGB), center=True)

        if len(tabla.rows) >= 2 and len(tabla.columns) >= 2:
            cel_c2_f2 = tabla.cell(1, 1)
            self.reset_page_x_de_y(cel_c2_f2)

    # ---------------------------- Orquestación --------------------------------------
    def format_document(self, input_source, output_path=None):
        if isinstance(input_source, str):
            doc = Document(input_source)
        elif isinstance(input_source, io.BytesIO):
            input_source.seek(0)
            doc = Document(input_source)
        else:
            doc = Document(input_source)

        self.aplicar_margenes_y_formato_general(doc)
        self.aplicar_formato_content_controls(doc)
        self.aplicar_minusculas_despues_de_dos_puntos(doc)
        self.verificar_y_corregir_tabla_encabezado(doc)

        if output_path:
            doc.save(output_path)
            return output_path
        else:
            mem_file = io.BytesIO()
            doc.save(mem_file)
            mem_file.seek(0)
            return mem_file
