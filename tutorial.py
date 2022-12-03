import json
import os.path
import struct
import tkinter
from dataclasses import dataclass
from typing import Any, List

with open("The Sword of Kumdor.hdm", "rb") as f:
    rom = f.read()


class Cursor(bytearray):
    ptr: int

    def __init__(self, buf):
        super().__init__(buf)
        self.ptr = 0

    def seek(self, i):
        self.ptr = i

    def skip(self, i):
        self.ptr += i

    def read(self, width, format):
        (val,) = struct.unpack(format, rom[self.ptr : self.ptr + width])
        self.ptr += width
        return val

    i8 = lambda self: self.read(1, "<b")
    u8 = lambda self: self.read(1, "<B")
    i16 = lambda self: self.read(2, "<h")
    u16 = lambda self: self.read(2, "<H")


root = tkinter.Tk()

scale = 2
canvas = tkinter.Canvas(root, bg="black", height=400 * scale, width=640 * scale)

rom = Cursor(rom)
rom.seek(0x2C000)


def draw_group():
    ptr_group = rom.ptr
    i = -1
    lines = []
    pen = "#004040"

    while True:
        i += 1
        ptr0 = rom.ptr
        x0 = x = rom.u16()
        y0 = y = rom.u16()

        if x == 0x5555:
            # End
            rom.skip(-4)
            return None

        if x // 256 == 0x96:
            op = rom.u8()  # IDK what this byte is
            if y == 0x5B30:
                pen = "#00a000"
            elif op == 1:
                pen = "#800000"
            else:
                pen = "#004080"

            print(f"{i:4} {ptr0:5x} {x0:4x} {y0:4x} {op:02x} @@@@@@@")
            lines.append(MagicLine(bytes(rom[rom.ptr - 5 : rom.ptr])))
            continue
        if x == 0xC000:
            rom.skip(-2)
            group_rom = rom[ptr_group : rom.ptr]
            while rom[rom.ptr] == 0:
                rom.skip(1)
            # print(f"{i:4} {ptr0:5x} {x0:4x} {y0:4x} ----------")
            return (ptr_group, group_rom, lines)
        segments = []
        x0, y0 = x, y
        while True:
            dx = rom.i8()
            dy = rom.i8()
            if dx == dy == 0:
                break
            obj = canvas.create_line(
                x * scale,
                y * scale,
                (x + dx) * scale,
                (y + dy) * scale,
                fill=pen,
                width=1 * scale,
            )
            segment = Segment(dx, dy, obj)
            segments.append(segment)
            x += dx
            y += dy
        # print(f"{i:4} {ptr0:5x} {x0:4x} {y0:4x} {len(segments):4}")
        lines.append(Line(x0, y0, segments))


@dataclass
class Segment:
    dx: int
    dy: int
    obj: Any

    def encode(self) -> bytes:
        return struct.pack("bb", self.dx, self.dy)


def sgn(x):
    return (x > 0) - (x < 0)


@dataclass
class Line:
    x0: int
    y0: int
    segments: List[Segment]

    def encode(self) -> bytes:
        bs = bytearray(struct.pack("HH", self.x0, self.y0))
        last = None
        for s in self.segments:
            if (
                last
                and s.dx * last.dy == last.dx * s.dy
                and sgn(s.dx) == sgn(last.dx)
                and sgn(s.dy) == sgn(last.dy)
            ):
                # merge 'em
                tx = last.dx + s.dx
                ty = last.dy + s.dy
                bs[-2:] = struct.pack("bb", tx, ty)
                last = Segment(tx, ty, None)
            else:
                bs += struct.pack("bb", s.dx, s.dy)
                last = s
        return bs + b"\0\0"

    def to_json(self):
        return {
            "x0": self.x0,
            "y0": self.y0,
            "segments": [[s.dx, s.dy] for s in self.segments],
        }


@dataclass
class MagicLine:
    magic: bytes

    def encode(self) -> bytes:
        return self.magic

    def to_json(self):
        return {"magic": list(self.magic)}


@dataclass
class Group:
    ptr: int
    magic: bytes
    lines: List[Line]

    def encode(self) -> bytes:
        return self.magic + b"".join(l.encode() for l in self.lines) + b"\x00\xc0"


CYAN = "#00c0ff"
GREEN = "#00ff00"


