def test_multimodal_compose():
    from backend.fus import compose_multimodal_action

    a = compose_multimodal_action('Zoom here', gaze=(450, 320))
    assert a == 'ZOOM_REGION_450_320'

    b = compose_multimodal_action('Highlight this', gaze=(12.4, 99.6))
    assert b == 'HIGHLIGHT_REGION_12_100'

    c = compose_multimodal_action('Analyze this region', gaze=(2,3))
    assert c == 'ANALYZE_REGION_2_3'

    d = compose_multimodal_action('zoom in', gaze=None)
    assert d is None
