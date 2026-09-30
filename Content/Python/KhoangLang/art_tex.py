"""Khoang Lang 02:17 - procedural texture synthesis for the art pass.

Every texture in the art pass is generated here from noise and simple rules, so
the project carries no third-party art and no unlicensed reference photography.
Values are written as 8-bit PNGs (zlib + struct only, no imaging library) and
imported as Texture2D assets.
"""

import math
import os
import struct
import zlib

# --------------------------------------------------------------------------- #
# PNG output
# --------------------------------------------------------------------------- #


def write_png(path, w, h, rows_rgb):
    raw = b''.join(b'\x00' + bytes(row) for row in rows_rgb)

    def chunk(tag, data):
        c = tag + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c))

    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(raw, 6))
    png += chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(png)
    return len(png)


# --------------------------------------------------------------------------- #
# tiling value noise
# --------------------------------------------------------------------------- #


def _hash(x, y, seed):
    n = (x * 374761393 + y * 668265263 + seed * 2147483647) & 0xFFFFFFFF
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFFFF) / 16777215.0


def _smooth(t):
    return t * t * (3.0 - 2.0 * t)


class Noise(object):
    """Tiling value noise: sampling at x=size wraps back to x=0."""

    def __init__(self, size, seed):
        self.size = size
        self.seed = seed

    def at(self, x, y):
        xi = math.floor(x)
        yi = math.floor(y)
        tx = _smooth(x - xi)
        ty = _smooth(y - yi)
        x0 = xi % self.size
        y0 = yi % self.size
        x1 = (xi + 1) % self.size
        y1 = (yi + 1) % self.size
        a = _hash(x0, y0, self.seed)
        b = _hash(x1, y0, self.seed)
        c = _hash(x0, y1, self.seed)
        d = _hash(x1, y1, self.seed)
        top = a + (b - a) * tx
        bot = c + (d - c) * tx
        return top + (bot - top) * ty

    def fbm(self, x, y, octaves=4, gain=0.5, lac=2.0):
        amp = 1.0
        total = 0.0
        norm = 0.0
        fx, fy = x, y
        for o in range(octaves):
            total += amp * self.at(fx, fy)
            norm += amp
            amp *= gain
            fx *= lac
            fy *= lac
        return total / norm

    def ridged(self, x, y, octaves=4):
        amp = 1.0
        total = 0.0
        norm = 0.0
        fx, fy = x, y
        for _ in range(octaves):
            n = 1.0 - abs(self.at(fx, fy) * 2.0 - 1.0)
            total += amp * n * n
            norm += amp
            amp *= 0.5
            fx *= 2.0
            fy *= 2.0
        return total / norm


def clamp(v, lo=0.0, hi=1.0):
    return lo if v < lo else (hi if v > hi else v)


def mix(a, b, t):
    return a + (b - a) * t


def rgb(lin):
    """linear 0..1 -> 0..255 (the PNG is sRGB, so encode roughly)."""
    out = []
    for v in lin:
        v = clamp(v)
        if v <= 0.0031308:
            s = v * 12.92
        else:
            s = 1.055 * (v ** (1.0 / 2.4)) - 0.055
        out.append(int(clamp(s, 0.0, 1.0) * 255.0 + 0.5))
    return out


def gray(v):
    u = int(clamp(v, 0.0, 1.0) * 255.0 + 0.5)
    return [u, u, u]


# --------------------------------------------------------------------------- #
# normal map from a height field
# --------------------------------------------------------------------------- #


def normal_rows(height, w, h, strength=2.2):
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            hl = height[y][(x - 1) % w]
            hr = height[y][(x + 1) % w]
            hu = height[(y - 1) % h][x]
            hd = height[(y + 1) % h][x]
            dx = (hl - hr) * strength
            dy = (hu - hd) * strength
            nz = 1.0
            ln = math.sqrt(dx * dx + dy * dy + nz * nz)
            row += [int(clamp(dx / ln * 0.5 + 0.5) * 255),
                    int(clamp(dy / ln * 0.5 + 0.5) * 255),
                    int(clamp(nz / ln * 0.5 + 0.5) * 255)]
        rows.append(row)
    return rows


# --------------------------------------------------------------------------- #
# surface families
# --------------------------------------------------------------------------- #


def _grime(n, x, y, f, strength):
    """large slow blotches + fine speckle, used by every surface"""
    big = n.fbm(x * f, y * f, 4, 0.55)
    fine = n.fbm(x * f * 7.0, y * f * 7.0, 3, 0.5)
    return clamp(big * 0.72 + fine * 0.28)


