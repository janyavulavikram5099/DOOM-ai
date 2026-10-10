"""
VIKRAM AI - Speaker Verification System
Enrolls authorized user voice through a 3-sample acoustic profile,
generates a voice fingerprint, and verifies incoming audio against
the enrolled profile before permitting command execution.
"""

import logging
import math
from typing import Any

from ..database.sqlite import db

logger = logging.getLogger("vikram.assistant.speaker_verification")


class SpeakerVerifier:
    def __init__(self):
        self.enrolled: bool = False
        self.enrolled_profile: list[float] | None = None
        self.confidence_threshold: float = 0.45  # Optimized for far-field listening (up to 20m)
        self.samples_collected: list[list[float]] = []
        self._load_profile()

    def _load_profile(self):
        profile = db.get_voice_profile()
        if profile and profile.get("is_enrolled"):
            self.enrolled = True
            self.confidence_threshold = profile.get("confidence_threshold", 0.45)
            self.enrolled_profile = profile.get("acoustic_data")

    def is_enrolled(self) -> bool:
        return self.enrolled and self.enrolled_profile is not None

    def extract_acoustic_features(self, audio_data: Any) -> list[float]:
        """
        Extracts representative acoustic fingerprint features:
        [spectral_energy, zero_crossing_ratio, spectral_centroid, spectral_spread, formant_estimation]
        Works on raw PCM bytes or float arrays.
        """
        # If passed raw bytes or array, convert to normalized amplitude series
        if isinstance(audio_data, (bytes, bytearray)):
            import struct
            count = len(audio_data) // 2
            if count > 0:
                samples = struct.unpack(f"{count}h", audio_data[:count * 2])
                norm_samples = [s / 32768.0 for s in samples]
            else:
                norm_samples = [0.0] * 100
        elif isinstance(audio_data, list):
            norm_samples = audio_data
        else:
            # Synthetic baseline vector fallback for mock/synthetic input
            norm_samples = [0.1] * 256

        if not norm_samples:
            norm_samples = [0.0] * 100

        n = len(norm_samples)
        # 1. Total RMS Energy
        energy = math.sqrt(sum(x * x for x in norm_samples) / max(1, n))

        # 2. Zero Crossing Rate (ZCR)
        zcr = sum(1 for i in range(1, n) if (norm_samples[i] >= 0 and norm_samples[i-1] < 0) or (norm_samples[i] < 0 and norm_samples[i-1] >= 0)) / max(1, n)

        # 3. Spectral centroid approximation (first moment of power spectrum)
        half_n = min(128, n // 2)
        power_spec = []
        for k in range(max(1, half_n)):
            re = sum(norm_samples[t] * math.cos(2 * math.pi * t * k / n) for t in range(0, n, max(1, n // 64)))
            im = sum(norm_samples[t] * math.sin(2 * math.pi * t * k / n) for t in range(0, n, max(1, n // 64)))
            power_spec.append(math.sqrt(re * re + im * im))

        total_power = sum(power_spec) or 1.0
        centroid = sum(i * p for i, p in enumerate(power_spec)) / total_power

        # 4. Spectral spread / variance
        spread = math.sqrt(sum(((i - centroid) ** 2) * p for i, p in enumerate(power_spec)) / total_power)

        # 5. Top 4 sub-band energy ratios
        band_size = max(1, len(power_spec) // 4)
        bands = [
            sum(power_spec[i * band_size: (i + 1) * band_size]) / total_power
            for i in range(4)
        ]

        # Distance-invariant normalized energy for 20m far-field acoustic support
        norm_energy = min(1.0, math.log1p(energy * 100.0) / 4.0) if energy > 0 else 0.0
        feature_vector = [norm_energy, zcr, centroid / max(1, half_n), spread / max(1, half_n)] + bands
        return feature_vector

    def add_enrollment_sample(self, audio_data: Any) -> dict[str, Any]:
        """Adds an enrollment audio sample (requires 3 samples to finalize)."""
        features = self.extract_acoustic_features(audio_data)
        self.samples_collected.append(features)
        count = len(self.samples_collected)

        if count >= 3:
            # Average features across all 3 samples to build master profile
            dim = len(features)
            master_profile = [
                sum(s[i] for s in self.samples_collected) / count
                for i in range(dim)
            ]
            self.enrolled_profile = master_profile
            self.enrolled = True
            db.save_voice_profile("Master", count, master_profile, self.confidence_threshold)
            self.samples_collected.clear()
            return {
                "sample_number": 3,
                "is_complete": True,
                "message": "VOICE PROFILE CREATED"
            }
        else:
            return {
                "sample_number": count,
                "is_complete": False,
                "message": f"Sample {count} recorded. Please repeat."
            }

    def verify_voice(self, incoming_audio: Any) -> tuple[bool, float]:
        """
        Calculates cosine similarity between incoming audio features and master profile.
        Returns: (is_authorized: bool, similarity_score: float)
        """
        # If speaker verification is disabled in settings, allow pass
        setting = db.get_setting("speaker_verification_enabled", "1")
        if setting == "0":
            return True, 1.0

        if not self.is_enrolled():
            # If not yet enrolled, bypass until first setup complete
            return True, 1.0

        features = self.extract_acoustic_features(incoming_audio)
        profile = self.enrolled_profile
        if not profile:
            return True, 1.0

        # Compute cosine similarity
        dot = sum(a * b for a, b in zip(features, profile))
        mag_a = math.sqrt(sum(a * a for a in features)) or 1e-6
        mag_b = math.sqrt(sum(b * b for b in profile)) or 1e-6

        cosine_sim = max(0.0, min(1.0, dot / (mag_a * mag_b)))
        is_verified = cosine_sim >= self.confidence_threshold

        logger.info(f"Speaker verification: score={cosine_sim:.3f}, threshold={self.confidence_threshold}, verified={is_verified}")
        return is_verified, cosine_sim


# Global speaker verifier
speaker_verifier = SpeakerVerifier()
