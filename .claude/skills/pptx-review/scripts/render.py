"""pptx のスライドを PNG に書き出す。

使い方: python render.py <入力.pptx> <出力ディレクトリ> [--prefix before] [--slides 1,3,5] [--width 1600]

PowerPoint の COM 操作（Windows、PowerShell 経由）を優先し、使えなければ
LibreOffice（soffice）で PDF にしてから PNG にする（pdftoppm か PyMuPDF が必要）。
出力は <出力ディレクトリ>/<prefix>-<スライド番号>.png。
最初の行に使った手段を "renderer: powerpoint" のように出す。
どの手段も使えなければ導入方法を出して終了コード 1 で終わる。
"""

import argparse
import glob
import os
import shutil
import subprocess
import sys
import tempfile
import time

TIMEOUT_SEC = 300

# 既に開いている利用者の PowerPoint を閉じないよう、自分が開いたファイルだけ閉じ、
# 他に開いているプレゼンテーションが無いときだけ Quit する。
PS_SCRIPT = r"""
param([string]$Src, [string]$Out, [string]$Prefix, [string]$Slides, [int]$Width)
$ErrorActionPreference = 'Stop'
$app = New-Object -ComObject PowerPoint.Application
$app.DisplayAlerts = 1  # ppAlertsNone
$pres = $null
try {
  # ReadOnly, Untitled, WithWindow
  $pres = $app.Presentations.Open($Src, -1, 0, 0)
  $w = $pres.PageSetup.SlideWidth
  $h = $pres.PageSetup.SlideHeight
  $height = [int]([math]::Round($Width * $h / $w))
  $targets = if ($Slides) { $Slides.Split(',') | ForEach-Object { [int]$_ } } else { 1..$pres.Slides.Count }
  foreach ($i in $targets) {
    if ($i -lt 1 -or $i -gt $pres.Slides.Count) { continue }
    $path = Join-Path $Out ("{0}-{1}.png" -f $Prefix, $i)
    $pres.Slides.Item($i).Export($path, 'PNG', $Width, $height)
  }
} finally {
  if ($pres -ne $null) { $pres.Close() }
  if ($app.Presentations.Count -eq 0) { $app.Quit() }
  [System.Runtime.InteropServices.Marshal]::ReleaseComObject($app) | Out-Null
}
"""

INSTALL_HINT = """画像化の手段が見つかりませんでした。次のどれかを用意してください。
- Windows: Microsoft PowerPoint（デスクトップ版）
- LibreOffice: https://www.libreoffice.org/download/ を入れ、soffice にパスを通す
  さらに PDF から PNG への変換に、次のどちらかが必要です
  - PyMuPDF: pip install pymupdf
  - poppler の pdftoppm（macOS: brew install poppler / Ubuntu: apt install poppler-utils）"""


def render_powerpoint(src, out, prefix, slides, width):
    if sys.platform != "win32":
        return False, "not windows"
    fd, ps1 = tempfile.mkstemp(suffix=".ps1")
    with os.fdopen(fd, "w", encoding="utf-8-sig") as f:
        f.write(PS_SCRIPT)
    try:
        cmd = [
            "powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
            "-File", ps1, "-Src", src, "-Out", out, "-Prefix", prefix,
            "-Slides", ",".join(map(str, slides)) if slides else "", "-Width", str(width),
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT_SEC)
        if r.returncode != 0:
            return False, (r.stderr or r.stdout).strip()
        return True, ""
    except (OSError, subprocess.TimeoutExpired) as e:
        return False, str(e)
    finally:
        os.remove(ps1)


def find_soffice():
    for name in ("soffice", "libreoffice"):
        path = shutil.which(name)
        if path:
            return path
    for path in (
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    ):
        if os.path.exists(path):
            return path
    return None


def pdf_to_png(pdf, out, prefix, slides, width):
    try:
        import fitz  # PyMuPDF
    except ImportError:
        fitz = None
    if fitz is not None:
        doc = fitz.open(pdf)
        for i, page in enumerate(doc, start=1):
            if slides and i not in slides:
                continue
            zoom = width / page.rect.width
            page.get_pixmap(matrix=fitz.Matrix(zoom, zoom)).save(os.path.join(out, f"{prefix}-{i}.png"))
        return True, ""
    pdftoppm = shutil.which("pdftoppm")
    if pdftoppm is None:
        return False, "PyMuPDF も pdftoppm も見つかりません"
    with tempfile.TemporaryDirectory() as tmp:
        r = subprocess.run([pdftoppm, "-png", "-scale-to-x", str(width), "-scale-to-y", "-1",
                            pdf, os.path.join(tmp, "p")], capture_output=True, text=True, timeout=TIMEOUT_SEC)
        if r.returncode != 0:
            return False, r.stderr.strip()
        # pdftoppm はページ数に応じて p-1.png / p-01.png のように桁を揃えるので、番号を読み直す
        for path in glob.glob(os.path.join(tmp, "p-*.png")):
            i = int(os.path.basename(path)[2:-4])
            if slides and i not in slides:
                continue
            shutil.move(path, os.path.join(out, f"{prefix}-{i}.png"))
    return True, ""


def render_libreoffice(src, out, prefix, slides, width):
    soffice = find_soffice()
    if soffice is None:
        return False, "soffice が見つかりません"
    with tempfile.TemporaryDirectory() as tmp:
        try:
            r = subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", tmp, src],
                               capture_output=True, text=True, timeout=TIMEOUT_SEC)
        except (OSError, subprocess.TimeoutExpired) as e:
            return False, str(e)
        pdf = os.path.join(tmp, os.path.splitext(os.path.basename(src))[0] + ".pdf")
        if r.returncode != 0 or not os.path.exists(pdf):
            return False, (r.stderr or r.stdout).strip()
        return pdf_to_png(pdf, out, prefix, slides, width)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--prefix", default="slide")
    ap.add_argument("--slides", default="", help="カンマ区切りのスライド番号。省略時は全スライド")
    ap.add_argument("--width", type=int, default=1600)
    args = ap.parse_args()

    src = os.path.abspath(args.src)
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)
    slides = [int(s) for s in args.slides.split(",") if s.strip()]

    errors = []
    for name, fn in (("powerpoint", render_powerpoint), ("libreoffice", render_libreoffice)):
        started = time.time()
        ok, err = fn(src, out, args.prefix, slides, args.width)
        if ok:
            # 前回の残りを数えないよう、今回書き出したものだけ数える
            files = [f for f in glob.glob(os.path.join(out, f"{args.prefix}-*.png"))
                     if os.path.getmtime(f) >= started - 1]
            print(f"renderer: {name}")
            print(f"{len(files)} images -> {out}")
            return 0
        errors.append(f"{name}: {err}")

    print("renderer: none")
    print("\n".join(errors), file=sys.stderr)
    print(INSTALL_HINT, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    sys.exit(main())
