#!/usr/bin/env python3
"""
おでんスタンド Instagram リール動画生成スクリプト
コンセプト: ドリンク推し（18-25秒 / 1080x1920 / 9:16）
"""

import os
import subprocess
import math
import unicodedata
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = "/home/user/0324oden"
OUT = os.path.join(BASE, "reel")
os.makedirs(OUT, exist_ok=True)

W, H = 1080, 1920
FPS = 30

# --- Font setup ---
FONT_PATH = "/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf"
FONT_BOLD_PATH = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"


def load_font(size, bold=False):
    path = FONT_BOLD_PATH if bold else FONT_PATH
    return ImageFont.truetype(path, size)


def fit_image(img, target_w, target_h, mode="cover"):
    """Resize and crop image to fill target dimensions."""
    iw, ih = img.size
    if mode == "cover":
        scale = max(target_w / iw, target_h / ih)
    else:
        scale = min(target_w / iw, target_h / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    img = img.resize((nw, nh), Image.LANCZOS)
    left = (nw - target_w) // 2
    top = (nh - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))


def add_gradient_bottom(img, height=500, opacity=220):
    """Add a gradient overlay at the bottom."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for y in range(img.height - height, img.height):
        alpha = int(opacity * (y - (img.height - height)) / height)
        draw.line([(0, y), (img.width, y)], fill=(0, 0, 0, alpha))
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    return Image.alpha_composite(img, overlay)


def add_gradient_top(img, height=300, opacity=180):
    """Add a gradient overlay at the top."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for y in range(height):
        alpha = int(opacity * (1 - y / height))
        draw.line([(0, y), (img.width, y)], fill=(0, 0, 0, alpha))
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    return Image.alpha_composite(img, overlay)


def draw_text_with_shadow(draw, pos, text, font, fill=(255, 255, 255), shadow_color=(0, 0, 0, 160), offset=3):
    """Draw text with a drop shadow."""
    x, y = pos
    # Shadow
    draw.text((x + offset, y + offset), text, font=font, fill=shadow_color)
    draw.text((x, y), text, font=font, fill=fill)


def draw_centered_text(draw, y, text, font, fill=(255, 255, 255), shadow=True, img_width=W):
    """Draw centered text."""
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    x = (img_width - tw) // 2
    if shadow:
        draw_text_with_shadow(draw, (x, y), text, font, fill)
    else:
        draw.text((x, y), text, font=font, fill=fill)


def draw_rounded_rect(draw, bbox, radius, fill):
    """Draw a rounded rectangle."""
    x0, y0, x1, y1 = bbox
    draw.rounded_rectangle(bbox, radius=radius, fill=fill)


def load_img(filename):
    """Load image from base directory, handling NFC/NFD unicode."""
    path = os.path.join(BASE, filename)
    if os.path.exists(path):
        return Image.open(path).convert("RGB")
    # Try NFC/NFD normalization
    for form in ("NFC", "NFD"):
        norm = unicodedata.normalize(form, filename)
        path = os.path.join(BASE, norm)
        if os.path.exists(path):
            return Image.open(path).convert("RGB")
    # Fuzzy search
    target_nfc = unicodedata.normalize("NFC", filename)
    for f in os.listdir(BASE):
        f_nfc = unicodedata.normalize("NFC", f)
        if target_nfc == f_nfc or target_nfc in f_nfc or f_nfc in target_nfc:
            return Image.open(os.path.join(BASE, f)).convert("RGB")
    raise FileNotFoundError(f"Cannot find {filename}")


