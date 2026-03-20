# Svg2Ez — SVG to EzCad3 DXF Converter

**Free tool for laser engravers using Inkscape or Adobe Illustrator with EzCad3.**

[![Download](https://img.shields.io/badge/Download-Windows%20.exe-00b5e1?style=for-the-badge&logo=windows)](https://github.com/kibalyion/svg2ez/releases/latest)
[![Donate](https://img.shields.io/badge/Donate-PayPal-ffc439?style=for-the-badge&logo=paypal)](https://www.paypal.com/donate/?hosted_button_id=W9BE8867AF8SA)

---

## The problem

EzCad3 struggles with SVG files from Inkscape:
- ❌ Crashes or distorts complex designs
- ❌ Doesn't understand fill areas (needed for hatching)
- ❌ Loses group structure — everything becomes one object
- ❌ Paths arrive open, so EzCad3 can't generate hatches

## The solution

Svg2Ez converts your SVG to a clean DXF that EzCad3 imports perfectly:
- ✅ Every Inkscape group becomes an independent object in EzCad3
- ✅ All paths are perfectly closed — hatch works first time
- ✅ Colors map to EzCad3 layers automatically
- ✅ Compatible with **Inkscape** and **Adobe Illustrator**
- ✅ All layers arrive in black (no color conflicts)

---

## Download

👉 **[Download Svg2Ez.exe for Windows](https://github.com/kibalyion/svg2ez/releases/latest)**

No installation required. Just run the `.exe`.

---

## How to use

### 1. Prepare your SVG in Inkscape

Assign colors to each element using the SLC palette:

| Color | Hex | Purpose |
|-------|-----|---------|
| ⬛ Black | `#000000` | Interior cut |
| 🟣 Purple | `#8800FF` | Exterior cut |
| 🔵 Blue | `#0000FF` | Engrave (hatch) |

Group each design with **Ctrl+G**. Name your groups — the name will appear in EzCad3.

### 2. Convert with Svg2Ez

- Open `Svg2Ez.exe`
- Click **Open SVG & Convert** or drag the SVG onto the window
- A `_ezcad.dxf` file is created in the same folder

### 3. Import in EzCad3

- `File → Import → select the .dxf`
- Each design appears as an independent group
- Select the `ENGRAVE` layer → `Modify → Hatch` to generate fill lines

---

## Features

- 🌍 **Multilingual** — English, Español, Deutsch, 中文
- ⚙️ **Configurable color mapping** — customize which SVG colors map to which layer types
- 🎨 **Output color control** — set the DXF color for each layer (controls EzCad3 pen assignment)
- 🐛 **Bug reports** — built-in feedback button
- 📊 **Privacy-respecting analytics** — anonymous usage counter, no personal data collected

---

## Run from source

```bash
pip install lxml ezdxf tkinterdnd2
python svg2ez.py
```

---

## Build .exe

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "Svg2Ez" --collect-all tkinterdnd2 svg2ez.py
```

---

## Contributing

Found a bug? Have a suggestion?
👉 [Open an issue](https://github.com/kibalyion/svg2ez/issues/new)

---

## License

MIT License — free to use, modify and distribute.

---

## Support the project

Svg2Ez is free. If it saves you time, a small donation helps keep it maintained.

[![Donate with PayPal](https://img.shields.io/badge/Donate-PayPal-ffc439?style=flat&logo=paypal)](https://www.paypal.com/donate/?hosted_button_id=W9BE8867AF8SA)# svg2ez
Free SVG to DXF converter for EzCad3 laser engravers. Works with Inkscape and Adobe Illustrator.
