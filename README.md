# GR4-XPanUnlock

**An XPan (65:24) panoramic aspect ratio for your RICOH GR IV.**

GR4-XPanUnlock replaces the GR IV's **16:9** aspect ratio with **XPan**, the
65:24 panoramic frame of the classic 35 mm panorama cameras. It works like a native
ratio: focus stays inside the picture, JPEGs are saved at XPan size, and RAW
Development offers it too. In live view, XPan, 4:3 and 1:1 show the **whole
frame**, with the area outside the crop dimmed, like a rangefinder's open
viewfinder. Everything else on your camera stays exactly as it was, and you can
go back to the official firmware at any time.

This repository contains no RICOH firmware. You download the official firmware
from RICOH yourself; the included tool turns it into the XPan version on your
own computer.

> **Unofficial, at your own risk.** Not made or endorsed by RICOH IMAGING.
> Installing modified firmware may void your warranty. Please read
> [Before you start](#before-you-start) and [Risks](#risks) first.

## What's new in 1.1.0

- **Open-gate live view in the crop ratios.** XPan, 4:3 and 1:1 no longer black
  out the area outside the crop. Live view shows the whole 3:2 frame; the part
  that will not be in the picture is dimmed, with a thin white line at the crop
  edge, the same style as the camera's own Crop screen. 3:2 is unchanged.
- Pictures, RAW files, focus limits and everything else are the same as 1.0.0.
- Already on 1.0.0? See [Updating from 1.0.0](#updating-from-100).

## What you get

In the aspect ratio setting (menu and ADJ), **16:9 is replaced by XPan**, with
its own "XPan" label (in every menu language) and icon.

| Crop / size | XPan image size |
| --- | --- |
| Full frame (28 mm), L | 6192 × 2288 |
| 35 mm crop, or size M | 4944 × 1824 |
| 50 mm crop, or size S | 3504 × 1296 |
| Size XS | 1920 × 712 |

- **Live view** shows the whole frame. Above and below the XPan band the
  scene is dimmed by half, with a thin white line at each crop edge, so you can
  see what is about to enter the picture. Everything between the lines is what
  the picture contains. **4:3 and 1:1** work the same way, dimmed at the left
  and right. The status icons stay on top of the dimmed area.
- **Focus** stays inside the picture: the focus frame can be placed anywhere
  inside both the camera's focus limits and the crop, right up to the lines,
  but never in the dimmed area (by buttons or by touch). Auto-area AF covers
  the whole XPan band.
- **Exposure and white balance** metering for the picture covers the XPan band.
- **RAW (DNG)** files keep the full sensor image, exactly as with the native
  ratios. Their crop information marks the XPan frame, so RAW converters open
  them at XPan, and you can still widen the crop later.
- **RAW Development** in the camera offers XPan.
- **Crop** (in-camera trimming of JPEGs in playback) offers XPan frames, from
  6192 × 2288 down to 1920 × 712.
- Pictures in 3:2, 4:3 and 1:1, the 3:2 live view, playback and movie recording
  are unchanged.

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
wrote output/fwdc248b.bin  (SHA-256 4534d44297b69bb6d305bac2ad62fef98b0caf7a6558d6da36c049dbb88f80c8)
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

- Set the aspect ratio to **XPan** (where 16:9 used to be).
- The firmware version still shows **1.11** — that is normal.
- Delete `fwdc248b.bin` from the card (or format the card) so the update is not
  started again by accident.

## Updating from 1.0.0

Make the 1.1.0 file from the **official** RICOH `fwdc248b.bin`, exactly as in
[Install](#install), and install it the same way. There is no need to go back to
the official firmware first. The tool refuses a 1.0.0 XPan file as input, so
always start from RICOH's file.

## Going back to the official firmware

Repeat steps 3–5 with the **official** `fwdc248b.bin` from RICOH instead. The
camera again shows **1.11 → 1.11**; confirm it, and your camera is back to stock
with 16:9 restored.

## Good to know

- **XPan replaces 16:9; it is not added as a fifth ratio.** While this firmware
  is installed, still photos cannot be taken in 16:9. Movies are not affected.
- **Older 16:9 pictures** on the card still display normally, but the camera now
  treats them as 3:2 in playback, so some in-camera editing options may differ
  for them.
- **MF and Snap focus** keep their fixed focus area, which can extend over the
  dimmed area. This does not affect where the camera focuses in those modes.
- **Live-view brightness** is now measured over the whole frame rather than only
  the XPan band, so with a very bright or dark sky outside the band, XPan
  exposure may differ slightly from 1.0.0.
- **Face detection** has not been specifically tested in XPan.
- **GR4-MonoUnlock and GR4-XPanUnlock cannot be installed together.** Each tool
  starts from the official firmware, and this tool refuses a MonoUnlock file.
- **An official RICOH update removes XPan.** It replaces the whole firmware. This
  tool only supports 1.11; do not use it with another version.
- **Before sending the camera for service,** go back to the official firmware.
- To check any firmware file before copying it to a card:

  ```sh
  python3 gr4_xpanunlock.py check path/to/fwdc248b.bin
  ```

  It tells you whether the file is the official 1.11, the XPan version made by
  this tool (1.1.0, or the older 1.0.0), or something else.

## Risks

- Your camera cannot tell a good firmware file from a damaged one. Only copy a
  file the tool has written (or confirmed with `check`) to your card.
- If an update is interrupted, or a firmware file cannot start, the camera may
  not reach the update function again, and it would then need RICOH service.
  This did not happen in testing, but it cannot be ruled out.
- Your camera's own calibration data is not touched.

## How it works

The GR IV already handles four aspect ratios. The tool takes over every setting
the camera keeps for 16:9 and gives it XPan values instead: image sizes, RAW
crop, preview and thumbnail placement, metering area, focus limits, Crop
frames, playback recognition, the menu label and the icon.

For the open-gate live view, the cropped ratios borrow the 3:2 live-view
geometry, so the whole frame is shown while pictures are still saved at their
own ratio. A small drawing routine then dims the outside of the crop and draws
the boundary lines, under the camera's own on-screen display. It is hooked into
the live-view framing grid, so it never appears in playback. The routine is
written over code the camera never runs, and it only reads from the firmware,
never writes to it.

All 260 changes are made in place, so no code moves and every size and address
in the firmware stays the same. Each change is listed with a short description
in `gr4_xpanunlock.py`.

## Testing status

| What | Status |
| --- | --- |
| Update accepted, camera starts, XPan label and icon shown | tested on a GR IV 1.11 |
| RAW Development with XPan | tested on a GR IV 1.11 |
| Open-gate live view in XPan, 4:3 and 1:1 (dimmed outside, boundary lines) | tested on a GR IV 1.11 |
| Crop marks persist; status icons stay readable on top of the dimmed area | tested on a GR IV 1.11 |
| Framing grid on and off with the crop marks | not yet tested; please report your results |
| No lines or dimming in playback; 3:2 live view unchanged | tested on a GR IV 1.11 |
| Focus limited to the crop, up to the boundary lines | tested on a GR IV 1.11 |
| Live-view exposure in XPan compared with 1.0.0 | not yet compared; please report your results |
| Going back to the official 1.11 restores the camera completely | tested on a GR IV 1.11 (same update method) |
| Saved JPEG and DNG sizes match the table above | verified by firmware emulation; please report your results |
| Crop (playback trimming) to XPan | tested on a GR IV 1.11 |
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
| XPan `fwdc248b.bin` made by this tool (1.1.0) | `4534d44297b69bb6d305bac2ad62fef98b0caf7a6558d6da36c049dbb88f80c8` |
| XPan `fwdc248b.bin` made by 1.0.0 (letterboxed live view) | `fa2c67d1b67e16675a0c75b98d58c519b803f049a00e40e34103e54ca9a6a6c7` |
