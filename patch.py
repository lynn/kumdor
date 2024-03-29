import struct
import json
import os.path
import textwrap
import sys

with open("The Sword of Kumdor.hdm", "rb") as f:
    rom = f.read()

rom = memoryview(rom)

# For text insertion, work off the tutorial.py output:
saved = os.path.exists("saved.hdm") and not "--release" in sys.argv
source = "saved.hdm" if saved else "tutorial/output.hdm"

with open(source, "rb") as f:
    patched = bytearray(f.read())


def check(start: int, bs: bytes | str):
    if isinstance(bs, str):
        bs = bs.encode("shift-jis")
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
write(0x10, b"the SWORD OF KUMDOR (english v1)")

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

if saved:
    # Give myself a bunch of money and items when testing.
    write(0xC020, struct.pack("<L", 100000))
    write(0xC028, struct.pack("<L", 9999))
    write(0xC02C, struct.pack("<L", 9999))
    soba = "\x06\x00"
    mati = "\x14\x00"
    akari = "\x18\x00"
    smokemoss = "\x21\x00"
    crystal = "\x31\x00"
    tamaorin = "\x33\x00"
    write(0xC100, b"\xff" * 64)
    write(0xC080, smokemoss * 6 + soba * 6 + mati * 4 + akari * 6 + crystal * 8)

    # Add a shortcut in the last dungeon.
    write(0x69A1A, b" " * 128)


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
strings("comm", 0x4D000, 0x4DFF0 + 256)
# padding(0x4E000, 0x50000, b"\xe5")

check(0x50000, b"MAP TOWN01/02")
map_town12 = rom[0x50000:0x54000]

strings("twn1", 0x54000, 0x555F0 + 256)
strings("twn2", 0x56000, 0x574F0)

check(0x58000, b"TWN03 MAP")
map_town3 = rom[0x58000:0x5C000]
strings("twn3", 0x5C000, 0x5D6F0)
strings("twn4", 0x5E000, 0x5FAF0 + 256)

check(0x60000, b"MAP:TWN04/06")
strings("twn5", 0x64000, 0x656F0)
strings("twn6", 0x66000, 0x66AF0)
check(0x68000, b"MAP TOWN 07")


# 0xc0000:0xcd800 = monster data
ptr = 0xC0000

monsters = [
    "Slime",
    "Ay",
    "Dee",
    "Eff",
    "Jay",
    "Kay",
    "Ell",
    "Semicolon",
    "Plus",
    "Arr",
    "Wye",
    "Yew",
    "Zee",
    "Queue",
    "Iye",
    "Atsine",
    "Ex",
    "Cee",
    "Slash",
    "Vee",
    "Emm",
    "7even",
    "1ne",
    "Zer0",
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
bosses = "Firesoul Stix Thoushand Mist Spiralure Mimicky Heatwave Eyeron Qilin".split()
assert len(bosses) == 9
for i, name in enumerate(bosses):
    write(ptr + 0x70, name + "\0")
    ptr += 0x1000

assert ptr == 0xD9000
padding(0xD8F80, 0x134000, b"\xe5")
assert len(rom) == 0x134000

write(0x13270, b"Talk/Look\rInventory\rSpell\rKeyboard\rScore\rSystem\0")


def exact(addr: int, source: str, target: str):
    source = source.encode("shift-jis")
    target = target.encode("shift-jis")
    assert len(source) == len(target)
    check(addr, source)
    write(addr, target)


exact(0x13353, "(F=方向変更)", " (F=rotate)\0")
exact(0x13364, "終了", "exit")
exact(0x1338E, "終了", "exit")
exact(0x133C0, "所持品使用(F:\x1e)", "Use item  (F:\x1e)")
exact(0x133D5, "終了", "exit")
exact(0x13430, "呪文を唱える(f=中止)", "Cast a spell(f=quit)")
exact(0x134E0, "町へ(f=中止)", "Warp(f=stay)")

with open(f"text/item.py") as f:
    item_names = eval(f.read())
    spells = "".join(x.strip("\x1a\x1b") + "\0" for x in item_names[0x11:0x1A])
    write(0x13520, spells)


class Patch:
    def __init__(self, addr):
        self.label = self.addr = addr

    def raw(self, bs: bytes):
        patched[self.addr : self.addr + len(bs)] = bs
        self.addr += len(bs)

    def call(self, target):
        rel = (target - (self.addr + 3)) & 0xFFFF
        self.raw(bytes([0xE8, rel & 0xFF, rel >> 8]))

    mov_cl = lambda self, imm: self.raw(bytes([0xB1, imm]))
    mov_di = lambda self, imm: self.raw(bytes([0xBF, imm & 0xFF, imm >> 8]))
    mov_dl_cl = lambda self: self.raw(b"\x88\xca")
    mov_cl_dl = lambda self: self.raw(b"\x88\xd1")
    push_ax = lambda self: self.raw(b"\x50")
    pop_ax = lambda self: self.raw(b"\x58")
    ret = lambda self: self.raw(b"\xc3")


gettext_glob = 0x733C
gettext_comm = 0x7341
blank = 0xABFA

# Function that prints "There is a ", then glob[CL]:
there_is_a = Patch(blank)
there_is_a.mov_dl_cl()  # Store key name
there_is_a.mov_cl(0x70)  # "There is a "
there_is_a.call(gettext_glob)
there_is_a.mov_cl_dl()  # Retrieve key name
there_is_a.call(gettext_glob)
there_is_a.ret()
blank = there_is_a.addr

# Call the there_is_a patch when examining a key on the ground.
check(0xA8C9, b"\xe8\x70\xca")
Patch(0xA8C9).call(there_is_a.label)


def di_patch(addr: int, cl: int) -> None:
    """
    Patch a `mov di,0xc000` instruction with a call to `p() { di=0xc000; gettext_comm(cl) }`.

    (`di` is used as a pointer for message-writing and `0xc000` is the start of a global message buffer.)

    This is to insert text like "You got a " in front of messages that ordinarily start with variables.

    Parameters:
    * `addr` - the address of the instruction to patch.
    * `cl` - the index of the comm.py string to print.
    """
    global blank
    p = Patch(blank)
    p.mov_di(0xC000)
    p.push_ax()
    p.mov_cl(cl)
    p.call(gettext_comm)
    p.pop_ax()
    p.ret()
    blank = p.addr
    check(addr, b"\xbf\x00\xc0")
    Patch(addr).call(p.label)


# "You got a " when picking up an item:
di_patch(0x6A44, 0x60)

# "You deal " n pt. of damage:
di_patch(0x86AE + 0x800, 0x20)

# "Got " n spice at the end of a battle:
di_patch(0x89EC + 0x800, 0x10)

# Patch out the copy protection check in the final dungeon.
check(0xB85AE, b"\x75\x03")  # jnz $+5
write(0xB85AE, b"\x90\x90")  # nop / nop

# Write a ROM with inserted text:
out_path = "patched.hdm"
with open(out_path, "wb") as f:
    f.write(patched)
    print(f"Wrote {out_path}.")
