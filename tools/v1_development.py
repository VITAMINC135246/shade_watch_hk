"""Bounded, reproducible V1 development measurements (not acceptance)."""
from __future__ import annotations
import argparse
from dataclasses import asdict
from datetime import datetime
import json
from pathlib import Path
import statistics
import subprocess
import sys
import time

import numpy as np
from pyproj import Transformer
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))
from src import v1
from src.horizon import pixel_centred_horizon
from src.pipeline import memory_monitor
from src.spatial import digest_file, expand, read_window
from src.v1_cache import atomic_json, canonical_origin, diagnostic_horizon, entry_paths, tile_grid, valid_entry
from v1_oracle import ray_oracle, classification_oracle, meeus_solar


def generated_bytes(paths):
    return sum(p.stat().st_size for base in paths if base.exists() for p in base.rglob("*") if p.is_file())


class Campaign:
    def __init__(self, directory):
        if not directory.is_relative_to(ROOT / "outputs"):
            raise ValueError("Development campaign must be isolated under outputs/")
        self.directory = directory
        self.evidence = directory / "evidence"
        self.cache = ROOT / "data/processed/shade_v1" / directory.name.removeprefix("v1_")
        self.ledger_path = self.evidence / "ledger.json"
        self.ledger = json.loads(self.ledger_path.read_text()) if self.ledger_path.exists() else dict(
            real_job_wall_seconds=0., ceiling_seconds=3600., entries=[],
            memory_ceiling_bytes=8 * 1024**3, artifact_ceiling_bytes=10 * 1024**3,
            filesystem_cache="not flushed; same-process paired trials", workers=1)

    def job(self, name, function, reserve=120.):
        if self.ledger["real_job_wall_seconds"] + reserve > self.ledger["ceiling_seconds"]:
            raise RuntimeError("Remaining real-DSM budget cannot admit this workload")
        entry = dict(name=name, status="running", reserved_seconds=reserve)
        self.ledger["entries"].append(entry)
        atomic_json(self.ledger_path, self.ledger)
        start = time.perf_counter()
        try:
            with memory_monitor() as memory:
                result = function()
            entry.update(status="complete", **memory)
            return result
        except BaseException as exc:
            entry.update(status="failed", error=repr(exc))
            raise
        finally:
            elapsed = time.perf_counter() - start
            entry["wall_seconds"] = elapsed
            self.ledger["real_job_wall_seconds"] += elapsed
            entry["generated_bytes"] = generated_bytes([self.directory, self.cache,
                                                         ROOT / "data/processed/horizon_cache_v1_legacy_smoke"])
            atomic_json(self.ledger_path, self.ledger)
            print(json.dumps(dict(job=name, seconds=round(elapsed, 3), status=entry["status"],
                                  cumulative_real_seconds=round(self.ledger["real_job_wall_seconds"], 3))), flush=True)
            if entry["generated_bytes"] > self.ledger["artifact_ceiling_bytes"]:
                raise RuntimeError("Campaign artifact budget exceeded")
            if entry.get("peak_tree_rss_bytes", 0) > self.ledger["memory_ceiling_bytes"]:
                raise MemoryError("Campaign memory budget exceeded")

    def query(self, name, cache, **kwargs):
        def execute():
            started = time.perf_counter()
            plan = v1.plan_shade(output_dir=str(self.directory / name), cache_dir=str(cache), **kwargs)
            result = v1.run_shade(plan)
            return dict(plan=plan.to_dict(), result=asdict(result),
                        plan_and_run_seconds=time.perf_counter() - started)
        result = self.job(name, execute)
        atomic_json(self.evidence / f"{name}.json", result)
        return result


