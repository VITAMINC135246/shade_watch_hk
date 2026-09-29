"""Run an independent, CPU-only Shade Watch reconstruction for HKUST.

Entry point: .venv/bin/python -m src.shade_watch
"""

from __future__ import annotations

import hashlib
import json
import math
import platform
import re
import sys
import threading
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import imageio as imageio_pkg
import imageio.v2 as imageio
import numpy as np
import psutil
import pyproj
import rasterio
import scipy
from PIL import Image, ImageDraw, ImageFont, PngImagePlugin
from pyproj import Transformer
from rasterio.merge import merge
from rasterio.transform import from_origin

from .horizon import direct_ray_reference, horizon_at_output, pixel_centred_horizon
from .solar import HKT, daylight_bounds, daylight_samples, position

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/dsm/2020/D12.DSM.TIFF"
OUT = ROOT / "outputs/600x450"
RESOLUTION = 0.5
OUTPUT_WIDTH_M = 600.0
OUTPUT_HEIGHT_M = 450.0
BUFFER_M = 1000.0
OUTPUT_WIDTH_PX = round(OUTPUT_WIDTH_M / RESOLUTION)
OUTPUT_HEIGHT_PX = round(OUTPUT_HEIGHT_M / RESOLUTION)
BUFFER_PX = round(BUFFER_M / RESOLUTION)
NODATA = 255
PAPER_AZIMUTHS = set(range(40, 321, 5))
COLORS = {0: (255, 255, 255), 1: (0, 0, 0), 255: (160, 160, 160)}
SOURCE_OWNER = "Government of the Hong Kong Special Administrative Region"
SOURCE_LINE = "CEDD 2020 LiDAR DSM; source and data owner: " + SOURCE_OWNER


def parse_coordinate(value: str) -> float:
    """Accept user-entered decimal degrees or DMS; preserve the source text."""
    value = value.strip().strip("[]")
    direction = -1 if re.search(r"\b(south|west|[SW])\b", value, re.I) else 1
    numbers = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", value)]
    if not numbers:
        raise ValueError(f"Missing coordinate: {value!r}")
    if len(numbers) == 1:
        return float(value) if value.replace(".", "", 1).lstrip("+-").isdigit() else direction * numbers[0]
    if len(numbers) != 3 or numbers[1] >= 60 or numbers[2] >= 60:
        raise ValueError(f"Expected DMS degrees, minutes, seconds: {value!r}")
    return direction * (numbers[0] + numbers[1] / 60 + numbers[2] / 3600)


def load_study_area() -> dict:
    text = (ROOT / "config/study_area.md").read_text()
    def field(label: str) -> str:
        found = re.search(rf"^- {re.escape(label)}[^\n]*?:\s*(.+?)\s*$", text, re.M)
        if not found:
            raise ValueError(f"Missing study-area field: {label}")
        return found.group(1).strip()
    latitude = parse_coordinate(field("Centre latitude"))
    longitude = parse_coordinate(field("Centre longitude"))
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError("Study-area coordinates are outside WGS84 limits")
    raw_date = field("Simulation date").strip("[]")
    simulation_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
    return {"latitude": latitude, "longitude": longitude, "date": simulation_date,
            "source_coordinate_text": {"latitude": field("Centre latitude"), "longitude": field("Centre longitude")}}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_inventory(tiles: list[Path]) -> dict:
    used = [ROOT / "references/Shade Watch.pdf", ROOT / "config/study_area.md",
            ROOT / "data/raw/dsm/2020/Metedata for LiDAR Data (2020).html",
            ROOT / "data/raw/dsm/Terms and Conditions of Use.pdf",
            ROOT / "data/raw/validation/DJI_20260107143259_0005_V.JPG"] + tiles
    inventory = []
    for path in used:
        if path.exists():
            inventory.append({"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size,
                              "sha256": sha256(path)})
    return {"files_used": inventory,
            "alternate_source_formats_present": sorted(p.name for p in (ROOT / "data/raw/dsm/2020").iterdir()
                                                     if p.is_dir() and p.name != "D12.DSM.TIFF")}


def tile_audit(tiles):
    from .spatial import inventory
    return inventory(tiles)


