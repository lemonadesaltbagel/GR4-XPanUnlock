# GR4-XPanUnlock

**An XPan (65:24) panoramic aspect ratio for your RICOH GR IV.**

GR4-XPanUnlock adds **XPan**, the 65:24 panoramic frame of the classic 35 mm
panorama cameras, to the GR IV as a **fifth aspect ratio**, next to 3:2, 4:3,
1:1 and 16:9. It works like a native ratio: focus stays inside the picture,
JPEGs are saved at XPan size, Instant Review shows the XPan frame, and RAW
Development and Crop offer it too. In live view, the cropped ratios show the
**whole frame**, with the area outside the crop dimmed, like a rangefinder's
open viewfinder. Everything else on your camera stays exactly as it was, and
you can go back to the official firmware at any time.

This repository contains no RICOH firmware. You download the official firmware
from RICOH yourself; the included tool turns it into the XPan version on your
own computer.

> **Unofficial, at your own risk.** Not made or endorsed by RICOH IMAGING.
> Installing modified firmware may void your warranty. Please read
> [Before you start](#before-you-start) and [Risks](#risks) first.

## What's new in 2.0.0

- **16:9 is back.** XPan is now an extra ratio instead of a replacement, so
  you can shoot 16:9 and XPan on the same firmware.
- **Both have their own icon.** 16:9 shows its original icon again; XPan has
  its own "XPan" icon everywhere it appears.
- **RAW Development** offers XPan as its own choice, next to 16:9.
- **Crop** (playback trimming) offers XPan as its own ratio, next to 16:9.
- **Instant Review** shows an XPan picture in its XPan frame.
- Older 16:9 pictures on the card are recognised as 16:9 again.
- Updating from 1.x? See [Updating from 1.x](#updating-from-1x).

## What you get

In the aspect ratio setting (menu, ADJ and the Fn/dial shortcut), **XPan
appears after 16:9**, with its own "XPan" label (in every menu language) and
icon. The shortcut cycles 3:2 → 4:3 → 1:1 → 16:9 → XPan.

| Crop / size | XPan image size |
| --- | --- |
| Full frame (28 mm), L | 6192 × 2288 |
| 35 mm crop, or size M | 4944 × 1824 |
| 50 mm crop, or size S | 3504 × 1296 |
| Size XS | 1920 × 712 |

- **Live view** shows the whole frame. Outside the crop the scene is dimmed by
  half, with a thin white line at each crop edge, so you can see what is about
  to enter the picture. Everything between the lines is what the picture
  contains. **16:9, 4:3 and 1:1** work the same way. The status icons stay on
  top of the dimmed area. 3:2 is unchanged.
- **Focus** stays inside the picture: the focus frame can be placed anywhere
  inside both the camera's focus limits and the crop, right up to the lines,
  but never in the dimmed area (by buttons or by touch). Auto-area AF covers
  the whole XPan band.
- **Instant Review** shows the picture you just took in its XPan frame.
- **RAW (DNG)** files keep the full sensor image, exactly as with the native
  ratios. Their crop information marks the XPan frame, so RAW converters open
  them at XPan, and you can still widen the crop later.
- **RAW Development** in the camera: a 3:2 RAW can be developed to 3:2, 4:3,
  1:1, 16:9 or XPan; a 16:9 or XPan RAW to 16:9 or XPan.
- **Crop** (in-camera trimming of JPEGs in playback) offers XPan frames, from
  6192 × 2288 down to 1920 × 712, next to the 16:9 frames.
- The menu's image-size readout shows the XPan size.
- Pictures in 3:2, 4:3, 1:1 and 16:9, playback and movie recording are
  unchanged.

## Before you start

- **Camera:** RICOH GR IV (the standard colour model). Other models are not
  supported.
- **Your camera must already be on firmware 1.11.** Check the version in the
  camera's setup menu.
  - Older version: first update to 1.11 the normal way, with RICOH's official file.
  - Newer version: **do not use this tool.** It only supports 1.11.
- **A fully charged battery.** A firmware update must never lose power.
- **An SD card** you can format.
- **A computer with Python 3.8 or newer.** macOS and most Linux systems already
  have it; on Windows, install it from python.org. Nothing else is needed.
- Note down any custom settings (C1, C2, …) you would not want to set up again.

## Install

### 1. Download the official firmware

From RICOH IMAGING's official GR IV support page, download **firmware
version 1.11**. Unpack it if needed until you have the file **`fwdc248b.bin`**.

### 2. Make the XPan firmware

Open a terminal in this folder and run (use the path where you saved the
official file):

```sh
python3 gr4_xpanunlock.py patch ~/Downloads/fwdc248b.bin
```

On Windows:

```bat
py gr4_xpanunlock.py patch C:\Users\you\Downloads\fwdc248b.bin
```

The tool first makes sure you gave it the genuine official 1.11 file, then
creates the XPan firmware and checks it. When everything is right, it ends
with:

```
wrote output/fwdc248b.bin  (SHA-256 aa9ac5dbb05d0e362019b78c678ac322fe9b6786d980cafe1846bf191f739cb0)
```

If something is wrong (for example a different firmware version, an already
modified file, or a damaged download), it prints `refused: …` and writes
**nothing**.

### 3. Copy it to the SD card

1. **Format the SD card in the camera.**
2. Copy **`output/fwdc248b.bin`** to the **top level** of the card: not into a
   folder, and keep the name exactly `fwdc248b.bin`.

### 4. Update the camera

1. Insert the fully charged battery and the SD card.
2. Start the firmware update from the camera's setup menu, as described in
   RICOH's official GR IV firmware update instructions.
3. **The camera shows an update from version 1.11 to version 1.11.** This is
   expected — the XPan firmware keeps the version number. Confirm the update.
4. **Do not turn the camera off, open the battery or card door, or remove the
   card** until the update has finished and the camera has restarted.

### 5. Enjoy

- Set the aspect ratio to **XPan** (after 16:9).
- The firmware version still shows **1.11** — that is normal.
- Delete `fwdc248b.bin` from the card (or format the card) so the update is not
  started again by accident.

## Updating from 1.x

Make the 2.0.0 file from the **official** RICOH `fwdc248b.bin`, exactly as in
[Install](#install), and install it the same way. There is no need to go back to
the official firmware first. The tool refuses a 1.x XPan file as input, so
always start from RICOH's file.

After the update, a camera that was set to XPan on 1.x shows **16:9**, because
1.x used the 16:9 slot for XPan. Select **XPan** again (also in C1, C2, … if you
saved it there).

## Going back to the official firmware

1. **First set the aspect ratio to anything other than XPan**, for example
   3:2, and do the same in every custom mode (C1, C2, …) that uses XPan. The
   official firmware has no XPan setting.
2. Then repeat steps 3–5 with the **official** `fwdc248b.bin` from RICOH
   instead. The camera again shows **1.11 → 1.11**; confirm it, and your camera
   is back to stock.

## Good to know

- **The camera files XPan pictures under 16:9 internally.** You will notice this
  in a few places:
  - RAW Development of an XPan RAW starts at 16:9; select XPan.
  - Playback editing other than Crop (for example Resize) has not been
    specifically tested on XPan pictures.
  - Exposure and white-balance metering for an XPan picture covers the 16:9
    area around it. In practice the difference is small.
- **MF and Snap focus** keep their fixed focus area, which can extend over the
  dimmed area. This does not affect where the camera focuses in those modes.
- **Live-view brightness** is measured over the whole frame rather than only
  the crop, so with a very bright or dark sky outside the band, exposure may
  differ slightly from what you expect.
- **Face detection** has not been specifically tested in XPan.
- **GR4-MonoUnlock and GR4-XPanUnlock cannot be installed together.** Each tool
  starts from the official firmware, and this tool refuses a MonoUnlock file.
- **An official RICOH update removes XPan.** It replaces the whole firmware. Set
  a ratio other than XPan first (see
  [Going back](#going-back-to-the-official-firmware)). This tool only supports
  1.11; do not use it with another version.
- **Before sending the camera for service,** go back to the official firmware.
- To check any firmware file before copying it to a card:

  ```sh
  python3 gr4_xpanunlock.py check path/to/fwdc248b.bin
  ```

  It tells you whether the file is the official 1.11, the XPan version made by
  this tool (2.0.0, or an older 1.x), or something else.

## Risks

- Your camera cannot tell a good firmware file from a damaged one. Only copy a
  file the tool has written (or confirmed with `check`) to your card.
- If an update is interrupted, or a firmware file cannot start, the camera may
  not reach the update function again, and it would then need RICOH service.
  This did not happen in testing, but it cannot be ruled out.
- Going back to the official firmware while XPan is still selected has not
  been tested. Set another ratio first.
- Your camera's own calibration data is not touched.

## How it works

The GR IV's menus, picture processing, live view, RAW Development and Crop are
all built around four aspect ratios. The tool adds XPan as a fifth menu entry,
which the camera handles as a variant of 16:9. At each point where the shape of
a picture is decided (image size, RAW crop, preview, Instant Review, focus
limits, live-view marks, Crop frames), a small added routine gives XPan its own
values and leaves the other ratios exactly as they were.

The new routines are written over code the camera never runs, and they only
read from the firmware, never write to it. The XPan icon is stored in space
freed by an icon the firmware happens to keep twice. All changes are made in
place, so no code moves and every size and address in the firmware stays the
same. Each change is listed with a short description in `gr4_xpanunlock.py`.

## Testing status

| What | Status |
| --- | --- |
| Update accepted, camera starts | tested on a GR IV 1.11 |
| Five-ratio menu, XPan label and icon, 16:9 with its own icon | tested on a GR IV 1.11 |
| 16:9 and XPan pictures saved at their own sizes, also after switching between them | tested on a GR IV 1.11 |
| Instant Review in the XPan frame | tested on a GR IV 1.11 |
| RAW Development with XPan and 16:9 | tested on a GR IV 1.11 |
| Crop (playback trimming) with XPan and 16:9 | tested on a GR IV 1.11 |
| Open-gate live view with crop marks; status icons readable on top | tested on a GR IV 1.11 |
| No marks in playback; 3:2 live view unchanged | tested on a GR IV 1.11 |
| Focus limited to the crop, up to the boundary lines | tested on a GR IV 1.11 |
| Framing grid on and off with the crop marks | not yet tested; please report your results |
| Saved JPEG and DNG sizes match the table above | verified by firmware emulation; please report your results |
| Going back to the official 1.11 restores the camera completely | tested from 1.x on a GR IV 1.11; from 2.0.0 not yet tested |
| The tool reproduces the tested firmware exactly | tested |

## Files

```
GR4-XPanUnlock/
├── README.md            this guide
└── gr4_xpanunlock.py    the tool
```

| File | SHA-256 |
| --- | --- |
| official RICOH GR IV 1.11 `fwdc248b.bin` | `a2f664dfca034059eb0fd6e18ab08684c326b4a034d85c164dad7e1ec9b5655f` |
| XPan `fwdc248b.bin` made by this tool (2.0.0) | `aa9ac5dbb05d0e362019b78c678ac322fe9b6786d980cafe1846bf191f739cb0` |
| XPan `fwdc248b.bin` made by 1.1.0 (16:9 replaced by XPan) | `4534d44297b69bb6d305bac2ad62fef98b0caf7a6558d6da36c049dbb88f80c8` |
| XPan `fwdc248b.bin` made by 1.0.0 (16:9 replaced, letterboxed live view) | `fa2c67d1b67e16675a0c75b98d58c519b803f049a00e40e34103e54ca9a6a6c7` |