def make_plaster(size=256, seed=11, tint=(0.72, 0.65, 0.44), patch=(0.58, 0.50, 0.33)):
    """Aged ochre paint over plaster: the dominant school wall surface."""
    n = Noise(64, seed)
    nf = Noise(64, seed + 7)
    alb, rgh, hgt = [], [], []
    for y in range(size):
        ra, rr, rh = [], [], []
        for x in range(size):
            u, v = x / float(size), y / float(size)
            g = _grime(n, u, v, 5.0, 1.0)
            peel = clamp((n.fbm(u * 3.0, v * 3.0, 3) - 0.52) * 5.0, 0.0, 1.0)
            plaster = n.fbm(u * 18.0, v * 18.0, 3)
            grit = nf.at(u * 96.0, v * 96.0)
            base = [mix(tint[k], patch[k], g * 0.75) for k in range(3)]
            # exposed lime plaster under the paint, slightly greyer and cooler
            exposed = [0.70, 0.68, 0.62]
            col = [mix(base[k], exposed[k], peel * 0.55) for k in range(3)]
            col = [mix(c, 1.0, (plaster - 0.5) * 0.10 + (grit - 0.5) * 0.05)
                   for k, c in enumerate(col)]
            ra += rgb(col)
            rough = 0.90 - peel * 0.04 + (plaster - 0.5) * 0.08
            rr += gray(rough)
            h = 0.5 + (plaster - 0.5) * 0.35 + peel * 0.10 + (grit - 0.5) * 0.10
            rh.append(clamp(h))
        alb.append(ra)
        rgh.append(rr)
        hgt.append(rh)
    return {'albedo': alb, 'rough': rgh, 'height': hgt}


def make_exterior_plaster(size=256, seed=23):
    """Rain-worn outside render: vertical streaks, moss at the base."""
    n = Noise(64, seed)
    alb, rgh, hgt = [], [], []
    for y in range(size):
        ra, rr, rh = [], [], []
        for x in range(size):
            u, v = x / float(size), y / float(size)
            streak = n.fbm(u * 26.0, v * 1.6, 3)
            blotch = n.fbm(u * 4.0, v * 4.0, 4)
            grit = n.at(u * 120.0, v * 120.0)
            base = [0.60, 0.55, 0.40]
            col = [mix(b, 0.42, clamp(streak * 0.55 + (blotch - 0.5) * 0.5))
                   for b in base]
            # damp dark band along the bottom of the panel
            damp = clamp((v - 0.72) * 4.2, 0.0, 1.0)
            col = [mix(c, 0.20, damp * 0.75) for c in col]
            col = [mix(c, 0.26, damp * 0.35 * clamp(blotch)) for c in col]
            col = [mix(c, 1.0, (grit - 0.5) * 0.10) for c in col]
            ra += rgb(col)
            rr += gray(0.90 - damp * 0.12 + (blotch - 0.5) * 0.06)
            rh.append(clamp(0.5 + (blotch - 0.5) * 0.30 + (grit - 0.5) * 0.22
                            - streak * 0.10))
        alb.append(ra)
        rgh.append(rr)
        hgt.append(rh)
    return {'albedo': alb, 'rough': rgh, 'height': hgt}


def make_concrete(size=256, seed=31, tint=(0.36, 0.36, 0.35)):
    n = Noise(64, seed)
    nf = Noise(64, seed + 3)
    alb, rgh, hgt = [], [], []
    for y in range(size):
        ra, rr, rh = [], [], []
        for x in range(size):
            u, v = x / float(size), y / float(size)
            broad = n.fbm(u * 5.0, v * 5.0, 4)
            agg = nf.fbm(u * 60.0, v * 60.0, 2)
            pits = clamp((nf.at(u * 48.0, v * 48.0) - 0.80) * 8.0, 0.0, 1.0)
            col = [mix(tint[k], 0.52, clamp((agg - 0.45) * 1.2)) for k in range(3)]
            col = [mix(c, 0.20, pits * 0.7) for c in col]
            col = [mix(c, 0.46, clamp((broad - 0.5) * 0.55)) for c in col]
            ra += rgb(col)
            rr += gray(0.86 + (agg - 0.5) * 0.10 + pits * 0.06)
            rh.append(clamp(0.5 + (agg - 0.5) * 0.28 + (broad - 0.5) * 0.20
                            - pits * 0.35))
        alb.append(ra)
        rgh.append(rr)
        hgt.append(rh)
    return {'albedo': alb, 'rough': rgh, 'height': hgt}