def benchmarks(campaign, manifest):
    output = campaign.evidence / "benchmarks.json"
    if output.exists():
        print("Benchmarks already recorded; not repeated", flush=True)
        return
    # Synthetic JIT preload is explicit and outside real-DSM measurements.
    pixel_centred_horizon(np.zeros((8, 8), np.float32), np.array([4]), np.array([4]), 90., 1., 1.)
    settings = manifest["benchmarks"]
    trials = []
    for i in range(settings["trials"]):
        cache = campaign.cache / f"benchmark_{i}"
        if cache.exists() and any(cache.rglob("*.tif")):
            raise RuntimeError("Cold scientific cache is not empty; select a new campaign")
        kwargs = dict(tile=settings["tile"], instants=[settings["instant"]])
        cold = campaign.query(f"cold_{i}", cache, **kwargs)
        warm = campaign.query(f"warm_{i}", cache, **kwargs)
        plan = v1.plan_shade(output_dir=str(campaign.directory / f"warm_{i}"), cache_dir=str(cache), **kwargs)
        final_hit = campaign.job(f"final_hit_{i}", lambda: asdict(v1.run_shade(plan)))
        assert cold["result"]["jobs"]["computed"] == 1
        assert warm["result"]["jobs"]["computed"] == 0 and warm["result"]["jobs"]["reused"] == 1
        assert warm["result"]["jobs"]["final_result_hits"] == 0
        assert final_hit["jobs"]["final_result_hits"] == 1
        for field in ("raster", "quality_raster"):
            with rasterio.open(cold["result"]["frames"][0][field]) as a, rasterio.open(warm["result"]["frames"][0][field]) as b:
                assert a.shape == b.shape == (1200, 1500)
                assert a.transform == b.transform and a.crs.to_string() == "EPSG:2326"
                assert np.array_equal(a.read(1), b.read(1))
        trials.append(dict(cold=cold, warm=warm, final_hit=final_hit))
    cold_median = statistics.median(t["cold"]["result"]["performance"]["run_seconds"] for t in trials)
    warm_median = statistics.median(t["warm"]["result"]["performance"]["run_seconds"] for t in trials)
    assert warm_median < cold_median
    atomic_json(output, dict(trials=trials, cold_median_seconds=cold_median, warm_median_seconds=warm_median,
                             cold_warm_identical_settings=True, default_direction="nearest5",
                             jit="synthetic preload; existing Numba disk compilation cache",
                             filesystem_cache="not flushed, already used DSM may remain in OS cache",
                             comparison="run_shade incl hashes/validation/compression; planning separately measured"))


def operations(campaign, manifest):
    output = campaign.evidence / "real_operations.json"
    if output.exists():
        return
    cache = campaign.cache / "benchmark_0"
    tile = manifest["tiles"][0]
    alone = json.loads((campaign.evidence / "cold_0.json").read_text())
    reused = campaign.query("cross_date", cache, tile=tile, instants=[manifest["timestamps"][1]])
    assert reused["result"]["jobs"]["horizon_calls"] == 0
    odd = campaign.query("odd_crop", cache, tile=tile, crop=(901, 701, 24, 20),
                        instants=[manifest["timestamps"][0]], jpg=True)
    combo = campaign.query("combined", cache, tiles=manifest["tiles"],
                          instants=[manifest["timestamps"][0]])
    custom = campaign.query("custom_crop", cache, mode="custom",
                           bounds=(844700.51, 822439.51, 844712.49, 822449.49),
                           instants=[manifest["timestamps"][0]])
    for field in ("raster", "quality_raster"):
        with rasterio.open(alone["result"]["frames"][0][field]) as a, \
                rasterio.open(odd["result"]["frames"][0][field]) as b, \
                rasterio.open(combo["result"]["frames"][0][field]) as c, \
                rasterio.open(custom["result"]["frames"][0][field]) as d:
            aa = a.read(1)
            assert np.array_equal(aa, c.read(1)[:, :1500])
            assert np.array_equal(aa[701:721, 901:925], b.read(1))
            assert np.array_equal(aa[701:721, 901:925], d.read(1))
    sequence = campaign.query("multi_date", cache, tile=tile, dates=manifest["real_sequence_dates"],
                              interval_minutes=manifest["sequence_interval_minutes"], crop=(301, 201, 24, 20),
                              jpg=False, mp4=True)
    assert len({f["local_time"][:10] for f in sequence["result"]["frames"]}) == 2
    assert sequence["result"]["jobs"]["computed"] > 0
    atomic_json(output, dict(cross_date=reused, odd_crop=odd, combined=combo, custom=custom, sequence=sequence,
                             output_invariance="shade and quality arrays exact; native and odd-offset custom/crop",
                             complete_native_shape=[1200, 1500]))


