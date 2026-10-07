#!/usr/bin/env python3
"""GR4-XPanUnlock: an XPan (65:24) aspect ratio for the RICOH GR IV (firmware 1.11).

Replaces the 16:9 aspect ratio with XPan. Turns the official RICOH firmware file
you downloaded yourself into the XPan version. A file is written only if every
check passes.

Usage
  python3 gr4_xpanunlock.py patch  OFFICIAL_fwdc248b.bin  [-o OUTPUT_DIR]
  python3 gr4_xpanunlock.py check  ANY_fwdc248b.bin

Python 3.8 or newer, no extra packages.
"""
import argparse
import base64
import hashlib
import struct
import sys
import zlib
from pathlib import Path

VERSION = '1.0.0'

OFFICIAL_SHA256 = 'a2f664dfca034059eb0fd6e18ab08684c326b4a034d85c164dad7e1ec9b5655f'
OFFICIAL_BYTES = 38648776

UNLOCKED_SHA256 = 'fa2c67d1b67e16675a0c75b98d58c519b803f049a00e40e34103e54ca9a6a6c7'

# Other known GR IV 1.11 builds that this tool should not be fed (identified by `check`).
OTHER_KNOWN = {
    '4c04b48c65897f2edd028df0f5e04666ca241488c81502bae0f34e040ee454eb': 'GR4-MonoUnlock 1.0.0 (monochrome looks unlocked)',
}

