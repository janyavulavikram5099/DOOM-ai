"""
Unit tests for Speaker Verification & Voice Profile Enrollment.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.assistant.speaker_verification import SpeakerVerifier


class TestSpeakerVerification(unittest.TestCase):
    def test_voice_enrollment_and_verification(self):
        verifier = SpeakerVerifier()
        # Ensure fresh state for test
        verifier.enrolled = False
        verifier.enrolled_profile = None
        verifier.samples_collected.clear()

        # Step 1: Add sample 1
        res1 = verifier.add_enrollment_sample([0.1, 0.3, 0.5, 0.7, 0.4])
        self.assertEqual(res1["sample_number"], 1)
        self.assertFalse(res1["is_complete"])

        # Step 2: Add sample 2
        res2 = verifier.add_enrollment_sample([0.12, 0.32, 0.48, 0.69, 0.42])
        self.assertEqual(res2["sample_number"], 2)
        self.assertFalse(res2["is_complete"])

        # Step 3: Add sample 3
        res3 = verifier.add_enrollment_sample([0.11, 0.31, 0.51, 0.71, 0.39])
        self.assertEqual(res3["sample_number"], 3)
        self.assertTrue(res3["is_complete"])
        self.assertTrue(verifier.is_enrolled())

        # Test verification of similar voice
        ok, score = verifier.verify_voice([0.11, 0.31, 0.50, 0.70, 0.40])
        self.assertTrue(ok)
        self.assertGreater(score, 0.8)


if __name__ == "__main__":
    unittest.main()
