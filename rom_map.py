import struct

with open("The Sword of Kumdor.hdm", "rb") as f:
    rom = f.read()

rom = memoryview(rom)

def at(start, bs):
    assert rom[start:start+len(bs)] == bs

def padding(start, stop, byte):
    assert rom[start:stop] == byte * (stop-start)

def strings(name, start, stop):
    ss = bytes(rom[start:stop]).rstrip(b" U\xe5\0").split(b"\0")
    for i, s in enumerate(ss):
        print(f"{name}_{i:02x}:", repr(s.decode("shift-jis")))

def u32(i):
    return struct.unpack("<L", rom[i:i+4])[0]


# There's a 512b custom boot sector that starts with a JMP instruction:
boot_sector = rom[0x00000:0x00200]
at(0x0, b"\xeb\x7e")
at(0x10, b"the SWORD OF KUMDOR")

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

print("Save 1 spice:", u32(0xC000 + 0x20))

padding(0x0E000, 0x10000, b"\xe5")

title_data = rom[0x10000:0x13000]
gfx_maybe = rom[0x14000:0x35000]
# protagonist at 0x28000
# title screen data (format???) at 0x2c000

padding(0x35000, 0x40000, b"\xe5")

at(0x40000, b"MAP SOLFACE")
map_solface = rom[0x40000:0x44000]

at(0x44000, b"OUT MAP")
map_out = rom[0x44000:0x48000]

# Story text
at(0x48000, "A.P.(ポーラ暦)405年".encode("shift-jis"))

padding(0x491F0, 0x49800, b"U")

# Typing data
at(0x49800, b"00\0add\0af\0as")

padding(0x49be8, 0x49cf0, b"\0")
padding(0x49cf0, 0x4a000, b"U")
unknown_data = rom[0x4a000:0x4a594]
padding(0x4a594, 0x4b780, b"\xe5")
padding(0x4a594, 0x4b780, b"\xe5")
unknown_data2 = rom[0x4b780:0x4bc00]
strings("item", 0x4bc00, 0x4bff0)
strings("glob", 0x4c000, 0x4cbf0)
padding(0x4cbf0, 0x4d000, b"U")
strings("comm", 0x4d000, 0x4dff0)
padding(0x4e000, 0x50000, b"\xe5")

at(0x50000, b"MAP TOWN01/02")
map_town12 = rom[0x50000:0x54000]

strings("twn1", 0x54000, 0x555f0)
strings("twn2", 0x56000, 0x574f0)

at(0x58000, b"TWN03 MAP")
map_town3 = rom[0x58000:0x5c000]


def onebpp(bs, width=64, height=64):
    rows = []
    for y in range(height):
        row = []
        for x in range(width // 8):
            for b in range(8):
                bit = bs[width//8*y+x] >> (7-b) & 1
                row.append(bit)
        rows.append(row)

    return rows


def twobpp(bs, width=64, height=64):
    l1 = onebpp(bs, width, height)
    l2 = onebpp(bs[width//8 * height:], width, height)
    return [[r+2*g for r,g in zip(rr,gg)] for rr,gg in zip(l1,l2)]

def threebpp(bs, width=64, height=64):
    l1 = onebpp(bs, width, height)
    l2 = onebpp(bs[width//8 * height:], width, height)
    l3 = onebpp(bs[width//8 * height * 2:], width, height)
    return [[r+2*g+4*b for r,g,b in zip(rr,gg,bb)] for rr,gg,bb in zip(l1,l2,l3)]

def show(matrix):
    for row in matrix:
        print("".join("\x1b[%dm%s\x1b[0m" % ([40, 102,107,103,101,106,105,104][x],"  ") for x in row))

start = 0x10000
w = 64
h = 64
for i in range(2000):
    addr = start + i * w*h//8
    print(f"0x{addr:05x}")
    show(onebpp(rom[addr:], w, h))
    input()
exit()
# 0xc0000:0xcd800 = monster data
ptr = 0xc0000
for i in range(27):
    print(i, bytes(rom[ptr+2:ptr+16]).rstrip(b"\0").decode("ascii"), bytes(rom[ptr+0x70:ptr+0x7e]).rstrip(b"\0").decode("shift-jis"))
    red   = onebpp(bytes(rom[ptr+0x200:ptr+0x400]))
    green = onebpp(bytes(rom[ptr+0x400:ptr+0x600]))
    blue  = onebpp(bytes(rom[ptr+0x600:ptr+0x800]))
    if False:
        total = [[1*r+2*g+4*b for r,g,b in zip(rr,gg,bb)] for rr,gg,bb in zip(red,green,blue)]
        for row in total: print("".join("\x1b[%dm%s\x1b[0m" % ([40, 102,107,103,101,106,105,104][x],"  ") for x in row))


    ptr += 0x800

assert ptr == 0xcd800
padding(0xcd800, 0xd0000, b"\xe5")

# bosses???
ptr = 0xd0000
for i in range(9):
    print(i, bytes(rom[ptr+2:ptr+14]).rstrip(b"\0").decode("ascii"), bytes(rom[ptr+0x70:ptr+0x7e]).rstrip(b"\0").decode("shift-jis"))
    ptr += 0x1000

assert ptr == 0xd9000
padding(0xd8f80, 0x134000, b"\xe5")
assert len(rom) == 0x134000
