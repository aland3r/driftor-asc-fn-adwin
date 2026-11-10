from adwin.domain.segments import change_percent, segment_means


def test_segment_means_between_drifts():
    values = [1, 1, 5, 5, 9, 9]
    assert segment_means(values, [2, 4]) == [(1.0, 5.0), (5.0, 9.0)]
    assert change_percent(10, 15) == 50.0
    assert change_percent(0, 3) == 0.0