class Sketch:
    mousedown: bool = False
    segments: List[Segment]
    lines: List[Line]
    ptr_group: int
    group_rom: bytearray
    rom_lines: List[Line]
    groups: List[Group]
    x0: int
    y0: int
    x: int
    y: int
    done: bool
    group_num: int = 0
    pen: str = CYAN

    def __init__(self):
        self.mousedown = False
        self.segments = []
        self.lines = []
        self.groups = []
        self.done = False
        self.text = None
        self.next_group()

    def line(self, x, y, dx, dy, fill=None):
        return canvas.create_line(
            x * scale,
            y * scale,
            (x + dx) * scale,
            (y + dy) * scale,
            fill=fill or self.pen,
            width=2 * scale,
        )

    def next_group(self):
        self.group_num += 1
        canvas.delete("all")
        if maybe := draw_group():
            self.ptr_group, self.group_rom, self.rom_lines = maybe
        else:
            with open("tutorial/output.hdm", "wb") as f:
                copy = rom[:]
                for g in self.groups:
                    ge = g.encode()
                    copy[g.ptr : g.ptr + len(ge)] = ge
                f.write(copy)
            print("Wrote rom to tutorial/output.hdm")
            self.done = True

        if os.path.exists(f"tutorial/tut{self.group_num}.json"):
            with open(f"tutorial/tut{self.group_num}.json") as f:
                line_data = json.load(f)
            for line in line_data:
                segments = []
                if "magic" in line:
                    magic = bytes([0x96 if b == 0x98 else b for b in line["magic"]])
                    self.process_magic(magic)
                    self.lines.append(MagicLine(magic))
                else:
                    x0 = x = line["x0"]
                    y0 = y = line["y0"]
                    for [dx, dy] in line["segments"]:
                        obj = self.line(x, y, dx, dy)
                        x += dx
                        y += dy
                        segments.append(Segment(dx, dy, obj))
                    self.lines.append(Line(x0, y0, segments))

        self.report()

    def save_group(self):
        magic = bytes(self.group_rom[0:5])
        group = Group(self.ptr_group, magic, self.lines)
        if len(group.encode()) > len(self.group_rom):
            print(f"Warning: {len(group.encode())} > {len(self.group_rom)} bytes")
        self.groups.append(group)

        if self.lines:
            with open(f"tutorial/tut{self.group_num}.json", "w") as f:
                json.dump([line.to_json() for line in self.lines], f)

        self.lines = []
        self.segments = []

    def undo(self):
        while self.lines:
            last = self.lines.pop()
            if isinstance(last, MagicLine):
                continue
            for s in last.segments:
                canvas.delete(s.obj)
            break
        self.report()


    def process_magic(self, magic):
        print(magic)
        if magic[4] == 0x01:
            print("RED")
            self.pen = "#ff6000"
        elif magic[3] == 0x5B:
            self.pen = GREEN
        else:
            self.pen = CYAN

    def key(self, event):
        if event.char == "j" and not self.done:
            self.save_group()
            self.next_group()
        elif event.char == "]":
            while self.lines:
                self.undo()
        elif event.char == "z" and self.lines:
            self.undo()
        elif event.char == "c":
            self.lines = []
            for line in self.rom_lines:
                segs = []
                if isinstance(line, MagicLine):
                    self.process_magic(line.magic)
                    self.lines.append(line)
                    continue
                x = line.x0
                y = line.y0
                for seg in line.segments:
                    obj = self.line(x, y, seg.dx, seg.dy)
                    x += seg.dx
                    y += seg.dy
                    segs.append(Segment(seg.dx, seg.dy, obj))
                self.lines.append(Line(line.x0, line.y0, segs))
        elif event.char == "1":
            self.pen = CYAN
            self.lines.append(MagicLine(b"\x91\x96\x30\x0a\x00"))
        elif event.char == "2":
            self.pen = GREEN
            self.lines.append(MagicLine(b"\x91\x96\x30\x5b\x00"))
        else:
            print(event)

    def move(self, event):
        down = event.state & 256 != 0
        if down and not self.mousedown:
            self.mousedown = True
            self.x0 = self.x = event.x // scale
            self.y0 = self.y = event.y // scale
        if down and self.mousedown:
            dx = (newx := event.x // scale) - self.x
            dy = (newy := event.y // scale) - self.y
            if dx**2 + dy**2 > 4**2:
                obj = self.line(self.x, self.y, dx, dy)
                self.segments.append(Segment(dx, dy, obj))
                self.x = newx
                self.y = newy
        if not down and self.mousedown:
            if not self.segments:  # dot
                obj = self.line(self.x, self.y, 2, 0)
                self.segments.append(Segment(2, 0, obj))
            self.lines.append(Line(self.x0, self.y0, self.segments))
            self.report()
            self.segments = []
            self.mousedown = False

    def report(self):
        if self.text: canvas.delete(self.text)
        self.text = canvas.create_text(
            10,
            10,
            anchor="nw",
            text=f"Page {self.group_num}, size: {sum(len(l.encode()) for l in self.lines)} / {len(self.group_rom)}",
            fill="white",
            font="Helvetica 15",
        )



# add to window and show
canvas.pack()
sketch = Sketch()
canvas.bind("<Motion>", sketch.move)
canvas.bind("<ButtonPress-1>", sketch.move)
canvas.bind("<ButtonRelease-1>", sketch.move)
canvas.bind("<Key>", sketch.key)
canvas.focus_set()

root.mainloop()
