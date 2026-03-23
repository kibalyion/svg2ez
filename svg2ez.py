#!/usr/bin/env python3
"""
Svg2Ez v2.0 — SVG to EzCad3 DXF Converter
Free tool for laser engravers using Inkscape + EzCad3
https://github.com/kibalyion/svg2ez
"""

import sys, os, math, re, threading, webbrowser, json, urllib.request, glob
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, colorchooser

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

from lxml import etree
import ezdxf

# ─── App info ─────────────────────────────────────────────────────────────────
APP_NAME       = "Svg2Ez"
VERSION        = "2.0.0"
PAYPAL_URL     = "https://www.paypal.com/donate/?hosted_button_id=W9BE8867AF8SA"
WEBSITE_URL    = "https://github.com/kibalyion/svg2ez"
ISSUES_URL     = "https://github.com/kibalyion/svg2ez/issues/new"
FEEDBACK_EMAIL = "contacto@joyeriahago.com"
ANALYTICS_URL  = "https://joyeriahago.com/modules/svg2ez/svg2ez_ping.php"
ANALYTICS_TOKEN= "svg2ez-hago-2024-xK9mP"

# ─── Color mapping ────────────────────────────────────────────────────────────
DEFAULT_COLOR_MAP = {
    "#000000": {"type": "CUT_INNER",  "label_key": "cut_inner"},
    "#8800ff": {"type": "CUT_OUTER",  "label_key": "cut_outer"},
    "#0000ff": {"type": "ENGRAVE",    "label_key": "engrave"},
    "#ff0000": {"type": "ENGRAVE",    "label_key": "engrave"},
    "#ff00ff": {"type": "ENGRAVE",    "label_key": "engrave"},
    "#00ffff": {"type": "OTHER",      "label_key": "other"},
    "#00ff00": {"type": "OTHER",      "label_key": "other"},
    "#ffbb00": {"type": "OTHER",      "label_key": "other"},
    "#ffff00": {"type": "OTHER",      "label_key": "other"},
}

DEFAULT_CONFIG = {
    "language":        "en",
    "color_map":       DEFAULT_COLOR_MAP,
    "bezier_quality":  8,
    "scale_factor":    100.0,
    "output_folder":   "",
    "show_donate":     True,
    "donated":         False,
    "check_updates":   True,
    "conversions_done": 0,
    "recent_files":    [],
}

INK_NS = "http://www.inkscape.org/namespaces/inkscape"

