# SPDX-License-Identifier: Apache-2.0
"""IHP SG13G2 dummy metal fill provider for ICE procedural layouts.

ICE calls :func:`add_dummy_fill` when a procedural layout script requests
dummy fill through ``layout.add_dummy_fill(...)``.  The implementation follows
the square-fill rules used by the open-source ``gdsfill`` project for IHP
SG13G2: a global staggered square lattice, a keep-out around existing geometry
on the same layer, and deterministic thinning to the target density.

The module intentionally has no dependency on gdsfill itself. It uses KLayout's
``pya`` geometry engine, which is also the geometry engine used by gdsfill's
Python flow.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

try:
    import pya
except ImportError as error:  # pragma: no cover - exercised only on broken installs
    raise RuntimeError(
        "IHP SG13G2 dummy fill requires KLayout's pya module. "
        "Install KLayout or run ICE with a Python interpreter that can import pya."
    ) from error


@dataclass(frozen=True)
class MetalRule:
    """IHP SG13G2 dummy-fill rules for one metal layer."""

    gds_layer: int
    min_size_um: float
    max_size_um: float
    min_space_um: float
    max_space_um: float
    density: float
    deviation: float


# Values adapted from gdsfill's IHP SG13G2 process definition.
METAL_RULES = {
    "Metal1": MetalRule(8, 1.0, 5.0, 0.42, 10.0, 50.0, 10.0),
    "Metal2": MetalRule(10, 1.0, 5.0, 0.42, 10.0, 50.0, 10.0),
    "Metal3": MetalRule(30, 1.0, 5.0, 0.42, 10.0, 50.0, 10.0),
    "Metal4": MetalRule(50, 1.0, 5.0, 0.42, 10.0, 50.0, 10.0),
    "Metal5": MetalRule(67, 1.0, 5.0, 0.42, 10.0, 50.0, 10.0),
    "TopMetal1": MetalRule(126, 5.0, 10.0, 3.0, 10.0, 40.0, 10.0),
    "TopMetal2": MetalRule(134, 5.0, 10.0, 3.0, 10.0, 40.0, 10.0),
}

_MANUFACTURING_GRID_UM = 0.005


def _resolve_layer_name(layout, requested):
    lowered = requested.lower()
    for name in layout.layers:
        if name.lower() == lowered:
            return name
    return requested


def _to_dbu(layout, micrometers):
    nanometers_per_unit = max(float(getattr(layout, "db_unit_nm", 1.0)), 1.0e-9)
    return max(1, int(round(micrometers * 1000.0 / nanometers_per_unit)))


def _manufacturing_grid_dbu(layout):
    nanometers_per_unit = max(float(getattr(layout, "db_unit_nm", 1.0)), 1.0e-9)
    return max(1, int(round(_MANUFACTURING_GRID_UM * 1000.0 / nanometers_per_unit)))


def _snap_even(value, grid):
    step = max(1, grid * 2)
    return max(step, int(round(value / step)) * step)


def _option_for_layer(value, layer_name, default):
    if value is None:
        return float(default)
    if isinstance(value, dict):
        for key, entry in value.items():
            if str(key).lower() == layer_name.lower():
                return float(entry)
        return float(default)
    return float(value)


def _analytical_size_space(rule, target_percent):
    """Mirror gdsfill's analytical square-lattice sizing."""
    ratio = math.sqrt(max(0.0, min(float(target_percent), 100.0)) / 100.0)
    if ratio <= 0.0:
        return rule.min_size_um, rule.max_space_um
    if ratio >= 1.0:
        return rule.max_size_um, rule.min_space_um
    pitch_low = max(rule.min_size_um / ratio, rule.min_space_um / (1.0 - ratio))
    pitch_high = min(rule.max_size_um / ratio, rule.max_space_um / (1.0 - ratio))
    pitch = max(pitch_low, pitch_high)
    size = min(max(ratio * pitch, rule.min_size_um), rule.max_size_um)
    space = min(max((1.0 - ratio) * pitch, rule.min_space_um), rule.max_space_um)
    return size, space


