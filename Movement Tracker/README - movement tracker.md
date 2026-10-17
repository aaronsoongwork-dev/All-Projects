# FoodAllCam – Staff Identification

Finds the staff member in an overhead fisheye video and reports where they are.

- **Task 1:** which frames contain the staff member?
- **Task 2:** what are the staff member's (x, y) coordinates when present?

## Why not detect the name tag?

The staff member wears a small white name tag with a black "piano-key" stripe pattern. In the sample clip the tag is only a few pixels wide and the camera looks down, so the chest tag is rarely visible. Direct tag detection (template matching, OCR, or a trained detector) is not reliable here.

Instead, this project uses a **proxy**: the staff member is assumed to be the person who keeps walking through the scene, while most other people are seated. The method is colour-agnostic and does not need a GPU.

## How it works

1. **Find moving things, any colour.** Each frame is compared with one 4 frames earlier and one 4 frames later (about 0.16 s at 25 fps), and also with a median background. A pixel counts only if it changed in all of these, so seated people are ignored and clothing colour does not matter.
2. **Group movement into short paths.** Person-sized moving shapes are linked from frame to frame with a strict jump limit, so a path does not hop between two people.
3. **Pick the anchor.** The short path with the longest walked distance is taken as the staff member.
4. **Join paths across the clothing change.** Earlier and later short paths are attached to the anchor if they start close in space (within 90 px) and time (within 8 s). The person is followed by position and time, not colour, so a change such as light shirt to dark coat is bridged.
5. **Fill small gaps.** Short dropouts and the gaps between joined paths are filled by linear interpolation and flagged `interp` in the CSV (orange box in the video).
6. **Write the output.** Per-frame presence and position, an annotated video, a timeline and a trajectory image.

## Requirements

- Python 3
- `opencv-python`
- `numpy`

```bash
pip install opencv-python numpy
```

## Usage

```bash
python staff_detect.py input.mp4 [out_dir]
```

`out_dir` defaults to `out`. It runs on a laptop CPU, with the video processed at 480x360.

## Output

| File | Contents |
|---|---|
| `staff_frames.csv` | One row per frame: `frame, time_s, staff_present, x, y, source` |
| `staff_annotated.mp4` | Original video with a box, centre dot, recent trail and a STAFF / no staff label |
| `timeline.png` | Strip over the whole clip: dark = present, grey = estimated, white = absent |
| `trajectory.jpg` | One frame with the full path drawn as dots, coloured by time (blue to red) |

Notes on the CSV:

- `staff_present` is 1 or 0. `x` and `y` are empty when it is 0.
- `x`, `y` are the centre of the bounding box in the **original video pixels** (for example 960x720), not the 480x360 working size.
- `source` is `tracked` for a real detection and `interp` for an estimated position.

In the annotated video, a green box is a real detection and an orange box is an estimate.

## Parameters

Set at the top of `staff_detect.py`:

| Name | Default | Meaning |
|---|---|---|
| `W, H` | 480, 360 | Working resolution |
| `K` | 4 | Frame offset for motion comparison |
| `MOTION_T` | 22 | Grey-level change needed to count as motion |
| `BG_T` | 30 | Difference from background needed |
| `MIN_A, MAX_A` | 350, 9000 | Person-sized area range (working pixels) |
| `MAX_JUMP` | 25 | Max movement between frames (px) |
| `MAX_GAP` | 25 | Frames a path survives without a match |
| `MIN_FRAMES, MIN_PATH` | 12, 60 | Minimum length and distance of a usable short path |
| `LINK_DIST` | 90 | Max distance to join two short paths (px) |
| `LINK_TIME` | 8.0 | Max time gap to join two short paths (s) |

## Limitations

- **This is a proxy, not tag verification.** It assumes the staff member is the sustained walker.
- When several people walk at once, it can follow the wrong person or merge them, so presence may be over-estimated in those moments.
- Only one person is followed: the longest walked path becomes the seed, and other walkers are ignored.
- A staff member who stays still for a long time is not detected, because the method relies on motion.
- Interpolated positions are straight-line guesses and are less reliable than tracked ones, especially over long gaps.
- Pixel positions come from a fisheye view and are not converted to floor coordinates.
- There is no ground truth, so no accuracy figure is reported. Results were checked visually on the annotated video.

## Future work with the full dataset

1. Label staff and non-staff crops and fine-tune a person detector (YOLO or RT-DETR) on overhead fisheye views.
2. Train a small tag classifier on upsampled person crops, using the tag's high-contrast stripe pattern. Pool its score over a track, since the tag is only visible in some frames.
3. Add appearance features (ReID) so identity survives occlusion, and de-warp the fisheye to a ground plane to get positions in metres.
4. Evaluate on a held-out set with frame-level precision and recall and localisation error.

## Files

- `staff_detect.py` – the code
