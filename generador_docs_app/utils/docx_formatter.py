"""
Formateador Robusto de Documentos Word (OOXML)
===============================================
Código completo del script de Colab adaptado para Flask.
Mantiene toda la lógica de formato sin simplificaciones.
"""

import os
import re
import io
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL, WD_ROW_HEIGHT_RULE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.shared import OxmlElement, qn
from docx.text.paragraph import Paragraph
from docx.table import Table


class ProcedureFormatter:
    """
    Formateador completo de documentos institucionales.
    Implementa todas las funciones del script de Colab.
    """

    # =========================
    # CONSTANTES INSTITUCIONALES
    # =========================
    HEADER_FILL = "E2E8F0"   # Gris claro (Blanco, fondo 1, Oscuro 15%)
    CODE_FILL = "0F4C81"     # Azul oscuro institucional
    
    BODY_FONT = "Calibri"
    BODY_SIZE = 11
    BODY_COLOR = (45, 55, 72)
    BODY_LINE = 1.15
    
    TITLE_FONT = "Calibri"
    TITLE_SIZE = 12
    TITLE_COLOR = (27, 54, 93)  # Turquesa institucional
    
    PAGINACION_STYLE_NAME = "Doc_Paginacion"
    
    _TITULOS_BASE = [
        "objetivo", "alcance", "periodicidad", "responsables",
        "normativas y políticas", "normativas y politicas",
        "normativa y políticas", "normativa y politicas",
        "normatividad y políticas", "normatividad y politicas",
        "definiciones",
        "descripción de actividades", "descripcion de actividades",
        "documentos y registros relacionados",
        "lista de anexos",
        "control de versión", "control de version",
        "elaboración, revisión y aprobación", "elaboracion, revision y aprobacion"
    ]

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
        if self.config.get('body_font_family'): self.BODY_FONT = self.config['body_font_family']
        if self.config.get('body_font_size'): self.BODY_SIZE = int(self.config['body_font_size'])
        if self.config.get('body_font_color'): self.BODY_COLOR = self._hex_to_rgb(self.config['body_font_color'])
        if self.config.get('title_font_family'): self.TITLE_FONT = self.config['title_font_family']
        if self.config.get('title_font_size'): self.TITLE_SIZE = int(self.config['title_font_size'])
        if self.config.get('title_font_color'): self.TITLE_COLOR = self._hex_to_rgb(self.config['title_font_color'])
        if self.config.get('table_header_fill'): self.HEADER_FILL = self.config['table_header_fill'].strip().lstrip('#').upper()
        if self.config.get('header_code_fill'): self.CODE_FILL = self.config['header_code_fill'].strip().lstrip('#').upper()
        self.MARGIN_TOP = float(self.config.get('margin_top', 2.5))
        self.MARGIN_BOTTOM = float(self.config.get('margin_bottom', 2.5))
        self.MARGIN_LEFT = float(self.config.get('margin_left', 2.5))
        self.MARGIN_RIGHT = float(self.config.get('margin_right', 2.5))
        self._TITULOS_NORM = set(self._norm(t) for t in self._TITULOS_BASE)

    # =========================
    # HELPERS GENERALES
    # =========================
    
    @staticmethod
    def cm_to_twips(cm: float) -> int:
        return int(round(cm * 567))

    @staticmethod
    def _length_cm(length):
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
        """Obtiene el color de relleno actual de una celda."""
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
        """Elimina completamente el sombreado de una celda."""
        tcPr = cell._element.find(qn("w:tcPr"))
        if tcPr is None:
            return
        for shd in list(tcPr.findall(qn("w:shd"))):
            tcPr.remove(shd)

    def clear_row_shading(self, row):
        """Elimina el sombreado a nivel de fila."""
        try:
            trPr = row._tr.trPr
            if trPr is None:
                return
            for shd_old in list(trPr.findall(qn("w:shd"))):
                trPr.remove(shd_old)
        except Exception:
            pass

    # =========================
    # CELDAS: LIMPIAR / MÁRGENES / TIPOGRAFÍA
    # =========================
    
    def clear_cell(self, cell):
        tc = cell._element
        for child in list(tc):
            if child.tag in (qn("w:p"), qn("w:tbl")):
                tc.remove(child)

    def set_cell_margins(self, cell, top=0, left=0, bottom=0, right=0):
        tc = cell._element
        tcPr = tc.find(qn("w:tcPr"))
        if tcPr is None:
            tcPr = OxmlElement("w:tcPr")
            tc.append(tcPr)
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
    # SOMBREADO DE ENCABEZADOS DE TABLAS
    # =========================
    
    def shade_row_cells(self, tabla, row_idx, cols=None, hex_fill=None):
        """Aplica sombreado a celdas específicas de una fila."""
        if hex_fill is None:
            hex_fill = self.HEADER_FILL
        if row_idx >= len(tabla.rows):
            return
        row = tabla.rows[row_idx]
        self.clear_row_shading(row)
        rng = range(len(row.cells)) if cols is None else cols
        for c in rng:
            if c < len(row.cells):
                self.shade_cell_robust(row.cells[c], hex_fill)

    def shade_table_header_generic(self, tabla, hex_fill=None):
        """Aplica sombreado a toda la primera fila de una tabla."""
        if hex_fill is None:
            hex_fill = self.HEADER_FILL
        if len(tabla.rows) == 0:
            return
        self.shade_row_cells(tabla, 0, cols=None, hex_fill=hex_fill)

    # =========================
    # XML HELPERS TABLA: ANCHO FIJO + GRID + CELDAS
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
        tcPr = tc.find(qn("w:tcPr"))
        if tcPr is None:
            tcPr = OxmlElement("w:tcPr")
            tc.append(tcPr)
        tcW = tcPr.find(qn("w:tcW"))
        if tcW is None:
            tcW = OxmlElement("w:tcW")
            tcPr.append(tcW)
        tcW.set(qn("w:w"), str(width_twips))
        tcW.set(qn("w:type"), "dxa")

    def merge_h(self, table, row, col_left, col_right):
        a = table.cell(row, col_left)
        b = table.cell(row, col_right)
        if a._tc is b._tc:
            return a
        a.merge(b)
        return a

    def merge_v(self, table, col, row_top=0, row_bottom=1):
        top = table.cell(row_top, col)
        bottom = table.cell(row_bottom, col)
        if top._tc is bottom._tc:
            return top
        top.merge(bottom)
        return top

    # =========================
    # TABLA DE ENCABEZADO (DOCUMENTO)
    # =========================
    
    def aplicar_tipografia_header_default(self, tabla):
        """Formatea todas las celdas del header con Formata Light 10, RGB(88,89,91)."""
        for row in tabla.rows:
            for cell in row.cells:
                self.set_cell_margins(cell, 0, 0, 0, 0)
                self.format_cell_paragraphs_fonts(
                    cell,
                    font_name=self.BODY_FONT,
                    size_pt=10,
                    rgb_tuple=self.BODY_COLOR,
                    bold=False,
                    center=True,
                    line=1.0
                )

    def estilizar_celda_codigo(self, tabla):
        """CELDA DE CÓDIGO: Fondo gris oscuro 58595B con texto blanco."""
        cel = tabla.cell(0, 0)
        self.shade_cell_robust(cel, hex_fill=self.CODE_FILL)
        self.format_cell_paragraphs_fonts(
            cel,
            self.TITLE_FONT,
            14,
            (255, 255, 255),
            bold=False,
            center=True,
            line=1.0
        )

    @staticmethod
    def _to_sentence_case_es(texto: str) -> str:
        s = (texto or "").strip()
        if not s:
            return s
        s = s.lower()
        return s[0].upper() + s[1:] if len(s) > 1 else s.upper()

    def estilizar_celda_titulo(self, tabla):
        """Celda de título con color institucional."""
        cel = tabla.cell(0, 2)
        texto = "\n".join(p.text for p in cel.paragraphs).strip()
        nuevo = self._to_sentence_case_es(texto)
        self.clear_cell(cel)
        self.set_cell_margins(cel, 0, 0, 0, 0)
        p = cel.add_paragraph(nuevo)
        pf = p.paragraph_format
        pf.first_line_indent = Cm(0)
        pf.left_indent = Cm(0)
        pf.right_indent = Cm(0)
        pf.space_before = Pt(0)
        pf.space_after = Pt(0)
        pf.line_spacing = 1.0
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            r.font.name = self.TITLE_FONT
            r.font.size = Pt(14)
            r.font.bold = False
            r.font.color.rgb = RGBColor(*self.TITLE_COLOR)

    def estilizar_celdas_fila2_col1y2(self, tabla):
        """Estiliza las celdas de paginación (fila 2, columnas 1 y 2)."""
        c1f2 = tabla.cell(1, 0)
        self.format_cell_paragraphs_fonts(c1f2, self.TITLE_FONT, 8, self.BODY_COLOR, bold=False, center=True, line=1.0)
        c2f2 = tabla.cell(1, 1)
        self.format_cell_paragraphs_fonts(c2f2, self.TITLE_FONT, 8, self.BODY_COLOR, bold=False, center=True, line=1.0)

    # =========================
    # ESTILO DE PAGINACIÓN
    # =========================
    
    def asegurar_estilo_paginacion(self, doc):
        styles = doc.styles
        try:
            style = styles[self.PAGINACION_STYLE_NAME]
        except KeyError:
            style = styles.add_style(self.PAGINACION_STYLE_NAME, WD_STYLE_TYPE.CHARACTER)

        font = style.font
        font.name = self.TITLE_FONT
        font.size = Pt(8)
        font.bold = False
        font.color.rgb = RGBColor(*self.BODY_COLOR)
        return style

    def configurar_paginacion_header(self, tabla, style_name=None):
        if style_name is None:
            style_name = self.PAGINACION_STYLE_NAME
        if len(tabla.rows) < 2 or len(tabla.columns) < 2:
            return

        cel = tabla.cell(1, 1)
        self.clear_cell(cel)

        p = cel.add_paragraph()
        pf = p.paragraph_format
        pf.first_line_indent = Cm(0)
        pf.left_indent = Cm(0)
        pf.right_indent = Cm(0)
        pf.space_before = Pt(0)
        pf.space_after = Pt(0)
        pf.line_spacing = 1.0
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER

        font_name = self.TITLE_FONT
        size_pt = 8
        rgb = self.BODY_COLOR
        hex_color = "{:02X}{:02X}{:02X}".format(*rgb)

        def _add_text_run(texto):
            r = p.add_run(texto)
            r.style = style_name
            return r

        def _add_field_code(instr):
            r_begin = OxmlElement("w:r")
            fld_begin = OxmlElement("w:fldChar")
            fld_begin.set(qn("w:fldCharType"), "begin")
            r_begin.append(fld_begin)
            p._p.append(r_begin)

            r_instr = OxmlElement("w:r")
            instr_text = OxmlElement("w:instrText")
            instr_text.set(qn("xml:space"), "preserve")
            instr_text.text = instr
            r_instr.append(instr_text)
            p._p.append(r_instr)

            r_sep = OxmlElement("w:r")
            fld_sep = OxmlElement("w:fldChar")
            fld_sep.set(qn("w:fldCharType"), "separate")
            r_sep.append(fld_sep)
            p._p.append(r_sep)

            r_res = OxmlElement("w:r")
            rPr = OxmlElement("w:rPr")

            rStyle = OxmlElement("w:rStyle")
            rStyle.set(qn("w:val"), style_name)
            rPr.append(rStyle)

            rFonts = OxmlElement("w:rFonts")
            for k in ("ascii", "hAnsi", "eastAsia", "cs"):
                rFonts.set(qn(f"w:{k}"), font_name)
            rPr.append(rFonts)

            sz = OxmlElement("w:sz")
            sz.set(qn("w:val"), str(int(size_pt * 2)))
            rPr.append(sz)

            color = OxmlElement("w:color")
            color.set(qn("w:val"), hex_color)
            rPr.append(color)

            r_res.append(rPr)

            t = OxmlElement("w:t")
            t.text = "1"
            r_res.append(t)

            p._p.append(r_res)

            r_end = OxmlElement("w:r")
            fld_end = OxmlElement("w:fldChar")
            fld_end.set(qn("w:fldCharType"), "end")
            r_end.append(fld_end)
            p._p.append(r_end)

        _add_text_run("Página ")
        _add_field_code("PAGE")
        _add_text_run(" de ")
        _add_field_code("NUMPAGES")

    # =========================
    # VERIFICAR/INSERTAR TABLA DE ENCABEZADO 4x2
    # =========================
    
    def verificar_o_insertar_tabla_encabezado(self, doc, insertar_si_no_existe=True):
        sec = doc.sections[0]
        header = sec.header
        orient_h, size = self.get_page_setup(doc)

        if not orient_h:
            c3_cm = 9.5
        else:
            c3_cm = 16.0 if size == "letter" else 21.0 if size == "legal" else 16.0

        c1_cm, c2_cm, c4_cm = 2.0, 2.5, 4.0
        col_cm = [c1_cm, c2_cm, c3_cm, c4_cm]
        col_tw = [self.cm_to_twips(x) for x in col_cm]
        total_tw = sum(col_tw)

        if header.tables:
            tabla = header.tables[0]
            if len(tabla.rows) < 2 or len(tabla.columns) < 4:
                if insertar_si_no_existe:
                    tabla = header.add_table(rows=2, cols=4)
                else:
                    return None
        else:
            if insertar_si_no_existe:
                tabla = header.add_table(rows=2, cols=4)
            else:
                return None

        tabla.alignment = WD_TABLE_ALIGNMENT.CENTER
        try:
            tabla.autofit = False
            if hasattr(tabla, "allow_autofit"):
                tabla.allow_autofit = False
        except Exception:
            pass

        self.set_tbl_pr_fixed_width(tabla._element, total_tw)
        self.set_tbl_grid(tabla._element, col_tw)

        for row in tabla.rows:
            row.height_rule = WD_ROW_HEIGHT_RULE.EXACTLY
            row.height = Cm(0.8)
            for cell in row.cells:
                cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
                self.set_cell_margins(cell, 0, 0, 0, 0)

        for r in range(min(2, len(tabla.rows))):
            for c in range(min(4, len(tabla.columns))):
                self.set_cell_width_twips(tabla.cell(r, c), col_tw[c])

        self.merge_h(tabla, row=0, col_left=0, col_right=1)
        self.merge_v(tabla, col=2, row_top=0, row_bottom=1)
        self.merge_v(tabla, col=3, row_top=0, row_bottom=1)

        # ORDEN CRÍTICO: Primero tipografía default, LUEGO estilos específicos
        self.aplicar_tipografia_header_default(tabla)
        self.estilizar_celda_codigo(tabla)
        self.estilizar_celda_titulo(tabla)
        self.configurar_paginacion_header(tabla)
        self.estilizar_celdas_fila2_col1y2(tabla)

        return tabla

    # =========================
    # MÁRGENES Y HEADER/FOOTER DISTANCE
    # =========================
    
    def aplicar_margenes_y_encabezado_pie(self, doc):
        orient_h, _ = self.get_page_setup(doc)
        for sec in doc.sections:
            sec.top_margin = Cm(getattr(self, "MARGIN_TOP", 2.5))
            sec.bottom_margin = Cm(getattr(self, "MARGIN_BOTTOM", 2.5))
            sec.left_margin = Cm(getattr(self, "MARGIN_LEFT", 2.5))
            sec.right_margin = Cm(getattr(self, "MARGIN_RIGHT", 2.5))
            sec.header_distance = Cm(1.5 if orient_h else 1.0)
            sec.footer_distance = Cm(1.0)
            sec.gutter = Cm(0)

    def normalizar_parrafos_header_footer_fuera_de_tablas(self, doc):
        for sec in doc.sections:
            for p in sec.header.paragraphs:
                pf = p.paragraph_format
                pf.space_before = Pt(0)
                pf.space_after = Pt(0)
                pf.first_line_indent = Cm(0)
                pf.left_indent = Cm(0)
                pf.right_indent = Cm(0)
            for p in sec.footer.paragraphs:
                pf = p.paragraph_format
                pf.space_before = Pt(0)
                pf.space_after = Pt(0)
                pf.first_line_indent = Cm(0)
                pf.left_indent = Cm(0)
                pf.right_indent = Cm(0)

    # =========================
    # TIPOGRAFÍA CUERPO / TÍTULOS
    # =========================
    
    def _norm(self, txt: str) -> str:
        if txt is None:
            return ""
        s = txt.strip().lower()
        if s.endswith(":"):
            s = s[:-1].strip()
        for a, b in (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u")):
            s = s.replace(a, b)
        return " ".join(s.split())

    def _es_titulo(self, texto: str) -> bool:
        s = self._norm(texto)
        if not s:
            return False
        if s in self._TITULOS_NORM:
            return True
        if any(s.startswith(t + " ") for t in self._TITULOS_NORM):
            return True
        s_sin_num = re.sub(r"^[0-9]+(\.[0-9]+)*[\)\.]?\s*", "", s)
        if not s_sin_num:
            return False
        if s_sin_num in self._TITULOS_NORM:
            return True
        if any(s_sin_num.startswith(t + " ") for t in self._TITULOS_NORM):
            return True
        return False

    def _aplicar_formato_runs(self, runs, font_name, size_pt, color_rgb, bold=False, all_caps=False):
        for r in runs:
            r.font.name = font_name
            r.font.size = Pt(size_pt)
            r.font.bold = bool(bold)
            r.font.color.rgb = RGBColor(*color_rgb)
            r.font.all_caps = bool(all_caps)

    def _dar_formato_parrafo(self, p, font_name, size_pt, color_rgb, line=None, bold=False, all_caps=False):
        if line is None:
            line = self.BODY_LINE
        
        # Asegurar que el párrafo tiene propiedades independientes
        pf = p.paragraph_format
        pf.line_spacing = line
        pf.widow_control = True  # Separar control de párrafo
        
        # Aplicar formato a nivel de run (no de estilo global)
        for r in p.runs:
            r.font.name = font_name
            r.font.size = Pt(size_pt)
            r.font.bold = bool(bold)
            r.font.color.rgb = RGBColor(*color_rgb)
            # Usar transformación de texto en lugar de all_caps para independencia
            if all_caps:
                r.text = r.text.upper()
                # NO aplicar all_caps como propiedad de fuente para mantener editabilidad
                r.font.all_caps = False

    def aplicar_tipografia_cuerpo_y_titulos(self, doc):
        for p in doc.paragraphs:
            parent_tag = getattr(getattr(p._p, "getparent", lambda: None)(), "tag", "")
            if isinstance(parent_tag, str) and ("hdr" in parent_tag or "ftr" in parent_tag):
                continue
            texto = p.text.strip()
            if self._es_titulo(texto):
                self._dar_formato_parrafo(p, self.TITLE_FONT, self.TITLE_SIZE, self.TITLE_COLOR, 
                                          line=self.BODY_LINE, bold=False, all_caps=True)
            else:
                self._dar_formato_parrafo(p, self.BODY_FONT, self.BODY_SIZE, self.BODY_COLOR, 
                                          line=self.BODY_LINE, bold=False, all_caps=False)

        for t in doc.tables:
            parent_tag = t._element.getparent().tag
            if "hdr" in parent_tag or "ftr" in parent_tag:
                continue
            for row in t.rows:
                for cell in row.cells:
                    for p in cell.paragraphs:
                        texto = p.text.strip()
                        if self._es_titulo(texto):
                            self._dar_formato_parrafo(p, self.TITLE_FONT, self.TITLE_SIZE, self.TITLE_COLOR, 
                                                      line=self.BODY_LINE, bold=False, all_caps=True)
                        else:
                            self._dar_formato_parrafo(p, self.BODY_FONT, self.BODY_SIZE, self.BODY_COLOR, 
                                                      line=self.BODY_LINE, bold=False, all_caps=False)

    # =========================
    # NUMERALES (SOLO LISTAS NUMERADAS)
    # =========================
    
    def colorear_numerales_listas(self, doc, rgb_tuple=None, font_name=None, size_pt=12, hanging_cm=0.63):
        if rgb_tuple is None: rgb_tuple = self.TITLE_COLOR
        if font_name is None: font_name = self.TITLE_FONT
        try:
            num_part = doc.part.numbering_part
        except Exception:
            return

        root = num_part.element
        hex_color = "{:02X}{:02X}{:02X}".format(*rgb_tuple)
        sz_val = str(int(size_pt * 2))
        hanging_tw = str(self.cm_to_twips(hanging_cm))

        for abstract_num in root.iter(qn("w:abstractNum")):
            for lvl in abstract_num.iter(qn("w:lvl")):
                numFmt = lvl.find(qn("w:numFmt"))
                if numFmt is not None and (numFmt.get(qn("w:val")) or "").lower() == "bullet":
                    continue

                rPr = lvl.find(qn("w:rPr"))
                if rPr is None:
                    rPr = OxmlElement("w:rPr")
                    lvl.insert(0, rPr)

                rFonts = rPr.find(qn("w:rFonts"))
                if rFonts is None:
                    rFonts = OxmlElement("w:rFonts")
                    rPr.append(rFonts)
                for k in ("ascii", "hAnsi", "eastAsia", "cs"):
                    rFonts.set(qn(f"w:{k}"), font_name)

                color_el = rPr.find(qn("w:color"))
                if color_el is None:
                    color_el = OxmlElement("w:color")
                    rPr.append(color_el)
                color_el.set(qn("w:val"), hex_color)

                sz = rPr.find(qn("w:sz"))
                if sz is None:
                    sz = OxmlElement("w:sz")
                    rPr.append(sz)
                sz.set(qn("w:val"), sz_val)

                szCs = rPr.find(qn("w:szCs"))
                if szCs is None:
                    szCs = OxmlElement("w:szCs")
                    rPr.append(szCs)
                szCs.set(qn("w:val"), sz_val)

                pPr = lvl.find(qn("w:pPr"))
                if pPr is None:
                    pPr = OxmlElement("w:pPr")
                    lvl.append(pPr)

                ind = pPr.find(qn("w:ind"))
                if ind is None:
                    ind = OxmlElement("w:ind")
                    pPr.append(ind)
                ind.set(qn("w:left"), "0")
                ind.set(qn("w:right"), "0")
                ind.set(qn("w:hanging"), hanging_tw)

                spacing = pPr.find(qn("w:spacing"))
                if spacing is None:
                    spacing = OxmlElement("w:spacing")
                    pPr.append(spacing)
                spacing.set(qn("w:before"), "0")
                spacing.set(qn("w:after"), "0")

    # =========================
    # ESTILOS TABLAS PROCEDIMIENTO
    # =========================
    
    def aplicar_estilos_a_tablas_procedimiento(self, doc):
        for t in doc.tables:
            parent_tag = t._element.getparent().tag
            if "hdr" in parent_tag or "ftr" in parent_tag:
                continue
            for r_idx, row in enumerate(t.rows):
                for c_idx, cell in enumerate(row.cells):
                    for p in cell.paragraphs:
                        pf = p.paragraph_format
                        pf.line_spacing = 1.15
                        pf.space_before = Pt(0)
                        pf.space_after = Pt(0)
                        pf.first_line_indent = Cm(0)
                        pf.left_indent = Cm(0)
                        pf.right_indent = Cm(0)
                        
                        # Asegurar alineación centrada para columna "No." (columna 0) si es fila de contenido
                        if r_idx > 0 and c_idx == 0:
                             p.alignment = WD_ALIGN_PARAGRAPH.CENTER

                        for run in p.runs:
                            run.font.bold = False
                            run.font.color.rgb = RGBColor(*self.BODY_COLOR)
                            if r_idx == 0:
                                run.font.name = self.TITLE_FONT
                                run.font.size = Pt(10)
                            else:
                                run.font.name = self.BODY_FONT
                                run.font.size = Pt(9)

    # =========================
    # LÍNEA FINAL MICRO
    # =========================
    
    def agregar_linea_final_micro(self, doc, font_name=None):
        if font_name is None: font_name = self.BODY_FONT
        def _es_microlinea(p):
            txt = (p.text or "").replace("\u00A0", " ").strip()
            if len(txt) > 0:
                return False
            for r in p.runs:
                if r.font.size and abs(r.font.size.pt - 1.0) <= 0.2:
                    return True
            return False

        if len(doc.paragraphs) == 0:
            p = doc.add_paragraph()
        else:
            p = doc.paragraphs[-1]

        if _es_microlinea(p):
            return

        if (p.text or "").strip() == "" and len(p.runs) == 0:
            par = p
        else:
            par = doc.add_paragraph()

        pf = par.paragraph_format
        pf.space_before = Pt(0)
        pf.space_after = Pt(0)
        pf.first_line_indent = Cm(0)
        pf.left_indent = Cm(0)
        pf.right_indent = Cm(0)
        pf.line_spacing = 1.0

        run = par.add_run("\u00A0")
        run.font.name = font_name
        run.font.size = Pt(1)
        run.font.bold = False
        run.font.color.rgb = RGBColor(*self.BODY_COLOR)

    # =========================
    # ITERADOR DE BLOQUES
    # =========================
    
    def _iter_doc_blocks(self, doc):
        body = doc.element.body
        for child in body.iterchildren():
            tag = child.tag
            if tag.endswith("}p"):
                yield Paragraph(child, doc)
            elif tag.endswith("}tbl"):
                yield Table(child, doc)

    # =========================
    # CONFIGURAR TABLAS POR SECCIÓN
    # =========================
    
    def find_next_table_after_title(self, doc, title_variants):
        wanted = set(self._norm(t) for t in title_variants)
        blocks = list(self._iter_doc_blocks(doc))
        for i, blk in enumerate(blocks):
            if isinstance(blk, Paragraph) and self._norm(blk.text) in wanted:
                for j in range(i + 1, len(blocks)):
                    nb = blocks[j]
                    if isinstance(nb, Table):
                        return nb
                    if isinstance(nb, Paragraph) and self._es_titulo(nb.text):
                        return None
        return None

    def apply_table_widths_cm(self, tabla, widths_cm):
        col_tw = [self.cm_to_twips(w) for w in widths_cm]
        self.set_tbl_pr_fixed_width(tabla._element, sum(col_tw))
        self.set_tbl_grid(tabla._element, col_tw)
        for c in range(min(len(widths_cm), len(tabla.columns))):
            wtw = col_tw[c]
            for row in tabla.rows:
                self.set_cell_width_twips(row.cells[c], wtw)

    def set_header_titles(self, tabla, titles, font=None, size_pt=10, color=None):
        if font is None: font = self.TITLE_FONT
        if color is None:
            color = RGBColor(*self.BODY_COLOR)
        if len(tabla.rows) == 0:
            tabla.add_row()
        row0 = tabla.rows[0]
        for i, txt in enumerate(titles):
            if i >= len(row0.cells):
                break
            cell = row0.cells[i]
            self.clear_cell(cell)
            p = cell.add_paragraph(txt)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            pf = p.paragraph_format
            pf.line_spacing = 1.15
            pf.space_before = Pt(0)
            pf.space_after = Pt(0)
            for r in p.runs:
                r.font.name = font
                r.font.size = Pt(size_pt)
                r.font.bold = False
                r.font.color.rgb = color

    def set_row_heights_cm(self, tabla, heights_cm, start_row=0):
        for idx, h in enumerate(heights_cm):
            r = start_row + idx
            if r < len(tabla.rows):
                tabla.rows[r].height_rule = WD_ROW_HEIGHT_RULE.EXACTLY
                tabla.rows[r].height = Cm(h)

    def _ensure_table_rows(self, tabla, n_rows):
        while len(tabla.rows) < n_rows:
            tabla.add_row()
        while len(tabla.rows) > n_rows:
            tabla._tbl.remove(tabla.rows[-1]._tr)

    def configurar_tabla_descripcion_actividades(self, doc):
        t = self.find_next_table_after_title(doc, ["descripción de actividades", "descripcion de actividades"])
        if not t:
            return
        self.apply_table_widths_cm(t, [1.0, 3.6, 9.6, 3.8])
        self.set_header_titles(t, ["No.", "Responsable", "Actividad(descripción)", "Registros relacionados"])
        self.shade_table_header_generic(t, hex_fill=self.HEADER_FILL)
        self.set_row_heights_cm(t, [0.9], start_row=0)

    def configurar_tabla_doc_reg(self, doc):
        t = self.find_next_table_after_title(doc, ["documentos y registros relacionados"])
        if not t:
            return
        self.apply_table_widths_cm(t, [3.6, 11.5, 2.9])
        self.set_header_titles(t, ["Tipo", "Nombre", "Código"])
        self.shade_table_header_generic(t, hex_fill=self.HEADER_FILL)

    def configurar_tabla_lista_anexos(self, doc):
        t = self.find_next_table_after_title(doc, ["lista de anexos"])
        if not t:
            return
        self.apply_table_widths_cm(t, [1.0, 5.5, 11.5])
        self.set_header_titles(t, ["No.", "Nombre del documento", "Código"])
        self.shade_table_header_generic(t, hex_fill=self.HEADER_FILL)

    def configurar_tabla_control_version(self, doc):
        t = self.find_next_table_after_title(doc, ["control de versión", "control de version"])
        if not t:
            return
        self.apply_table_widths_cm(t, [1.0, 14.8, 2.2])
        self.set_header_titles(t, ["No.", "Identificación del cambio", "Fecha"])
        self.shade_table_header_generic(t, hex_fill=self.HEADER_FILL)

    def configurar_tabla_aprobaciones(self, doc):
        t = self.find_next_table_after_title(
            doc,
            [
                "elaboración, revisión y aprobación", "elaboracion, revision y aprobacion",
                "modificación, revisión y aprobación", "modificacion, revision y aprobacion",
                "aprobaciones"
            ]
        )
        if not t:
            return

        self.apply_table_widths_cm(t, [2.1, 5.3, 5.3, 5.3])
        self._ensure_table_rows(t, 4)
        self.set_header_titles(t, ["", "Modificó", "Revisó", "Aprobó"])
        self.shade_row_cells(t, 0, cols=range(1, min(4, len(t.columns))), hex_fill=self.HEADER_FILL)
        for r in range(1, len(t.rows)):
            if len(t.rows[r].cells) > 0:
                cell = t.rows[r].cells[0]
                self.shade_cell_robust(cell, self.HEADER_FILL)
                # FIX: Primera columna con formato institucional
                self.format_cell_paragraphs_fonts(
                    cell, 
                    font_name=self.TITLE_FONT, 
                    size_pt=10, 
                    rgb_tuple=self.BODY_COLOR, 
                    bold=False, 
                    center=True, 
                    line=1.0
                )
        self.set_row_heights_cm(t, [0.6, 0.6, 0.9], start_row=1)

    # =========================
    # PASADA FINAL DE SOMBREADO (CRÍTICO)
    # =========================
    
    def _is_aprobaciones_header_row(self, tabla):
        if len(tabla.rows) == 0 or len(tabla.rows[0].cells) < 4:
            return False
        c1 = self._norm(tabla.rows[0].cells[1].text)
        c2 = self._norm(tabla.rows[0].cells[2].text)
        c3 = self._norm(tabla.rows[0].cells[3].text)
        return (c1 in {"modifico", "modificó"} and c2.startswith("revis") and c3.startswith("aprobo"))

    def reaplicar_color_headers_final(self, doc, hex_fill=None):
        """
        PASADA FINAL CRÍTICA: Reaplica sombreado a encabezados del cuerpo.
        NUNCA toca celdas con fill 58595B (celda de código).
        """
        if hex_fill is None:
            hex_fill = self.HEADER_FILL

        for t in doc.tables:
            parent_tag = t._element.getparent().tag
            if "hdr" in parent_tag or "ftr" in parent_tag:
                continue

            if len(t.rows) == 0:
                continue

            if self._is_aprobaciones_header_row(t):
                if len(t.rows[0].cells) > 0:
                    self.clear_cell_shading(t.rows[0].cells[0])

                for c in range(1, len(t.rows[0].cells)):
                    cell = t.rows[0].cells[c]
                    current_fill = self.get_cell_fill_hex(cell)
                    if current_fill == self.CODE_FILL.upper():
                        continue
                    self.shade_cell_robust(cell, hex_fill)

                for r in range(1, len(t.rows)):
                    if len(t.rows[r].cells) > 0:
                        cell = t.rows[r].cells[0]
                        current_fill = self.get_cell_fill_hex(cell)
                        if current_fill == self.CODE_FILL.upper():
                            continue
                        self.shade_cell_robust(cell, hex_fill)
            else:
                for c in range(len(t.rows[0].cells)):
                    cell = t.rows[0].cells[c]
                    current_fill = self.get_cell_fill_hex(cell)
                    if current_fill == self.CODE_FILL.upper():
                        continue
                    self.shade_cell_robust(cell, hex_fill)

    # =========================
    # CORRECCIÓN DE NOMENCLATURA
    # =========================

    def corregir_nomenclatura_secciones(self, doc):
        """
        Busca y reemplaza títulos de secciones para asegurar consistencia institucional.
        Busca tanto en párrafos del cuerpo como dentro de TABLAS.
        """
        reemplazos = {
            "periodicidad": "PERIODICIDAD",
            "perodicidad": "PERIODICIDAD",
            "normatividad": "NORMATIVA Y POLÍTICAS",
            "normatividad y políticas": "NORMATIVA Y POLÍTICAS",
            "documentos relacionados": "DOCUMENTOS Y REGISTROS RELACIONADOS",
            "documentos y registros relacionados": "DOCUMENTOS Y REGISTROS RELACIONADOS",
            "control de cambios": "CONTROL DE VERSIÓN",
            "control de versión": "CONTROL DE VERSIÓN",
            "aprobación": "ELABORACIÓN, REVISIÓN Y APROBACIÓN",
            "aprobacion": "ELABORACIÓN, REVISIÓN Y APROBACIÓN",
            "elaboración, revisión y aprobación": "ELABORACIÓN, REVISIÓN Y APROBACIÓN"
        }

        def _procesar_parrafo(p):
            texto_raw = p.text
            texto_norm = texto_raw.strip().lower()
            
            # Caso 1: Coincidencia exacta (ignorando case)
            if texto_norm in reemplazos:
                nuevo_texto = reemplazos[texto_norm]
                # Limpiar párrafo y agregar nuevo run con formato
                p.clear()
                run = p.add_run(nuevo_texto)
                run.font.name = self.TITLE_FONT
                run.font.size = Pt(self.TITLE_SIZE)
                run.font.color.rgb = RGBColor(*self.TITLE_COLOR)
                run.font.bold = False
                p.paragraph_format.line_spacing = self.BODY_LINE
                return

            # Caso 2: Título numerado (ej "3. Perodicidad")
            match = re.match(r"^(\d+(\.\d+)*[\)\.]?)\s*(.*)$", texto_raw)
            if match:
                numeral = match.group(1)
                resto = match.group(3).lower()
                if resto in reemplazos:
                    nuevo_texto = f"{numeral} {reemplazos[resto]}"
                    # Limpiar párrafo y agregar nuevo run con formato
                    p.clear()
                    run = p.add_run(nuevo_texto)
                    run.font.name = self.TITLE_FONT
                    run.font.size = Pt(self.TITLE_SIZE)
                    run.font.color.rgb = RGBColor(*self.TITLE_COLOR)
                    run.font.bold = False
                    p.paragraph_format.line_spacing = self.BODY_LINE

        # 1. Buscar en párrafos del cuerpo
        for p in doc.paragraphs:
            _procesar_parrafo(p)

        # 2. Buscar en todas las tablas
        for t in doc.tables:
            for row in t.rows:
                for cell in row.cells:
                    for p in cell.paragraphs:
                        _procesar_parrafo(p)

        # 3. BÚSQUEDA AGRESIVA A NIVEL DE RUN para "Perodicidad" (caso donde texto está fragmentado)
        typo_replacements = [
            ("Perodicidad", "PERIODICIDAD"),
            ("PERODICIDAD", "PERIODICIDAD"),
            ("perodicidad", "PERIODICIDAD"),
        ]
        
        def _fix_runs_in_paragraph(p):
            for run in p.runs:
                for typo, fix in typo_replacements:
                    if typo in run.text:
                        run.text = run.text.replace(typo, fix)

        for p in doc.paragraphs:
            _fix_runs_in_paragraph(p)
        
        for t in doc.tables:
            for row in t.rows:
                for cell in row.cells:
                    for p in cell.paragraphs:
                        _fix_runs_in_paragraph(p)

    # =========================
    # FLUJO PRINCIPAL
    # =========================
    
    def format_document(self, input_source, output_path=None):
        """
        Formatea un documento Word aplicando todos los estilos institucionales.
        
        Args:
            input_source: Puede ser un path (str), un objeto BytesIO, o un archivo abierto
            output_path: Path de salida opcional. Si es None, retorna BytesIO
            
        Returns:
            Si output_path es None: BytesIO con el documento formateado
            Si output_path es str: El path del archivo guardado
        """
        # Cargar documento
        if isinstance(input_source, str):
            doc = Document(input_source)
        elif isinstance(input_source, io.BytesIO):
            input_source.seek(0)
            doc = Document(input_source)
        else:
            doc = Document(input_source)

        # 0. CORRECCIÓN DE NOMENCLATURA (Antes de formatear estilos)
        self.corregir_nomenclatura_secciones(doc)

        # 1. Configurar estilos de paginación
        self.asegurar_estilo_paginacion(doc)

        # 2. Aplicar márgenes y distancias de encabezado/pie
        self.aplicar_margenes_y_encabezado_pie(doc)

        # 3. Crear/verificar tabla de encabezado (incluye celda código 58595B)
        self.verificar_o_insertar_tabla_encabezado(doc, insertar_si_no_existe=True)

        # 4. Normalizar párrafos de header/footer
        self.normalizar_parrafos_header_footer_fuera_de_tablas(doc)

        # 5. Aplicar tipografías a cuerpo y títulos
        self.aplicar_tipografia_cuerpo_y_titulos(doc)

        # 6. Colorear numerales de listas
        self.colorear_numerales_listas(
            doc,
            rgb_tuple=self.TITLE_COLOR,
            font_name=self.TITLE_FONT,
            size_pt=12,
            hanging_cm=0.63
        )

        # 7. Aplicar estilos a tablas de procedimiento
        self.aplicar_estilos_a_tablas_procedimiento(doc)

        # 8. Configurar tablas por sección
        self.configurar_tabla_descripcion_actividades(doc)
        self.configurar_tabla_doc_reg(doc)
        self.configurar_tabla_lista_anexos(doc)
        self.configurar_tabla_control_version(doc)
        self.configurar_tabla_aprobaciones(doc)

        # 9. Agregar línea final micro
        self.agregar_linea_final_micro(doc)

        # 10. PASADA FINAL CRÍTICA: Reaplicar sombreado de encabezados
        self.reaplicar_color_headers_final(doc, hex_fill=self.HEADER_FILL)

        # Guardar resultado
        if output_path:
            doc.save(output_path)
            return output_path
        else:
            mem_file = io.BytesIO()
            doc.save(mem_file)
            mem_file.seek(0)
            return mem_file