def seam_audit(tiles):
    from .spatial import inventory, seam_audit as windowed_audit
    return windowed_audit(inventory(tiles))


def read_buffered_dsm(tiles, x, y):
    """Compatibility reader for the historical custom rectangle, windowed I/O."""
    from .spatial import Grid, inventory, read_window
    transform = from_origin(x-OUTPUT_WIDTH_M/2, y+OUTPUT_HEIGHT_M/2, RESOLUTION, RESOLUTION)
    grid = Grid(OUTPUT_WIDTH_PX, OUTPUT_HEIGHT_PX, tuple(transform)[:6], "EPSG:2326")
    core = (-BUFFER_PX, -BUFFER_PX, OUTPUT_WIDTH_PX+2*BUFFER_PX, OUTPUT_HEIGHT_PX+2*BUFFER_PX)
    return read_window(inventory(tiles), grid, core), grid.local_transform(core)


def nearest_bin(azimuth: float) -> int:
    return int(math.floor(((azimuth % 360) + 2.5) / 5) * 5) % 360


def classify(horizon_deg: np.ndarray, supported: np.ndarray, surface_valid: np.ndarray,
             apparent_elevation_deg: float, distant_threshold_deg: float) -> tuple[np.ndarray, np.ndarray]:
    """0 sunlit, 1 shaded, 255 invalid; quality 0/1/2/3/4."""
    labels = np.full(surface_valid.shape, NODATA, dtype=np.uint8)
    quality = np.full(surface_valid.shape, 1, dtype=np.uint8)
    known = surface_valid & np.isfinite(horizon_deg)
    if apparent_elevation_deg <= 0:
        quality[known] = 4
        return labels, quality
    shaded = known & (horizon_deg > apparent_elevation_deg)
    labels[shaded] = 1
    quality[shaded] = 0
    possible_sun = known & ~shaded
    quality[possible_sun & ~supported] = 2
    quality[possible_sun & supported] = 3
    sunlit = possible_sun & supported & (apparent_elevation_deg > distant_threshold_deg)
    labels[sunlit] = 0
    quality[sunlit] = 0
    return labels, quality


