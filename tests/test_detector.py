from __future__ import annotations

import math

import pytest

from sentinelops.detector import _compute_stats, _z_score_to_severity
from sentinelops.models import Severity


class TestComputeStats:
    def test_uniform_values(self):
        values = [10.0, 10.0, 10.0, 10.0]
        mean, stddev = _compute_stats(values)
        assert mean == 10.0
        assert stddev == 0.0

    def test_known_distribution(self):
        values = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
        mean, stddev = _compute_stats(values)
        assert mean == 5.0
        assert math.isclose(stddev, 2.0, abs_tol=0.01)

    def test_single_value(self):
        mean, stddev = _compute_stats([42.0])
        assert mean == 42.0
        assert stddev == 0.0

    def test_large_variance(self):
        values = [0.0, 100.0]
        mean, stddev = _compute_stats(values)
        assert mean == 50.0
        assert stddev == 50.0


class TestZScoreToSeverity:
    def test_p1(self):
        thresholds = {"p1": 5.0, "p2": 3.5, "p3": 2.5, "p4": 2.0}
        assert _z_score_to_severity(6.0, thresholds) == Severity.P1
        assert _z_score_to_severity(5.0, thresholds) == Severity.P1

    def test_p2(self):
        thresholds = {"p1": 5.0, "p2": 3.5, "p3": 2.5, "p4": 2.0}
        assert _z_score_to_severity(4.0, thresholds) == Severity.P2
        assert _z_score_to_severity(3.5, thresholds) == Severity.P2

    def test_p3(self):
        thresholds = {"p1": 5.0, "p2": 3.5, "p3": 2.5, "p4": 2.0}
        assert _z_score_to_severity(3.0, thresholds) == Severity.P3
        assert _z_score_to_severity(2.5, thresholds) == Severity.P3

    def test_p4(self):
        thresholds = {"p1": 5.0, "p2": 3.5, "p3": 2.5, "p4": 2.0}
        assert _z_score_to_severity(2.0, thresholds) == Severity.P4
        assert _z_score_to_severity(2.1, thresholds) == Severity.P4
