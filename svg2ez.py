#!/usr/bin/env python3
"""
Svg2Ez — SVG to EzCad3 DXF Converter
Free tool for laser engravers using Inkscape + EzCad3
"""

import sys, os, math, re, threading, webbrowser, json, urllib.request
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, colorchooser

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

from lxml import etree
import ezdxf

# ─── App info ────────────────────────────────────────────────────────────────
APP_NAME     = "Svg2Ez"
VERSION      = "1.0.0"
PAYPAL_URL    = "https://www.paypal.com/donate/?hosted_button_id=W9BE8867AF8SA"
WEBSITE_URL   = "https://github.com/kibalyion/svg2ez"
ISSUES_URL    = "https://github.com/kibalyion/svg2ez/issues/new"
FEEDBACK_EMAIL = "contacto@joyeriahago.com"
ANALYTICS_URL = "https://joyeriahago.com/svg2ez_ping.php"  # Contador propio

# ─── Config file ─────────────────────────────────────────────────────────────
CONFIG_DIR  = os.path.join(os.path.expanduser("~"), ".svg2ez")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_COLOR_MAP = {
    "#000000": {"type": "CUT_INNER",  "label_key": "cut_inner",  "dxf_color": "#000000"},
    "#8800ff": {"type": "CUT_OUTER",  "label_key": "cut_outer",  "dxf_color": "#8800ff"},
    "#0000ff": {"type": "ENGRAVE",    "label_key": "engrave",    "dxf_color": "#0000ff"},
    "#ff0000": {"type": "ENGRAVE",    "label_key": "engrave",    "dxf_color": "#ff0000"},
    "#ff00ff": {"type": "ENGRAVE",    "label_key": "engrave",    "dxf_color": "#ff00ff"},
    "#00ffff": {"type": "OTHER",      "label_key": "other",      "dxf_color": "#00ffff"},
    "#00ff00": {"type": "OTHER",      "label_key": "other",      "dxf_color": "#00ff00"},
    "#ffbb00": {"type": "OTHER",      "label_key": "other",      "dxf_color": "#ffbb00"},
    "#ffff00": {"type": "OTHER",      "label_key": "other",      "dxf_color": "#ffff00"},
}

DEFAULT_CONFIG = {
    "language": "en",
    "color_map": DEFAULT_COLOR_MAP,
    "bezier_quality": 8,
    "show_donate_after": True,
    "conversions_done": 0,
}

