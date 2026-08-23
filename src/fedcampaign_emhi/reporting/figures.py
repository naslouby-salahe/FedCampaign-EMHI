from pathlib import Path

from fedcampaign_emhi.artifacts.records import SeedSummaryRecord
from fedcampaign_emhi.domain.types import CanonicalUtf8Bytes, FiniteFloat


def _scaled_y(
    value: FiniteFloat, minimum: FiniteFloat, maximum: FiniteFloat
) -> FiniteFloat:
    if maximum == minimum:
        return 50
    return 90 - (80 * (value - minimum) / (maximum - minimum))


def paired_difference_svg(records: tuple[SeedSummaryRecord, ...]) -> CanonicalUtf8Bytes:
    values = tuple(
        record.paired_difference
        for record in records
        if record.paired_difference is not None
    )
    if not values:
        raise ValueError("paired-difference figure requires paired seed summaries")
    minimum = min(min(values), 0.0)
    maximum = max(max(values), 0.0)
    width = max(240, 40 * len(values) + 80)
    zero_y = _scaled_y(0.0, minimum, maximum)
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="120" viewBox="0 0 {width} 120">',
        '<rect x="0" y="0" width="100%" height="100%" fill="white"/>',
        f'<line x1="40" y1="{zero_y:.3f}" x2="{width - 20}" y2="{zero_y:.3f}" stroke="black" stroke-width="1"/>',
    ]
    for index, value in enumerate(values):
        x = 60 + index * 40
        y = _scaled_y(value, minimum, maximum)
        lines.append(f'<circle cx="{x}" cy="{y:.3f}" r="4" fill="black"/>')
        lines.append(f'<text x="{x - 6}" y="110" font-size="9">{index}</text>')
    lines.append("</svg>")
    return "\n".join(lines).encode("utf-8")


def write_paired_difference_figure(
    destination: Path, records: tuple[SeedSummaryRecord, ...]
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.with_suffix(destination.suffix + ".partial")
    staging.write_bytes(paired_difference_svg(records))
    staging.replace(destination)