# ============================================================
# SCENE 1: Hook (0-3s = frames 0-89)
# フルーツサワー3種 + テロップ「え、おでん屋でこれ出てくるん？」
# Ken Burns: slow zoom in
# ============================================================
def render_scene1(frame_num, total_frames=90):
    img = load_img("ドリンク_フルーツサワー0003.jpg")
    progress = frame_num / total_frames

    # Ken Burns: slow zoom in (1.0 -> 1.08)
    zoom = 1.0 + 0.08 * progress
    zw, zh = int(W * zoom), int(H * zoom)
    img = fit_image(img, zw, zh)
    left = (zw - W) // 2
    top = (zh - H) // 2
    img = img.crop((left, top, left + W, top + H))

    img = add_gradient_bottom(img, 600, 200)
    img = add_gradient_top(img, 250, 150)
    img = img.convert("RGB")
    draw = ImageDraw.Draw(img)

    # テロップ: fade in from frame 15
    if frame_num >= 15:
        text_alpha = min(1.0, (frame_num - 15) / 20)
        font = load_font(52, bold=True)
        text = "え、おでん屋で"
        text2 = "これ出てくるん？"

        # Background pill
        bbox1 = draw.textbbox((0, 0), text, font=font)
        bbox2 = draw.textbbox((0, 0), text2, font=font)
        tw1 = bbox1[2] - bbox1[0]
        tw2 = bbox2[2] - bbox2[0]
        max_tw = max(tw1, tw2)

        y_base = 1340
        pad = 24
        rx = (W - max_tw) // 2 - pad
        ry = y_base - pad
        rw = max_tw + pad * 2
        rh = 160 + pad * 2

        draw_rounded_rect(draw, (rx, ry, rx + rw, ry + rh), 16,
                          fill=(0, 0, 0, int(140 * text_alpha)))

        c = int(255 * text_alpha)
        draw_centered_text(draw, y_base, text, font, fill=(c, c, c), shadow=True)
        draw_centered_text(draw, y_base + 80, text2, font, fill=(c, c, c), shadow=True)

    # 上部に小さいテキスト
    if frame_num >= 5:
        small_font = load_font(42)
        draw_centered_text(draw, 70, "おでんスタンド", small_font,
                           fill=(212, 162, 78))

    return img