# ─── Traducciones ─────────────────────────────────────────────────────────────
LANGS = {
    "en": {
        "app_title":      "Svg2Ez — SVG to EzCad3 Converter",
        "open_btn":       "📂  Open SVG & Convert",
        "drag_hint":      "⬇  Drag an SVG file here",
        "settings":       "⚙ Settings",
        "help":           "? Help",
        "donate":         "💛 Donate",
        "converting":     "Converting...",
        "designs_found":  "Designs found",
        "entities":       "entities",
        "layers":         "layers",
        "saved_to":       "Saved to",
        "error":          "Error",
        "done_title":     "Conversion complete!",
        "done_msg":       "File saved:\n{path}\n\nSvg2Ez is free. If it saved you time,\na small donation keeps it maintained. ☕",
        "donate_ask":     "Open PayPal to donate?",
        "wrong_format":   "Please drop an .SVG file",
        "cut_inner":      "Cut Interior",
        "cut_outer":      "Cut Exterior",
        "engrave":        "Engrave",
        "other":          "Other",
        "settings_title": "Color Mapping",
        "settings_info":  "Map each SVG color to a layer type.\nColors in Inkscape determine how EzCad3 will process each object.",
        "add_color":      "+ Add color",
        "remove":         "Remove",
        "save":           "Save",
        "cancel":         "Cancel",
        "quality_label":  "Curve quality (higher = smoother but slower):",
        "help_title":     "How Svg2Ez works",
        "help_text": """SVG2EZ — Quick Guide
═══════════════════════════════════════

WHAT IT DOES
  Converts Inkscape SVG files to DXF files that EzCad3
  can import correctly — keeping groups separate and all
  paths perfectly closed so EzCad3 can generate hatches.

WHY YOU NEED IT
  EzCad3 crashes or distorts complex SVGs from Inkscape.
  Svg2Ez pre-processes the file solving these problems.

HOW TO USE IT
  1. In Inkscape: assign colors to each element:
       Black  #000000 → Interior cut
       Purple #8800FF → Exterior cut
       Blue   #0000FF → Engrave (hatching)
  2. Group each design with Ctrl+G
  3. Open the SVG with Svg2Ez (button or drag & drop)
  4. A _ezcad.dxf file is created in the same folder
  5. In EzCad3: File → Import → select the .dxf
  6. Each design appears as an independent group
  7. Select the ENGRAVE layer → Modify → Hatch

TIPS
  • Each Inkscape group = one independent design in EzCad3
  • Name your groups in Inkscape (Object Properties)
    so they appear with that name in EzCad3
  • You can customize colors in Settings ⚙
  • The DXF is always in the same folder as the SVG

COMPATIBLE APPLICATIONS
  ✓ Inkscape        — Full support, recommended workflow
  ✓ Adobe Illustrator — CSS class styles read automatically
                        Text → Create Outlines before converting
  ✓ LightBurn       — Exported SVGs work directly
                        Layer colors are preserved

  Svg2Ez reads fill/stroke colors from any SVG source
  and maps them to EzCad3 layers automatically.""",
        "lang_label":     "Language:",
        "feedback": "🐛 Feedback",
        "feedback_title": "Bug report / Suggestion",
        "feedback_msg": "How do you want to send your feedback?",
        "via_github": "GitHub (recommended)",
        "via_email": "Email",
        "feedback_hint": "Report bugs or suggest features",
        "restart_needed":  "Language changed. Please restart Svg2Ez to apply.",
        "restart_title":  "Restart required",
        "output_color":  "DXF Color (EzCad3)",
        "input_color":  "SVG Color",
    },
    "es": {
        "app_title":      "Svg2Ez — Conversor SVG a EzCad3",
        "open_btn":       "📂  Abrir SVG y Convertir",
        "drag_hint":      "⬇  Arrastra un archivo SVG aquí",
        "settings":       "⚙ Ajustes",
        "help":           "? Ayuda",
        "donate":         "💛 Donar",
        "converting":     "Convirtiendo...",
        "designs_found":  "Diseños encontrados",
        "entities":       "entidades",
        "layers":         "capas",
        "saved_to":       "Guardado en",
        "error":          "Error",
        "done_title":     "¡Conversión completada!",
        "done_msg":       "Archivo guardado:\n{path}\n\nSvg2Ez es gratuito. Si te ha ahorrado tiempo,\nuna donación ayuda a mantenerlo. ☕",
        "donate_ask":     "¿Abrir PayPal para donar?",
        "wrong_format":   "Por favor arrastra un archivo .SVG",
        "cut_inner":      "Corte Interior",
        "cut_outer":      "Corte Exterior",
        "engrave":        "Grabado",
        "other":          "Otro",
        "settings_title": "Mapeo de Colores",
        "settings_info":  "Asigna cada color SVG a un tipo de capa.\nLos colores en Inkscape determinan cómo procesará EzCad3 cada objeto.",
        "add_color":      "+ Añadir color",
        "remove":         "Eliminar",
        "save":           "Guardar",
        "cancel":         "Cancelar",
        "quality_label":  "Calidad de curvas (mayor = más suave pero más lento):",
        "help_title":     "Cómo funciona Svg2Ez",
        "help_text": """SVG2EZ — Guía rápida
═══════════════════════════════════════

QUÉ HACE
  Convierte SVGs de Inkscape a archivos DXF que EzCad3
  puede importar correctamente — manteniendo los grupos
  separados y todos los paths bien cerrados para que
  EzCad3 pueda generar los hatches sin errores.

POR QUÉ LO NECESITAS
  EzCad3 se cae o distorsiona SVGs complejos de Inkscape.
  Svg2Ez preprocesa el archivo resolviendo estos problemas.

CÓMO USARLO
  1. En Inkscape: asigna colores a cada elemento:
       Negro  #000000 → Corte interior
       Morado #8800FF → Corte exterior
       Azul   #0000FF → Grabado (hatch)
  2. Agrupa cada diseño con Ctrl+G
  3. Abre el SVG con Svg2Ez (botón o arrastrar)
  4. Se crea un archivo _ezcad.dxf en la misma carpeta
  5. En EzCad3: File → Import → selecciona el .dxf
  6. Cada diseño aparece como grupo independiente
  7. Selecciona la capa GRABADO → Modify → Hatch

CONSEJOS
  • Cada grupo de Inkscape = un diseño independiente en EzCad3
  • Nombra tus grupos en Inkscape (Propiedades del objeto)
    para que aparezcan con ese nombre en EzCad3
  • Puedes personalizar los colores en Ajustes ⚙
  • El DXF se guarda siempre en la misma carpeta que el SVG

APLICACIONES COMPATIBLES
  ✓ Inkscape          — Soporte completo, flujo recomendado
  ✓ Adobe Illustrator — Estilos CSS leídos automáticamente
                        Convierte texto a trazados antes
  ✓ LightBurn         — Los SVG exportados funcionan directamente
                        Los colores de capas se preservan

  Svg2Ez lee colores fill/stroke de cualquier SVG y los
  mapea a capas de EzCad3 automáticamente.""",
        "lang_label":     "Idioma:",
        "feedback": "🐛 Feedback",
        "feedback_title": "Bug / Sugerencia",
        "feedback_msg": "¿Cómo quieres enviar tu comentario?",
        "via_github": "GitHub (recomendado)",
        "via_email": "Email",
        "feedback_hint": "Reporta errores o sugiere mejoras",
        "restart_needed":  "Idioma cambiado. Reinicia Svg2Ez para aplicarlo.",
        "restart_title":  "Reinicio necesario",
        "output_color":  "Color DXF (EzCad3)",
        "input_color":  "Color SVG",
    },
    "de": {
        "app_title":      "Svg2Ez — SVG zu EzCad3 Konverter",
        "open_btn":       "📂  SVG öffnen & konvertieren",
        "drag_hint":      "⬇  SVG-Datei hier ablegen",
        "settings":       "⚙ Einstellungen",
        "help":           "? Hilfe",
        "donate":         "💛 Spenden",
        "converting":     "Konvertiere...",
        "designs_found":  "Designs gefunden",
        "entities":       "Elemente",
        "layers":         "Ebenen",
        "saved_to":       "Gespeichert in",
        "error":          "Fehler",
        "done_title":     "Konvertierung abgeschlossen!",
        "done_msg":       "Datei gespeichert:\n{path}\n\nSvg2Ez ist kostenlos. Eine kleine Spende\nhilft, es weiterzuentwickeln. ☕",
        "donate_ask":     "PayPal für Spende öffnen?",
        "wrong_format":   "Bitte eine .SVG-Datei ablegen",
        "cut_inner":      "Innenschnitt",
        "cut_outer":      "Außenschnitt",
        "engrave":        "Gravur",
        "other":          "Sonstige",
        "settings_title": "Farb-Zuordnung",
        "settings_info":  "Ordne jeder SVG-Farbe einen Ebenentyp zu.",
        "add_color":      "+ Farbe hinzufügen",
        "remove":         "Entfernen",
        "save":           "Speichern",
        "cancel":         "Abbrechen",
        "quality_label":  "Kurvenqualität (höher = glatter aber langsamer):",
        "help_title":     "Wie Svg2Ez funktioniert",
        "help_text": """SVG2EZ — Kurzanleitung
═══════════════════════════════════════

WAS ES TUT
  Konvertiert Inkscape SVG-Dateien in DXF-Dateien,
  die EzCad3 korrekt importieren kann.

WARUM SIE ES BRAUCHEN
  EzCad3 stürzt bei komplexen SVGs aus Inkscape ab.
  Svg2Ez löst diese Probleme.

WIE MAN ES BENUTZT
  1. In Inkscape: Farben zuweisen:
       Schwarz #000000 → Innenschnitt
       Lila    #8800FF → Außenschnitt
       Blau    #0000FF → Gravur (Schraffur)
  2. Jedes Design mit Ctrl+G gruppieren
  3. SVG mit Svg2Ez öffnen
  4. Eine _ezcad.dxf-Datei wird erstellt
  5. In EzCad3: Datei → Importieren → .dxf auswählen""",
        "lang_label":     "Sprache:",
        "feedback": "🐛 Feedback",
        "feedback_title": "Fehler / Vorschlag",
        "feedback_msg": "Wie möchten Sie Ihr Feedback senden?",
        "via_github": "GitHub (empfohlen)",
        "via_email": "E-Mail",
        "feedback_hint": "Fehler melden oder Funktionen vorschlagen",
        "restart_needed":  "Sprache geändert. Bitte Svg2Ez neu starten.",
        "restart_title":  "Neustart erforderlich",
        "output_color":  "DXF-Farbe (EzCad3)",
        "input_color":  "SVG-Farbe",
    },
    "zh": {
        "app_title":      "Svg2Ez — SVG转EzCad3工具",
        "open_btn":       "📂  打开SVG文件并转换",
        "drag_hint":      "⬇  将SVG文件拖放到此处",
        "settings":       "⚙ 设置",
        "help":           "? 帮助",
        "donate":         "💛 捐赠",
        "converting":     "转换中...",
        "designs_found":  "发现设计",
        "entities":       "个图形",
        "layers":         "个图层",
        "saved_to":       "已保存至",
        "error":          "错误",
        "done_title":     "转换完成！",
        "done_msg":       "文件已保存：\n{path}\n\nSvg2Ez是免费软件。如果对您有帮助，\n欢迎小额捐赠以支持维护。☕",
        "donate_ask":     "打开PayPal捐赠？",
        "wrong_format":   "请拖放一个.SVG文件",
        "cut_inner":      "内切割",
        "cut_outer":      "外切割",
        "engrave":        "雕刻",
        "other":          "其他",
        "settings_title": "颜色映射",
        "settings_info":  "将每个SVG颜色映射到图层类型。",
        "add_color":      "+ 添加颜色",
        "remove":         "删除",
        "save":           "保存",
        "cancel":         "取消",
        "quality_label":  "曲线质量（越高越平滑但越慢）：",
        "help_title":     "Svg2Ez使用说明",
        "help_text": """SVG2EZ — 快速指南
═══════════════════════════════════════

功能说明
  将Inkscape SVG文件转换为EzCad3可正确导入的DXF文件。
  保持分组独立，所有路径完全闭合，
  使EzCad3可以正常生成填充线。

为什么需要它
  EzCad3导入复杂SVG时会崩溃或变形。
  Svg2Ez预处理文件解决这些问题。

使用方法
  1. 在Inkscape中分配颜色：
       黑色 #000000 → 内切割
       紫色 #8800FF → 外切割
       蓝色 #0000FF → 雕刻（填充）
  2. 用Ctrl+G对每个设计分组
  3. 用Svg2Ez打开SVG文件
  4. 在同一文件夹生成_ezcad.dxf文件
  5. 在EzCad3中: 文件 → 导入 → 选择.dxf文件
  6. 每个设计作为独立组出现""",
        "lang_label":     "语言：",
        "feedback": "🐛 反馈",
        "feedback_title": "错误报告 / 建议",
        "feedback_msg": "您想如何发送反馈？",
        "via_github": "GitHub（推荐）",
        "via_email": "电子邮件",
        "feedback_hint": "报告错误或提出功能建议",
        "restart_needed":  "语言已更改。请重启 Svg2Ez 以应用。",
        "restart_title":  "需要重启",
        "output_color":  "DXF颜色 (EzCad3)",
        "input_color":  "SVG颜色",
    },
}