# ─── Traducciones ─────────────────────────────────────────────────────────────
LANGS = {
"en": {
    "app_title":      "Svg2Ez — SVG to EzCad3 Converter",
    "open_btn":       "📂  Open SVG & Convert",
    "batch_btn":      "📁  Convert Folder",
    "drag_hint":      "⬇  Drag an SVG file or folder here",
    "settings":       "⚙ Settings",
    "help":           "? Help",
    "donate":         "💛 Donate",
    "feedback":       "🐛 Feedback",
    "converting":     "Converting...",
    "designs_found":  "Designs",
    "entities":       "entities",
    "layers":         "layers",
    "saved_to":       "Saved",
    "error":          "Error",
    "done_title":     "Done!",
    "done_msg":       "File saved:\n{path}",
    "donate_ask":     "Svg2Ez is free. A small donation helps keep it maintained.\nOpen PayPal to donate?",
    "wrong_format":   "Please drop an .SVG file or folder",
    "cut_inner":      "Cut Interior",
    "cut_outer":      "Cut Exterior",
    "engrave":        "Engrave",
    "other":          "Other",
    "settings_title": "Settings",
    "settings_info":  "Map SVG colors to EzCad3 layer types.",
    "input_color":    "SVG Color",
    "output_color":   "DXF Color (EzCad3)",
    "add_color":      "+ Add color",
    "remove":         "✕",
    "save":           "Save",
    "cancel":         "Cancel",
    "quality_label":  "Curve quality (higher = smoother, slower):",
    "scale_label":    "Scale correction (%):",
    "scale_hint":     "100 = no correction",
    "output_folder":  "Output folder:",
    "output_same":    "Same folder as SVG (leave blank)",
    "browse":         "📁",
    "clear":          "✕",
    "donated_lbl":    "I already donated ❤️",
    "donated_thanks": "Thank you! The donate button is now hidden.",
    "lang_label":     "Language:",
    "restart_title":  "Restart required",
    "restart_needed": "Language changed. Please restart Svg2Ez to apply.",
    "help_title":     "How Svg2Ez works",
    "help_text": """SVG2EZ v2.0 — Quick Guide
═══════════════════════════════════════

WHAT IT DOES
  Converts Inkscape/Illustrator SVG files to DXF that
  EzCad3 imports correctly — groups preserved, paths
  closed, ready for hatching.

HOW TO USE
  1. In Inkscape assign colors:
       Black  #000000 → Interior cut
       Purple #8800FF → Exterior cut
       Blue   #0000FF → Engrave (hatch)
  2. Group each design: Ctrl+G
  3. Open SVG with Svg2Ez → _ezcad.dxf created
  4. EzCad3: File → Import → select .dxf
  5. Select ENGRAVE layer → Modify → Hatch

BATCH CONVERSION
  Click "Convert Folder" or drag a folder onto the
  window to convert all SVGs inside at once.

ILLUSTRATOR COMPATIBLE
  CSS class styles (.cls-1{fill:#000}) are read
  automatically. Convert text to outlines first.

SETTINGS
  • Color mapping: customize SVG→layer assignment
  • DXF Color: control pen color in EzCad3
  • Scale correction: fix size differences
  • Output folder: save DXFs to a specific folder

TIPS
  • Each Inkscape group = independent object in EzCad3
  • Name your groups — names appear in EzCad3
  • Unknown colors are detected before conversion""",
    "feedback_title": "Feedback",
    "feedback_msg":   "How do you want to send feedback?",
    "via_github":     "GitHub (recommended)",
    "via_email":      "Email",
    "feedback_hint":  "Report bugs or suggest features",
    "update_title":   "Update available",
    "update_msg":     "Svg2Ez {new} is available (you have {cur}).\nDownload now?",
    "unknown_colors": "Unknown colors",
    "unknown_colors_msg": "These colors are not mapped:\n{colors}\n\nConvert anyway?",
    "batch_done":     "Batch complete",
    "batch_result":   "{ok} converted, {err} errors.",
    "recent":         "Recent files",
    "no_recent":      "No recent files",
},
"es": {
    "app_title":      "Svg2Ez — Conversor SVG a EzCad3",
    "open_btn":       "📂  Abrir SVG y Convertir",
    "batch_btn":      "📁  Convertir Carpeta",
    "drag_hint":      "⬇  Arrastra un SVG o carpeta aquí",
    "settings":       "⚙ Ajustes",
    "help":           "? Ayuda",
    "donate":         "💛 Donar",
    "feedback":       "🐛 Feedback",
    "converting":     "Convirtiendo...",
    "designs_found":  "Diseños",
    "entities":       "entidades",
    "layers":         "capas",
    "saved_to":       "Guardado",
    "error":          "Error",
    "done_title":     "¡Listo!",
    "done_msg":       "Archivo guardado:\n{path}",
    "donate_ask":     "Svg2Ez es gratuito. Una donación ayuda a mantenerlo.\n¿Abrir PayPal para donar?",
    "wrong_format":   "Arrastra un archivo .SVG o una carpeta",
    "cut_inner":      "Corte Interior",
    "cut_outer":      "Corte Exterior",
    "engrave":        "Grabado",
    "other":          "Otro",
    "settings_title": "Ajustes",
    "settings_info":  "Mapea colores SVG a tipos de capa en EzCad3.",
    "input_color":    "Color SVG",
    "output_color":   "Color DXF (EzCad3)",
    "add_color":      "+ Añadir color",
    "remove":         "✕",
    "save":           "Guardar",
    "cancel":         "Cancelar",
    "quality_label":  "Calidad de curvas (mayor = más suave, más lento):",
    "scale_label":    "Corrección de escala (%):",
    "scale_hint":     "100 = sin corrección",
    "output_folder":  "Carpeta de salida:",
    "output_same":    "Misma carpeta que el SVG (dejar vacío)",
    "browse":         "📁",
    "clear":          "✕",
    "donated_lbl":    "Ya he donado ❤️",
    "donated_thanks": "¡Gracias! El botón de donación está ahora oculto.",
    "lang_label":     "Idioma:",
    "restart_title":  "Reinicio necesario",
    "restart_needed": "Idioma cambiado. Reinicia Svg2Ez para aplicarlo.",
    "help_title":     "Cómo funciona Svg2Ez",
    "help_text": """SVG2EZ v2.0 — Guía rápida
═══════════════════════════════════════

QUÉ HACE
  Convierte SVGs de Inkscape/Illustrator a DXF que
  EzCad3 importa correctamente — grupos separados,
  paths cerrados, listo para hatch.

CÓMO USARLO
  1. En Inkscape asigna colores:
       Negro  #000000 → Corte interior
       Morado #8800FF → Corte exterior
       Azul   #0000FF → Grabado (hatch)
  2. Agrupa cada diseño: Ctrl+G
  3. Abre el SVG con Svg2Ez → se crea _ezcad.dxf
  4. EzCad3: File → Import → selecciona el .dxf
  5. Selecciona capa GRABADO → Modify → Hatch

CONVERSIÓN POR LOTES
  Clic en "Convertir Carpeta" o arrastra una carpeta
  para convertir todos los SVGs de golpe.

COMPATIBLE CON ILLUSTRATOR
  Los estilos CSS (.cls-1{fill:#000}) se leen
  automáticamente. Convierte textos a trazados antes.

AJUSTES
  • Mapeo de colores: personaliza SVG→capa
  • Color DXF: controla el pen en EzCad3
  • Corrección de escala: ajusta diferencias de tamaño
  • Carpeta de salida: guarda los DXF donde quieras

CONSEJOS
  • Cada grupo de Inkscape = objeto independiente en EzCad3
  • Nombra los grupos — el nombre aparece en EzCad3
  • Los colores desconocidos se detectan antes de convertir""",
    "feedback_title": "Feedback",
    "feedback_msg":   "¿Cómo quieres enviar tu comentario?",
    "via_github":     "GitHub (recomendado)",
    "via_email":      "Email",
    "feedback_hint":  "Reporta errores o sugiere mejoras",
    "update_title":   "Nueva versión disponible",
    "update_msg":     "Svg2Ez {new} está disponible (tienes {cur}).\n¿Descargar ahora?",
    "unknown_colors": "Colores no reconocidos",
    "unknown_colors_msg": "Estos colores no están en tu mapeo:\n{colors}\n\n¿Convertir de todas formas?",
    "batch_done":     "Lote completado",
    "batch_result":   "{ok} convertidos, {err} errores.",
    "recent":         "Archivos recientes",
    "no_recent":      "Sin archivos recientes",
},
"de": {
    "app_title":      "Svg2Ez — SVG zu EzCad3 Konverter",
    "open_btn":       "📂  SVG öffnen & konvertieren",
    "batch_btn":      "📁  Ordner konvertieren",
    "drag_hint":      "⬇  SVG-Datei oder Ordner hier ablegen",
    "settings":       "⚙ Einstellungen",
    "help":           "? Hilfe",
    "donate":         "💛 Spenden",
    "feedback":       "🐛 Feedback",
    "converting":     "Konvertiere...",
    "designs_found":  "Designs",
    "entities":       "Elemente",
    "layers":         "Ebenen",
    "saved_to":       "Gespeichert",
    "error":          "Fehler",
    "done_title":     "Fertig!",
    "done_msg":       "Datei gespeichert:\n{path}",
    "donate_ask":     "Svg2Ez ist kostenlos. Eine Spende hilft.\nPayPal öffnen?",
    "wrong_format":   "Bitte eine SVG-Datei oder einen Ordner ablegen",
    "cut_inner":      "Innenschnitt",
    "cut_outer":      "Außenschnitt",
    "engrave":        "Gravur",
    "other":          "Sonstige",
    "settings_title": "Einstellungen",
    "settings_info":  "SVG-Farben EzCad3-Ebenentypen zuordnen.",
    "input_color":    "SVG-Farbe",
    "output_color":   "DXF-Farbe (EzCad3)",
    "add_color":      "+ Farbe hinzufügen",
    "remove":         "✕",
    "save":           "Speichern",
    "cancel":         "Abbrechen",
    "quality_label":  "Kurvenqualität (höher = glatter, langsamer):",
    "scale_label":    "Skalierungskorrektur (%):",
    "scale_hint":     "100 = keine Korrektur",
    "output_folder":  "Ausgabeordner:",
    "output_same":    "Gleicher Ordner wie SVG (leer lassen)",
    "browse":         "📁",
    "clear":          "✕",
    "donated_lbl":    "Ich habe bereits gespendet ❤️",
    "donated_thanks": "Danke! Der Spenden-Button ist ausgeblendet.",
    "lang_label":     "Sprache:",
    "restart_title":  "Neustart erforderlich",
    "restart_needed": "Sprache geändert. Bitte Svg2Ez neu starten.",
    "help_title":     "Wie Svg2Ez funktioniert",
    "help_text":      "SVG2EZ v2.0 — Kurzanleitung\n\nKonvertiert SVG zu DXF für EzCad3.",
    "feedback_title": "Feedback",
    "feedback_msg":   "Wie möchten Sie Ihr Feedback senden?",
    "via_github":     "GitHub (empfohlen)",
    "via_email":      "E-Mail",
    "feedback_hint":  "Fehler melden oder Funktionen vorschlagen",
    "update_title":   "Neue Version verfügbar",
    "update_msg":     "Svg2Ez {new} verfügbar (Sie haben {cur}).\nHerunterladen?",
    "unknown_colors": "Unbekannte Farben",
    "unknown_colors_msg": "Diese Farben sind nicht zugeordnet:\n{colors}\n\nTrotzdem konvertieren?",
    "batch_done":     "Stapel abgeschlossen",
    "batch_result":   "{ok} konvertiert, {err} Fehler.",
    "recent":         "Letzte Dateien",
    "no_recent":      "Keine letzten Dateien",
},
"zh": {
    "app_title":      "Svg2Ez — SVG转EzCad3工具",
    "open_btn":       "📂  打开SVG并转换",
    "batch_btn":      "📁  批量转换文件夹",
    "drag_hint":      "⬇  将SVG文件或文件夹拖放到此处",
    "settings":       "⚙ 设置",
    "help":           "? 帮助",
    "donate":         "💛 捐赠",
    "feedback":       "🐛 反馈",
    "converting":     "转换中...",
    "designs_found":  "设计",
    "entities":       "个图形",
    "layers":         "个图层",
    "saved_to":       "已保存",
    "error":          "错误",
    "done_title":     "完成！",
    "done_msg":       "文件已保存：\n{path}",
    "donate_ask":     "Svg2Ez是免费的。捐赠帮助维护它。\n打开PayPal捐赠？",
    "wrong_format":   "请拖放SVG文件或文件夹",
    "cut_inner":      "内切割",
    "cut_outer":      "外切割",
    "engrave":        "雕刻",
    "other":          "其他",
    "settings_title": "设置",
    "settings_info":  "将SVG颜色映射到EzCad3图层类型。",
    "input_color":    "SVG颜色",
    "output_color":   "DXF颜色 (EzCad3)",
    "add_color":      "+ 添加颜色",
    "remove":         "✕",
    "save":           "保存",
    "cancel":         "取消",
    "quality_label":  "曲线质量（越高越平滑，越慢）：",
    "scale_label":    "比例校正（%）：",
    "scale_hint":     "100 = 无校正",
    "output_folder":  "输出文件夹：",
    "output_same":    "与SVG相同的文件夹（留空）",
    "browse":         "📁",
    "clear":          "✕",
    "donated_lbl":    "我已捐赠 ❤️",
    "donated_thanks": "谢谢！捐赠按钮已隐藏。",
    "lang_label":     "语言：",
    "restart_title":  "需要重启",
    "restart_needed": "语言已更改。请重启Svg2Ez以应用。",
    "help_title":     "Svg2Ez使用说明",
    "help_text":      "SVG2EZ v2.0 — 快速指南\n\n将SVG转换为EzCad3的DXF文件。",
    "feedback_title": "反馈",
    "feedback_msg":   "您想如何发送反馈？",
    "via_github":     "GitHub（推荐）",
    "via_email":      "电子邮件",
    "feedback_hint":  "报告错误或提出功能建议",
    "update_title":   "有新版本",
    "update_msg":     "Svg2Ez {new} 可用（您有 {cur}）。\n立即下载？",
    "unknown_colors": "未知颜色",
    "unknown_colors_msg": "这些颜色未映射：\n{colors}\n\n仍然转换？",
    "batch_done":     "批量处理完成",
    "batch_result":   "已转换 {ok} 个，{err} 个错误。",
    "recent":         "最近文件",
    "no_recent":      "没有最近的文件",
},
}

