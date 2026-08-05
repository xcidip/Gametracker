import os
import sys
import ctypes
import logging
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from config import ICONS_DIR, COLOR_ACCENT, COLOR_CYAN

logger = logging.getLogger("IconExtractor")

if sys.platform == "win32":
    from ctypes import wintypes

    class ICONINFO(ctypes.Structure):
        _fields_ = [
            ("fIcon", wintypes.BOOL),
            ("xHotspot", wintypes.DWORD),
            ("yHotspot", wintypes.DWORD),
            ("hbmMask", wintypes.HBITMAP),
            ("hbmColor", wintypes.HBITMAP),
        ]

    class BITMAP(ctypes.Structure):
        _fields_ = [
            ("bmType", wintypes.LONG),
            ("bmWidth", wintypes.LONG),
            ("bmHeight", wintypes.LONG),
            ("bmWidthBytes", wintypes.LONG),
            ("bmPlanes", wintypes.WORD),
            ("bmBitsPixel", wintypes.WORD),
            ("bmBits", wintypes.LPVOID),
        ]

    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ("biSize", wintypes.DWORD),
            ("biWidth", wintypes.LONG),
            ("biHeight", wintypes.LONG),
            ("biPlanes", wintypes.WORD),
            ("biBitCount", wintypes.WORD),
            ("biCompression", wintypes.DWORD),
            ("biSizeImage", wintypes.DWORD),
            ("biXPelsPerMeter", wintypes.LONG),
            ("biYPelsPerMeter", wintypes.LONG),
            ("biClrUsed", wintypes.DWORD),
            ("biClrImportant", wintypes.DWORD),
        ]

    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32
    shell32 = ctypes.windll.shell32

    # Win32 Function Signatures for 64-bit safety
    user32.PrivateExtractIconsW.argtypes = [
        wintypes.LPCWSTR, ctypes.c_int, ctypes.c_int, ctypes.c_int,
        ctypes.POINTER(wintypes.HICON), ctypes.POINTER(wintypes.UINT),
        wintypes.UINT, wintypes.UINT
    ]
    user32.PrivateExtractIconsW.restype = wintypes.UINT

    shell32.ExtractIconExW.argtypes = [
        wintypes.LPCWSTR, ctypes.c_int,
        ctypes.POINTER(wintypes.HICON), ctypes.POINTER(wintypes.HICON),
        wintypes.UINT
    ]
    shell32.ExtractIconExW.restype = wintypes.UINT

    user32.GetIconInfo.argtypes = [wintypes.HICON, ctypes.POINTER(ICONINFO)]
    user32.GetIconInfo.restype = wintypes.BOOL

    user32.GetDC.argtypes = [wintypes.HWND]
    user32.GetDC.restype = wintypes.HDC

    user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
    user32.ReleaseDC.restype = ctypes.c_int

    user32.DestroyIcon.argtypes = [wintypes.HICON]
    user32.DestroyIcon.restype = wintypes.BOOL

    gdi32.GetObjectW.argtypes = [wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID]
    gdi32.GetObjectW.restype = ctypes.c_int

    gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
    gdi32.CreateCompatibleDC.restype = wintypes.HDC

    gdi32.DeleteDC.argtypes = [wintypes.HDC]
    gdi32.DeleteDC.restype = wintypes.BOOL

    gdi32.DeleteObject.argtypes = [wintypes.HANDLE]
    gdi32.DeleteObject.restype = wintypes.BOOL

    gdi32.GetDIBits.argtypes = [
        wintypes.HDC, wintypes.HBITMAP, wintypes.UINT, wintypes.UINT,
        wintypes.LPVOID, wintypes.LPVOID, wintypes.UINT
    ]
    gdi32.GetDIBits.restype = ctypes.c_int


def extract_icon_from_exe(exe_path: str, output_icon_name: str, size: int = 64) -> str:
    """
    Extracts high-quality icon from executable or file path on Windows.
    Saves to ICONS_DIR / output_icon_name.png.
    Returns path to saved icon image, or fallback icon path if extraction fails.
    """
    target_path = ICONS_DIR / f"{output_icon_name}.png"
    if target_path.exists():
        return str(target_path)

    if not exe_path or not os.path.exists(exe_path):
        return create_fallback_icon(output_icon_name, size)

    if sys.platform == "win32":
        try:
            pil_image = _win32_extract_hicon_to_pil(exe_path, size)
            if pil_image:
                pil_image.save(target_path, "PNG")
                return str(target_path)
        except Exception as e:
            logger.warning(f"Win32 icon extraction failed for {exe_path}: {e}")

    return create_fallback_icon(output_icon_name, size)