# (payload offset, original bytes, new bytes, what it does)
# Code and text in the RTOS section; all changes keep every size and address unchanged.
CHANGES = [
    (0x08e7d08, '983d00e3', 'f03800e3',
     'image size: 16:9 6192x3480 -> XPan 6192x2288'),
    (0x08e7cf4, 'ae3ea0e3', '723ea0e3',
     'image size: 16:9 4944x2784 -> XPan 4944x1824'),
    (0x08e7cdc, '7b3ea0e3', '513ea0e3',
     'image size: 16:9 3504x1968 -> XPan 3504x1296'),
    (0x08e7cc8, '383400e3', 'c83200e3',
     'image size: 16:9 1920x1080 -> XPan 1920x712'),
    (0x08e7e0c, '2610a0e3', '6b10a0e3',
     'preview image placement: ScreenNail letterbox y 38 -> 107'),
    (0x08e7ec4, '1010a0e3', '1e10a0e3',
     'thumbnail placement: Thumbnail letterbox y 16 -> 30'),
    (0x0899770, '98cd00e3', 'f0c800e3',
     'live-view sensor window: LV 16:9 window height 3480 -> 2288'),
    (0x03b975c, '0940a0e3', '1840a0e3',
     'playback ratio detection: ratio term 9 -> 24'),
    (0x03b9764, '0142a0e1', '014381e0',
     'playback ratio detection: 16*S -> 65*S'),
    (0x03ba8bc, '983d00e3', 'f03800e3',
     'playback camera-size check: 16:9 height 3480 -> 2288'),
    (0x03ba83c, 'ae0e54e3', '720e54e3',
     'playback camera-size check: 16:9 height 2784 -> 1824'),
    (0x03ba8a4, '7b0e54e3', '510e54e3',
     'playback camera-size check: 16:9 height 1968 -> 1296'),
    (0x03ba948, '383400e3', 'c83200e3',
     'playback camera-size check: 16:9 XS height 1080 -> 712'),
    (0x0894578, '82e100e3', 'eee300e3',
     'exposure/white-balance metering area: 16:9 crop0 OriginV 386 -> 1006'),
    (0x08945b0, '82e100e3', 'eee300e3',
     'exposure/white-balance metering area: 16:9 crop0 OriginV 386 -> 1006'),
    (0x08945f8, '82e100e3', 'eee300e3',
     'exposure/white-balance metering area: 16:9 crop0 OriginV 386 -> 1006'),
    (0x0894640, '82e100e3', 'eee300e3',
     'exposure/white-balance metering area: 16:9 crop0 OriginV 386 -> 1006'),
    (0x0894588, '38e0a0e3', '24e0a0e3',
     'exposure/white-balance metering area: 16:9 crop0 BlockV 56 -> 36'),
    (0x08945c8, '38e0a0e3', '24e0a0e3',
     'exposure/white-balance metering area: 16:9 crop0 BlockV 56 -> 36'),
    (0x0894610, '38e0a0e3', '24e0a0e3',
     'exposure/white-balance metering area: 16:9 crop0 BlockV 56 -> 36'),
    (0x0894664, '38e0a0e3', '24e0a0e3',
     'exposure/white-balance metering area: 16:9 crop0 BlockV 56 -> 36'),
    (0x0894698, 'f6e200e3', 'a8e400e3',
     'exposure/white-balance metering area: 16:9 crop1 OriginV 758 -> 1192'),
    (0x08946a0, '2c40a0e3', '1e40a0e3',
     'exposure/white-balance metering area: 16:9 crop1 BlockV 44 -> 30'),
    (0x08946e4, '2c40a0e3', '1e40a0e3',
     'exposure/white-balance metering area: 16:9 crop1 BlockV 44 -> 30'),
    (0x0894718, '2c40a0e3', '1e40a0e3',
     'exposure/white-balance metering area: 16:9 crop1 BlockV 44 -> 30'),
    (0x0894764, '2c40a0e3', '1e40a0e3',
     'exposure/white-balance metering area: 16:9 crop1 BlockV 44 -> 30'),
    (0x0894794, '6a4400e3', 'de4500e3',
     'exposure/white-balance metering area: 16:9 crop2 OriginV 1130 -> 1502'),
    (0x089479c, '2050a0e3', '1450a0e3',
     'exposure/white-balance metering area: 16:9 crop2 BlockV 32 -> 20'),
    (0x0894348, '2060a0e3', '1460a0e3',
     'exposure/white-balance metering area: 16:9 crop2 BlockV 32 -> 20'),
    (0x0894828, '2060a0e3', '1460a0e3',
     'exposure/white-balance metering area: 16:9 crop2 BlockV 32 -> 20'),
    (0x089485c, '2040a0e3', '1440a0e3',
     'exposure/white-balance metering area: 16:9 crop2 BlockV 32 -> 20'),
    (0x089f9fc, '0a0296e2', '000096e2',
     'live-view display window: LV window H const low word (405<<29 -> 264<<29)'),
    (0x089fa04, '3210a1e2', '2110a1e2',
     'live-view display window: LV window H const high word 0x32 -> 0x21'),
    (0x08a2cf8, '650fa003', '420fa003',
     'live-view image height: LV VRAM V (base 480) 16:9 404 -> XPan 264'),
    (0x08a2d64, '260ea003', '190ea003',
     'live-view image height: LV VRAM V (base 720) 16:9 608 -> XPan 400'),
    (0x08a2da0, '620fa003', '010ca003',
     'live-view image height: LV VRAM V (base 464) 16:9 392 -> XPan 256'),
    (0x08a2ddc, '5e0fa003', 'f800a003',
     'live-view image height: LV VRAM V (base 448) 16:9 376 -> XPan 248'),
    (0x08a2e7c, '5a0fa003', 'ec00a003',
     'live-view image height: LV VRAM V (base 424) 16:9 360 -> XPan 236'),
    (0x08a2edc, 'cc00a003', '8400a003',
     'live-view image height: LV VRAM V (base 240) 16:9 204 -> XPan 132'),
    (0x08a2f18, '150ea003', 'dc00a003',
     'live-view image height: LV VRAM V (base 400) 16:9 336 -> XPan 220'),
    (0x08a2f5c, '7f0fa003', '530fa003',
     'live-view image height: LV VRAM V (base 600) 16:9 508 -> XPan 332'),
    (0x08a2ff0, '5a0fa003', 'ec00a003',
     'live-view image height: LV VRAM V (base 424) 16:9 360 -> XPan 236'),
    (0x08a30c0, 'b400a003', '7400a003',
     'live-view image height: LV VRAM V (base 212) 16:9 180 -> XPan 116'),
    (0x08a3110, 'd800a003', '8c00a003',
     'live-view image height: LV VRAM V (base 256) 16:9 216 -> XPan 140'),
    (0x03b6468, '020050e3', '010050e3',
     'focus area limits: aspect<=1 keeps the 3:2 rect (16:9 slot leaves the shared path)'),
    (0x03b648c, '28380de3', '740100e3',
     'focus area limits: XPan rect bottom 372 (r0)'),
    (0x03b6490, 'd01803e3', '0a3da0e3',
     'focus area limits: XPan rect right 640 (r3)'),
    (0x03b6494, 'db3345e3', '6c20a0e3',
     'focus area limits: XPan rect top 108 (r2)'),
    (0x03b6498, 'e0280ce3', '5010a0e3',
     'focus area limits: XPan rect left 80 (r1)'),
    (0x03b649c, '00308de5', 'eaffffea',
     'focus area limits: branch to shared Rect construction'),
    (0x03b66b4, 'e8e93953', '50ea3953',
     'auto-area focus size: mode-0 aspect table entry 2 -> XPan size block'),
    (0x03b6760, '50380de3', '0500a0e1',
     'auto-area focus size: XPan block: mov r0, r5'),
    (0x03b6764, 'd01803e3', '231ea0e3',
     'auto-area focus size: XPan block: width 560'),
    (0x03b6768, 'db3345e3', '422fa0e3',
     'auto-area focus size: XPan block: height 264'),
    (0x03b676c, 'e0280ce3', 'c12d15eb',
     'auto-area focus size: XPan block: bl Size::Set'),
    (0x03b6770, '00308de5', 'afffffea',
     'auto-area focus size: XPan block: b epilogue'),
    (0x03f5e14, '982d00e3', 'f02800e3',
     'playback Crop frame: Crop frame 6192x3480 -> 6192x2288'),
    (0x03f5e24, 'a82c00e3', '502800e3',
     'playback Crop frame: Crop frame 5760x3240 -> 5760x2128'),
    (0x03f5e34, 'bd2ea0e3', '1f2da0e3',
     'playback Crop frame: Crop frame 5376x3024 -> 5376x1984'),
    (0x03f5e44, 'f82a00e3', '302700e3',
     'playback Crop frame: Crop frame 4992x2808 -> 4992x1840'),
    (0x03f5e54, 'ae2ea0e3', '722ea0e3',
     'playback Crop frame: Crop frame 4944x2784 -> 4944x1824'),
    (0x03f5e64, '482900e3', '182600e3',
     'playback Crop frame: Crop frame 4224x2376 -> 4224x1560'),
    (0x03f5e74, '872ea0e3', '592ea0e3',
     'playback Crop frame: Crop frame 3840x2160 -> 3840x1424'),
    (0x03f5e84, '7b2ea0e3', '512ea0e3',
     'playback Crop frame: Crop frame 3504x1968 -> 3504x1296'),
    (0x03f5e94, '1b2da0e3', '472ea0e3',
     'playback Crop frame: Crop frame 3072x1728 -> 3072x1136'),
    (0x03f5ea4, 'e82500e3', 'e02300e3',
     'playback Crop frame: Crop frame 2688x1512 -> 2688x992'),
    (0x03f5eb4, '512ea0e3', '352ea0e3',
     'playback Crop frame: Crop frame 2304x1296 -> 2304x848'),
    (0x03f5ec4, '382400e3', 'c82200e3',
     'playback Crop frame: Crop frame 1920x1080 -> 1920x712'),
    (0x03ba7c8, 'a83c00e3', '503800e3',
     'playback camera-size check: native size 5760x3240 -> 5760x2128'),
    (0x03ba7fc, 'bd0e54e3', '1f0d54e3',
     'playback camera-size check: native size 5376x3024 -> 5376x1984'),
    (0x03ba820, 'f83a00e3', '303700e3',
     'playback camera-size check: native size 4992x2808 -> 4992x1840'),
    (0x03ba864, '483900e3', '183600e3',
     'playback camera-size check: native size 4224x2376 -> 4224x1560'),
    (0x03ba88c, '870e54e3', '590e54e3',
     'playback camera-size check: native size 3840x2160 -> 3840x1424'),
    (0x03ba8d8, 'e83500e3', 'e03300e3',
     'playback camera-size check: native size 2688x1512 -> 2688x992'),
    (0x03ba788, '510e54e3', '350e54e3',
     'playback camera-size check: native size 2304x1296 -> 2304x848'),
    (0x0df0dc8, '05010000', '05010000',
     'menu label "16:9" -> "XPan" (Czech, length)'),
    (0x0deed30, '310036003a00390000000000', '5800500061006e0000000000',
     'menu label "16:9" -> "XPan" (Czech, text)'),
    (0x0dfbc14, '05010000', '05010000',
     'menu label "16:9" -> "XPan" (Danish, length)'),
    (0x0dfbe44, '310036003a00390000000000', '5800500061006e0000000000',
     'menu label "16:9" -> "XPan" (Danish, text)'),
    (0x0e026c4, '05010000', '05010000',
     'menu label "16:9" -> "XPan" (English, length)'),
    (0x0e04cbc, '310036003a00390000000000', '5800500061006e0000000000',
     'menu label "16:9" -> "XPan" (English, text)'),
    (0x0e0d0e0, '05010000', '05010000',
     'menu label "16:9" -> "XPan" (Finnish, length)'),
    (0x0e12834, '310036003a00390000000000', '5800500061006e0000000000',
     'menu label "16:9" -> "XPan" (Finnish, text)'),
    (0x0e1a9a8, '05010000', '05010000',
     'menu label "16:9" -> "XPan" (French, length)'),
    (0x0e1abf8, '310036003a00390000000000', '5800500061006e0000000000',
     'menu label "16:9" -> "XPan" (French, text)'),
    (0x0e23834, '05010000', '05010000',
     'menu label "16:9" -> "XPan" (German, length)'),
    (0x0e25804, '310036003a00390000000000', '5800500061006e0000000000',
     'menu label "16:9" -> "XPan" (German, text)'),
    (0x0e2e4d0, '05010000', '05010000',
     'menu label "16:9" -> "XPan" (Greek, length)'),
    (0x0e32c4c, '310036003a00390000000000', '5800500061006e0000000000',
     'menu label "16:9" -> "XPan" (Greek, text)'),
    (0x0e39a48, '05010000', '05010000',
     'menu label "16:9" -> "XPan" (Hungarian, length)'),
    (0x0e39dd0, '310036003a00390000000000', '5800500061006e0000000000',
     'menu label "16:9" -> "XPan" (Hungarian, text)'),
    (0x0e43e34, '05010000', '05010000',
     'menu label "16:9" -> "XPan" (Italian, length)'),
    (0x0e435f0, '310036003a00390000000000', '5800500061006e0000000000',
     'menu label "16:9" -> "XPan" (Italian, text)'),
    (0x0e4c0c0, '05010000', '05010000',
     'menu label "16:9" -> "XPan" (Japanese, length)'),
    (0x0e4e1d4, '310036003a00390000000000', '5800500061006e0000000000',
     'menu label "16:9" -> "XPan" (Japanese, text)'),
    (0x0e543b0, '05010000', '05010000',
     'menu label "16:9" -> "XPan" (Korean, length)'),
    (0x0e4fd68, '310036003a00390000000000', '5800500061006e0000000000',
     'menu label "16:9" -> "XPan" (Korean, text)'),
    (0x0e58c34, '05010000', '05010000',
     'menu label "16:9" -> "XPan" (Dutch, length)'),
    (0x0e5a5dc, '310036003a00390000000000', '5800500061006e0000000000',
     'menu label "16:9" -> "XPan" (Dutch, text)'),
    (0x0e615ac, '05010000', '05010000',
     'menu label "16:9" -> "XPan" (Polish, length)'),
    (0x0e65e38, '310036003a00390000000000', '5800500061006e0000000000',
     'menu label "16:9" -> "XPan" (Polish, text)'),
    (0x0e6e3a0, '05010000', '05010000',
     'menu label "16:9" -> "XPan" (Portuguese, length)'),
    (0x0e6d948, '310036003a00390000000000', '5800500061006e0000000000',
     'menu label "16:9" -> "XPan" (Portuguese, text)'),
    (0x0e742c8, '05010000', '05010000',
     'menu label "16:9" -> "XPan" (Russian, length)'),
    (0x0e7d0f4, '310036003a00390000000000', '5800500061006e0000000000',
     'menu label "16:9" -> "XPan" (Russian, text)'),
    (0x0e806a4, '05010000', '05010000',
     'menu label "16:9" -> "XPan" (Chinese-S, length)'),
    (0x0e81d04, '310036003a00390000000000', '5800500061006e0000000000',
     'menu label "16:9" -> "XPan" (Chinese-S, text)'),
    (0x0e86cb8, '05010000', '05010000',
     'menu label "16:9" -> "XPan" (Spanish, length)'),
    (0x0e83618, '310036003a00390000000000', '5800500061006e0000000000',
     'menu label "16:9" -> "XPan" (Spanish, text)'),
    (0x0e91974, '05010000', '05010000',
     'menu label "16:9" -> "XPan" (Swedish, length)'),
    (0x0e94ee0, '310036003a00390000000000', '5800500061006e0000000000',
     'menu label "16:9" -> "XPan" (Swedish, text)'),
    (0x0e9f600, '05010000', '05010000',
     'menu label "16:9" -> "XPan" (Thai, length)'),
    (0x0e9ddfc, '310036003a00390000000000', '5800500061006e0000000000',
     'menu label "16:9" -> "XPan" (Thai, text)'),
    (0x0ea1430, '05010000', '05010000',
     'menu label "16:9" -> "XPan" (Chinese-T, length)'),
    (0x0ea1094, '310036003a00390000000000', '5800500061006e0000000000',
     'menu label "16:9" -> "XPan" (Chinese-T, text)'),
    (0x0ea6f98, '05010000', '05010000',
     'menu label "16:9" -> "XPan" (Turkish, length)'),
    (0x0ea653c, '310036003a00390000000000', '5800500061006e0000000000',
     'menu label "16:9" -> "XPan" (Turkish, text)'),
]