LANG_NAMES = {"en": "English", "es": "Español", "de": "Deutsch", "zh": "中文"}

# ─── Config ───────────────────────────────────────────────────────────────────
CONFIG_DIR  = os.path.join(os.path.expanduser("~"), ".svg2ez")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

def load_config():
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
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
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

cfg = load_config()

def t(key):
    lang = cfg.get("language", "en")
    return LANGS.get(lang, LANGS["en"]).get(key, LANGS["en"].get(key, key))

# ─── Analytics ────────────────────────────────────────────────────────────────
def ping_analytics():
    try:
        url = f"{ANALYTICS_URL}?v={VERSION}&token={ANALYTICS_TOKEN}"
        req = urllib.request.Request(url, headers={"User-Agent": f"Svg2Ez/{VERSION}"})
        urllib.request.urlopen(req, timeout=3)
    except Exception:
        pass

# ─── Update check ─────────────────────────────────────────────────────────────
def check_for_updates():
    try:
        api = "https://api.github.com/repos/kibalyion/svg2ez/releases/latest"
        req = urllib.request.Request(api, headers={"User-Agent": f"Svg2Ez/{VERSION}"})
        resp = urllib.request.urlopen(req, timeout=5)
        data = json.loads(resp.read())
        latest = data.get("tag_name", "").lstrip("v")
        url    = data.get("html_url", WEBSITE_URL)
        # Solo avisar si la versión de GitHub es MAYOR que la actual
        if latest and latest != VERSION:
            def ver_tuple(v):
                try: return tuple(int(x) for x in v.split("."))
                except: return (0,)
            if ver_tuple(latest) > ver_tuple(VERSION):
                return latest, url
    except Exception:
        pass
    return None

# ─── SVG utilities ────────────────────────────────────────────────────────────
def normalize_color(s):
    if not s or s.strip().lower() in ("none","inherit","transparent",""): return None
    s = s.strip().lower()
    if s.startswith("#"):
        h = s[1:]
        if len(h) == 3: h = h[0]*2+h[1]*2+h[2]*2
        return "#" + h.zfill(6)
    return None

def parse_style(st):
    p = {}
    if not st: return p
    for part in st.split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            p[k.strip()] = v.strip()
    return p

def svg_tag(el):
    t = el.tag
    return t.split("}", 1)[1] if "}" in t else t

def has_color(el, css=None):
    st = resolve_style(el, css or {})
    for c in [st.get("fill", el.get("fill","")), st.get("stroke", el.get("stroke",""))]:
        if c and c.strip().lower() not in ("","none"): return True
    return False

def parse_css_block(root):
    css = {}
    SVG_NS = "http://www.w3.org/2000/svg"
    pat = re.compile(r"[.#]([\w-]+)\s*\{([^}]+)\}")
    for el in root.iter(f"{{{SVG_NS}}}style"):
        for m in pat.finditer(el.text or ""):
            props = {}
            for prop in m.group(2).split(";"):
                prop = prop.strip()
                if ":" in prop:
                    k, v = prop.split(":", 1)
                    props[k.strip()] = v.strip()
            css[m.group(1)] = props
    return css

def resolve_style(el, css):
    result = {}
    for attr in ["fill","stroke","stroke-width","opacity"]:
        val = el.get(attr)
        if val: result[attr] = val
    for cls in el.get("class","").split():
        if cls in css: result.update(css[cls])
    result.update(parse_style(el.get("style","")))
    return result

def detect_unknown_colors(svg_path, color_map):
    try:
        tree = etree.parse(svg_path)
        root = tree.getroot()
        css  = parse_css_block(root)
        found = set()
        for el in root.iter():
            if svg_tag(el) not in ("path","circle","ellipse","rect","line"): continue
            st = resolve_style(el, css)
            for attr in ["fill","stroke"]:
                c = normalize_color(st.get(attr, el.get(attr,"")))
                if c: found.add(c)
        return [c for c in found if c not in color_map]
    except Exception:
        return []

def hex_to_dxf_color(hex_color):
    ACI = {7:(0,0,0),1:(255,0,0),2:(255,255,0),3:(0,255,0),
           4:(0,255,255),5:(0,0,255),6:(255,0,255),8:(128,128,128),
           9:(192,192,192),30:(255,128,0),11:(0,128,255),141:(128,0,255)}
    try:
        h = hex_color.lstrip("#")
        r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
        return min(ACI.keys(), key=lambda i: (r-ACI[i][0])**2+(g-ACI[i][1])**2+(b-ACI[i][2])**2)
    except Exception:
        return 7

# ─── Transform math ───────────────────────────────────────────────────────────
def parse_transform(t):
    if not t: return [1,0,0,1,0,0]
    m = [1,0,0,1,0,0]
    mo = re.search(r"matrix\(([^)]+)\)", t)
    if mo:
        v = [float(x) for x in re.split(r"[,\s]+", mo.group(1).strip())]
        if len(v)==6: m = v
    tr = re.search(r"translate\(([^)]+)\)", t)
    if tr:
        v = [float(x) for x in re.split(r"[,\s]+", tr.group(1).strip())]
        m = mul(m,[1,0,0,1,v[0],v[1] if len(v)>1 else 0])
    sc = re.search(r"scale\(([^)]+)\)", t)
    if sc:
        v = [float(x) for x in re.split(r"[,\s]+", sc.group(1).strip())]
        m = mul(m,[v[0],0,0,v[1] if len(v)>1 else v[0],0,0])
    ro = re.search(r"rotate\(([^)]+)\)", t)
    if ro:
        v = [float(x) for x in re.split(r"[,\s]+", ro.group(1).strip())]
        a = math.radians(v[0]); ca,sa = math.cos(a),math.sin(a)
        rm = [ca,sa,-sa,ca,0,0]
        if len(v)==3:
            cx,cy = v[1],v[2]; rm[4]=cx-cx*ca+cy*sa; rm[5]=cy-cx*sa-cy*ca
        m = mul(m,rm)
    return m