def numerical(campaign, manifest):
    output = campaign.evidence / "numerical.json"
    if output.exists():
        return
    records = v1.index_sources(v1.RAW)
    source_by_name = {Path(r["path"]).name: r for r in records}
    cache = campaign.cache / "benchmark_0"
    primary_plan = v1.plan_shade(tile=manifest["tiles"][0], instants=[manifest["timestamps"][0]], cache_dir=str(cache))
    entry = valid_entry(cache, primary_plan.tiles[0].spatial_key, 215., primary_plan.tiles[0].source)
    primary_threshold = entry["threshold_deg"]
    primary_stats = entry["stats"]
    # Fixed before outcomes in the manifest; uses declared windows/dates only.
    cases = [(0, 0, 0), (0, 1, 3), (0, 2, 4), (0, 0, 5), (0, 1, 6), (1, 3, 2), (1, 3, 7)]
    results = []
    for number, (tile_i, window_i, time_i) in enumerate(cases):
        tile = source_by_name[manifest["tiles"][tile_i]]
        window = tuple(manifest["windows"][window_i])
        instant = datetime.fromisoformat(manifest["timestamps"][time_i])
        reference = v1.output_reference(tile_grid(tile))
        sun = v1.position(instant, reference["latitude"], reference["longitude"])
        plan = v1.plan_shade(tile=Path(tile["path"]).name, instants=[instant], cache_dir=str(cache))
        threshold = primary_threshold
        if tile_i == 1:
            second_entry = valid_entry(cache, plan.tiles[0].spatial_key, 215., tile)
            threshold = second_entry["threshold_deg"]
        def measure():
            start = time.perf_counter()
            grid = tile_grid(tile)
            region = expand(window, 2000)
            dsm = read_window(records, grid, region)
            rr, cc = np.indices((window[3], window[2]), dtype=np.int32)
            rr += 2000; cc += 2000
            origin_row, origin_col = canonical_origin(grid, region)
            ref_start = time.perf_counter()
            ref = ray_oracle(dsm, rr.ravel(), cc.ravel(), sun.azimuth_deg,
                             origin_row=origin_row, origin_col=origin_col)
            ref = tuple(a.reshape(window[3], window[2]) for a in ref)
            reference_seconds = time.perf_counter() - ref_start
            del dsm
            candidates = {}
            metrics = {}
            for method in ("direct", "nearest5", "nearest2_5"):
                direction = v1.direction_for(sun.azimuth_deg, method)
                calculation_start = time.perf_counter()
                got = diagnostic_horizon(records, tile, window, direction)
                elapsed = time.perf_counter() - calculation_start
                finite = np.isfinite(ref[0]) & np.isfinite(got[0])
                error = np.abs(got[0][finite] - ref[0][finite])
                expected = classification_oracle(ref[0], ref[1], sun.apparent_elevation_deg, threshold)
                observed = v1.classify(got[0], got[1].astype(bool), np.isfinite(got[0]), sun.apparent_elevation_deg, threshold)
                equality = finite & (np.abs(ref[0] - sun.apparent_elevation_deg) <= 1e-4)
                label_diff = observed[0] != expected[0]
                quality_diff = observed[1] != expected[1]
                if error.size:
                    err_grid = np.where(finite, np.abs(got[0] - ref[0]), -1)
                    rmax, cmax = np.unravel_index(np.argmax(err_grid), err_grid.shape)
                    spatial_example = dict(row=int(rmax + window[1]), column=int(cmax + window[0]),
                                           exact_horizon=float(ref[0][rmax, cmax]), candidate_horizon=float(got[0][rmax, cmax]))
                else:
                    spatial_example = None
                metrics[method] = dict(direction_deg=direction, exact_azimuth_deg=sun.azimuth_deg,
                                       total_denominator=window[2] * window[3], finite_denominator=int(finite.sum()),
                                       max_horizon_error_deg=float(error.max()) if error.size else None,
                                       mean_horizon_error_deg=float(error.mean()) if error.size else None,
                                       p95_horizon_error_deg=float(np.quantile(error, .95)) if error.size else None,
                                       finite_mask_differences=int(np.count_nonzero(np.isfinite(got[0]) != np.isfinite(ref[0]))),
                                       support_disagreement=int(np.count_nonzero(got[1] != ref[1])),
                                       shade_disagreement=int(label_diff.sum()), quality_disagreement=int(quality_diff.sum()),
                                       shade_disagreement_outside_equality=int(np.count_nonzero(label_diff & ~equality)),
                                       equality_count=int(equality.sum()), valid_mask_disagreement=int(np.count_nonzero((observed[0] != 255) != (expected[0] != 255))),
                                       runtime_including_buffer_io_seconds=elapsed, spatial_example=spatial_example)
                candidates[method] = got
                if method == "direct":
                    assert not error.size or error.max() <= 1e-4
                    assert np.array_equal(got[1], ref[1])
                    assert np.array_equal(np.isfinite(got[0]), np.isfinite(ref[0]))
                    assert not np.any(label_diff & ~equality) and not np.any(quality_diff & ~equality)
            native = tile_grid(tile)
            yy, xx = np.indices((window[3], window[2]))
            x = native.affine.c + (xx + window[0] + .5) * .5
            y = native.affine.f - (yy + window[1] + .5) * .5
            lon, lat = Transformer.from_crs("EPSG:2326", "EPSG:4326", always_xy=True).transform(x, y)
            pixel_suns = [v1.position(instant, a, b) for a, b in zip(lat.ravel(), lon.ravel())]
            pixel_az = np.array([s.azimuth_deg for s in pixel_suns])
            pixel_el = np.array([s.apparent_elevation_deg for s in pixel_suns])
            angular = np.abs((pixel_az - sun.azimuth_deg + 180) % 360 - 180)
            meeus = meeus_solar(instant, reference["latitude"], reference["longitude"])
            np.savez_compressed(campaign.evidence / f"arrays_case_{number}.npz", reference_horizon=ref[0], reference_support=ref[1],
                                direct_horizon=candidates["direct"][0], baseline_horizon=candidates["nearest5"][0],
                                candidate_horizon=candidates["nearest2_5"][0], baseline_support=candidates["nearest5"][1],
                                candidate_support=candidates["nearest2_5"][1])
            return dict(tile=Path(tile["path"]).name, window=window, instant=instant.isoformat(), sun=asdict(sun),
                        threshold_deg=threshold, metrics=metrics, independent_reference_seconds=reference_seconds,
                        total_seconds=time.perf_counter() - start,
                        tile_centre_vs_pixel=dict(max_azimuth_difference_deg=float(angular.max()),
                                                  max_apparent_elevation_difference_deg=float(np.max(np.abs(pixel_el - sun.apparent_elevation_deg)))),
                        fractional_year_vs_meeus=dict(reference_azimuth_deg=meeus[0], reference_geometric_elevation_deg=meeus[1],
                                                      azimuth_difference_deg=float(abs((sun.azimuth_deg - meeus[0] + 180) % 360 - 180)),
                                                      geometric_elevation_difference_deg=abs(sun.geometric_elevation_deg - meeus[1])))
        results.append(campaign.job(f"numerical_case_{number}", measure, reserve=30.))
    native = tile_grid(source_by_name[manifest["tiles"][0]])
    boundary = []
    for stamp in manifest["timestamps"][:5]:
        instant = datetime.fromisoformat(stamp)
        refs = [v1.output_reference(tile_grid(source_by_name[name])) for name in manifest["tiles"]]
        suns = [v1.position(instant, r["latitude"], r["longitude"]) for r in refs]
        lons, lats = Transformer.from_crs("EPSG:2326", "EPSG:4326", always_xy=True).transform(
            [844999.75, 845000.25], [822649.75, 822649.75])
        true_suns = [v1.position(instant, lat, lon) for lat, lon in zip(lats, lons)]
        boundary.append(dict(instant=stamp, canonical_elevation_jump_deg=abs(suns[1].apparent_elevation_deg - suns[0].apparent_elevation_deg),
                             pixel_elevation_jump_deg=abs(true_suns[1].apparent_elevation_deg - true_suns[0].apparent_elevation_deg),
                             canonical_azimuth_jump_deg=abs((suns[1].azimuth_deg - suns[0].azimuth_deg + 180) % 360 - 180),
                             threshold_jump_deg=abs(primary_threshold - second_entry["threshold_deg"])))
    storage = dict(full_native_uncompressed_bytes_per_direction=native.width * native.height * 12,
                   nearest5_full_table_directions=72, nearest2_5_full_table_directions=144,
                   direct="one entry per distinct requested tile-reference azimuth; no fixed finite table",
                   actual_campaign_cache_bytes=generated_bytes([campaign.cache]))
    atomic_json(output, dict(cases=results, boundary_effects=boundary, storage=storage,
                             primary_threshold=primary_threshold, primary_statistics=primary_stats,
                             default_choice="nearest5 retained for V1; nearest2_5 and direct are explicit options",
                             limitation="denser bins sometimes reduce error but can still miss narrow blockers; no agreed physical-error threshold",
                             numerical_reference="separate NumPy 0.25 m ray operator; shares source-window I/O and adopted model assumptions",
                             astronomical_reference="separately transcribed NOAA Julian-century/Meeus equations; not observations",
                             noaa_primary_source="https://gml.noaa.gov/grad/solcalc/main.js"))


