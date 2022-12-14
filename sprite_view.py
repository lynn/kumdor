
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