def mul(a,b):
    a1,b1,c1,d1,e1,f1=a; a2,b2,c2,d2,e2,f2=b
    return [a1*a2+c1*b2,b1*a2+d1*b2,a1*c2+c1*d2,b1*c2+d1*d2,a1*e2+c1*f2+e1,b1*e2+d1*f2+f1]

def compose(stack):
    r=[1,0,0,1,0,0]
    for t in stack: r=mul(r,t)
    return r

def am(m,x,y):
    a,b,c,d,e,f=m; return a*x+c*y+e, b*x+d*y+f

def get_svg_scale(root):
    def pu(s):
        s=s.strip()
        for u,f in [("mm",1.0),("cm",10.0),("in",25.4),("pt",25.4/72),("px",25.4/96)]:
            if s.endswith(u): return float(s[:-len(u)])*f
        try: return float(s)*(25.4/96)
        except: return 1.0
    w=pu(root.get("width","0")); h=pu(root.get("height","0"))
    vb=root.get("viewBox","")
    if vb:
        p=[float(x) for x in re.split(r"[,\s]+",vb.strip())]
        return (w/p[2] if p[2] else 1.0), (h/p[3] if p[3] else 1.0), h
    return 1.0,1.0,h

# ─── Path parser ──────────────────────────────────────────────────────────────
def tokenize_path(d):
    return re.findall(r"[MmZzLlHhVvCcSsQqTtAa]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?", d)

def bezier3(p0,p1,p2,p3,n):
    x0,y0=p0; x1,y1=p1; x2,y2=p2; x3,y3=p3
    pts=[]
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

def path_to_subpaths(d, matrix, sx, sy, h_mm, bsegs=8):
    tokens=tokenize_path(d); subpaths=[]; current=[]
    pos=[0.0,0.0]; start=[0.0,0.0]; lc=None; cmd="M"; i=0
    def mm(x,y):
        tx,ty=am(matrix,x,y); return tx*sx, h_mm-ty*sy
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
        if re.match(r"^[A-Za-z]$",tk_):
            cmd=tk_; i+=1
            if cmd in ("Z","z"):
                if current and len(current)>2:
                    fx,fy=current[0]; lx,ly=current[-1]
                    if abs(fx-lx)>1e-4 or abs(fy-ly)>1e-4: current.append((fx,fy))
                    subpaths.append({"pts":current,"closed":True})
                current=[]; pos[0]=start[0]; pos[1]=start[1]; lc=None
            continue
        if cmd in ("M","m"):
            if current: subpaths.append({"pts":current,"closed":False})
            v=gn(2)
            if len(v)<2: continue
            if cmd=="m": pos[0]+=v[0]; pos[1]+=v[1]
            else: pos[0]=v[0]; pos[1]=v[1]
            start=pos[:]; current=[mm(pos[0],pos[1])]
            cmd="l" if cmd=="m" else "L"
        elif cmd in ("L","l"):
            v=gn(2)
            if len(v)<2: continue
            if cmd=="l": pos[0]+=v[0]; pos[1]+=v[1]
            else: pos[0]=v[0]; pos[1]=v[1]
            current.append(mm(pos[0],pos[1])); lc=None
        elif cmd in ("H","h"):
            v=gn(1)
            if not v: continue
            if cmd=="h": pos[0]+=v[0]
            else: pos[0]=v[0]
            current.append(mm(pos[0],pos[1])); lc=None
        elif cmd in ("V","v"):
            v=gn(1)
            if not v: continue
            if cmd=="v": pos[1]+=v[0]
            else: pos[1]=v[0]
            current.append(mm(pos[0],pos[1])); lc=None
        elif cmd in ("C","c"):
            v=gn(6)
            if len(v)<6: continue
            if cmd=="c": x1=pos[0]+v[0];y1=pos[1]+v[1];x2=pos[0]+v[2];y2=pos[1]+v[3];x3=pos[0]+v[4];y3=pos[1]+v[5]
            else: x1,y1,x2,y2,x3,y3=v
            for pt in bezier3((pos[0],pos[1]),(x1,y1),(x2,y2),(x3,y3),bsegs): current.append(mm(*pt))
            lc=(x2,y2); pos[0]=x3; pos[1]=y3
        elif cmd in ("S","s"):
            v=gn(4)
            if len(v)<4: continue
            x1=(2*pos[0]-lc[0]) if lc else pos[0]; y1=(2*pos[1]-lc[1]) if lc else pos[1]
            if cmd=="s": x2=pos[0]+v[0];y2=pos[1]+v[1];x3=pos[0]+v[2];y3=pos[1]+v[3]
            else: x2,y2,x3,y3=v
            for pt in bezier3((pos[0],pos[1]),(x1,y1),(x2,y2),(x3,y3),bsegs): current.append(mm(*pt))
            lc=(x2,y2); pos[0]=x3; pos[1]=y3
        elif cmd in ("Q","q"):
            v=gn(4)
            if len(v)<4: continue
            if cmd=="q": x1=pos[0]+v[0];y1=pos[1]+v[1];x2=pos[0]+v[2];y2=pos[1]+v[3]
            else: x1,y1,x2,y2=v
            cx1=pos[0]+(2/3)*(x1-pos[0]); cy1=pos[1]+(2/3)*(y1-pos[1])
            cx2=x2+(2/3)*(x1-x2); cy2=y2+(2/3)*(y1-y2)
            for pt in bezier3((pos[0],pos[1]),(cx1,cy1),(cx2,cy2),(x2,y2),bsegs): current.append(mm(*pt))
            lc=(x1,y1); pos[0]=x2; pos[1]=y2
        elif cmd in ("T","t"):
            v=gn(2)
            if len(v)<2: continue
            x1=(2*pos[0]-lc[0]) if lc else pos[0]; y1=(2*pos[1]-lc[1]) if lc else pos[1]
            if cmd=="t": x2=pos[0]+v[0];y2=pos[1]+v[1]
            else: x2,y2=v
            cx1=pos[0]+(2/3)*(x1-pos[0]); cy1=pos[1]+(2/3)*(y1-pos[1])
            cx2=x2+(2/3)*(x1-x2); cy2=y2+(2/3)*(y1-y2)
            for pt in bezier3((pos[0],pos[1]),(cx1,cy1),(cx2,cy2),(x2,y2),bsegs): current.append(mm(*pt))
            lc=(x1,y1); pos[0]=x2; pos[1]=y2
        elif cmd in ("A","a"):
            v=gn(7)
            if len(v)<7: continue
            rx,ry,xr,la,sw,ex,ey=v
            if cmd=="a": ex+=pos[0]; ey+=pos[1]
            for pt in arc_points(pos[0],pos[1],rx,ry,xr,int(la),int(sw),ex,ey): current.append(mm(*pt))
            pos[0]=ex; pos[1]=ey; lc=None
        else:
            i+=1; continue
    if current and len(current)>1:
        subpaths.append({"pts":current,"closed":False})
    return subpaths

