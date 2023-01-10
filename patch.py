import struct
import json
import os.path
import textwrap

with open("The Sword of Kumdor.hdm", "rb") as f:
    rom = f.read()

rom = memoryview(rom)

# For text insertion, work off the tutorial.py output:
saved = os.path.exists("saved.hdm")
source = "saved.hdm" if saved else "tutorial/output.hdm"

with open(source, "rb") as f:
    patched = bytearray(f.read())


def check(start: int, bs: bytes):
    assert rom[start : start + len(bs)] == bs


def write(start: int, text: bytes | str):
    if isinstance(text, str):
        text = text.encode("shift-jis")
    patched[start : start + len(text)] = text


def padding(start: int, stop: int, byte):
    assert rom[start:stop] == byte * (stop - start)


def wrap(text: str):
    if text.startswith("~"):
        text = text[1:].replace("\x15", "\n")
        text = textwrap.fill(text, width=40)
        return text.replace("\n", "\x15")
    else:
        return text


def strings(name: str, start: int, stop: int):
    ss = bytes(rom[start:stop]).rstrip(b" U\xe5\0").split(b"\0")
    if not os.path.exists(f"text/{name}.py"):
        lines = ["["]
        for i, s in enumerate(ss):
            text = s.decode("shift-jis")
            text_r = json.dumps(text, ensure_ascii=False)
            if i > 0:
                lines.append("")
            lines.append(f"    # {i:02x} = {text_r}")
            lines.append(f"    {text_r},")
        lines.append("]")
        with open(f"text/{name}.py", "w") as f:
            f.write("\n".join(lines) + "\n")
    else:
        code = open(f"text/{name}.py").read()
        translation = [wrap(s) for s in eval(code)]
        enc = ("\0".join(translation) + "\0").encode("shift-jis")
        if len(enc) > stop - start:
            raise ValueError(
                f"translations too long! {name}: {len(enc)} > {stop - start}"
            )
        else:
            print(f"ok: {name}: {len(enc)} <= {stop - start}")
        patched[start : start + len(enc)] = enc


def u32(addr: int):
    return struct.unpack("<L", rom[addr : addr + 4])[0]


# There's a 512b custom boot sector that starts with a JMP instruction:
boot_sector = rom[0x00000:0x00200]
check(0x0, b"\xeb\x7e")
check(0x10, b"the SWORD OF KUMDOR")

padding(0x0300, 0x0400, b"U")
padding(0x0400, 0x1400, b"\xff")
padding(0x1400, 0x1800, b"\x00")
# I think rom[0x1800:0xABFA] is all code.
padding(0xABFA, 0xC000, b"U")

# Save data structs:
save1 = rom[0xC000:0xC800]
save2 = rom[0xC800:0xD000]
save3 = rom[0xD000:0xD800]
save4 = rom[0xD800:0xE000]

# print("Save 1 spice:", u32(0xC000 + 0x20))

# Give myself a bunch of money when testing.
if saved:
    write(0xC020, struct.pack("<L", 100000))
    soba = "\x06\x00"
    mati = "\x14\x00"
    smokemoss = "\x21\x00"
    crystal = "\x31\x00"
    tamaorin = "\x33\x00"
    write(0xC080, smokemoss*8 + soba*6 + mati*6)

padding(0x0E000, 0x10000, b"\xe5")

title_data = rom[0x10000:0x13000]
gfx_maybe = rom[0x14000:0x35000]
# protagonist at 0x28000

# Use a nicer apostrophe glyph:
font_data = rom[0x12000:0x12800]
apostrophe = rom[0x12270:0x12280]
write(0x12270, b"\0\0\0\x18\x18\x08\x10\0\0\0\0\0\0\0\0\0")

title_bmp = rom[0x2B000:0x2BB94]

# from PIL import Image
# from sprite_view import onebpp
# data = b"".join(bytes([r * 255 for r in row]) for row in onebpp(title_bmp, 312, 76))
# im = Image.frombytes("L", (312, 76), data)
# im.show()