LANG_NAMES = {"en": "English", "es": "Español", "de": "Deutsch", "zh": "中文"}


# ─── Config manager ───────────────────────────────────────────────────────────
def load_config():
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            # Merge con defaults para claves nuevas
            for k, v in DEFAULT_CONFIG.items():
                if k not in cfg:
                    cfg[k] = v
            return cfg
    except Exception:
        pass
    return DEFAULT_CONFIG.copy()

def save_config(cfg):
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


# ─── Analytics (anónimo, solo cuenta aperturas) ───────────────────────────────
ANALYTICS_TOKEN = 'svg2ez-hago-2024-xK9mP'  # debe coincidir con el PHP

def ping_analytics():
    """Envía ping anónimo al contador propio. Falla silenciosamente."""
    try:
        url = f"{ANALYTICS_URL}?v={VERSION}&token={ANALYTICS_TOKEN}"
        req = urllib.request.Request(
            url,
            headers={'User-Agent': f'Svg2Ez/{VERSION}'},
        )
        urllib.request.urlopen(req, timeout=3)
    except Exception:
        pass


# ─── Motor de conversión ──────────────────────────────────────────────────────
INK_NS      = 'http://www.inkscape.org/namespaces/inkscape'

def normalize_color(s):
    if not s or s.strip().lower() in ('none','inherit','transparent',''): return None
    s=s.strip().lower()
    if s.startswith('#'):
        h=s[1:]
        if len(h)==3: h=h[0]*2+h[1]*2+h[2]*2
        return '#'+h.zfill(6)
    return None

def parse_style(st):
    p={}
    if not st: return p
    for part in st.split(';'):
        if ':' in part:
            k,v=part.split(':',1); p[k.strip()]=v.strip()
    return p

def hex_to_dxf_color(hex_color):
    """Convierte color hex (#rrggbb) al índice de color ACI de DXF más cercano."""
    # Colores ACI estándar de DXF (índice: (R,G,B))
    ACI = {
        7:  (0,0,0),        # Negro
        1:  (255,0,0),     # Rojo
        2:  (255,255,0),   # Amarillo
        3:  (0,255,0),     # Verde
        4:  (0,255,255),   # Cyan
        5:  (0,0,255),     # Azul
        6:  (255,0,255),   # Magenta
        8:  (128,128,128), # Gris oscuro
        9:  (192,192,192), # Gris claro
        30: (255,128,0),   # Naranja
        40: (255,200,0),   # Amarillo-naranja
        11: (0,128,255),   # Azul claro
        141:(128,0,255),   # Violeta
    }
    try:
        h = hex_color.lstrip('#')
        r,g,b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
        best_idx = 7
        best_dist = float('inf')
        for idx,(ar,ag,ab) in ACI.items():
            dist = (r-ar)**2 + (g-ag)**2 + (b-ab)**2
            if dist < best_dist:
                best_dist = dist
                best_idx = idx
        return best_idx
    except Exception:
        return 7  # negro por defecto

def parse_css_block(root):
    """Lee bloque <style>. Compatible con Illustrator (.cls-1{fill:#xxx})"""
    css = {}
    SVG_NS = "http://www.w3.org/2000/svg"
    import re as _re2
    pat = _re2.compile(r"[.#]([\w-]+)\s*\{([^}]+)\}")
    for style_el in root.iter(f"{{{SVG_NS}}}style"):
        text = style_el.text or ""
        for match in pat.finditer(text):
            props = {}
            for prop in match.group(2).split(";"):
                prop = prop.strip()
                if ":" in prop:
                    k, v = prop.split(":", 1)
                    props[k.strip()] = v.strip()
            css[match.group(1)] = props
    return css

def resolve_style(el, css_classes):
    """
    Obtiene los estilos reales de un elemento considerando:
    1. Atributos directos (fill=, stroke=)
    2. style inline (style='fill:#xxx')
    3. Clases CSS del bloque <style> (class='cls-1')
    Prioridad: inline > clase CSS > atributo directo
    """
    # Empezar con atributos directos
    result = {}
    for attr in ['fill', 'stroke', 'stroke-width', 'opacity']:
        val = el.get(attr)
        if val: result[attr] = val

    # Clases CSS
    class_attr = el.get('class', '')
    for cls in class_attr.split():
        if cls in css_classes:
            result.update(css_classes[cls])

    # Style inline (mayor prioridad)
    inline = parse_style(el.get('style', ''))
    result.update(inline)

    return result

def svg_tag(el):
    t = el.tag
    if callable(t): return '##comment##'  # comentarios XML, PIs, etc.
    return t.split('}',1)[1] if '}' in t else t

def has_color(el, css_classes=None):
    """Detecta si un elemento tiene color, incluyendo clases CSS de Illustrator."""
    st = resolve_style(el, css_classes or {})
    for c in [st.get('fill', el.get('fill','')), st.get('stroke', el.get('stroke',''))]:
        if c and c.strip().lower() not in ('','none'): return True
    # También detectar si tiene class= que podría tener color
    if el.get('class','') and css_classes:
        for cls in el.get('class','').split():
            if cls in css_classes: return True
    return False

def parse_transform(t):
    if not t: return [1,0,0,1,0,0]
    m=[1,0,0,1,0,0]
    mo=re.search(r'matrix\(([^)]+)\)',t)
    if mo:
        v=[float(x) for x in re.split(r'[,\s]+',mo.group(1).strip())]
        if len(v)==6: m=v
    tr=re.search(r'translate\(([^)]+)\)',t)
    if tr:
        v=[float(x) for x in re.split(r'[,\s]+',tr.group(1).strip())]
        m=mul(m,[1,0,0,1,v[0],v[1] if len(v)>1 else 0])
    sc=re.search(r'scale\(([^)]+)\)',t)
    if sc:
        v=[float(x) for x in re.split(r'[,\s]+',sc.group(1).strip())]
        m=mul(m,[v[0],0,0,v[1] if len(v)>1 else v[0],0,0])
    ro=re.search(r'rotate\(([^)]+)\)',t)
    if ro:
        v=[float(x) for x in re.split(r'[,\s]+',ro.group(1).strip())]
        a=math.radians(v[0]); ca,sa=math.cos(a),math.sin(a)
        rm=[ca,sa,-sa,ca,0,0]
        if len(v)==3:
            cx,cy=v[1],v[2]; rm[4]=cx-cx*ca+cy*sa; rm[5]=cy-cx*sa-cy*ca
        m=mul(m,rm)
    return m