def make_floor_tile(size=256, seed=41, tiles=4, grout=0.030, base=(0.34, 0.33, 0.31)):
    """Worn painted concrete floor tiles, the standard rural school floor."""
    n = Noise(64, seed)
    nf = Noise(64, seed + 5)
    alb, rgh, hgt = [], [], []
    ts = float(tiles)
    for y in range(size):
        ra, rr, rh = [], [], []
        for x in range(size):
            u, v = x / float(size), y / float(size)
            fu = (u * ts) % 1.0
            fv = (v * ts) % 1.0
            du = min(fu, 1.0 - fu)
            dv = min(fv, 1.0 - fv)
            d = min(du, dv)
            is_grout = 1.0 if d < grout else 0.0
            edge = clamp((d - grout) / 0.035, 0.0, 1.0)
            # per-tile shade variation so the floor does not read as one sheet
            tile_id = (int(u * ts) * 7 + int(v * ts) * 13) % 5
            shade = (0.86, 0.92, 1.0, 0.96, 0.89)[tile_id]
            wear = n.fbm(u * 9.0, v * 9.0, 4)
            speck = nf.fbm(u * 70.0, v * 70.0, 2)
            col = [mix(b, b * shade, 1.0) for b in base]
            col = [mix(c, 1.06, clamp((wear - 0.5) * 0.9)) for c in col]
            col = [mix(c, 0.55, (1.0 - edge)) for c in col]
            col = [mix(c, 0.30, is_grout * 0.85) for c in col]
            col = [mix(c, 1.0, (speck - 0.5) * 0.13) for c in col]
            # scuffed traffic path
            path = clamp(1.0 - abs(u - 0.5) * 2.4, 0.0, 1.0)
            col = [mix(c, c * 1.18, path * clamp(wear * 1.2, 0.0, 1.0) * 0.5)
                   for c in col]
            ra += rgb(col)
            rr += gray(0.80 - path * 0.16 * wear + (speck - 0.5) * 0.08
                       + is_grout * 0.08)
            rh.append(clamp(0.62 - is_grout * 0.30 + (speck - 0.5) * 0.10))
        alb.append(ra)
        rgh.append(rr)
        hgt.append(rh)
    return {'albedo': alb, 'rough': rgh, 'height': hgt}


def make_wood(size=256, seed=53, tint=(0.30, 0.17, 0.08), painted=None,
              chip=0.0):
    """Sawn timber: straight fine grain along U, a few knots, optional flaking
    paint over bare wood."""
    n = Noise(64, seed)
    nf = Noise(64, seed + 2)
    alb, rgh, hgt = [], [], []
    for y in range(size):
        ra, rr, rh = [], [], []
        for x in range(size):
            u, v = x / float(size), y / float(size)
            # grain runs along U; a slow warp keeps it from looking printed
            warp = (n.fbm(u * 2.0, v * 2.0, 3) - 0.5) * 0.55
            rings = math.sin((v + warp) * 58.0) * 0.5 + 0.5
            fibre = nf.fbm(u * 8.0, v * 220.0, 2)
            knot = n.fbm(u * 5.0, v * 5.0, 2)
            k = clamp((knot - 0.74) * 12.0, 0.0, 1.0)
            col = [mix(tint[k2] * 0.72, tint[k2] * 1.22, rings) for k2 in range(3)]
            col = [mix(c, c * 0.72, k) for c in col]
            col = [mix(c, c * 0.86, clamp((fibre - 0.5) * 1.5)) for c in col]
            rough = 0.74 + (fibre - 0.5) * 0.12 - k * 0.10
            height = 0.5 + (rings - 0.5) * 0.14 + (fibre - 0.5) * 0.10 - k * 0.10
            if painted is not None:
                flake = n.fbm(u * 6.0, v * 6.0, 4)
                bare = clamp((flake - 0.44) * 7.0 * chip, 0.0, 1.0)
                col = [mix(painted[k2], col[k2], bare) for k2 in range(3)]
                rough = mix(0.60, rough, bare)
                height = mix(0.60, height, bare)
            ra += rgb(col)
            rr += gray(rough)
            rh.append(clamp(height))
        alb.append(ra)
        rgh.append(rr)
        hgt.append(rh)
    return {'albedo': alb, 'rough': rgh, 'height': hgt}