def write_raster(path: Path, array: np.ndarray, transform, *, nodata: int | None, tags: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(path, "w", driver="GTiff", width=array.shape[1], height=array.shape[0],
                       count=1, dtype="uint8", crs="EPSG:2326", transform=transform,
                       nodata=nodata, compress="deflate", predictor=1) as ds:
        ds.write(array, 1)
        ds.update_tags(**{k: str(v) for k, v in {**tags, "source_and_owner": SOURCE_LINE}.items()})


def write_binary_png(path: Path, labels: np.ndarray):
    path.parent.mkdir(parents=True, exist_ok=True)
    alpha = np.where(labels == NODATA, 0, 255).astype(np.uint8)
    metadata = PngImagePlugin.PngInfo()
    metadata.add_text("Source and owner", SOURCE_LINE)
    Image.fromarray(np.stack([labels, alpha], axis=2), mode="LA").save(
        path, optimize=True, pnginfo=metadata)


def _font(size: int, bold: bool = False):
    candidates = ["/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else
                  "/System/Library/Fonts/Supplemental/Arial.ttf",
                  "/System/Library/Fonts/Helvetica.ttc"]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def presentation_frame(labels: np.ndarray, local_time: datetime, sun,
                       valid_fraction: float, *, sunrise: datetime, sunset: datetime) -> Image.Image:
    """One native DSM pixel per image pixel, with a monochrome map."""
    if labels.shape != (OUTPUT_HEIGHT_PX, OUTPUT_WIDTH_PX):
        raise ValueError(f"Unexpected map shape: {labels.shape}")
    out = Image.new("RGB", (1536, 1088), "white")
    draw = ImageDraw.Draw(out)
    draw.text((32, 22), "SHADE WATCH HK  /  HKUST", font=_font(32, True), fill="black")
    draw.text((33, 67), local_time.strftime("%Y-%m-%d  %H:%M HKT"),
              font=_font(26, True), fill="black")
    rgb = np.zeros((*labels.shape, 3), dtype=np.uint8)
    for value, color in COLORS.items():
        rgb[labels == value] = color
    out.paste(Image.fromarray(rgb, "RGB"), (32, 108))
    draw.rectangle((31, 107, 1232, 1008), outline="black", width=1)
    draw.text((1266, 114), "N", font=_font(26, True), fill="black")
    draw.polygon([(1280, 153), (1266, 190), (1294, 190)], fill="black")
    draw.text((1266, 219), "600 × 450 m", font=_font(19, True), fill="black")
    draw.text((1266, 249), "0.5 m / pixel", font=_font(17), fill="black")
    for i, (value, label) in enumerate([(1, "Shaded"), (0, "Sunlit"), (255, "Invalid / uncertain")]):
        y = 310 + i * 54
        draw.rectangle((1266, y, 1294, y + 28), fill=COLORS[value], outline="black")
        draw.text((1305, y + 3), label, font=_font(17), fill="black")
    draw.text((1266, 524), f"Azimuth  {sun.azimuth_deg:.1f}°", font=_font(16), fill="black")
    draw.text((1266, 553), f"Elevation  {sun.apparent_elevation_deg:.1f}°", font=_font(16), fill="black")
    draw.text((1266, 595), f"Valid  {valid_fraction:.1%}", font=_font(16), fill="black")
    draw.text((1266, 647), "Clear-sky direct sun", font=_font(17, True), fill="black")
    draw.text((1266, 675), "at DSM surface", font=_font(17), fill="black")
    draw.rectangle((1268, 795, 1468, 803), fill="black")
    draw.line((1268, 790, 1268, 808), fill="black", width=2)
    draw.line((1468, 790, 1468, 808), fill="black", width=2)
    draw.text((1268, 814), "100 m", font=_font(17), fill="black")
    draw.text((33, 1018), f"Daylight {sunrise:%H:%M}–{sunset:%H:%M} HKT  ·  UTC {local_time.astimezone(timezone.utc):%H:%M}  ·  Source: CEDD 2020 LiDAR DSM",
              font=_font(15), fill="black")
    draw.text((33, 1045), "Data owner: Government of the Hong Kong Special Administrative Region",
              font=_font(14), fill="black")
    return out


def validate_against_direct_ray(dsm: np.ndarray, azimuth: int,
                                rotated: np.ndarray, refined: np.ndarray,
                                support: np.ndarray) -> dict:
    """Compare independent 0.5 m rays with rotated and 0.25 m ray profiles."""
    rr, cc = np.meshgrid(
        np.linspace(0, refined.shape[0] - 1, 20, dtype=np.int32),
        np.linspace(0, refined.shape[1] - 1, 20, dtype=np.int32), indexing="ij")
    rows = (BUFFER_PX + rr.ravel()).astype(np.int32)
    cols = (BUFFER_PX + cc.ravel()).astype(np.int32)
    reference, complete = direct_ray_reference(dsm, rows, cols, float(azimuth))
    rotated_sample = rotated[rr, cc].ravel()
    refined_sample = refined[rr, cc].ravel()
    valid = (np.isfinite(reference) & np.isfinite(rotated_sample) & np.isfinite(refined_sample)
             & (complete.astype(bool)) & support[rr, cc].ravel())
    rotation_delta = np.abs(reference[valid] - rotated_sample[valid])
    refined_delta = np.abs(reference[valid] - refined_sample[valid])
    return {"sample_points": int(len(rows)), "comparable_points": int(valid.sum()),
            "rotation_vs_0p5m_direct_median_abs_deg": float(np.median(rotation_delta)) if len(rotation_delta) else None,
            "rotation_vs_0p5m_direct_p95_abs_deg": float(np.quantile(rotation_delta, .95)) if len(rotation_delta) else None,
            "refined_vs_0p5m_direct_median_abs_deg": float(np.median(refined_delta)) if len(refined_delta) else None,
            "refined_vs_0p5m_direct_p95_abs_deg": float(np.quantile(refined_delta, .95)) if len(refined_delta) else None,
            "refined_vs_0p5m_direct_max_abs_deg": float(refined_delta.max()) if len(refined_delta) else None,
            "note": "All methods use the same DSM; this is an internal numerical check, not observational validation."}


def run() -> None:
    from .pipeline import main
    main()


if __name__ == "__main__":
    run()
