#!/usr/bin/env python3
"""Generate Crudo Football PWA icons as PNGs using only the stdlib.
Retro Game Boy look: green shell background with a pixel-art football."""
import struct, zlib, os

def hx(h):
    h = h.lstrip("#")
    return (int(h[0:2],16), int(h[2:4],16), int(h[4:6],16))

GB_BG      = hx("c4cfa1")   # game boy body green
SCREEN_DK  = hx("222222")   # dark screen frame
FIELD      = hx("3a7d34")   # pitch green
FIELD_LN   = hx("5fae57")   # pitch light stripe
BALL_W     = hx("f2f2f2")   # ball white
BALL_K     = hx("222222")   # ball black patches
BORDER     = hx("111111")

def write_png(path, size, maskable=False):
    W = H = size
    # RGBA framebuffer
    px = [[GB_BG for _ in range(W)] for _ in range(H)]

    def fill_rect(x0, y0, x1, y1, col):
        for y in range(max(0,y0), min(H,y1)):
            row = px[y]
            for x in range(max(0,x0), min(W,x1)):
                row[x] = col

    def fill_circle(cx, cy, r, col):
        r2 = r*r
        for y in range(max(0,cy-r), min(H,cy+r+1)):
            dy = y-cy
            for x in range(max(0,cx-r), min(W,cx+r+1)):
                dx = x-cx
                if dx*dx+dy*dy <= r2:
                    px[y][x] = col

    # For maskable icons keep content within the safe zone (~80%).
    inset = int(size*0.10) if maskable else int(size*0.06)

    # Dark rounded-ish screen panel (simple rect frame)
    fill_rect(inset, inset, W-inset, H-inset, SCREEN_DK)
    fld = inset + int(size*0.045)
    fill_rect(fld, fld, W-fld, H-fld, FIELD)

    # pitch stripes
    stripe_h = max(2, size//14)
    y = fld
    toggle = False
    while y < H-fld:
        if toggle:
            fill_rect(fld, y, W-fld, min(H-fld, y+stripe_h), FIELD_LN)
        y += stripe_h
        toggle = not toggle

    # center line + circle
    cx, cy = W//2, H//2
    fill_rect(fld, cy-max(1,size//160), W-fld, cy+max(1,size//160), FIELD_LN)
    # football (pixel-art soccer ball)
    r = int(size*0.20)
    fill_circle(cx, cy, r+max(1,size//64), BALL_K)   # thin outline
    fill_circle(cx, cy, r, BALL_W)
    # central black pentagon (blocky)
    pr = int(r*0.42)
    fill_rect(cx-pr, cy-pr, cx+pr, cy+pr, BALL_K)
    # a few surrounding patches
    off = int(r*0.62)
    ps = max(2, int(r*0.22))
    for (ox,oy) in [(-off,-off),(off,-off),(-off,off),(off,off)]:
        fill_rect(cx+ox-ps, cy+oy-ps, cx+ox+ps, cy+oy+ps, BALL_K)

    # outer border
    b = max(2, size//64)
    fill_rect(0,0,W,b,BORDER); fill_rect(0,H-b,W,H,BORDER)
    fill_rect(0,0,b,H,BORDER); fill_rect(W-b,0,W,H,BORDER)

    # Encode PNG (RGB, no alpha needed)
    raw = bytearray()
    for y in range(H):
        raw.append(0)  # filter type 0
        for x in range(W):
            r_,g_,b_ = px[y][x]
            raw += bytes((r_,g_,b_))
    comp = zlib.compress(bytes(raw), 9)

    def chunk(typ, data):
        c = struct.pack(">I", len(data)) + typ + data
        c += struct.pack(">I", zlib.crc32(typ+data) & 0xffffffff)
        return c

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)  # 8-bit, colortype 2 (RGB)
    with open(path, "wb") as f:
        f.write(sig)
        f.write(chunk(b"IHDR", ihdr))
        f.write(chunk(b"IDAT", comp))
        f.write(chunk(b"IEND", b""))
    print("wrote", path, size, "maskable" if maskable else "")

os.makedirs("icons", exist_ok=True)
write_png("icons/icon-192.png", 192)
write_png("icons/icon-512.png", 512)
write_png("icons/icon-maskable-512.png", 512, maskable=True)
write_png("icons/apple-touch-icon.png", 180)