def _space_for_size(rule, size_um, target_percent):
    """Compute the spacing that reaches the target for a fixed square size."""
    ratio = math.sqrt(max(0.0, min(float(target_percent), 100.0)) / 100.0)
    if ratio <= 0.0:
        return rule.max_space_um
    if ratio >= 1.0:
        return rule.min_space_um
    space = size_um * (1.0 - ratio) / ratio
    return min(max(space, rule.min_space_um), rule.max_space_um)


def _area_region(layout, area, bounds):
    if area is None:
        return pya.Region(pya.Box(*bounds))
    if (
        isinstance(area, (list, tuple))
        and len(area) == 4
        and all(isinstance(value, (int, float)) for value in area)
    ):
        x0, y0, x1, y1 = (int(round(value)) for value in area)
        if x1 <= x0 or y1 <= y0:
            raise ValueError("area must have positive width and height")
        return pya.Region(pya.Box(x0, y0, x1, y1))
    points = []
    for point in area:
        if isinstance(point, dict):
            points.append(pya.Point(int(round(point["x"])), int(round(point["y"]))))
        else:
            x, y = point
            points.append(pya.Point(int(round(x)), int(round(y))))
    if len(points) < 3:
        raise ValueError(
            "area must be (x0, y0, x1, y1) or a polygon with at least three points"
        )
    return pya.Region(pya.Polygon(points)).merged()


def _region_for_layer(layout, layer_name):
    region = pya.Region()
    for _, points in layout.iter_polygons(layer_name):
        polygon = pya.Polygon([pya.Point(int(x), int(y)) for x, y in points])
        region.insert(polygon)
    return region.merged()