def legacy(campaign):
    output = campaign.evidence / "legacy_smoke.json"
    if output.exists():
        return
    config = json.loads((ROOT / "config/processing.json").read_text())
    centre_lon, centre_lat = Transformer.from_crs("EPSG:2326", "EPSG:4326", always_xy=True).transform(844706.5, 822444.5)
    config.update(output_mode="custom", custom_width_m=12, custom_height_m=10,
                  custom_center_wgs84=dict(latitude=centre_lat, longitude=centre_lon),
                  output_directory=str(campaign.directory / "legacy_smoke"),
                  cache_directory="data/processed/horizon_cache_v1_legacy_smoke", workers=1)
    config_path = campaign.evidence / "legacy_config.json"
    atomic_json(config_path, config)
    def execute():
        log = campaign.evidence / "legacy_smoke.log"
        with log.open("w") as handle:
            process = subprocess.run([sys.executable, "-m", "src.shade_watch", "--config", str(config_path)],
                                     cwd=ROOT, stdout=handle, stderr=subprocess.STDOUT, timeout=180)
        if process.returncode:
            raise RuntimeError(f"Legacy smoke failed; inspect {log}")
        data = json.loads((campaign.directory / "legacy_smoke/result_inventory.json").read_text())
        assert data["daylight"]["frames"] == data["daylight"]["decoded_video_frames"] == 65
        assert data["grid"]["width"] == 24 and data["grid"]["height"] == 20
        assert data["grid"]["crs"] == "EPSG:2326" and data["grid"]["transform"][0] == .5
        return dict(command=[sys.executable, "-m", "src.shade_watch", "--config", str(config_path)],
                    inventory=str(campaign.directory / "legacy_smoke/result_inventory.json"),
                    performance=data["performance"], jobs=data["jobs"], frames=data["daylight"]["frames"])
    atomic_json(output, campaign.job("legacy_real_smoke", execute, reserve=180.))