def make_chalkboard(size=256, seed=61):
    """Dark green board: chalk dust, erased ghost writing, felt texture."""
    n = Noise(64, seed)
    nf = Noise(64, seed + 9)
    alb, rgh, hgt = [], [], []
    for y in range(size):
        ra, rr, rh = [], [], []
        for x in range(size):
            u, v = x / float(size), y / float(size)
            felt = nf.fbm(u * 90.0, v * 90.0, 2)
            ghost = n.fbm(u * 6.0, v * 22.0, 4)
            smear = clamp((ghost - 0.55) * 3.0, 0.0, 1.0)
            base = [0.055, 0.115, 0.085]
            col = [mix(b, 1.25, felt * 0.35) for b in base]
            col = [mix(c, 0.30, smear * 0.55) for c in col]
            ra += rgb(col)
            rr += gray(0.88 - smear * 0.25 + (felt - 0.5) * 0.06)
            rh.append(clamp(0.5 + (felt - 0.5) * 0.20))
        alb.append(ra)
        rgh.append(rr)
        hgt.append(rh)
    return {'albedo': alb, 'rough': rgh, 'height': hgt}


def make_metal(size=256, seed=71, tint=(0.34, 0.35, 0.36), rust=0.25):
    n = Noise(64, seed)
    nf = Noise(64, seed + 4)
    alb, rgh, hgt = [], [], []
    for y in range(size):
        ra, rr, rh = [], [], []
        for x in range(size):
            u, v = x / float(size), y / float(size)
            brush = nf.fbm(u * 4.0, v * 70.0, 2)
            rustn = n.fbm(u * 8.0, v * 8.0, 4)
            r = clamp((rustn - 0.52) * 5.0 * rust, 0.0, 1.0)
            shade = 0.85 + (brush - 0.5) * 0.35
            col = [tint[k] * shade for k in range(3)]
            col = [mix(c, 0.36, r) for c in col]
            ra += rgb(col)
            rr += gray(0.42 + r * 0.42 + (brush - 0.5) * 0.10)
            rh.append(clamp(0.5 + (brush - 0.5) * 0.16 + r * 0.18))
        alb.append(ra)
        rgh.append(rr)
        hgt.append(rh)
    return {'albedo': alb, 'rough': rgh, 'height': hgt}


def make_paper(size=256, seed=83, tint=(0.74, 0.70, 0.58)):
    n = Noise(64, seed)
    alb, rgh, hgt = [], [], []
    for y in range(size):
        ra, rr, rh = [], [], []
        for x in range(size):
            u, v = x / float(size), y / float(size)
            fibre = n.fbm(u * 70.0, v * 70.0, 2)
            stain = n.fbm(u * 4.0, v * 4.0, 4)
            foxing = clamp((n.fbm(u * 11.0, v * 11.0, 3) - 0.62) * 6.0, 0.0, 1.0)
            col = [mix(tint[k], tint[k] * 0.82, stain) for k in range(3)]
            col = [mix(c, 0.42, foxing * 0.55) for c in col]
            col = [mix(c, 1.0, (fibre - 0.5) * 0.09) for c in col]
            ra += rgb(col)
            rr += gray(0.92 + (fibre - 0.5) * 0.05)
            rh.append(clamp(0.5 + (fibre - 0.5) * 0.10))
        alb.append(ra)
        rgh.append(rr)
        hgt.append(rh)
    return {'albedo': alb, 'rough': rgh, 'height': hgt}


def make_ceiling(size=256, seed=97):
    """Painted ceiling board with brown water stains and flaking."""
    n = Noise(64, seed)
    nf = Noise(64, seed + 6)
    alb, rgh, hgt = [], [], []
    for y in range(size):
        ra, rr, rh = [], [], []
        for x in range(size):
            u, v = x / float(size), y / float(size)
            stain = n.fbm(u * 3.0, v * 3.0, 4)
            edge = clamp((stain - 0.56) * 5.0, 0.0, 1.0)
            core = clamp((stain - 0.70) * 7.0, 0.0, 1.0)
            grit = nf.fbm(u * 80.0, v * 80.0, 2)
            col = [0.80, 0.79, 0.74]
            col = [mix(c, 0.52, edge * 0.75) for c in col]
            col = [mix(c, 0.34, core * 0.70) for c in col]
            col = [mix(c, 1.0, (grit - 0.5) * 0.10) for c in col]
            ra += rgb(col)
            rr += gray(0.86 + core * 0.08 + (grit - 0.5) * 0.06)
            rh.append(clamp(0.5 + (grit - 0.5) * 0.18 - core * 0.20))
        alb.append(ra)
        rgh.append(rr)
        hgt.append(rh)
    return {'albedo': alb, 'rough': rgh, 'height': hgt}