# ─── Conversion engine ────────────────────────────────────────────────────────
def convert_svg(svg_path, color_map, bezier_segs=8, scale_factor=100.0,
                log_fn=None, output_path=None):
    def log(msg):
        if log_fn: log_fn(msg)

    tree=etree.parse(svg_path); root=tree.getroot()
    sx,sy,h_mm=get_svg_scale(root)
    # Apply scale correction
    if scale_factor != 100.0:
        f = scale_factor/100.0
        sx *= f; sy *= f

    css=parse_css_block(root)
    log(f"SVG: {root.get('width')} × {root.get('height')}")

    doc=ezdxf.new(dxfversion="R2010"); msp=doc.modelspace()
    created=set(); stats={}

    # All layers black in DXF — EzCad3 ignores ACI color anyway

    def get_type(color):
        if color and color in color_map:
            return color_map[color].get("type","OTHER")
        return "OTHER"

    def ensure(name, tipo="OTHER"):
        if name not in created:
            doc.layers.add(name=name, color=7)  # negro — los colores se ajustan en EzCad3
            created.add(name)

    def lname(did, tipo): return f"{did}_{tipo}"[:31]

    def emit(pts, layer, closed=False):
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
        msp.add_lwpolyline([(x,y,0) for x,y in clean],format="xyz",
                           dxfattribs={"layer":layer,"flags":flags})
        stats[layer]=stats.get(layer,0)+1

    def add_path(d,matrix,f,s,did):
        ft=get_type(f) if f and f!="none" else None
        st=get_type(s) if s and s!="none" else None
        for sp in path_to_subpaths(d,matrix,sx,sy,h_mm,bezier_segs):
            pts=sp["pts"]; cl=sp["closed"]
            if len(pts)<2: continue
            if cl and ft: l=lname(did,ft); ensure(l,ft); emit(pts,l,True)
            elif st: l=lname(did,st); ensure(l,st); emit(pts,l,cl)
            elif ft: l=lname(did,ft); ensure(l,ft); emit(pts,l,cl)

    def add_circle(el,matrix,f,s,did):
        cx=float(el.get("cx",0)); cy=float(el.get("cy",0)); r=float(el.get("r",0))
        if r==0: return
        tcx,tcy=am(matrix,cx,cy); mx=tcx*sx; my=h_mm-tcy*sy
        a,b,c,d=matrix[0],matrix[1],matrix[2],matrix[3]
        r_mm=r*math.sqrt(abs(a*d-b*c))*sx
        if s and s!="none":
            tipo=get_type(s); l=lname(did,tipo); ensure(l,tipo)
            msp.add_circle((mx,my),r_mm,dxfattribs={"layer":l}); stats[l]=stats.get(l,0)+1
        if f and f!="none":
            tipo=get_type(f); l=lname(did,tipo); ensure(l,tipo)
            n=64
            pts=[(mx+r_mm*math.cos(2*math.pi*k/n),my+r_mm*math.sin(2*math.pi*k/n)) for k in range(n)]
            emit(pts,l,True)

    def process(el,tstack,did,pf,ps):
        tag=svg_tag(el)
        if tag in ("defs","namedview","metadata","title","desc","clipPath","symbol","style","script"): return
        ns=tstack+[parse_transform(el.get("transform",""))]; matrix=compose(ns)
        st=resolve_style(el,css)
        f=normalize_color(st.get("fill",el.get("fill",""))) or pf
        s=normalize_color(st.get("stroke",el.get("stroke",""))) or ps
        if tag=="g":
            for ch in el: process(ch,ns,did,f,s)
        elif tag=="path":
            d=el.get("d","")
            if d: add_path(d,matrix,f,s,did)
        elif tag=="circle":
            add_circle(el,matrix,f,s,did)
        elif tag in ("ellipse","rect"):
            if tag=="ellipse":
                cx=float(el.get("cx",0));cy=float(el.get("cy",0))
                rx=float(el.get("rx",0));ry=float(el.get("ry",0)); n=48
                raw=[(cx+rx*math.cos(2*math.pi*k/n),cy+ry*math.sin(2*math.pi*k/n)) for k in range(n)]
            else:
                x=float(el.get("x",0));y=float(el.get("y",0))
                w=float(el.get("width",0));h2=float(el.get("height",0))
                raw=[(x,y),(x+w,y),(x+w,y+h2),(x,y+h2)]
            pts=[]
            for px,py in raw:
                tx,ty=am(matrix,px,py); pts.append((tx*sx,h_mm-ty*sy))
            for col in [s,f]:
                if col and col!="none":
                    tipo=get_type(col); l=lname(did,tipo); ensure(l,tipo); emit(pts,l,True)
        elif tag not in ("text","image","use"):
            for ch in el: process(ch,ns,did,f,s)

    # Find main layer
    layer1=None
    for el in root.iter():
        if el.get(f"{{{INK_NS}}}groupmode")=="layer": layer1=el; break
    if layer1 is None: layer1=root

    # Detect top-level designs
    idx=1; designs=[]
    for ch in layer1:
        tag=svg_tag(ch)
        if tag in ("defs","namedview","metadata","text"): continue
        colored=[e for e in ch.iter()
                 if svg_tag(e) in ("path","circle","ellipse","rect","line") and has_color(e,css)]
        if not colored: continue
        label=ch.get(f"{{{INK_NS}}}label","").strip()
        id_=ch.get("id","").strip()
        did=re.sub(r"[^a-zA-Z0-9_-]","_",label or id_ or f"D{idx}")[:20]
        designs.append((did,ch)); idx+=1

    log(f"{t('designs_found')}: {len(designs)}")
    for did,el in designs:
        inner=[e for e in el.iter() if svg_tag(e) in ("path","circle","ellipse","rect")]
        log(f"  → {did} ({len(inner)})")
        process(el,[parse_transform("")],did,None,None)

    out=output_path or (os.path.splitext(svg_path)[0]+"_ezcad.dxf")
    doc.saveas(out)
    total=sum(stats.values())
    log(f"\n✓ {total} {t('entities')} · {len(created)} {t('layers')}")
    return out, total, len(created)