# ============================================================
# SCENE 2: フルーツサワー5色紹介 (3-8s = frames 90-239)
# 3カット切り替え: gp_58 -> gp_59 -> gp_60
# 各カット50フレーム、テロップでフルーツ名
# ============================================================
def render_scene2(frame_num, total_frames=150):
    cuts = ["gp_58.JPG", "gp_59.JPG", "gp_60.JPG"]
    fruits = [
        ["ライム", "マンゴー", "キウイ", "ミックスベリー", "レモン"],
        ["ライム", "マンゴー", "キウイ", "ミックスベリー", "レモン"],
        ["ライム", "マンゴー", "キウイ", "ミックスベリー", "レモン"],
    ]

    cut_idx = min(frame_num // 50, 2)
    cut_frame = frame_num % 50

    img = load_img(cuts[cut_idx])

    # Ken Burns: alternate pan direction per cut
    progress = cut_frame / 50
    zoom = 1.06
    zw, zh = int(W * zoom), int(H * zoom)
    img = fit_image(img, zw, zh)

    # Pan direction
    max_offset = zw - W
    if cut_idx % 2 == 0:
        left = int(max_offset * progress)
    else:
        left = int(max_offset * (1 - progress))
    top = (zh - H) // 2
    img = img.crop((left, top, left + W, top + H))

    img = add_gradient_bottom(img, 500, 210)
    img = img.convert("RGB")
    draw = ImageDraw.Draw(img)

    # Scene title
    title_font = load_font(32)
    draw_centered_text(draw, 1440, "- フルーツサワー -", title_font,
                       fill=(255, 255, 255))

    return img


# ============================================================
# SCENE 3: 乾杯 (8-11s = frames 240-329)
# 乾杯カット + 「推しはどれ？」
# ============================================================
def render_scene3(frame_num, total_frames=90):
    img = load_img("ドリンク_フルーツサワー0008.jpg")
    progress = frame_num / total_frames

    # Slow zoom out (1.1 -> 1.0)
    zoom = 1.1 - 0.1 * progress
    zw, zh = int(W * zoom), int(H * zoom)
    img = fit_image(img, zw, zh)
    left = (zw - W) // 2
    top = (zh - H) // 2
    img = img.crop((left, top, left + W, top + H))

    img = add_gradient_bottom(img, 500, 200)
    img = add_gradient_top(img, 200, 120)
    img = img.convert("RGB")
    draw = ImageDraw.Draw(img)

    # 乾杯テロップ
    if frame_num >= 10:
        font = load_font(56, bold=True)
        alpha = min(1.0, (frame_num - 10) / 20)
        c = int(255 * alpha)
        draw_centered_text(draw, 1380, "かんぱ〜い！", font, fill=(c, c, c))

    # 「推しはどれ？」
    if frame_num >= 40:
        font2 = load_font(42, bold=True)
        alpha2 = min(1.0, (frame_num - 40) / 20)
        c2 = int(255 * alpha2)
        g = int(212 * alpha2)
        b = int(78 * alpha2)

        # Background pill
        text = "あなたの推しはどれ？"
        bbox = draw.textbbox((0, 0), text, font=font2)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        px, py = (W - tw) // 2, 1500
        pad = 16
        draw_rounded_rect(draw, (px - pad, py - pad, px + tw + pad, py + th + pad * 2),
                          12, fill=(0, 0, 0, int(150 * alpha2)))
        draw.text((px, py), text, font=font2, fill=(c2, g, b))

    return img


# ============================================================
# SCENE 4: 日本酒 (11-19s = frames 330-569)
# 日本酒ボトル + 酒器 + 冷蔵ケース
# 3カット: sake_0002 -> sake_0005 -> gp_43 (各80フレーム=2.67秒)
# ============================================================
def render_scene4(frame_num, total_frames=240):
    CUT_LEN = 80  # 各カット80フレーム (2.67秒)
    cuts = [
        "ドリンク_日本酒_0002.jpg",   # 0-79
        "ドリンク_日本酒_0005.jpg",   # 80-159
        "gp_43.JPG",                   # 160-239
    ]
    labels = [
        "",
        "",
        "常時 8種以上ご用意",
    ]

    cut_idx = min(frame_num // CUT_LEN, 2)
    cut_frame = frame_num % CUT_LEN

    img = load_img(cuts[cut_idx])
    progress = cut_frame / CUT_LEN

    # Ken Burns - ゆっくりズーム
    zoom = 1.04 + 0.04 * progress
    zw, zh = int(W * zoom), int(H * zoom)
    img = fit_image(img, zw, zh)

    # Slow pan
    max_pan_x = zw - W
    max_pan_y = zh - H
    if cut_idx == 0:
        left = int(max_pan_x * progress * 0.3)
        top = int(max_pan_y * 0.3)
    elif cut_idx == 1:
        left = int(max_pan_x * (1 - progress) * 0.3)
        top = int(max_pan_y * 0.4)
    else:
        left = int(max_pan_x * progress * 0.5)
        top = int(max_pan_y * 0.3)

    left = max(0, min(left, zw - W))
    top = max(0, min(top, zh - H))
    img = img.crop((left, top, left + W, top + H))

    img = add_gradient_bottom(img, 550, 220)
    img = add_gradient_top(img, 250, 160)
    img = img.convert("RGB")
    draw = ImageDraw.Draw(img)

    # Scene transition text - ゆっくりフェードイン→長めに表示→フェードアウト
    if frame_num < 55:
        if frame_num < 20:
            alpha = min(1.0, frame_num / 20)
        elif frame_num < 40:
            alpha = 1.0
        else:
            alpha = max(0, 1.0 - (frame_num - 40) / 15)
        font = load_font(44, bold=True)
        c = int(255 * alpha)
        draw_centered_text(draw, H // 2 - 40, "実は、日本酒も", font, fill=(c, c, c))
        draw_centered_text(draw, H // 2 + 30, "揃ってます。", font, fill=(c, c, c))

    # Label for current cut - ゆっくりフェードイン（30フレーム後に表示開始）
    if cut_frame >= 20:
        alpha = min(1.0, (cut_frame - 20) / 25)
        font = load_font(38, bold=True)
        c = int(255 * alpha)
        g = int(220 * alpha)
        b = int(180 * alpha)
        draw_centered_text(draw, 1480, labels[cut_idx], font, fill=(c, g, b))

    # Top badge: 日本酒
    badge_font = load_font(26)
    draw_rounded_rect(draw, (40, 80, 200, 120), 20, fill=(212, 162, 78, 200))
    draw.text((60, 85), "日本酒", font=badge_font, fill=(20, 10, 0))

    return img


# ============================================================
# SCENE 5: 全種集合 + CTA (19-24s = frames 570-719)
# ドリンク全種 + 店舗情報 + CTA
# ============================================================
def render_scene5(frame_num, total_frames=150):
    img = load_img("gp_57.JPG")
    progress = frame_num / total_frames

    # Slow zoom out
    zoom = 1.12 - 0.08 * progress
    zw, zh = int(W * zoom), int(H * zoom)
    img = fit_image(img, zw, zh)
    left = (zw - W) // 2
    top = (zh - H) // 2
    img = img.crop((left, top, left + W, top + H))

    img = add_gradient_bottom(img, 700, 230)
    img = add_gradient_top(img, 300, 180)
    img = img.convert("RGB")
    draw = ImageDraw.Draw(img)

    # CTA text
    if frame_num >= 15:
        alpha = min(1.0, (frame_num - 15) / 25)
        font = load_font(48, bold=True)
        c = int(255 * alpha)
        draw_centered_text(draw, 1280, "おでんに合う一杯、", font, fill=(c, c, c))
        draw_centered_text(draw, 1350, "見つけにおいで。", font, fill=(c, c, c))

    # Store info - fade in later
    if frame_num >= 60:
        alpha = min(1.0, (frame_num - 60) / 25)
        info_font = load_font(28)
        small_font = load_font(24)
        c = int(200 * alpha)
        g = int(170 * alpha)

        y = 1500
        draw_centered_text(draw, y, "おでんスタンド", load_font(51, bold=True),
                           fill=(int(212 * alpha), int(162 * alpha), int(78 * alpha)))
        draw_centered_text(draw, y + 50, "梅田 EST FOODHALL", info_font,
                           fill=(c, c, c))
        draw_centered_text(draw, y + 90, "11:00〜23:00（L.O. 22:30）", small_font,
                           fill=(g, g, g))

    # Top: おでんスタンド logo text
    top_font = load_font(45)
    draw_centered_text(draw, 70, "おでんスタンド", top_font,
                       fill=(212, 162, 78))

    return img


# ============================================================
# RENDER ALL FRAMES
# ============================================================
def render_frame(global_frame):
    """Route to the correct scene renderer."""
    # Scene1: 0-89 (3s)  フック
    # Scene2: 90-239 (5s) フルーツサワー
    # Scene3: 240-329 (3s) 乾杯
    # Scene4: 330-569 (8s) 日本酒 ← 拡大: 各カット80f x 3 = 240f
    # Scene5: 570-719 (5s) CTA + 店舗情報
    if global_frame < 90:
        return render_scene1(global_frame, 90)
    elif global_frame < 240:
        return render_scene2(global_frame - 90, 150)
    elif global_frame < 330:
        return render_scene3(global_frame - 240, 90)
    elif global_frame < 570:
        return render_scene4(global_frame - 330, 240)
    elif global_frame < 720:
        return render_scene5(global_frame - 570, 150)
    else:
        return render_scene5(149, 150)


TOTAL_FRAMES = 720  # 24 seconds at 30fps

print(f"Rendering {TOTAL_FRAMES} frames ({TOTAL_FRAMES/FPS:.1f}s) at {W}x{H}...")

frame_dir = os.path.join(OUT, "frames")
os.makedirs(frame_dir, exist_ok=True)

for i in range(TOTAL_FRAMES):
    frame = render_frame(i)
    if frame.mode != "RGB":
        frame = frame.convert("RGB")
    frame.save(os.path.join(frame_dir, f"frame_{i:05d}.jpg"), quality=95)
    if i % 30 == 0:
        print(f"  Frame {i}/{TOTAL_FRAMES} ({i/FPS:.1f}s)")

print("Frames done. Encoding video with ffmpeg...")

# Encode with ffmpeg
output_path = os.path.join(BASE, "reel_drink_push.mp4")
bgm_path = os.path.join(BASE, "Neon_City_Serenade.mp3")
has_bgm = os.path.exists(bgm_path)

if has_bgm:
    # Video + BGM: fade in 1s, fade out 2s, trim to video length
    duration = TOTAL_FRAMES / FPS
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", os.path.join(frame_dir, "frame_%05d.jpg"),
        "-i", bgm_path,
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-vf", "scale=1080:1920",
        "-af", f"afade=t=in:st=0:d=1,afade=t=out:st={duration - 2}:d=2",
        "-shortest",
        "-movflags", "+faststart",
        output_path
    ]
    print(f"Adding BGM: {bgm_path} (fade in 1s, fade out 2s)")
else:
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", os.path.join(frame_dir, "frame_%05d.jpg"),
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-vf", "scale=1080:1920",
        "-movflags", "+faststart",
        output_path
    ]
    print("Warning: BGM file not found, encoding video without audio.")

result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode == 0:
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"\nDone! Video saved to: {output_path}")
    print(f"Size: {size_mb:.1f} MB")
    print(f"Duration: {TOTAL_FRAMES/FPS:.1f}s | Resolution: {W}x{H} | FPS: {FPS}")
    if has_bgm:
        print("BGM: Neon_City_Serenade.mp3 ✓")
else:
    print("ffmpeg error:", result.stderr[-500:])