def _grid_candidates(bounds, size_dbu, space_dbu, grid_dbu):
    x0, y0, x1, y1 = bounds
    grid = max(1, grid_dbu)
    x0 = ((x0 + grid - 1) // grid) * grid
    y0 = ((y0 + grid - 1) // grid) * grid
    x1 = (x1 // grid) * grid
    y1 = (y1 // grid) * grid
    pitch = size_dbu + space_dbu
    half = size_dbu // 2
    drift = pitch // 2
    candidates = pya.Region()
    column = 0
    center_x = x0 + half
    while center_x + half <= x1:
        stagger = drift if column % 2 else 0
        center_y = y0 + half + stagger
        while center_y + half <= y1:
            candidates.insert(
                pya.Box(
                    center_x - half,
                    center_y - half,
                    center_x - half + size_dbu,
                    center_y - half + size_dbu,
                )
            )
            center_y += pitch
        center_x += pitch
        column += 1
    return candidates


def _hash01(x, y):
    """Deterministic SplitMix64-style hash used to thin the fill lattice."""
    mask = (1 << 64) - 1
    value = ((x & mask) * 0x9E3779B97F4A7C15) & mask
    value ^= ((y & mask) * 0xC2B2AE3D27D4EB4F) & mask
    value = ((value ^ (value >> 29)) * 0xBF58476D1CE4E5B9) & mask
    value = ((value ^ (value >> 27)) * 0x94D049BB133111EB) & mask
    value ^= value >> 31
    return (value >> 11) / float(1 << 53)


def _fill_layer(layout, layer_name, rule, density, deviation, area_region):
    target_density = max(0.0, min(float(density), 100.0))
    tolerance = max(0.0, float(deviation))
    existing = _region_for_layer(layout, layer_name)
    reference_area = area_region.area()
    if reference_area <= 0:
        return 0
    existing_area = (existing & area_region).area()
    running_density = existing_area / reference_area * 100.0
    if target_density - running_density <= tolerance / 2.0:
        return 0
    budget_area = max(0.0, target_density / 100.0 * reference_area - existing_area)
    if budget_area <= 0:
        return 0

    size_um, space_um = _analytical_size_space(rule, target_density)
    grid = _manufacturing_grid_dbu(layout)
    min_size = _snap_even(_to_dbu(layout, rule.min_size_um), grid)
    max_size = max(min_size, _snap_even(_to_dbu(layout, rule.max_size_um), grid))
    min_space = _snap_even(_to_dbu(layout, rule.min_space_um), grid)
    max_space = max(min_space, _snap_even(_to_dbu(layout, rule.max_space_um), grid))
    size_dbu = min(max(_snap_even(_to_dbu(layout, size_um), grid), min_size), max_size)
    space_dbu = min(
        max(_snap_even(_to_dbu(layout, space_um), grid), min_space), max_space
    )

    def candidates_for(current_size, current_space):
        keepout = existing.sized(current_space).merged()
        fill_area = (area_region - keepout).merged()
        if fill_area.is_empty():
            return None
        fill_bbox = fill_area.bbox()
        candidates = _grid_candidates(
            (fill_bbox.left, fill_bbox.bottom, fill_bbox.right, fill_bbox.top),
            current_size,
            current_space,
            grid,
        )
        valid = candidates.inside(fill_area)
        return valid if valid.area() > 0 else None

    valid = candidates_for(size_dbu, space_dbu)
    if valid is None and size_dbu > min_size:
        # Small layouts cannot fit the density-optimal square. Fall back to the
        # minimum legal square and derive spacing from the same density target.
        size_dbu = min_size
        fallback_space_um = _space_for_size(rule, rule.min_size_um, target_density)
        space_dbu = min(
            max(_snap_even(_to_dbu(layout, fallback_space_um), grid), min_space),
            max_space,
        )
        valid = candidates_for(size_dbu, space_dbu)
    if valid is None:
        return 0
    candidate_area = valid.area()
    if candidate_area <= 0:
        return 0
    keep_ratio = min(1.0, budget_area / candidate_area)
    if keep_ratio <= 0:
        return 0

    existing_number = layout.layer_number(layer_name)
    if existing_number is None:
        handle = layout.layer(layer_name, rule.gds_layer)
    else:
        handle = layout.layer(layer_name, existing_number)
    added = 0
    for polygon in valid.each():
        box = polygon.bbox()
        if box.width() != size_dbu or box.height() != size_dbu:
            continue
        center_x = (box.left + box.right) // 2
        center_y = (box.bottom + box.top) // 2
        if keep_ratio < 1.0 and _hash01(center_x, center_y) >= keep_ratio:
            continue
        handle.rectangle(box.left, box.bottom, box.width(), box.height())
        added += 1
    return added


def add_dummy_fill(
    layout, layers=None, density=None, deviation=None, area=None, **options
):
    """Add IHP SG13G2 dummy metal fill to an ICE procedural layout.

    Args:
        layout: ICE procedural layout builder.
        layers: Optional layer name or iterable of layer names. Defaults to all
            supported metal layers.
        density: Target density in percent, or a mapping keyed by layer name.
        deviation: Allowed deviation in percent, or a mapping keyed by layer.
        area: Optional ``(x0, y0, x1, y1)`` box or polygon point list. Defaults
            to the bounding box of the layout.
        **options: Reserved for future PDK options. Unknown options are rejected
            so script typos are not silently ignored.
    """
    if options:
        unknown = ", ".join(sorted(options))
        raise ValueError(f"Unsupported IHP dummy fill option(s): {unknown}")
    if layers is None:
        selected = list(METAL_RULES)
    elif isinstance(layers, str):
        selected = [layers]
    else:
        selected = list(layers)
    if not selected:
        raise ValueError("add_dummy_fill() needs at least one layer")

    resolved = []
    for requested in selected:
        name = _resolve_layer_name(layout, str(requested))
        matched_rule = None
        for rule_name in METAL_RULES:
            if rule_name.lower() == name.lower():
                matched_rule = rule_name
                break
        if matched_rule is None:
            supported = ", ".join(METAL_RULES)
            raise ValueError(
                f"IHP SG13G2 does not provide dummy fill for '{requested}'. Supported: {supported}"
            )
        if matched_rule not in resolved:
            resolved.append(matched_rule)

    bounds = layout.bounds()
    if bounds is None:
        raise ValueError(
            "add_dummy_fill() requires at least one existing shape to determine the fill area"
        )
    area_region = _area_region(layout, area, bounds)
    if area_region.is_empty():
        raise ValueError("add_dummy_fill() fill area is empty")

    total = 0
    for name in resolved:
        rule = METAL_RULES[name]
        layer_density = _option_for_layer(density, name, rule.density)
        layer_deviation = _option_for_layer(deviation, name, rule.deviation)
        total += _fill_layer(
            layout, name, rule, layer_density, layer_deviation, area_region
        )
    return total