# ─── GUI Windows ──────────────────────────────────────────────────────────────
class SettingsWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent=parent
        self.title(t("settings_title"))
        self.geometry("680x740")
        self.resizable(True,True)
        self.configure(bg="#f5f5f5")
        self.grab_set()

        tk.Label(self,text=t("settings_title"),font=("Arial",13,"bold"),
                 bg="#f5f5f5",fg="#1a1a2e").pack(pady=(14,2),padx=16,anchor="w")
        tk.Label(self,text=t("settings_info"),font=("Arial",9),
                 bg="#f5f5f5",fg="#666",justify="left").pack(padx=16,anchor="w")

        # Language
        lf=tk.Frame(self,bg="#f5f5f5"); lf.pack(fill="x",padx=16,pady=(8,4))
        tk.Label(lf,text=t("lang_label"),font=("Arial",9,"bold"),
                 bg="#f5f5f5",fg="#1a1a2e").pack(side="left",padx=(0,8))
        self.lang_var=tk.StringVar(value=cfg.get("language","en"))
        for code,name in LANG_NAMES.items():
            tk.Radiobutton(lf,text=name,variable=self.lang_var,value=code,
                           bg="#f5f5f5",font=("Arial",9),
                           activebackground="#f5f5f5").pack(side="left",padx=4)
        tk.Frame(self,bg="#ddd",height=1).pack(fill="x",padx=16,pady=4)

        # Color table con scroll
        tk.Label(self,text="Color Mapping",font=("Arial",10,"bold"),
                 bg="#f5f5f5",fg="#1a1a2e").pack(padx=16,anchor="w",pady=(4,2))
        table_container = tk.Frame(self, bg="#f5f5f5", relief="solid", bd=1)
        table_container.pack(fill="x", padx=16, pady=(0,4))
        canvas = tk.Canvas(table_container, bg="#f5f5f5", height=280, highlightthickness=0)
        scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=canvas.yview)
        self.cols_frame = tk.Frame(canvas, bg="#f5f5f5")
        self.cols_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0,0), window=self.cols_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        for i,h in enumerate([t("input_color"),"Hex SVG","Type",t("remove")]):
            tk.Label(self.cols_frame,text=h,font=("Arial",8,"bold"),bg="#ddd",
                     padx=4,pady=3).grid(row=0,column=i,sticky="ew",padx=1,pady=1)
        for c,w in [(0,50),(1,100),(2,160),(3,46)]:
            self.cols_frame.columnconfigure(c,minsize=w)

        self.rows=[]
        color_map=cfg.get("color_map",DEFAULT_COLOR_MAP)
        for hex_color,info in color_map.items():
            if not hex_color.startswith("#"): continue
            self._add_row(hex_color,info.get("type","OTHER"))

        tk.Button(self,text=t("add_color"),font=("Arial",9),bg="#e8f8ff",fg="#00b5e1",
                  relief="flat",padx=8,pady=4,command=self._add_new_row).pack(padx=16,pady=4,anchor="w")
        tk.Frame(self,bg="#ddd",height=1).pack(fill="x",padx=16,pady=4)

        # Quality
        tk.Label(self,text=t("quality_label"),font=("Arial",9),
                 bg="#f5f5f5",fg="#555").pack(padx=16,anchor="w")
        self.quality_var=tk.IntVar(value=cfg.get("bezier_quality",8))
        ttk.Scale(self,from_=4,to=20,variable=self.quality_var,
                  orient="horizontal").pack(fill="x",padx=16,pady=(0,2))
        tk.Label(self,textvariable=self.quality_var,font=("Arial",9),
                 bg="#f5f5f5",fg="#888").pack(anchor="w",padx=16)

        # Scale
        sf=tk.Frame(self,bg="#f5f5f5"); sf.pack(fill="x",padx=16,pady=(6,0))
        tk.Label(sf,text=t("scale_label"),font=("Arial",9),bg="#f5f5f5",fg="#555").pack(side="left")
        self.scale_var=tk.StringVar(value=str(cfg.get("scale_factor",100.0)))
        tk.Entry(sf,textvariable=self.scale_var,width=7,font=("Consolas",9)).pack(side="left",padx=6)
        tk.Label(sf,text=t("scale_hint"),font=("Arial",8),bg="#f5f5f5",fg="#aaa").pack(side="left")

        # Output folder
        tk.Label(self,text=t("output_folder"),font=("Arial",9,"bold"),
                 bg="#f5f5f5",fg="#1a1a2e").pack(padx=16,anchor="w",pady=(8,0))
        of=tk.Frame(self,bg="#f5f5f5"); of.pack(fill="x",padx=16,pady=2)
        self.out_var=tk.StringVar(value=cfg.get("output_folder",""))
        tk.Entry(of,textvariable=self.out_var,font=("Arial",8),state="readonly").pack(side="left",fill="x",expand=True)
        tk.Button(of,text=t("browse"),relief="flat",bg="#e8f8ff",
                  command=lambda:self.out_var.set(filedialog.askdirectory() or self.out_var.get())
                  ).pack(side="left",padx=2)
        tk.Button(of,text=t("clear"),relief="flat",bg="#ffeeee",fg="#cc0000",
                  command=lambda:self.out_var.set("")).pack(side="left")
        tk.Label(self,text=t("output_same"),font=("Arial",8),bg="#f5f5f5",fg="#aaa").pack(padx=16,anchor="w")

        # Donated
        df=tk.Frame(self,bg="#f5f5f5"); df.pack(fill="x",padx=16,pady=(8,0))
        self.donated_var=tk.BooleanVar(value=cfg.get("donated",False))
        tk.Checkbutton(df,text=t("donated_lbl"),variable=self.donated_var,
                       bg="#f5f5f5",font=("Arial",9),activebackground="#f5f5f5").pack(side="left")

        # Buttons — siempre visibles al fondo
        bf=tk.Frame(self,bg="#e8e8e8",relief="raised",bd=1)
        bf.pack(side="bottom",fill="x",padx=0,pady=0)
        tk.Button(bf,text=t("cancel"),font=("Arial",10),relief="flat",bg="#eee",
                  padx=14,pady=8,command=self.destroy).pack(side="right",padx=8,pady=6)
        tk.Button(bf,text=t("save"),font=("Arial",11,"bold"),relief="flat",
                  bg="#00b5e1",fg="white",padx=20,pady=8,
                  command=self._save).pack(side="right",pady=6)

    def _add_row(self,hex_color,layer_type):
        r=len(self.rows)+1
        def safe_bg(c):
            try: self.winfo_rgb(c); return c
            except: return "#ffffff"

        svg_btn=tk.Button(self.cols_frame,bg=safe_bg(hex_color),width=3,relief="solid",bd=1,cursor="hand2")
        svg_btn.grid(row=r,column=0,padx=2,pady=2,sticky="ew")
        hex_var=tk.StringVar(value=hex_color)
        tk.Entry(self.cols_frame,textvariable=hex_var,font=("Consolas",9),width=10).grid(row=r,column=1,padx=2,pady=2,sticky="ew")
        type_var=tk.StringVar(value=layer_type)
        ttk.Combobox(self.cols_frame,textvariable=type_var,
                     values=["CUT_INNER","CUT_OUTER","ENGRAVE","OTHER"],
                     state="readonly",width=14).grid(row=r,column=2,padx=2,pady=2,sticky="ew")
        del_btn=tk.Button(self.cols_frame,text="✕",font=("Arial",8,"bold"),relief="flat",
                          bg="#ffeeee",fg="#cc0000",padx=6,pady=2,cursor="hand2")
        del_btn.grid(row=r,column=3,padx=2,pady=2)

        def pick_svg(btn=svg_btn,hv=hex_var):
            col=colorchooser.askcolor(color=hv.get(),title="SVG Color")[1]
            if col: hv.set(col.lower()); btn.configure(bg=col)
        svg_btn.configure(command=pick_svg)

        row_data={"hex":hex_var,"type":type_var,
                  "widgets":[svg_btn,del_btn]}
        def remove(rd=row_data):
            for w in rd["widgets"]: w.destroy()
            # hide all in row
            for col in range(6):
                w=self.cols_frame.grid_slaves(row=r,column=col)
                if w: w[0].destroy()
            if rd in self.rows: self.rows.remove(rd)
        del_btn.configure(command=remove)
        self.rows.append(row_data)

    def _add_new_row(self):
        self._add_row("#ffffff","OTHER")

    def _save(self):
        new_map={}
        for rd in self.rows:
            h=rd["hex"].get().strip().lower()
            if not h.startswith("#"): h="#"+h
            new_map[h]={"type":rd["type"].get(),"label_key":rd["type"].get().lower()}
        cfg["color_map"]=new_map
        cfg["bezier_quality"]=int(self.quality_var.get())
        try: cfg["scale_factor"]=float(self.scale_var.get())
        except: cfg["scale_factor"]=100.0
        cfg["output_folder"]=self.out_var.get()
        donated_before=cfg.get("donated",False)
        cfg["donated"]=self.donated_var.get()
        if cfg["donated"] and not donated_before:
            messagebox.showinfo("❤️",t("donated_thanks"))
        lang_changed=(cfg.get("language","en")!=self.lang_var.get())
        cfg["language"]=self.lang_var.get()
        save_config(cfg)
        self.destroy()
        if lang_changed:
            new_lang=cfg["language"]
            title=LANGS.get(new_lang,LANGS["en"]).get("restart_title","Restart")
            msg=LANGS.get(new_lang,LANGS["en"]).get("restart_needed","Please restart.")
            messagebox.showinfo(title,msg)
        else:
            self.parent.refresh_lang()