def cli(campaign, manifest):
    output = campaign.evidence / "cli.json"
    if output.exists():
        return
    rows = []
    common = [sys.executable, "-m", "src.v1"]
    spatial = ["--tile", manifest["tiles"][0], "--crop", "901", "701", "24", "20",
               "--cache", str(campaign.cache / "benchmark_0")]
    examples = [
        ("planning", ["plan", "--at", manifest["timestamps"][0], "--jpg", "--mp4"]),
        ("instant", ["query", "--at", manifest["timestamps"][0]]),
        ("list", ["query", "--at", manifest["timestamps"][0], "--at", manifest["timestamps"][2]]),
        ("dates", ["query", "--date", "2026-01-07", "--date", "2026-06-21", "--interval-minutes", "360"]),
    ]
    for name, arguments in examples:
        directory = campaign.directory / f"cli_{name}"
        command = common + arguments + spatial + ["--output", str(directory)]
        def execute():
            process = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=120)
            (campaign.evidence / f"cli_{name}.stdout.json").write_text(process.stdout)
            (campaign.evidence / f"cli_{name}.stderr.log").write_text(process.stderr)
            if process.returncode:
                raise RuntimeError(f"CLI {name} failed: {process.stderr}")
            data = json.loads(process.stdout)
            if name == "planning":
                assert not directory.exists()
                assert data["schema"] == "shade-watch-v1-plan-1.0"
                # All needed directions are already present; zero jobs remain.
                assert data["resources"]["missing_direction_jobs"] == 0
            else:
                assert Path(data["index_path"]).exists()
            return dict(name=name, command=command, returncode=process.returncode,
                        planning_wrote_outputs=directory.exists() if name == "planning" else None,
                        jobs=data.get("jobs"), frames=len(data.get("frames", [])))
        rows.append(campaign.job(f"cli_{name}", execute))
    atomic_json(output, dict(examples=rows))


