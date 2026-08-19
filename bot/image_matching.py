from __future__ import annotations

import io
import json
import warnings
from dataclasses import dataclass

from PIL import Image, ImageOps, UnidentifiedImageError


MIN_IMAGE_SIDE = 320
MAX_IMAGE_PIXELS = 24_000_000
MAX_IMAGE_SIDE = 12_000
HASH_SIZE = 16
AUTO_APPROVE_SCORE = 0.88
CLEAR_MISMATCH_SCORE = 0.52


class InvalidMeterImage(ValueError):
    pass


@dataclass(frozen=True)
class MatchResult:
    score: float
    decision: str
    slot_scores: tuple[float, ...]


def _difference_hash(image: Image.Image) -> str:
    sample = image.convert("L").resize(
        (HASH_SIZE + 1, HASH_SIZE),
        Image.Resampling.LANCZOS,
    )
    pixels = list(sample.get_flattened_data())
    bits = []
    width = HASH_SIZE + 1
    for row in range(HASH_SIZE):
        offset = row * width
        for column in range(HASH_SIZE):
            bits.append(pixels[offset + column] > pixels[offset + column + 1])
    value = sum(1 << index for index, bit in enumerate(bits) if bit)
    return f"{value:0{HASH_SIZE * HASH_SIZE // 4}x}"


def _histogram(image: Image.Image) -> list[float]:
    histogram = image.convert("L").resize((128, 128)).histogram()
    total = float(sum(histogram)) or 1.0
    buckets = []
    for start in range(0, 256, 16):
        buckets.append(sum(histogram[start : start + 16]) / total)
    return buckets


def fingerprint_image(payload: bytes) -> str:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(payload)) as source:
                source.verify()
            with Image.open(io.BytesIO(payload)) as source:
                width, height = source.size
                if (
                    width <= 0
                    or height <= 0
                    or width > MAX_IMAGE_SIDE
                    or height > MAX_IMAGE_SIDE
                    or width * height > MAX_IMAGE_PIXELS
                ):
                    raise InvalidMeterImage(
                        "Rasm o'lchami xavfsizlik limitidan oshgan."
                    )
                image = ImageOps.exif_transpose(source).convert("RGB")
            width, height = image.size
            if min(width, height) < MIN_IMAGE_SIDE:
                raise InvalidMeterImage(
                    f"Rasm juda kichik: {width}x{height}. "
                    f"Kamida {MIN_IMAGE_SIDE}px bo'lishi kerak."
                )
            center = ImageOps.fit(
                image,
                (max(MIN_IMAGE_SIDE, width // 2), max(MIN_IMAGE_SIDE, height // 2)),
                centering=(0.5, 0.5),
            )
            data = {
                "version": 1,
                "width": width,
                "height": height,
                "dhash": _difference_hash(image),
                "center_dhash": _difference_hash(center),
                "histogram": _histogram(image),
            }
            return json.dumps(data, separators=(",", ":"), sort_keys=True)
    except (
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
        UnidentifiedImageError,
        OSError,
        ValueError,
    ) as error:
        if isinstance(error, InvalidMeterImage):
            raise
        raise InvalidMeterImage("Yuborilgan fayl haqiqiy rasm sifatida o'qilmadi.") from error


def _hash_similarity(left: str, right: str) -> float:
    left_value = int(left, 16)
    right_value = int(right, 16)
    bit_count = HASH_SIZE * HASH_SIZE
    distance = (left_value ^ right_value).bit_count()
    return max(0.0, 1.0 - distance / bit_count)


def fingerprint_similarity(left: str, right: str) -> float:
    first = json.loads(left)
    second = json.loads(right)
    full = _hash_similarity(first["dhash"], second["dhash"])
    center = _hash_similarity(first["center_dhash"], second["center_dhash"])
    histogram = sum(
        min(float(a), float(b))
        for a, b in zip(first["histogram"], second["histogram"])
    )
    return round((full * 0.45) + (center * 0.45) + (histogram * 0.10), 4)


def compare_photo_sets(
    submitted: list[str],
    references: list[str],
) -> MatchResult:
    if not submitted or not references or len(submitted) != len(references):
        return MatchResult(0.0, "review", ())

    matrix = [
        [fingerprint_similarity(photo, reference) for reference in references]
        for photo in submitted
    ]
    states: dict[int, tuple[float, tuple[float, ...]]] = {0: (0.0, ())}
    for photo_index in range(len(submitted)):
        next_states: dict[int, tuple[float, tuple[float, ...]]] = {}
        for mask, (total, scores) in states.items():
            for reference_index in range(len(references)):
                bit = 1 << reference_index
                if mask & bit:
                    continue
                score = matrix[photo_index][reference_index]
                next_mask = mask | bit
                candidate = (total + score, scores + (score,))
                if (
                    next_mask not in next_states
                    or candidate[0] > next_states[next_mask][0]
                ):
                    next_states[next_mask] = candidate
        states = next_states
    best_total, best_scores = states[(1 << len(references)) - 1]
    best_average = best_total / len(best_scores)

    weakest = min(best_scores)
    if best_average >= AUTO_APPROVE_SCORE and weakest >= 0.80:
        decision = "approve"
    elif best_average <= CLEAR_MISMATCH_SCORE or weakest <= 0.35:
        decision = "reject"
    else:
        decision = "review"
    return MatchResult(round(best_average, 4), decision, best_scores)