# The 16:9 aspect icon (ICONBIN section, 60x40 RGBA) repainted as "XPan".
ICON_OFFSET = 0x367e4c0
ICON_BYTES = 9600
ICON_OLD_SHA256 = '2aa121c9828a6654e60b75c843a868d7bb03b2e209d0b9d71cca6cdb5ee320fa'
ICON_NEW = (
    'eNrtms1PWkEQwPtPqRVsaKzgRxOtVUkUtJEqcrEnidZQKzGx8QtfE5tovCH2ZCONJfFMCcbEEqIF'
    'UUjUxHizBzXBD3TaGbsLDyilh5KH7iRz2Jl9L/vbj5lZHgDwAO6pDg8Pw13UXLwlJaV3SgWv4EUt'
    'dhG8+fEW2/4VvIJX8P6Zd2npE9lPTk5Ara7gdp/PR/b9/X0oLS2DlZUvsvhxeXkJkcgO2Gy2ouJt'
    'b+/gvoGB12SrqamFRCJBNkmSyJbOmyojIyNFtZ8jkQj5vF4vtaenJWpfXFyAVquT8R4eHkJfn5XW'
    'dXNzk2zHx8dQVvawaHjHxsbJd3V1RXw7O7vUXl1d5X0Y7/Z2hNuam1v4e5uamouGt7LyCcTj5+Rf'
    'Xnbzvj09lpy8+ByTrq5u2TtbWvTQ3W2ms5FqxxhRX99AqlKpQKfT0bNVVdqCxmePxyM7kyxO5ctr'
    'NveQraHhGYRCIW6/vr6mZ1UqNfktFgv3zc3Nwfn57TzH43Ho7X1VMF4cb6qwOJWLF/c+E6Oxnc5w'
    'LBbLGtPm5+czeG9ubmR9otFowXhxLXFNk3FKm5MX2XB9WG7SaB7T/mfidDqhs9MEW1vfqX10dJTB'
    '63Z/BpPJBOFwmNqYEwpZb7B4e3p6ChUVj7Ly4v7EXI1zkhy3m/o0Nj4Hu93+a0x2Hq8l6b2MJZW3'
    'o+OFLB9kG9//4tXr9bK9NTT0Nitvuvj9flrb1L44V5jX8Yy4XC4+T+m8ra1tZJucnCw478KCS8YR'
    'CASy8uK+xDW02d6AwWDMch+3w9nZWca8KIm3vFxFNQM7nyyWYH7NFa/Sta7uKZ1lFgPW19dhb29P'
    'cbxWq5X7DQYDZ3c6F/6Jd3BwkL/HZHpJtqkph+J4vd6vMpbFxY+/68QftPb58k5MJMedjFeSonhr'
    'a+v43cDhcJAN15hJf/9A3ryjo+/4c1hfYxzb2PimKN6ZmQ88X1RX13D77u5tDb22tpY3b1ubISNO'
    'sfpJCbxYYxwcHJAd77upPpYTcZxY6+bDizo7O0v3DpRgMEg1Cc4lxjEl5aO/KZ5jrPVZHZxLNRoN'
    'nRPxe47gFbyCV3xPEbzi+6/gvYu89+n/KvdBfwLw2Pur'
)

