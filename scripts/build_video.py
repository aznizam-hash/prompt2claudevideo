"""Bina video 30 saat: slaid teks + audio dari fail WAV yang diupload."""
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output"
FRAMES = OUT / "frames"
AUDIO_SRC = Path("/root/.claude/uploads/bf0056e1-3299-5d0a-82bc-786ee8cd1f79/7fcdb6fc-Generated_Audio_October_27_2026_-_6_36PM.wav")
W, H = 1920, 1080
BG = (16, 42, 67)
FG = (245, 245, 245)
HL = (255, 196, 61)
MUTED = (160, 190, 215)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# (durasi saat, tajuk kecil, baris [(teks, highlight?)])
SCENES = [
    (5.4, "30 SAAT", [("30 Cara Memuliakan Al-Quran", True)]),
    (5.4, "PEMBUKAAN", [("Bagaimana kita memuliakan Al-Quran?", False)]),
    (5.4, "LANGKAH 1", [
        ("Membaca, memahami dan", False),
        ("menghayati maknanya", True),
    ]),
    (5.4, "ADAB", [
        ("Berwuduk sebelum sentuh", False),
        ("mushaf, baca dengan", False),
        ("tartil", True),
    ]),
    (5.4, "AMALAN", [
        ("Hormati mushaf, ajar anak-anak,", False),
        ("kongsi ilmu, jadikan", False),
        ("Al-Quran panduan hidup", True),
    ]),
    (5.5, "KESIMPULAN", [
        ("Al-Quran dibaca, difahami,", False),
        ("diamalkan dan", False),
        ("dicintai", True),
    ]),
]
FADE = 0.5


def draw_scene(idx, tag, lines):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    f_tag = ImageFont.truetype(FONT, 46)
    f_line = ImageFont.truetype(FONT_REG, 92)
    f_hl = ImageFont.truetype(FONT, 104)
    d.rounded_rectangle((W // 2 - 220, 230, W // 2 + 220, 300), radius=35, fill=HL)
    d.text((W // 2, 265), tag, font=f_tag, fill=BG, anchor="mm")
    gap = 150
    y0 = H // 2 - (len(lines) - 1) * gap // 2 + 60
    for i, (text, hl) in enumerate(lines):
        font = f_hl if hl else f_line
        d.text((W // 2, y0 + i * gap), text, font=font,
               fill=HL if hl else FG, anchor="mm")
    d.text((W - 80, H - 80), f"{idx + 1}/{len(SCENES)}", font=f_tag, fill=MUTED, anchor="rb")
    path = FRAMES / f"scene_{idx}.png"
    img.save(path)
    return path


def run(cmd):
    subprocess.run(cmd, check=True, capture_output=True)


def main():
    FRAMES.mkdir(parents=True, exist_ok=True)
    clips = []
    for i, (dur, tag, lines) in enumerate(SCENES):
        png = draw_scene(i, tag, lines)
        clip = FRAMES / f"clip_{i}.mp4"
        run(["ffmpeg", "-y", "-loop", "1", "-i", str(png), "-t", str(dur),
             "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-preset", "veryfast",
             "-crf", "20", str(clip)])
        clips.append((clip, dur))

    # Gabung klip dengan crossfade (xfade)
    inputs, filt, prev, t = [], [], "[0:v]", 0.0
    for clip, _ in clips:
        inputs += ["-i", str(clip)]
    for i in range(1, len(clips)):
        t += clips[i - 1][1] - FADE
        label = f"[v{i}]" if i < len(clips) - 1 else "[vout]"
        src = f"[{i}:v]"
        filt.append(f"{prev}{src}xfade=transition=fade:duration={FADE}:offset={t:.2f}{label}")
        prev = label
    run(["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(filt),
         "-map", "[vout]", "-t", "30", "-c:v", "libx264", "-pix_fmt", "yuv420p",
         str(FRAMES / "visual.mp4")])

    # Audio: potong 30 saat + fade out 1.5 saat
    run(["ffmpeg", "-y", "-i", str(AUDIO_SRC), "-t", "30",
         "-af", "afade=t=out:st=28.5:d=1.5", "-c:a", "aac", "-b:a", "192k",
         str(FRAMES / "audio.m4a")])

    run(["ffmpeg", "-y", "-i", str(FRAMES / "visual.mp4"), "-i", str(FRAMES / "audio.m4a"),
         "-map", "0:v", "-map", "1:a", "-t", "30", "-c:v", "copy", "-c:a", "copy",
         "-movflags", "+faststart", str(OUT / "video_30s.mp4")])
    print("OK", OUT / "video_30s.mp4")


if __name__ == "__main__":
    main()
