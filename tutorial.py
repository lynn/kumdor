import struct
import tkinter

with open("The Sword of Kumdor.hdm", "rb") as f:
    rom = f.read()


class Cursor(bytearray):
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
grp = 0


def draw_group():
    for i in range(200):
        ptr0 = rom.ptr
        x0 = x = rom.u16()
        y0 = y = rom.u16()

        if x == 0x5555:
            # End
            rom.skip(-4)
            return

        if x // 256 == 0x96:
            print(f"{i:4} {ptr0:5x} {x0:4x} {y0:4x} {rom.u8():02x} @@@@@@@")
            continue
        if x == 0xC000:
            rom.skip(-2)
            while rom[rom.ptr] == 0:
                rom.skip(1)
            print(f"{i:4} {ptr0:5x} {x0:4x} {y0:4x} ----------")
            return
        segs = 0
        while True:
            dx = rom.i8()
            dy = rom.i8()
            if dx == dy == 0:
                break
            canvas.create_line(
                x * scale,
                y * scale,
                (x + dx) * scale,
                (y + dy) * scale,
                fill=f"#{i*16%256:02x}30e0",
                width=2*scale,
            )
            x += dx
            y += dy
            segs += 1

        print(f"{i:4} {ptr0:5x} {x0:4x} {y0:4x} {segs:4}")
        rom.skip(0)


def key(event):
    if event.char == 'c':
        canvas.create_rectangle(0, 0, 640*scale, 480*scale, fill="black")
    else:
        draw_group()


# add to window and show
canvas.pack()
canvas.bind("<Key>", key)
canvas.focus_set()

root.mainloop()