def mul(a,b):
    a1,b1,c1,d1,e1,f1=a; a2,b2,c2,d2,e2,f2=b
    return [a1*a2+c1*b2,b1*a2+d1*b2,a1*c2+c1*d2,b1*c2+d1*d2,a1*e2+c1*f2+e1,b1*e2+d1*f2+f1]

def compose(stack):
    r=[1,0,0,1,0,0]
    for t in stack: r=mul(r,t)
    return r

def am(m,x,y):
    a,b,c,d,e,f=m; return a*x+c*y+e,b*x+d*y+f

def get_svg_scale(root):
    def pu(s):
        s=s.strip()
        for u,f in [('mm',1.0),('cm',10.0),('in',25.4),('pt',25.4/72),('px',25.4/96)]:
            if s.endswith(u): return float(s[:-len(u)])*f
        try: return float(s)*(25.4/96)
        except: return 1.0
    w=pu(root.get('width','0')); h=pu(root.get('height','0'))
    vb=root.get('viewBox','')
    if vb:
        p=[float(x) for x in re.split(r'[,\s]+',vb.strip())]
        return w/p[2] if p[2] else 1.0,h/p[3] if p[3] else 1.0,h
    return 1.0,1.0,h

def tokenize_path(d):
    return re.findall(r'[MmZzLlHhVvCcSsQqTtAa]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?',d)

def bezier3(p0,p1,p2,p3,n):
    pts=[]; x0,y0=p0; x1,y1=p1; x2,y2=p2; x3,y3=p3
    for k in range(1,n+1):
        t=k/n; mt=1-t
        pts.append((mt**3*x0+3*mt**2*t*x1+3*mt*t**2*x2+t**3*x3,
                    mt**3*y0+3*mt**2*t*y1+3*mt*t**2*y2+t**3*y3))
    return pts

def arc_points(x1,y1,rx,ry,phi,large,sweep,x2,y2,n=24):
    if rx==0 or ry==0: return [(x2,y2)]
    pr=math.radians(phi); cp=math.cos(pr); sp=math.sin(pr)
    dx=(x1-x2)/2; dy=(y1-y2)/2
    x1p=cp*dx+sp*dy; y1p=-sp*dx+cp*dy
    r2x=rx*rx; r2y=ry*ry; x1p2=x1p*x1p; y1p2=y1p*y1p
    lam=x1p2/r2x+y1p2/r2y
    if lam>1: ls=math.sqrt(lam); rx*=ls; ry*=ls; r2x=rx*rx; r2y=ry*ry
    num=max(0,r2x*r2y-r2x*y1p2-r2y*x1p2); den=r2x*y1p2+r2y*x1p2
    sq=math.sqrt(num/den) if den else 0
    if large==sweep: sq=-sq
    cxp=sq*rx*y1p/ry; cyp=-sq*ry*x1p/rx
    cx=cp*cxp-sp*cyp+(x1+x2)/2; cy=sp*cxp+cp*cyp+(y1+y2)/2
    def ang(ux,uy,vx,vy):
        n2=math.sqrt((ux*ux+uy*uy)*(vx*vx+vy*vy))
        if n2==0: return 0
        c2=max(-1,min(1,(ux*vx+uy*vy)/n2)); a2=math.acos(c2)
        if ux*vy-uy*vx<0: a2=-a2
        return a2
    th1=ang(1,0,(x1p-cxp)/rx,(y1p-cyp)/ry)
    dth=ang((x1p-cxp)/rx,(y1p-cyp)/ry,(-x1p-cxp)/rx,(-y1p-cyp)/ry)
    if not sweep and dth>0: dth-=2*math.pi
    elif sweep and dth<0: dth+=2*math.pi
    return [(cp*rx*math.cos(th1+dth*k/n)-sp*ry*math.sin(th1+dth*k/n)+cx,
             sp*rx*math.cos(th1+dth*k/n)+cp*ry*math.sin(th1+dth*k/n)+cy)
            for k in range(1,n+1)]

def path_to_subpaths(d,matrix,sx,sy,h_mm,bsegs=8):
    tokens=tokenize_path(d); subpaths=[]; current=[]
    pos=[0.0,0.0]; start=[0.0,0.0]; lc=None; cmd='M'; i=0
    def mm(x,y):
        tx,ty=am(matrix,x,y); return tx*sx,h_mm-ty*sy
    def gn(n):
        nonlocal i
        r=[]
        for _ in range(n):
            if i<len(tokens):
                try: r.append(float(tokens[i])); i+=1
                except: break
        return r
    while i<len(tokens):
        tk_=tokens[i]
        if re.match(r'^[A-Za-z]$',tk_):
            cmd=tk_; i+=1
            if cmd in ('Z','z'):
                if current and len(current)>2:
                    fx,fy=current[0]; lx,ly=current[-1]
                    if abs(fx-lx)>1e-4 or abs(fy-ly)>1e-4: current.append((fx,fy))
                    subpaths.append({'pts':current,'closed':True})
                current=[]; pos[0]=start[0]; pos[1]=start[1]; lc=None
            continue
        if cmd in ('M','m'):
            if current: subpaths.append({'pts':current,'closed':False})
            v=gn(2)
            if len(v)<2: continue
            if cmd=='m': pos[0]+=v[0]; pos[1]+=v[1]
            else: pos[0]=v[0]; pos[1]=v[1]
            start=pos[:]; current=[mm(pos[0],pos[1])]
            cmd='l' if cmd=='m' else 'L'
        elif cmd in ('L','l'):
            v=gn(2)
            if len(v)<2: continue
            if cmd=='l': pos[0]+=v[0]; pos[1]+=v[1]
            else: pos[0]=v[0]; pos[1]=v[1]
            current.append(mm(pos[0],pos[1])); lc=None
        elif cmd in ('H','h'):
            v=gn(1)
            if not v: continue
            if cmd=='h': pos[0]+=v[0]
            else: pos[0]=v[0]
            current.append(mm(pos[0],pos[1])); lc=None
        elif cmd in ('V','v'):
            v=gn(1)
            if not v: continue
            if cmd=='v': pos[1]+=v[0]
            else: pos[1]=v[0]
            current.append(mm(pos[0],pos[1])); lc=None
        elif cmd in ('C','c'):
            v=gn(6)
            if len(v)<6: continue
            if cmd=='c': x1=pos[0]+v[0];y1=pos[1]+v[1];x2=pos[0]+v[2];y2=pos[1]+v[3];x3=pos[0]+v[4];y3=pos[1]+v[5]
            else: x1,y1,x2,y2,x3,y3=v
            for pt in bezier3((pos[0],pos[1]),(x1,y1),(x2,y2),(x3,y3),bsegs): current.append(mm(pt[0],pt[1]))
            lc=(x2,y2); pos[0]=x3; pos[1]=y3
        elif cmd in ('S','s'):
            v=gn(4)
            if len(v)<4: continue
            x1=(2*pos[0]-lc[0]) if lc else pos[0]; y1=(2*pos[1]-lc[1]) if lc else pos[1]
            if cmd=='s': x2=pos[0]+v[0];y2=pos[1]+v[1];x3=pos[0]+v[2];y3=pos[1]+v[3]
            else: x2,y2,x3,y3=v
            for pt in bezier3((pos[0],pos[1]),(x1,y1),(x2,y2),(x3,y3),bsegs): current.append(mm(pt[0],pt[1]))
            lc=(x2,y2); pos[0]=x3; pos[1]=y3
        elif cmd in ('Q','q'):
            v=gn(4)
            if len(v)<4: continue
            if cmd=='q': x1=pos[0]+v[0];y1=pos[1]+v[1];x2=pos[0]+v[2];y2=pos[1]+v[3]
            else: x1,y1,x2,y2=v
            cx1=pos[0]+(2/3)*(x1-pos[0]); cy1=pos[1]+(2/3)*(y1-pos[1])
            cx2=x2+(2/3)*(x1-x2); cy2=y2+(2/3)*(y1-y2)
            for pt in bezier3((pos[0],pos[1]),(cx1,cy1),(cx2,cy2),(x2,y2),bsegs): current.append(mm(pt[0],pt[1]))
            lc=(x1,y1); pos[0]=x2; pos[1]=y2
        elif cmd in ('T','t'):
            v=gn(2)
            if len(v)<2: continue
            x1=(2*pos[0]-lc[0]) if lc else pos[0]; y1=(2*pos[1]-lc[1]) if lc else pos[1]
            if cmd=='t': x2=pos[0]+v[0];y2=pos[1]+v[1]
            else: x2,y2=v
            cx1=pos[0]+(2/3)*(x1-pos[0]); cy1=pos[1]+(2/3)*(y1-pos[1])
            cx2=x2+(2/3)*(x1-x2); cy2=y2+(2/3)*(y1-y2)
            for pt in bezier3((pos[0],pos[1]),(cx1,cy1),(cx2,cy2),(x2,y2),bsegs): current.append(mm(pt[0],pt[1]))
            lc=(x1,y1); pos[0]=x2; pos[1]=y2
        elif cmd in ('A','a'):
            v=gn(7)
            if len(v)<7: continue
            rx,ry,xr,la,sw,ex,ey=v
            if cmd=='a': ex+=pos[0]; ey+=pos[1]
            for pt in arc_points(pos[0],pos[1],rx,ry,xr,int(la),int(sw),ex,ey): current.append(mm(pt[0],pt[1]))
            pos[0]=ex; pos[1]=ey; lc=None
        else:
            i+=1; continue
    if current and len(current)>1:
        subpaths.append({'pts':current,'closed':False})
    return subpaths

