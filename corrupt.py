import sys

#with open("The Sword of Kumdor.hdm", "rb") as f:
with open("saved.hdm", "rb") as f:
    rom = f.read()

rom = bytearray(rom)
_, start, stop, val = sys.argv

start = int(start, 16)
stop = int(stop, 16)
val = int(val, 16)
rom[0x10:0x30] = f"{start:5x}-{stop:5x}".rjust(32).encode("ascii")
import random

rom[start:stop] = bytes([val]) * (stop - start)

# 2c000: magic
# 2c005: u16 x
# 2c007: u16 y
# 2c009: s8 x
# 2c00a: s8 y
# 2c00b: s8 x
# 2c00c: s8 y
# ...
# 2c021-2c022: 0i8 0i8 (end of line)


with open("corrupt.hdm", "wb") as f:
    f.write(rom)
print(f"Wrote corrupt.hdm with rom[{start:5x}:{stop:5x}] = {val:2x}")