class HelpWindow(tk.Toplevel):
    def __init__(self,parent):
        super().__init__(parent)
        self.title(t("help_title"))
        self.geometry("560x520")
        self.resizable(True,True)
        self.configure(bg="#1a1a2e")
        self.grab_set()
        frame=tk.Frame(self,bg="#1a1a2e"); frame.pack(fill="both",expand=True,padx=2,pady=2)
        text=tk.Text(frame,font=("Consolas",9),bg="#1a1a2e",fg="#00b5e1",
                     relief="flat",padx=16,pady=12,wrap="word")
        scroll=ttk.Scrollbar(frame,command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right",fill="y"); text.pack(fill="both",expand=True)
        text.insert("1.0",t("help_text"))
        text.configure(state="disabled")
        tk.Button(self,text="OK",font=("Arial",10,"bold"),bg="#00b5e1",fg="white",
                  relief="flat",padx=20,pady=6,command=self.destroy).pack(pady=10)


# ─── Main App ─────────────────────────────────────────────────────────────────
class App:
    def __init__(self,root_win):
        self.root=root_win
        self._build_ui()
        threading.Thread(target=ping_analytics,daemon=True).start()
        if cfg.get("check_updates",True):
            root_win.after(4000,self._check_update_async)
        if len(sys.argv)>1:
            arg=sys.argv[1]
            if arg.lower().endswith(".svg"):
                root_win.after(400,lambda:self.run_conversion(arg))
            elif os.path.isdir(arg):
                root_win.after(400,lambda:self.pick_batch(arg))

    def _build_ui(self):
        root=self.root
        root.title(t("app_title"))
        root.geometry("510x510")
        root.resizable(False,False)
        root.configure(bg="#f5f5f5")

        # Header
        hdr=tk.Frame(root,bg="#1a1a2e"); hdr.pack(fill="x")
        tk.Label(hdr,text="Svg2Ez",font=("Arial",17,"bold"),
                 bg="#1a1a2e",fg="#00b5e1").pack(side="left",padx=16,pady=10)
        tk.Label(hdr,text=f"v{VERSION}",font=("Arial",8),
                 bg="#1a1a2e",fg="#444").pack(side="left",pady=10)

        btn_row=tk.Frame(hdr,bg="#1a1a2e"); btn_row.pack(side="right",padx=10)

        if not cfg.get("donated",False):
            self.donate_btn=tk.Button(btn_row,text=t("donate"),font=("Arial",9,"bold"),
                                      bg="#ffc439",fg="#003087",relief="flat",
                                      padx=8,pady=4,cursor="hand2",
                                      command=lambda:webbrowser.open(PAYPAL_URL))
            self.donate_btn.pack(side="right",padx=3,pady=8)
        else:
            self.donate_btn=None

        self.feedback_btn=tk.Button(btn_row,text=t("feedback"),font=("Arial",9),
                                    bg="#2a2a4e",fg="#aaa",relief="flat",
                                    padx=8,pady=4,cursor="hand2",command=self._open_feedback)
        self.feedback_btn.pack(side="right",padx=3,pady=8)

        self.help_btn=tk.Button(btn_row,text=t("help"),font=("Arial",9),
                                bg="#2a2a4e",fg="#aaa",relief="flat",
                                padx=8,pady=4,cursor="hand2",command=lambda:HelpWindow(self.root))
        self.help_btn.pack(side="right",padx=3,pady=8)

        self.settings_btn=tk.Button(btn_row,text=t("settings"),font=("Arial",9),
                                    bg="#2a2a4e",fg="#aaa",relief="flat",
                                    padx=8,pady=4,cursor="hand2",command=lambda:SettingsWindow(self.root))
        self.settings_btn.pack(side="right",padx=3,pady=8)

        # Main buttons
        bf=tk.Frame(root,bg="#f5f5f5"); bf.pack(pady=(16,6))
        self.open_btn=tk.Button(bf,text=t("open_btn"),font=("Arial",12,"bold"),
                                bg="#00b5e1",fg="white",activebackground="#0099c4",
                                activeforeground="white",relief="flat",padx=16,pady=11,
                                command=self.pick_and_convert)
        self.open_btn.pack(side="left",padx=4,ipadx=6)
        self.batch_btn=tk.Button(bf,text=t("batch_btn"),font=("Arial",10),
                                 bg="#2a2a4e",fg="#aaa",activebackground="#3a3a6e",
                                 activeforeground="white",relief="flat",padx=12,pady=11,
                                 command=lambda:self.pick_batch())
        self.batch_btn.pack(side="left",padx=4)

        # Drop zone
        if DND_AVAILABLE:
            self.drop_lbl=tk.Label(root,text=t("drag_hint"),font=("Arial",10),
                                   bg="#e4f6fb",fg="#00a0c8",relief="solid",bd=1,
                                   padx=10,pady=10,cursor="hand2")
            self.drop_lbl.pack(fill="x",padx=22,pady=(0,8))
            try:
                self.drop_lbl.drop_target_register(DND_FILES)
                self.drop_lbl.dnd_bind("<<Drop>>",self.on_drop)
                self.drop_lbl.dnd_bind("<<DragEnter>>",lambda e:self.drop_lbl.configure(bg="#b8e8f5"))
                self.drop_lbl.dnd_bind("<<DragLeave>>",lambda e:self.drop_lbl.configure(bg="#e4f6fb"))
                root.drop_target_register(DND_FILES)
                root.dnd_bind("<<Drop>>",self.on_drop)
            except Exception:
                pass
        else:
            self.drop_lbl=tk.Label(root,text=t("drag_hint"),font=("Arial",9),bg="#f5f5f5",fg="#bbb")
            self.drop_lbl.pack(pady=(0,8))

        # Log
        lf=tk.Frame(root,bg="#f5f5f5"); lf.pack(fill="both",expand=True,padx=22)
        self.log_text=tk.Text(lf,height=9,font=("Consolas",9),bg="#1a1a2e",fg="#00b5e1",
                              relief="flat",state="disabled")
        self.log_text.pack(fill="both",expand=True)

        self.progress=ttk.Progressbar(root,mode="indeterminate")
        self.progress.pack(fill="x",padx=22,pady=6)

        # Footer
        tk.Frame(root,bg="#ddd",height=1).pack(fill="x",padx=22)
        footer=tk.Frame(root,bg="#f5f5f5"); footer.pack(fill="x",padx=22,pady=6)
        tk.Label(footer,text="Free & open source · github.com/kibalyion/svg2ez",
                 font=("Arial",8),bg="#f5f5f5",fg="#aaa").pack(side="left")

    def refresh_lang(self):
        self.root.title(t("app_title"))
        self.open_btn.configure(text=t("open_btn"))
        self.batch_btn.configure(text=t("batch_btn"))
        if self.donate_btn: self.donate_btn.configure(text=t("donate"))
        self.feedback_btn.configure(text=t("feedback"))
        self.help_btn.configure(text=t("help"))
        self.settings_btn.configure(text=t("settings"))
        if hasattr(self,"drop_lbl"): self.drop_lbl.configure(text=t("drag_hint"))
        self.root.update()

    def on_drop(self,event):
        raw=event.data.strip()
        paths=re.findall(r"\{([^}]+)\}|(\S+\.(?:svg|SVG))",raw)
        path=None
        for p in paths:
            c=p[0] or p[1]
            if c.lower().endswith(".svg"): path=c; break
        if not path:
            clean=raw.strip("{}")
            if clean.lower().endswith(".svg"): path=clean
            elif os.path.isdir(clean): self.pick_batch(clean); return
        if path and os.path.exists(path):
            if hasattr(self,"drop_lbl") and DND_AVAILABLE:
                self.drop_lbl.configure(bg="#e4f6fb")
            self.run_conversion(path)
        else:
            messagebox.showwarning("",t("wrong_format"))

    def log(self,msg):
        self.log_text.configure(state="normal")
        self.log_text.insert("end",msg+"\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        self.root.update_idletasks()

    def _get_output_path(self,svg_path):
        base=os.path.splitext(svg_path)[0]+"_ezcad.dxf"
        custom=cfg.get("output_folder","")
        if custom and os.path.isdir(custom):
            return os.path.join(custom,os.path.basename(base))
        return base

    def _check_unknown_colors(self,svg_path):
        color_map=cfg.get("color_map",DEFAULT_COLOR_MAP)
        unknown=detect_unknown_colors(svg_path,color_map)
        if unknown:
            colors_str="\n".join(f"  • {c}" for c in unknown)
            msg=t("unknown_colors_msg").format(colors=colors_str)
            return messagebox.askyesno(t("unknown_colors"),msg,icon="warning")
        return True

    def _add_recent(self,path):
        recent=cfg.get("recent_files",[])
        if path in recent: recent.remove(path)
        recent.insert(0,path)
        cfg["recent_files"]=recent[:10]
        save_config(cfg)

    def _set_busy(self,busy):
        state="disabled" if busy else "normal"
        self.open_btn.configure(state=state,
            text=t("converting") if busy else t("open_btn"))
        self.batch_btn.configure(state=state)
        if busy: self.progress.start(10)
        else: self.progress.stop()

    def pick_and_convert(self):
        path=filedialog.askopenfilename(title="SVG",
            filetypes=[("SVG","*.svg"),("All","*.*")])
        if path: self.run_conversion(path)

    def run_conversion(self,svg_path):
        if not self._check_unknown_colors(svg_path): return
        self._set_busy(True)
        self.log_text.configure(state="normal"); self.log_text.delete("1.0","end"); self.log_text.configure(state="disabled")
        self.log(f"📄 {os.path.basename(svg_path)}")
        self.log("─"*40)
        color_map=cfg.get("color_map",DEFAULT_COLOR_MAP)
        bsegs=cfg.get("bezier_quality",8)
        scale=cfg.get("scale_factor",100.0)
        out_path=self._get_output_path(svg_path)
        def worker():
            try:
                out,e,l=convert_svg(svg_path,color_map,bsegs,scale,self.log,out_path)
                self._add_recent(svg_path)
                self.root.after(0,lambda:self.on_done(out,e,l))
            except Exception as ex:
                self.root.after(0,lambda:self.on_error(str(ex)))
        threading.Thread(target=worker,daemon=True).start()

    def pick_batch(self,folder=None):
        if not folder:
            folder=filedialog.askdirectory(title=t("batch_btn"))
        if not folder: return
        svgs=list(set(glob.glob(os.path.join(folder,"**","*.svg"),recursive=True)+
                      glob.glob(os.path.join(folder,"**","*.SVG"),recursive=True)))
        if not svgs: messagebox.showinfo("",t("no_recent")); return
        self._set_busy(True)
        self.log_text.configure(state="normal"); self.log_text.delete("1.0","end"); self.log_text.configure(state="disabled")
        self.log(f"📁 {len(svgs)} SVG files")
        self.log("─"*40)
        color_map=cfg.get("color_map",DEFAULT_COLOR_MAP)
        bsegs=cfg.get("bezier_quality",8)
        scale=cfg.get("scale_factor",100.0)
        def worker():
            ok=0; err=0
            for sv in svgs:
                try:
                    out_path=self._get_output_path(sv)
                    convert_svg(sv,color_map,bsegs,scale,None,out_path)
                    self.log(f"✅ {os.path.basename(sv)}"); ok+=1
                except Exception as ex:
                    self.log(f"❌ {os.path.basename(sv)}: {ex}"); err+=1
            self.root.after(0,lambda:self.on_batch_done(ok,err))
        threading.Thread(target=worker,daemon=True).start()

    def on_done(self,out,entities,layers):
        self._set_busy(False)
        self.log("─"*40)
        self.log(f"✅ {os.path.basename(out)}")
        self.log(f"📁 {os.path.dirname(out)}")
        cfg["conversions_done"]=cfg.get("conversions_done",0)+1
        save_config(cfg)
        show_donate=not cfg.get("donated",False) and cfg["conversions_done"]%3==0
        if show_donate:
            if messagebox.askyesno(t("done_title"),
                t("done_msg").format(path=out)+"\n\n"+t("donate_ask"),icon="info"):
                webbrowser.open(PAYPAL_URL)
        else:
            messagebox.showinfo(t("done_title"),t("done_msg").format(path=out))

    def on_batch_done(self,ok,err):
        self._set_busy(False)
        self.log("─"*40)
        msg=t("batch_result").format(ok=ok,err=err)
        self.log(f"📊 {msg}")
        messagebox.showinfo(t("batch_done"),msg)

    def on_error(self,err):
        self._set_busy(False)
        self.log(f"❌ {err}")
        messagebox.showerror(t("error"),err)

    def _open_feedback(self):
        win=tk.Toplevel(self.root)
        win.title(t("feedback_title"))
        win.geometry("360x180")
        win.resizable(False,False)
        win.configure(bg="#f5f5f5")
        win.grab_set()
        tk.Label(win,text=t("feedback_title"),font=("Arial",12,"bold"),
                 bg="#f5f5f5",fg="#1a1a2e").pack(pady=(16,4))
        tk.Label(win,text=t("feedback_msg"),font=("Arial",9),bg="#f5f5f5",fg="#666").pack(pady=(0,14))
        bf=tk.Frame(win,bg="#f5f5f5"); bf.pack()
        def go_github():
            import urllib.parse
            params=urllib.parse.urlencode({"title":f"[v{VERSION}] ","body":f"**Version:** {VERSION}\n\n**Description:**\n\n**Steps:**\n\n**Expected:**\n\n**Actual:**"})
            webbrowser.open(f"{ISSUES_URL}?{params}"); win.destroy()
        def go_email():
            import urllib.parse
            s=urllib.parse.quote(f"[Svg2Ez v{VERSION}]")
            webbrowser.open(f"mailto:{FEEDBACK_EMAIL}?subject={s}"); win.destroy()
        tk.Button(bf,text=t("via_github"),font=("Arial",10,"bold"),bg="#1a1a2e",fg="white",
                  relief="flat",padx=14,pady=8,cursor="hand2",command=go_github).pack(side="left",padx=6)
        tk.Button(bf,text=t("via_email"),font=("Arial",10),bg="#e8f8ff",fg="#00b5e1",
                  relief="flat",padx=14,pady=8,cursor="hand2",command=go_email).pack(side="left",padx=6)
        tk.Label(win,text=t("feedback_hint"),font=("Arial",8),bg="#f5f5f5",fg="#aaa").pack(pady=(12,0))

    def _check_update_async(self):
        if not cfg.get("check_updates",True): return
        def worker():
            result=check_for_updates()
            if result:
                new_ver,url=result
                self.root.after(0,lambda:self._show_update(new_ver,url))
        threading.Thread(target=worker,daemon=True).start()

    def _show_update(self,new_ver,url):
        msg=t("update_msg").format(new=new_ver,cur=VERSION)
        if messagebox.askyesno(t("update_title"),msg,icon="info"):
            webbrowser.open(url)


def main():
    if DND_AVAILABLE:
        root=TkinterDnD.Tk()
    else:
        root=tk.Tk()
    App(root)
    root.mainloop()

if __name__=="__main__":
    main()