def convert_svg(svg_path, color_map, bezier_segs=8, log_fn=None):
    def log(msg):
        if log_fn: log_fn(msg)
        else: print(msg)
    tree=etree.parse(svg_path); root=tree.getroot()
    sx,sy,h_mm=get_svg_scale(root)
    css_classes=parse_css_block(root)
    log(f"SVG: {root.get('width')} × {root.get('height')}")
    doc=ezdxf.new(dxfversion='R2010'); msp=doc.modelspace()
    created=set(); stats={}
    # Mapa tipo->color_dxf desde config
    type_to_dxf = {}
    for hex_c, info in color_map.items():
        tipo = info.get('type','OTHER')
        dxf_hex = info.get('dxf_color', '#000000')
        type_to_dxf[tipo] = hex_to_dxf_color(dxf_hex)

    def ensure(name, tipo='OTHER'):
        if name not in created:
            dxf_col = type_to_dxf.get(tipo, 7)
            doc.layers.add(name=name, color=dxf_col)
            created.add(name)
    def lname(did,tipo): return f"{did}_{tipo}"[:31]
    def emit(pts,layer,closed=False):
        if len(pts)<2: return
        clean=[pts[0]]
        for p in pts[1:]:
            lx,ly=clean[-1]
            if abs(p[0]-lx)>1e-6 or abs(p[1]-ly)>1e-6: clean.append(p)
        if len(clean)<2: return
        if closed:
            fx,fy=clean[0]; lx,ly=clean[-1]
            if abs(fx-lx)>1e-6 or abs(fy-ly)>1e-6: clean.append((fx,fy))
        flags=ezdxf.const.LWPOLYLINE_CLOSED if closed else 0
        msp.add_lwpolyline([(x,y,0) for x,y in clean],format='xyz',
                           dxfattribs={'layer':layer,'flags':flags})
        stats[layer]=stats.get(layer,0)+1
    def get_layer_type(color):
        if color and color in color_map:
            return color_map[color].get('type','OTHER')
        return 'OTHER'
    def add_path(d,matrix,f,s,did):
        ft=get_layer_type(f) if f and f!='none' else None
        st=get_layer_type(s) if s and s!='none' else None
        for sp in path_to_subpaths(d,matrix,sx,sy,h_mm,bezier_segs):
            pts=sp['pts']; cl=sp['closed']
            if len(pts)<2: continue
            if cl and ft: l=lname(did,ft); ensure(l,ft); emit(pts,l,True)
            elif st: l=lname(did,st); ensure(l,st); emit(pts,l,cl)
            elif ft: l=lname(did,ft); ensure(l,ft); emit(pts,l,cl)
    def add_circle(el,matrix,f,s,did):
        cx=float(el.get('cx',0)); cy=float(el.get('cy',0)); r=float(el.get('r',0))
        if r==0: return
        tcx,tcy=am(matrix,cx,cy); mx=tcx*sx; my=h_mm-tcy*sy
        a,b,c,d=matrix[0],matrix[1],matrix[2],matrix[3]
        r_mm=r*math.sqrt(abs(a*d-b*c))*sx
        if s and s!='none':
            l=lname(did,get_layer_type(s)); ensure(l)
            tipo_s=get_layer_type(s); ensure(l,tipo_s)
        msp.add_circle((mx,my),r_mm,dxfattribs={'layer':l}); stats[l]=stats.get(l,0)+1
        if f and f!='none':
            l=lname(did,get_layer_type(f)); ensure(l); n=64
            pts=[(mx+r_mm*math.cos(2*math.pi*k/n),my+r_mm*math.sin(2*math.pi*k/n)) for k in range(n)]
            emit(pts,l,True)
    def process(el,tstack,did,pf,ps):
        tag=svg_tag(el)
        if tag in ('defs','namedview','metadata','title','desc','clipPath','symbol','style','script'): return
        ns=tstack+[parse_transform(el.get('transform',''))]; matrix=compose(ns)
        st=resolve_style(el, css_classes)
        f=normalize_color(st.get('fill',el.get('fill',''))) or pf
        s=normalize_color(st.get('stroke',el.get('stroke',''))) or ps
        if tag=='g':
            for ch in el: process(ch,ns,did,f,s)
        elif tag=='path':
            d=el.get('d','')
            if d: add_path(d,matrix,f,s,did)
        elif tag=='circle':
            add_circle(el,matrix,f,s,did)
        elif tag in ('ellipse','rect'):
            if tag=='ellipse':
                cx=float(el.get('cx',0));cy=float(el.get('cy',0))
                rx=float(el.get('rx',0));ry=float(el.get('ry',0)); n=48
                raw=[(cx+rx*math.cos(2*math.pi*k/n),cy+ry*math.sin(2*math.pi*k/n)) for k in range(n)]
            else:
                x=float(el.get('x',0));y=float(el.get('y',0))
                w=float(el.get('width',0));h2=float(el.get('height',0))
                raw=[(x,y),(x+w,y),(x+w,y+h2),(x,y+h2)]
            pts=[]
            for px,py in raw:
                tx,ty=am(matrix,px,py); pts.append((tx*sx,h_mm-ty*sy))
            for col in [s,f]:
                if col and col!='none':
                    tipo_col=get_layer_type(col); l=lname(did,tipo_col); ensure(l,tipo_col); emit(pts,l,True)
        elif tag not in ('text','image','use'):
            for ch in el: process(ch,ns,did,f,s)
    layer1=None
    for el in root.iter():
        if el.get(f'{{{INK_NS}}}groupmode')=='layer': layer1=el; break
    if layer1 is None: layer1=root
    idx=1; designs=[]
    for ch in layer1:
        tag=svg_tag(ch)
        if tag in ('defs','namedview','metadata','text','##comment##'): continue

        # Detectar si el grupo tiene geometría con color — incluyendo herencia de padre
        # LightBurn pone fill/stroke en el <g>, los hijos no tienen estilo propio
        def element_has_geometry_with_color(el, inherited_fill=None, inherited_stroke=None):
            etag = svg_tag(el)
            if etag == '##comment##': return False
            st = resolve_style(el, css_classes)
            f = normalize_color(st.get('fill', el.get('fill',''))) or inherited_fill
            s = normalize_color(st.get('stroke', el.get('stroke',''))) or inherited_stroke
            if etag in ('path','circle','ellipse','rect','line','polyline','polygon'):
                if (f and f != 'none') or (s and s != 'none'):
                    return True
            if etag == 'g':
                for child in el:
                    if element_has_geometry_with_color(child, f, s):
                        return True
            return False

        if not element_has_geometry_with_color(ch):
            continue
        label=ch.get(f'{{{INK_NS}}}label','').strip()
        id_=ch.get('id','').strip()
        did=re.sub(r'[^a-zA-Z0-9_-]','_',label or id_ or f"D{idx}")[:20]
        designs.append((did,ch)); idx+=1
    log(f'Designs: {len(designs)}')
    for did,el in designs:
        inner=[e for e in el.iter() if svg_tag(e) in ('path','circle','ellipse','rect')]
        log(f"  → {did} ({len(inner)})")
        process(el,[parse_transform('')],did,None,None)
    output=os.path.splitext(svg_path)[0]+'_ezcad.dxf'
    doc.saveas(output)
    total=sum(stats.values())
    log(f'\n✓ {total} entities · {len(created)} layers')
    return output, total, len(created)