def audit(campaign):
    baseline = json.loads((campaign.evidence / "baseline.json").read_text())
    old = json.loads((campaign.evidence / "protected_files.json").read_text())
    differences = [path for path, signature in old.items() if not Path(path).exists()
                   or [Path(path).stat().st_size, Path(path).stat().st_mtime_ns] != signature]
    current = v1.index_sources(v1.RAW)
    assert [r["sha256"] for r in baseline["sources"]] == [r["sha256"] for r in current]
    assert not differences, differences
    histories = baseline["historical_json_identities"]
    assert all(digest_file(p) == v["sha256"] for p, v in histories.items())
    atomic_json(campaign.evidence / "protected_audit.json", dict(source_hashes_unchanged=True,
                protected_stat_signatures_unchanged=len(old), historical_json_hashes_unchanged=len(histories), differences=differences))
    files = {str(p.relative_to(ROOT)): dict(sha256=digest_file(p), bytes=p.stat().st_size)
             for p in campaign.evidence.rglob("*") if p.is_file() and p.name != "manifest.json"}
    atomic_json(campaign.evidence / "manifest.json", dict(files=files, ledger=str(campaign.ledger_path),
                contract_id=baseline["contract_id"], contract_sha256=baseline["contract_sha256"],
                starting_commit=baseline["starting_commit"], sources=baseline["sources"], environment=baseline["environment"]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("benchmarks", "operations", "numerical", "legacy", "cli", "audit", "all"))
    parser.add_argument("--campaign", default="outputs/v1_development_20261002")
    args = parser.parse_args()
    campaign = Campaign((ROOT / args.campaign).resolve())
    manifest = json.loads((campaign.evidence / "development_samples.json").read_text())
    stages = {"benchmarks": lambda: benchmarks(campaign, manifest), "operations": lambda: operations(campaign, manifest),
              "numerical": lambda: numerical(campaign, manifest), "legacy": lambda: legacy(campaign),
              "cli": lambda: cli(campaign, manifest), "audit": lambda: audit(campaign)}
    for name in stages if args.stage == "all" else [args.stage]:
        stages[name]()


if __name__ == "__main__":
    main()
