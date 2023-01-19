def onebpp(bs, width=64, height=64):
    rows = []
    for y in range(height):
        row = []
        for x in range(width // 8):
            for b in range(8):
                bit = bs[width // 8 * y + x] >> (7 - b) & 1
                row.append(bit)
        rows.append(row)

    return rows


def twobpp(bs, width=64, height=64):
    ir = onebpp(bs, width, height)
    ig = onebpp(bs[width // 8 * height :], width, height)
    return [[r + 2 * g for r, g in zip(lr, lg)] for lr, lg in zip(ir, ig)]


def threebpp(bs, width=64, height=64):
    ir = onebpp(bs, width, height)
    ig = onebpp(bs[width // 8 * height :], width, height)
    ib = onebpp(bs[width // 8 * height * 2 :], width, height)
    return [
        [r + 2 * g + 4 * b for r, g, b in zip(lr, lg, lb)]
        for lr, lg, lb in zip(ir, ig, ib)
    ]


def show(matrix):
    for row in matrix:
        print(
            "".join(
                "\x1b[%dm%s\x1b[0m" % ([40, 102, 107, 103, 101, 106, 105, 104][x], "  ")
                for x in row
            )
        )


def main(name="tiles", num=16, sz=32, k=2 * 32 * 32 // 8, start=0, h=10, func=twobpp):
    from PIL import Image

    im = Image.new("P", (num * sz, num * sz * h), 2)
    black = [0, 0, 0]
    blue = [0, 0, 255]
    green = [0, 255, 0]
    cyan = [0, 255, 255]
    red = [255, 0, 0]
    magenta = [255, 0, 255]
    yellow = [255, 255, 0]
    white = [255, 255, 255]
    im.putpalette([*black, *green, *white, *yellow, *red, *cyan, *magenta, *blue])

    with open("The Sword of Kumdor.hdm", "rb") as f:
        rom = f.read()

    for y in range(num * 20):
        for x in range(num):
            addr = start + k * (x + num * y)
            slic = rom[addr : addr + k]
            if len(slic) < k:
                break
            tile = func(slic, sz, sz)
            t = Image.frombytes("P", (sz, sz), bytes([b for row in tile for b in row]))
            im.paste(t, (x * sz, y * sz))
    im.save(f"kumdor-{name}.png")


if __name__ == "__main__":
    #main()
    main("player", num=16, k=3*32*32//8, start=0x28000, h=1, func=threebpp)
    #main("enemy", 6, 64, 0x800, 0xC0000 + 0x200, h=1, func=threebpp)
    #main("boss", 3, 96, 0x1000, 0xD0000 + 0x200, h=1, func=threebpp)