# ─── Interfaz gráfica ─────────────────────────────────────────────────────────
cfg = load_config()

def t(key, lang=None):
    """Traducción."""
    l = lang or cfg.get('language','en')
    return LANGS.get(l,LANGS['en']).get(key, LANGS['en'].get(key,key))


class SettingsWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        lang = cfg.get('language','en')
        self.title(t('settings_title'))
        self.geometry("560x620")
        self.resizable(False, False)
        self.configure(bg='#f5f5f5')
        self.grab_set()

        tk.Label(self, text=t('settings_title'), font=('Arial',13,'bold'),
                 bg='#f5f5f5', fg='#1a1a2e').pack(pady=(14,4), padx=16, anchor='w')
        tk.Label(self, text=t('settings_info'), font=('Arial',9),
                 bg='#f5f5f5', fg='#666', justify='left').pack(padx=16, anchor='w')

        # ── Idioma ──
        lang_frame = tk.Frame(self, bg='#f5f5f5')
        lang_frame.pack(fill='x', padx=16, pady=(8,4))
        tk.Label(lang_frame, text=t('lang_label'), font=('Arial',9,'bold'),
                 bg='#f5f5f5', fg='#1a1a2e').pack(side='left', padx=(0,8))
        self.lang_var = tk.StringVar(value=lang)
        for code,name in LANG_NAMES.items():
            tk.Radiobutton(lang_frame, text=name, variable=self.lang_var,
                           value=code, bg='#f5f5f5', font=('Arial',9),
                           activebackground='#f5f5f5').pack(side='left', padx=4)
        tk.Frame(self, bg='#ddd', height=1).pack(fill='x', padx=16, pady=4)

        # ── Tabla de colores ──
        cols_frame = tk.Frame(self, bg='#f5f5f5')
        cols_frame.pack(fill='both', expand=True, padx=16, pady=8)

        headers = [t('input_color'),'Hex SVG','Tipo',t('output_color'),'Hex DXF','']
        for i,h in enumerate(headers):
            tk.Label(cols_frame, text=h, font=('Arial',8,'bold'),
                     bg='#ddd', padx=4, pady=3).grid(row=0,column=i,sticky='ew',padx=1,pady=1)

        cols_frame.columnconfigure(0,minsize=36)
        cols_frame.columnconfigure(1,minsize=75)
        cols_frame.columnconfigure(2,minsize=120)
        cols_frame.columnconfigure(3,minsize=36)
        cols_frame.columnconfigure(4,minsize=75)
        cols_frame.columnconfigure(5,minsize=36)

        self.rows = []
        self.cols_frame = cols_frame
        self.row_offset = 1

        color_map = cfg.get('color_map', DEFAULT_COLOR_MAP)
        for hex_color, info in color_map.items():
            self._add_row(hex_color, info.get('type','OTHER'), info.get('dxf_color', hex_color))

        # ── Botón añadir ──
        btn_frame = tk.Frame(self, bg='#f5f5f5')
        btn_frame.pack(fill='x', padx=16, pady=4)
        tk.Button(btn_frame, text=t('add_color'), font=('Arial',9),
                  bg='#e8f8ff', fg='#00b5e1', relief='flat', padx=8, pady=4,
                  command=self._add_new_row).pack(side='left')

        # ── Calidad de curvas ──
        tk.Label(self, text=t('quality_label'), font=('Arial',9),
                 bg='#f5f5f5', fg='#555').pack(padx=16, anchor='w', pady=(8,0))
        self.quality_var = tk.IntVar(value=cfg.get('bezier_quality',8))
        quality_scale = ttk.Scale(self, from_=4, to=20, variable=self.quality_var,
                                  orient='horizontal')
        quality_scale.pack(fill='x', padx=16, pady=(0,4))
        tk.Label(self, textvariable=self.quality_var, font=('Arial',9),
                 bg='#f5f5f5', fg='#888').pack(anchor='w', padx=16)

        # ── Idioma (al principio, siempre visible) ──

        # ── Botones ──
        btn2 = tk.Frame(self, bg='#f5f5f5')
        btn2.pack(fill='x', padx=16, pady=(4,14))
        tk.Button(btn2, text=t('cancel'), font=('Arial',10), relief='flat',
                  bg='#eee', padx=14, pady=6, command=self.destroy).pack(side='right', padx=4)
        tk.Button(btn2, text=t('save'), font=('Arial',10,'bold'), relief='flat',
                  bg='#00b5e1', fg='white', padx=14, pady=6,
                  command=self._save).pack(side='right')

    def _add_row(self, hex_color, layer_type, dxf_color=None):
        if dxf_color is None:
            dxf_color = hex_color  # por defecto mismo color
        r = len(self.rows) + self.row_offset

        # Col 0: botón color SVG (entrada)
        svg_btn = tk.Button(self.cols_frame, bg=hex_color, width=3,
                             relief='solid', bd=1, cursor='hand2')
        svg_btn.grid(row=r, column=0, padx=2, pady=2, sticky='ew')

        # Col 1: hex SVG
        hex_var = tk.StringVar(value=hex_color)
        hex_entry = tk.Entry(self.cols_frame, textvariable=hex_var,
                             font=('Consolas',8), width=9)
        hex_entry.grid(row=r, column=1, padx=2, pady=2, sticky='ew')

        # Col 2: tipo de capa
        type_var = tk.StringVar(value=layer_type)
        type_menu = ttk.Combobox(self.cols_frame, textvariable=type_var,
                                  values=['CUT_INNER','CUT_OUTER','ENGRAVE','OTHER'],
                                  state='readonly', width=12)
        type_menu.grid(row=r, column=2, padx=2, pady=2, sticky='ew')

        # Col 3: botón color DXF (salida)
        try:
            dxf_bg = dxf_color if dxf_color else '#000000'
        except:
            dxf_bg = '#000000'
        dxf_btn = tk.Button(self.cols_frame, bg=dxf_bg, width=3,
                             relief='solid', bd=1, cursor='hand2')
        dxf_btn.grid(row=r, column=3, padx=2, pady=2, sticky='ew')

        # Col 4: hex DXF
        dxf_var = tk.StringVar(value=dxf_color or hex_color)
        dxf_entry = tk.Entry(self.cols_frame, textvariable=dxf_var,
                             font=('Consolas',8), width=9)
        dxf_entry.grid(row=r, column=4, padx=2, pady=2, sticky='ew')

        # Col 5: eliminar
        del_btn = tk.Button(self.cols_frame, text='✕', font=('Arial',8,'bold'),
                             relief='flat', bg='#ffeeee', fg='#cc0000',
                             padx=4, pady=2, cursor='hand2')
        del_btn.grid(row=r, column=5, padx=2, pady=2)

        def pick_svg(btn=svg_btn, hv=hex_var):
            col = colorchooser.askcolor(color=hv.get(), title="SVG Color")[1]
            if col: hv.set(col.lower()); btn.configure(bg=col)

        def pick_dxf(btn=dxf_btn, hv=dxf_var):
            col = colorchooser.askcolor(color=hv.get(), title="DXF Color (EzCad3)")[1]
            if col: hv.set(col.lower()); btn.configure(bg=col)

        svg_btn.configure(command=pick_svg)
        dxf_btn.configure(command=pick_dxf)

        row_data = {'hex': hex_var, 'type': type_var, 'dxf': dxf_var,
                    'widgets': [svg_btn, hex_entry, type_menu, dxf_btn, dxf_entry, del_btn]}

        def remove_row(rd=row_data):
            for w in rd['widgets']: w.destroy()
            if rd in self.rows: self.rows.remove(rd)

        del_btn.configure(command=remove_row)
        self.rows.append(row_data)

    def _add_new_row(self):
        self._add_row('#ffffff','OTHER','#ffffff')

    def _save(self):
        new_map = {}
        for rd in self.rows:
            h = rd['hex'].get().strip().lower()
            if not h.startswith('#'): h = '#'+h
            if len(h)==4: h='#'+h[1]*2+h[2]*2+h[3]*2
            new_map[h] = {'type': rd['type'].get(), 'label_key': rd['type'].get().lower(), 'dxf_color': rd['dxf'].get()}
        cfg['color_map'] = new_map
        cfg['bezier_quality'] = int(self.quality_var.get())
        # Calcular ANTES de actualizar cfg
        lang_changed = (cfg.get('language','en') != self.lang_var.get())
        cfg['language'] = self.lang_var.get()
        save_config(cfg)
        self.destroy()
        if lang_changed:
            # Usar el idioma nuevo para el mensaje
            new_lang = cfg['language']
            title = LANGS.get(new_lang, LANGS['en']).get('restart_title', 'Restart required')
            msg   = LANGS.get(new_lang, LANGS['en']).get('restart_needed', 'Please restart to apply language change.')
            messagebox.showinfo(title, msg)
        else:
            self.parent.refresh_lang()


class HelpWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title(t('help_title'))
        self.geometry("540x500")
        self.resizable(True, True)
        self.configure(bg='#1a1a2e')
        self.grab_set()

        frame = tk.Frame(self, bg='#1a1a2e')
        frame.pack(fill='both', expand=True, padx=2, pady=2)

        text = tk.Text(frame, font=('Consolas',10), bg='#1a1a2e', fg='#00b5e1',
                       relief='flat', padx=16, pady=12, wrap='word')
        scroll = ttk.Scrollbar(frame, command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        text.pack(fill='both', expand=True)

        text.insert('1.0', t('help_text'))
        text.configure(state='disabled')

        tk.Button(self, text='OK', font=('Arial',10,'bold'),
                  bg='#00b5e1', fg='white', relief='flat', padx=20, pady=6,
                  command=self.destroy).pack(pady=10)


class App:
    def __init__(self, root_win):
        self.root = root_win
        self._build_ui()
        threading.Thread(target=ping_analytics, daemon=True).start()
        if len(sys.argv)>1 and sys.argv[1].lower().endswith('.svg'):
            root_win.after(400, lambda: self.run_conversion(sys.argv[1]))

    def _build_ui(self):
        root = self.root
        root.title(t('app_title'))
        root.geometry("500x500")
        root.resizable(False, False)
        root.configure(bg='#f5f5f5')

        # ── Header ──
        self.header = tk.Frame(root, bg='#1a1a2e')
        self.header.pack(fill='x')

        tk.Label(self.header, text="Svg2Ez", font=('Arial',17,'bold'),
                 bg='#1a1a2e', fg='#00b5e1').pack(side='left', padx=16, pady=10)
        tk.Label(self.header, text=f"v{VERSION}", font=('Arial',8),
                 bg='#1a1a2e', fg='#444').pack(side='left', pady=10)

        # Botones header derecha
        btn_row = tk.Frame(self.header, bg='#1a1a2e')
        btn_row.pack(side='right', padx=10)

        self.donate_btn = tk.Button(btn_row, text=t('donate'),
                                    font=('Arial',9,'bold'),
                                    bg='#ffc439', fg='#003087',
                                    relief='flat', padx=8, pady=4, cursor='hand2',
                                    command=lambda: webbrowser.open(PAYPAL_URL))
        self.donate_btn.pack(side='right', padx=3, pady=8)

        self.feedback_btn = tk.Button(btn_row, text=t('feedback'),
                                      font=('Arial',9), bg='#2a2a4e', fg='#aaa',
                                      relief='flat', padx=8, pady=4, cursor='hand2',
                                      command=self.open_feedback)
        self.feedback_btn.pack(side='right', padx=3, pady=8)

        self.help_btn = tk.Button(btn_row, text=t('help'),
                                  font=('Arial',9), bg='#2a2a4e', fg='#aaa',
                                  relief='flat', padx=8, pady=4, cursor='hand2',
                                  command=lambda: HelpWindow(self.root))
        self.help_btn.pack(side='right', padx=3, pady=8)

        self.settings_btn = tk.Button(btn_row, text=t('settings'),
                                      font=('Arial',9), bg='#2a2a4e', fg='#aaa',
                                      relief='flat', padx=8, pady=4, cursor='hand2',
                                      command=lambda: SettingsWindow(self.root))
        self.settings_btn.pack(side='right', padx=3, pady=8)

        # ── Botón principal ──
        self.open_btn = tk.Button(root, text=t('open_btn'),
                                  font=('Arial',13,'bold'), bg='#00b5e1', fg='white',
                                  activebackground='#0099c4', activeforeground='white',
                                  relief='flat', padx=20, pady=13,
                                  command=self.pick_and_convert)
        self.open_btn.pack(pady=(20,8), ipadx=10)

        # ── Drag & Drop ──
        if DND_AVAILABLE:
            self.drop_lbl = tk.Label(root, text=t('drag_hint'),
                font=('Arial',10), bg='#e4f6fb', fg='#00a0c8',
                relief='solid', bd=1, padx=10, pady=10, cursor='hand2')
            self.drop_lbl.pack(fill='x', padx=22, pady=(0,10))
            # Registrar en el label Y en la ventana principal
            try:
                self.drop_lbl.drop_target_register(DND_FILES)
                self.drop_lbl.dnd_bind('<<Drop>>', self.on_drop)
                self.drop_lbl.dnd_bind('<<DragEnter>>', lambda e: self.drop_lbl.configure(bg='#b8e8f5'))
                self.drop_lbl.dnd_bind('<<DragLeave>>', lambda e: self.drop_lbl.configure(bg='#e4f6fb'))
                # También en la ventana raíz para mayor área de drop
                root.drop_target_register(DND_FILES)
                root.dnd_bind('<<Drop>>', self.on_drop)
            except Exception:
                pass
        else:
            self.drop_lbl = tk.Label(root, text=t('drag_hint'),
                font=('Arial',9), bg='#f5f5f5', fg='#bbb')
            self.drop_lbl.pack(pady=(0,8))

        # ── Log ──
        log_frame = tk.Frame(root, bg='#f5f5f5')
        log_frame.pack(fill='both', expand=True, padx=22)
        self.log_text = tk.Text(log_frame, height=9, font=('Consolas',9),
                                bg='#1a1a2e', fg='#00b5e1',
                                relief='flat', state='disabled')
        self.log_text.pack(fill='both', expand=True)

        # ── Progress ──
        self.progress = ttk.Progressbar(root, mode='indeterminate')
        self.progress.pack(fill='x', padx=22, pady=8)

        # ── Footer ──
        tk.Frame(root, bg='#ddd', height=1).pack(fill='x', padx=22)
        footer = tk.Frame(root, bg='#f5f5f5')
        footer.pack(fill='x', padx=22, pady=8)
        self.footer_lbl = tk.Label(footer, text="Free & open source · svg2ez.com · ☕ Donate if useful",
                                   font=('Arial',8), bg='#f5f5f5', fg='#aaa')
        self.footer_lbl.pack(side='left')

    def open_feedback(self):
        """Abre ventana de feedback con opción GitHub o Email."""
        win = tk.Toplevel(self.root)
        win.title(t('feedback_title'))
        win.geometry("360x200")
        win.resizable(False, False)
        win.configure(bg='#f5f5f5')
        win.grab_set()

        tk.Label(win, text=t('feedback_title'), font=('Arial',12,'bold'),
                 bg='#f5f5f5', fg='#1a1a2e').pack(pady=(18,4))
        tk.Label(win, text=t('feedback_msg'),
                 font=('Arial',9), bg='#f5f5f5', fg='#666').pack(pady=(0,16))

        btn_frame = tk.Frame(win, bg='#f5f5f5')
        btn_frame.pack()

        def go_github():
            import urllib.parse
            params = urllib.parse.urlencode({
                'title': f'[Svg2Ez v{VERSION}] ',
                'body':  f'**Version:** {VERSION}\n**OS:** Windows\n\n**Description:**\n\n**Steps to reproduce:**\n\n**Expected:**\n\n**Actual:**'
            })
            webbrowser.open(f'{ISSUES_URL}?{params}')
            win.destroy()

        def go_email():
            import urllib.parse
            subject = urllib.parse.quote(f'[Svg2Ez v{VERSION}] Bug/Suggestion')
            body    = urllib.parse.quote(
                f'Version: {VERSION}\n\nDescription:\n\nSteps to reproduce:\n\n')
            webbrowser.open(f'mailto:{FEEDBACK_EMAIL}?subject={subject}&body={body}')
            win.destroy()

        tk.Button(btn_frame, text=t('via_github'),
                  font=('Arial',10,'bold'), bg='#1a1a2e', fg='white',
                  relief='flat', padx=16, pady=8, cursor='hand2',
                  command=go_github).pack(side='left', padx=8)

        tk.Button(btn_frame, text=t('via_email'),
                  font=('Arial',10), bg='#e8f8ff', fg='#00b5e1',
                  relief='flat', padx=16, pady=8, cursor='hand2',
                  command=go_email).pack(side='left', padx=8)

        tk.Label(win, text=t('feedback_hint'),
                 font=('Arial',8), bg='#f5f5f5', fg='#aaa').pack(pady=(14,0))

    def refresh_lang(self):
        """Recarga TODOS los textos inmediatamente al cambiar idioma."""
        self.root.title(t('app_title'))
        self.open_btn.configure(text=t('open_btn'))
        self.donate_btn.configure(text=t('donate'))
        self.feedback_btn.configure(text=t('feedback'))
        self.help_btn.configure(text=t('help'))
        self.settings_btn.configure(text=t('settings'))
        if hasattr(self, 'drop_lbl'):
            self.drop_lbl.configure(text=t('drag_hint'))
        self.root.update()

    def on_drop(self, event):
        path=event.data.strip().strip('{}')
        if path.lower().endswith('.svg'):
            self.drop_lbl.configure(bg='#e4f6fb')
            self.run_conversion(path)
        else:
            messagebox.showwarning("Format", t('wrong_format'))

    def log(self, msg):
        self.log_text.configure(state='normal')
        self.log_text.insert('end', msg+'\n')
        self.log_text.see('end')
        self.log_text.configure(state='disabled')
        self.root.update_idletasks()

    def pick_and_convert(self):
        path=filedialog.askopenfilename(
            title="SVG",
            filetypes=[("SVG","*.svg"),("All","*.*")])
        if path: self.run_conversion(path)

    def run_conversion(self, svg_path):
        self.open_btn.configure(state='disabled', text=t('converting'))
        self.progress.start(10)
        self.log_text.configure(state='normal')
        self.log_text.delete('1.0','end')
        self.log_text.configure(state='disabled')
        self.log(f"📄 {os.path.basename(svg_path)}")
        self.log("─"*40)

        color_map = cfg.get('color_map', DEFAULT_COLOR_MAP)
        bsegs = cfg.get('bezier_quality', 8)

        def worker():
            try:
                out,entities,layers=convert_svg(svg_path,color_map,bsegs,log_fn=self.log)
                self.root.after(0,lambda: self.on_done(out,entities,layers))
            except Exception as e:
                import traceback
                self.root.after(0,lambda: self.on_error(str(e)))

        threading.Thread(target=worker,daemon=True).start()

    def on_done(self, out, entities, layers):
        self.progress.stop()
        self.open_btn.configure(state='normal', text=t('open_btn'))
        self.log("─"*40)
        self.log(f"✅ {os.path.basename(out)}")
        self.log(f"📁 {os.path.dirname(out)}")

        cfg['conversions_done'] = cfg.get('conversions_done',0)+1
        save_config(cfg)

        # Mostrar donación cada 3 conversiones
        show_donate = cfg.get('show_donate_after', True) and cfg['conversions_done'] % 3 == 0

        msg = t('done_msg').format(path=out)
        if show_donate:
            resp = messagebox.askyesno(t('done_title'), msg+f"\n\n{t('donate_ask')}", icon='info')
            if resp: webbrowser.open(PAYPAL_URL)
        else:
            messagebox.showinfo(t('done_title'), f"{t('saved_to')}:\n{out}")

    def on_error(self, err):
        self.progress.stop()
        self.open_btn.configure(state='normal', text=t('open_btn'))
        self.log(f"❌ {err}")
        messagebox.showerror(t('error'), err)


def main():
    if DND_AVAILABLE:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    App(root)
    root.mainloop()

if __name__ == '__main__':
    main()