try:
    from PIL import Image, ImageFont, ImageDraw

    img = Image.new("1", (312, 76), 1)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("C:\\Windows\\Fonts\\lucon.ttf", 15)
    draw.text((312 // 2, 20), "~ Master the Blind Touch ~", 0, font=font, anchor="ms")
    big = ImageFont.truetype("C:\\Windows\\Fonts\\timesbi.ttf", 40)
    draw.text((312 // 2, 45), "Sword of Kumdor", 0, font=big, anchor="mm")
    patched[0x2B000:0x2BB94] = img.tobytes()
except OSError as e:
    print(f"Skipping title screen patch ({e!r}).")

padding(0x35000, 0x40000, b"\xe5")

check(0x40000, b"MAP SOLFACE")
map_solface = rom[0x40000:0x44000]

check(0x44000, b"OUT MAP")
map_out = rom[0x44000:0x48000]

# Story text
check(0x48000, "A.P.(ポーラ暦)405年".encode("shift-jis"))
strings("intr", 0x48000, 0x491F0)
padding(0x491F0, 0x49800, b"U")

# Typing data
check(0x49800, b"00\0add\0af\0as")

padding(0x49BE8, 0x49CF0, b"\0")
padding(0x49CF0, 0x4A000, b"U")
unknown_data = rom[0x4A000:0x4A594]
padding(0x4A594, 0x4B780, b"\xe5")
padding(0x4A594, 0x4B780, b"\xe5")
unknown_data2 = rom[0x4B780:0x4BC00]
strings("item", 0x4BC00, 0x4BFF0)
strings("glob", 0x4C000, 0x4CBF0)
padding(0x4CBF0, 0x4D000, b"U")
strings("comm", 0x4D000, 0x4DFF0)
padding(0x4E000, 0x50000, b"\xe5")

check(0x50000, b"MAP TOWN01/02")
map_town12 = rom[0x50000:0x54000]

strings("twn1", 0x54000, 0x555F0)
strings("twn2", 0x56000, 0x574F0)

check(0x58000, b"TWN03 MAP")
map_town3 = rom[0x58000:0x5C000]
strings("twn3", 0x5C000, 0x5D6F0)
strings("twn4", 0x5E000, 0x5FAF0)

check(0x60000, b"MAP:TWN04/06")
strings("twn5", 0x64000, 0x656F0)
strings("twn6", 0x66000, 0x66AF0)
check(0x68000, b"MAP TOWN 07")


# 0xc0000:0xcd800 = monster data
ptr = 0xC0000

monsters = [
    "Regular Slime",
    "Ay",
    "Dee",
    "Eff",
    "Jay",
    "Kay",
    "Ell",
    "Semicolo",
    "Plus",
    "Arr",
    "Wye",
    "Yew",
    "Zee",
    "Queueue",
    "Iye",
    "Atsine",
    "Eckxs",
    "Cee",
    "Slash",
    "Vee",
    "Emm",
    "7even",
    "1ne",
    "Zero",
    "Hyphen",
    "Bracket",
    "Asterisk",
]
assert len(monsters) == 27

for i, name in enumerate(monsters):
    write(ptr + 0x70, name + "\0")
    ptr += 0x800

assert ptr == 0xCD800
padding(0xCD800, 0xD0000, b"\xe5")

ptr = 0xD0000
bosses = "Hidama Bou Senju Kasumi Uzumaneki Modoki Oonetsu Ishime Ryuu".split()
assert len(bosses) == 9
for i, name in enumerate(bosses):
    write(ptr + 0x70, name + "\0")
    ptr += 0x1000

assert ptr == 0xD9000
padding(0xD8F80, 0x134000, b"\xe5")
assert len(rom) == 0x134000

write(0x13270, "Talk/Look\rInventory\rSpell\rKeyboard\rScore\rSystem\0")

# Patch out the copy protection check in the final dungeon.
check(0xB85AE, b"\x75\x03")  # jnz $+5
write(0xB85AE, b"\x90\x90")  # nop / nop

# Write a ROM with inserted text:
out_path = "patched.hdm"
with open(out_path, "wb") as f:
    f.write(patched)
    print(f"Wrote {out_path}.")