def _win32_extract_hicon_to_pil(exe_path: str, size: int = 64) -> Image.Image:
    """Extracts HICON using PrivateExtractIconsW/ExtractIconExW and converts it to PIL Image with RGBA."""
    hicon_array = (wintypes.HICON * 1)()
    icon_id_array = (wintypes.UINT * 1)()

    # Try extracting 64x64 icon
    ret = user32.PrivateExtractIconsW(
        str(exe_path),
        0,              # Icon index
        size,           # cxIcon
        size,           # cyIcon
        hicon_array,
        icon_id_array,
        1,              # nIcons
        0               # flags
    )

    hicon = hicon_array[0] if ret > 0 and hicon_array[0] else None

    # Fallback to ExtractIconExW
    if not hicon:
        large_icons = (wintypes.HICON * 1)()
        small_icons = (wintypes.HICON * 1)()
        res = shell32.ExtractIconExW(str(exe_path), 0, large_icons, small_icons, 1)
        if res > 0 and large_icons[0]:
            hicon = large_icons[0]
            if small_icons[0]:
                user32.DestroyIcon(small_icons[0])

    if not hicon:
        return None

    try:
        icon_info = ICONINFO()
        if not user32.GetIconInfo(hicon, ctypes.byref(icon_info)):
            return None

        hbm_color = icon_info.hbmColor
        hbm_mask = icon_info.hbmMask

        bmp = BITMAP()
        if hbm_color:
            gdi32.GetObjectW(hbm_color, ctypes.sizeof(BITMAP), ctypes.byref(bmp))
            width = bmp.bmWidth
            height = bmp.bmHeight
        else:
            gdi32.GetObjectW(hbm_mask, ctypes.sizeof(BITMAP), ctypes.byref(bmp))
            width = bmp.bmWidth
            height = bmp.bmHeight // 2

        if width <= 0 or height <= 0:
            return None

        hdc = user32.GetDC(None)
        mem_dc = gdi32.CreateCompatibleDC(hdc)

        bmi = BITMAPINFOHEADER()
        bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.biWidth = width
        bmi.biHeight = -height  # Top-down
        bmi.biPlanes = 1
        bmi.biBitCount = 32     # BI_RGB 32-bit (BGRA)
        bmi.biCompression = 0   # BI_RGB

        buffer_len = width * height * 4
        buffer = ctypes.create_string_buffer(buffer_len)

        hbm_target = hbm_color if hbm_color else hbm_mask
        gdi32.GetDIBits(mem_dc, hbm_target, 0, height, buffer, ctypes.byref(bmi), 0)

        # Cleanup GDI handles
        gdi32.DeleteDC(mem_dc)
        user32.ReleaseDC(None, hdc)
        if icon_info.hbmColor:
            gdi32.DeleteObject(icon_info.hbmColor)
        if icon_info.hbmMask:
            gdi32.DeleteObject(icon_info.hbmMask)

        # Convert BGRA raw bytes to PIL RGBA image
        img = Image.frombytes("RGBA", (width, height), buffer.raw, "raw", "BGRA")

        # Fix transparent alpha if needed
        alpha = img.split()[3]
        if alpha.getextrema() == (0, 0):
            r, g, b, _ = img.split()
            img = Image.merge("RGBA", (r, g, b, Image.new("L", (width, height), 255)))

        return img
    finally:
        user32.DestroyIcon(hicon)


def create_fallback_icon(name: str, size: int = 64) -> str:
    """Generates a stylish modern gradient icon with initials if no icon extracted."""
    target_path = ICONS_DIR / f"{name}_fallback.png"
    if target_path.exists():
        return str(target_path)

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw rounded rectangle background
    shape = [(0, 0), (size - 1, size - 1)]
    draw.rounded_rectangle(shape, radius=12, fill="#272C45", outline="#6C5CE7", width=2)

    # Draw Initials text
    clean_name = "".join(c for c in name if c.isalnum()).upper()
    initials = clean_name[:2] if clean_name else "APP"

    try:
        font = ImageFont.truetype("arial.ttf", size // 2.5)
    except Exception:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), initials, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    tx = (size - tw) // 2
    ty = (size - th) // 2 - bbox[1]
    draw.text((tx, ty), initials, fill="#00CEC9", font=font)

    img.save(target_path, "PNG")
    return str(target_path)