HEADER, MAGIC, FOOTER_MAGIC = 128, b'RICOH\0\0\0', b'\xa5\x5a\x5a\xa5'
MAX_DISTANCE = 0x2000
LITERAL_CHUNK = 0x6000


class Refused(Exception):
    pass


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def word_sum(data):
    if len(data) % 4:
        raise Refused('data is not 4-byte aligned')
    return sum(w for (w,) in struct.iter_unpack('<I', data)) & 0xffffffff


def decode(data, limit=256 * 1024 * 1024):
    if len(data) < 160 or data[:8] != MAGIC:
        raise Refused('not a RICOH firmware container')
    out = bytearray()
    frames = []
    cursor = HEADER
    while True:
        start = cursor
        if cursor + 2 > len(data):
            raise Refused('container: missing frame terminator')
        descriptor = int.from_bytes(data[cursor:cursor + 2], 'big')
        cursor += 2
        if descriptor == 0:
            return bytes(out), frames, cursor
        size = descriptor & 0x7fff
        end = cursor + size
        if not size or end > len(data):
            raise Refused(f'container: invalid frame at {start:#x}')
        output_start = len(out)
        if descriptor & 0x8000:
            out += data[cursor:end]
            cursor = end
        else:
            while cursor < end:
                if cursor + 2 > end:
                    raise Refused(f'container: truncated flags at {cursor:#x}')
                flags = int.from_bytes(data[cursor:cursor + 2], 'big')
                cursor += 2
                for bit in range(15, -1, -1):
                    if cursor == end:
                        break
                    if not flags & (1 << bit):
                        out.append(data[cursor])
                        cursor += 1
                        continue
                    if cursor + 2 > end:
                        raise Refused('container: truncated reference')
                    a, b = data[cursor], data[cursor + 1]
                    cursor += 2
                    distance = ((a >> 3) << 8) | b
                    length = a & 7
                    if length == 7:
                        while True:
                            if cursor >= end:
                                raise Refused('container: truncated length')
                            extension = data[cursor]
                            cursor += 1
                            length += extension
                            if extension != 255:
                                break
                    if distance == 0:
                        break
                    if distance > len(out):
                        raise Refused('container: reference before start of output')
                    count = length + 3
                    if distance >= count:
                        out += out[-distance:len(out) - distance + count]
                    else:
                        pattern = bytes(out[-distance:])
                        out += (pattern * ((count + distance - 1) // distance))[:count]
                if len(out) > limit:
                    raise Refused('container: decoded size limit exceeded')
        frames.append((start, end, output_start, len(out)))


def check_container(data, payload=None, consumed=None):
    if payload is None:
        payload, _, consumed = decode(data)
    if data[-20:-16] != FOOTER_MAGIC:
        raise Refused('container: footer magic missing')
    enc, dec = struct.unpack_from('<II', data, len(data) - 12)
    if enc != consumed - HEADER or dec != len(payload):
        raise Refused('container: size fields do not match the content')
    if word_sum(data) or word_sum(payload):
        raise Refused('container: checksum mismatch')
    return payload


def sections(payload):
    out, pos = [], 0
    while pos + 16 <= len(payload):
        tag = payload[pos:pos + 8].rstrip(b'\0')
        if not tag or not tag.isalnum() or not tag.isupper():
            break
        size = struct.unpack_from('<I', payload, pos + 12)[0]
        if pos + 16 + size > len(payload):
            break
        out.append((tag.decode(), pos + 16, pos + 16 + size))
        pos += 16 + size
    return out


def differences(a, b, block=1 << 16):
    if len(a) != len(b):
        raise Refused('length mismatch')
    out = []
    for pos in range(0, len(a), block):
        x, y = a[pos:pos + block], b[pos:pos + block]
        if x != y:
            out += [pos + i for i in range(len(x)) if x[i] != y[i]]
    return out


def rezero(payload):
    buf = bytearray(payload)
    last = struct.unpack_from('<I', buf, len(buf) - 4)[0]
    struct.pack_into('<I', buf, len(buf) - 4, (last - word_sum(buf)) & 0xffffffff)
    return bytes(buf)


def literal_frames(data):
    out = bytearray()
    for pos in range(0, len(data), LITERAL_CHUNK):
        chunk = data[pos:pos + LITERAL_CHUNK]
        out += struct.pack('>H', 0x8000 | len(chunk)) + chunk
    return bytes(out)


def rebuild(source, frames, consumed, patched, changed):
    body = bytearray()
    reemitted = 0
    for (c0, c1, d0, d1) in frames:
        if any(d0 <= c < d1 or c < d0 < c + MAX_DISTANCE for c in changed):
            body += literal_frames(patched[d0:d1])
            reemitted += 1
        else:
            body += source[c0:c1]
    body += b'\0\0'
    trailer = bytearray(source[consumed:])
    struct.pack_into('<II', trailer, len(trailer) - 12, len(body), len(patched))
    struct.pack_into('<I', trailer, len(trailer) - 4, 0)
    padding = bytes((-HEADER - len(body) - len(trailer)) % 4)
    out = bytearray(source[:HEADER] + body + padding + trailer)
    struct.pack_into('<I', out, len(out) - 4, (-word_sum(out)) & 0xffffffff)
    return bytes(out), reemitted


def patch(source, log=print):
    digest = sha256(source)
    if digest != OFFICIAL_SHA256 or len(source) != OFFICIAL_BYTES:
        if digest == UNLOCKED_SHA256:
            raise Refused('this file already has XPan; use the official RICOH file')
        if digest in OTHER_KNOWN:
            raise Refused(f'this file is {OTHER_KNOWN[digest]}; use the official RICOH file')
        raise Refused('input is not the official RICOH GR IV 1.11 fwdc248b.bin '
                      f'(SHA-256 {digest}, expected {OFFICIAL_SHA256})')
    log('input: official RICOH GR IV 1.11 firmware (SHA-256 verified)')

    log('decoding container ...')
    payload, frames, consumed = decode(source)
    check_container(source, payload, consumed)
    secs = sections(payload)
    rtos = next((s for s in secs if s[0] == 'RTOS'), None)
    iconbin = next((s for s in secs if s[0] == 'ICONBIN'), None)
    if rtos is None or iconbin is None:
        raise Refused('payload: RTOS or ICONBIN section not found')

    buf = bytearray(payload)
    items = CHANGES
    for off, old, new, what in items:
        old, new = bytes.fromhex(old), bytes.fromhex(new)
        have = bytes(buf[off:off + len(old)])
        if have != old:
            raise Refused(f'unexpected original bytes at {off:#x}: {have.hex()} (expected {old.hex()})')
        if not (rtos[1] <= off and off + len(new) <= rtos[2]):
            raise Refused(f'change at {off:#x} is outside the RTOS section')
        buf[off:off + len(new)] = new
        log(f'  {off:#09x}  {what}')
    icon = zlib.decompress(base64.b64decode(''.join(ICON_NEW)))
    if len(icon) != ICON_BYTES or not (iconbin[1] <= ICON_OFFSET and ICON_OFFSET + ICON_BYTES <= iconbin[2]):
        raise Refused('icon data is damaged or outside the ICONBIN section')
    if sha256(bytes(buf[ICON_OFFSET:ICON_OFFSET + ICON_BYTES])) != ICON_OLD_SHA256:
        raise Refused(f'unexpected original icon at {ICON_OFFSET:#x}')
    buf[ICON_OFFSET:ICON_OFFSET + ICON_BYTES] = icon
    log(f'  {ICON_OFFSET:#09x}  aspect icon "16:9" -> "XPan" (60x40)')
    patched = rezero(bytes(buf))

    log('rebuilding container ...')
    changed = differences(payload, patched)
    out, reemitted = rebuild(source, frames, consumed, patched, changed)

    log('verifying result ...')
    again, _, used = decode(out)
    if again != patched:
        raise Refused('verification: rebuilt container does not decode to the patched firmware')
    check_container(out, again, used)
    if out[:HEADER] != source[:HEADER]:
        raise Refused('verification: header changed')
    allowed = {i for off, old, _, _ in items for i in range(off, off + len(bytes.fromhex(old)))}
    allowed |= set(range(ICON_OFFSET, ICON_OFFSET + ICON_BYTES))
    allowed |= set(range(len(payload) - 4, len(payload)))
    stray = [i for i in changed if i not in allowed]
    if stray:
        raise Refused(f'verification: unexpected changes at {[hex(i) for i in stray[:8]]}')
    if [s for s in sections(again)] != secs:
        raise Refused('verification: section layout changed')
    if sha256(out) != UNLOCKED_SHA256:
        raise Refused('verification: result differs from the research-verified image '
                      f'(got {sha256(out)}, expected {UNLOCKED_SHA256})')
    log(f'verified: {len(changed)} payload bytes changed, {reemitted} frames re-encoded, '
        f'only RTOS and ICONBIN changed, SHA-256 matches the verified build')
    return out


def write_atomic(data, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / 'fwdc248b.bin'
    if target.exists():
        raise Refused(f'{target} already exists; choose another output directory or remove it')
    tmp = target.with_name('.fwdc248b.bin.tmp')
    tmp.write_bytes(data)
    if sha256(tmp.read_bytes()) != sha256(data):
        tmp.unlink()
        raise Refused('write verification failed')
    tmp.rename(target)
    return target


def identify(data, log=print):
    digest = sha256(data)
    names = {OFFICIAL_SHA256: 'official RICOH GR IV 1.11 (unmodified)',
             UNLOCKED_SHA256: f'GR4-XPanUnlock {VERSION} (16:9 replaced by XPan)', **OTHER_KNOWN}
    log(f'SHA-256  {digest}')
    log(f'bytes    {len(data)}')
    log(f'file     {names.get(digest, "unknown - not produced by this tool and not the official 1.11 file")}')
    try:
        check_container(data)
        log('container: valid (size fields, footer, both checksums)')
    except Refused as exc:
        log(f'container: INVALID - {exc}')
        return 2
    return 0 if digest in names else 1


def main(argv=None):
    ap = argparse.ArgumentParser(prog='gr4_xpanunlock.py', description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--version', action='version', version=VERSION)
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('patch', help='make the XPan firmware from the official file')
    p.add_argument('input', type=Path, help='official RICOH fwdc248b.bin (GR IV 1.11)')
    p.add_argument('-o', '--output-dir', type=Path, default=Path('output'),
                   help='directory for the result (default: ./output); the file is named fwdc248b.bin')
    c = sub.add_parser('check', help='identify a fwdc248b.bin and validate its container')
    c.add_argument('input', type=Path)
    a = ap.parse_args(argv)
    sys.stdout.reconfigure(line_buffering=True)
    if sys.version_info < (3, 8):
        print('Python 3.8 or newer is required', file=sys.stderr)
        return 2
    try:
        data = a.input.read_bytes()
        if a.cmd == 'check':
            return identify(data)
        if (a.output_dir / 'fwdc248b.bin').exists():
            raise Refused(f'{a.output_dir / "fwdc248b.bin"} already exists; '
                          'choose another output directory or remove it')
        print(f'GR4-XPanUnlock {VERSION}')
        out = patch(data)
        target = write_atomic(out, a.output_dir)
        print(f'wrote {target}  (SHA-256 {sha256(out)})')
        print('Copy this file to the root of the SD card and run the camera\'s firmware update.')
        return 0
    except Refused as exc:
        print(f'refused: {exc}', file=sys.stderr)
        print('nothing was written.', file=sys.stderr)
        return 1
    except OSError as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())