def make_grunge(size=256, seed=101):
    """Large soft stain layer multiplied over everything so tiling hides."""
    n = Noise(64, seed)
    rows = []
    for y in range(size):
        row = []
        for x in range(size):
            u, v = x / float(size), y / float(size)
            big = n.fbm(u * 2.0, v * 2.0, 5, 0.58)
            streak = n.fbm(u * 14.0, v * 1.4, 3)
            g = clamp(0.42 + big * 0.52 + (streak - 0.5) * 0.24)
            row += [int(g * 255), int(g * 255), int(g * 255)]
        rows.append(row)
    return {'albedo': rows}


# --------------------------------------------------------------------------- #
# school signage (uppercase, unaccented - typical of hand-painted rural signs)
# --------------------------------------------------------------------------- #

_GLYPH = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "11110", "10001", "10001", "10001", "11110"),
    'C': ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "11110", "10000", "10000", "10000", "11111"),
    'F': ("11111", "10000", "11110", "10000", "10000", "10000", "10000"),
    'G': ("01111", "10000", "10000", "10011", "10001", "10001", "01111"),
    'H': ("10001", "10001", "11111", "10001", "10001", "10001", "10001"),
    'I': ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    'K': ("10001", "10010", "11100", "10010", "10010", "10001", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    '3': ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '-': ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
}


def draw_text(rows, w, h, text, ox, oy, scale, colour, spacing=1):
    cx = ox
    for ch in text.upper():
        g = _GLYPH.get(ch, _GLYPH[' '])
        gw, gh = 5, 7
        for gy in range(gh):
            for gx in range(gw):
                if g[gy][gx] != '1':
                    continue
                for sy in range(scale):
                    for sx in range(scale):
                        px = cx + gx * scale + sx
                        py = oy + gy * scale + sy
                        if 0 <= px < w and 0 <= py < h:
                            rows[py][px * 3:px * 3 + 3] = list(colour)
        cx += (gw + spacing) * scale
    return cx


def make_sign(w=512, h=256):
    """Hand-painted enamel school sign on the gate wall.

    Text is uppercase and unaccented, which is how these signs are actually
    painted in rural schools; a real accented version would need a font.
    """
    lines = [('TRUONG TIEU HOC', 5, 44), ('SO 3', 5, 100), ('KHE LAC', 3, 176)]
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            u = x / float(w)
            v = y / float(h)
            edge = min(u, 1.0 - u, v, 1.0 - v)
            fade = 0.80 + 0.30 * clamp(edge / 0.09)
            wear = 0.0
            base = [0.055, 0.135, 0.095]
            row += [int(min(255, base[0] * 255 * fade)),
                    int(min(255, base[1] * 255 * fade)),
                    int(min(255, base[2] * 255 * fade))]
        rows.append(row)
    # enamel border
    for y in range(h):
        for x in range(w):
            if 8 <= x < w - 8 and 8 <= y < h - 8:
                inset = min(x - 8, w - 9 - x, y - 8, h - 9 - y)
                if inset < 2:
                    rows[y][x * 3:x * 3 + 3] = [206, 198, 172]
    for text, scale, oy in lines:
        tw = len(text) * 6 * scale - scale
        draw_text(rows, w, h, text, max(4, (w - tw) // 2), oy, scale,
                  (222, 214, 190))
    return {'albedo': rows}


# --------------------------------------------------------------------------- #
# manifest
# --------------------------------------------------------------------------- #

TEXTURES = [
    # name, builder, srgb
    ('T_ART_Plaster', lambda: make_plaster(), True),
    ('T_ART_PlasterExt', lambda: make_exterior_plaster(), True),
    ('T_ART_Concrete', lambda: make_concrete(), True),
    ('T_ART_FloorTile', lambda: make_floor_tile(), True),
    ('T_ART_Wood', lambda: make_wood(), True),
    ('T_ART_WoodPaintGreen', lambda: make_wood(seed=57, tint=(0.30, 0.17, 0.08),
                                               painted=(0.20, 0.28, 0.20),
                                               chip=1.0), True),
    ('T_ART_WoodPaintBlue', lambda: make_wood(seed=59, tint=(0.32, 0.19, 0.09),
                                              painted=(0.16, 0.22, 0.30),
                                              chip=1.0), True),
    ('T_ART_Chalk', lambda: make_chalkboard(), True),
    ('T_ART_Metal', lambda: make_metal(), True),
    ('T_ART_MetalRust', lambda: make_metal(seed=73, tint=(0.30, 0.30, 0.30),
                                          rust=0.85), True),
    ('T_ART_Paper', lambda: make_paper(), True),
    ('T_ART_Ceiling', lambda: make_ceiling(), True),
    ('T_ART_Sign', lambda: make_sign(), True),
    ('T_ART_Grunge', lambda: make_grunge(), False),
]
