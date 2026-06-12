"""Unit tests for the shared offset pagination helper (pure function only)."""

from app.pagination import Page, paginate


def test_mid_range_page_has_more_and_next_start():
    assert paginate(total=100, start=20, page_size=20) == Page(has_more=True, next_start=40)


def test_first_page_of_many():
    page = paginate(total=200, start=0, page_size=10)
    assert page.has_more is True
    assert page.next_start == 10


def test_last_partial_page_stops():
    # window [40:60) over 45 rows returns 5 rows with nothing beyond
    page = paginate(total=45, start=40, page_size=20)
    assert page.has_more is False
    assert page.next_start is None


def test_page_past_tail_is_empty_tail():
    page = paginate(total=45, start=60, page_size=20)
    assert page.has_more is False
    assert page.next_start is None


def test_exact_last_full_page_stops():
    # start + page_size == total: the window is the final full page, no next cursor
    page = paginate(total=40, start=20, page_size=20)
    assert page.has_more is False
    assert page.next_start is None


def test_page_size_boundary_one_row_beyond():
    # a single row past the window keeps paging open
    page = paginate(total=41, start=20, page_size=20)
    assert page.has_more is True
    assert page.next_start == 40


def test_empty_total_has_no_pages():
    page = paginate(total=0, start=0, page_size=50)
    assert page.has_more is False
    assert page.next_start is None


def test_page_size_one_walks_to_the_end():
    assert paginate(total=3, start=0, page_size=1) == Page(has_more=True, next_start=1)
    assert paginate(total=3, start=2, page_size=1) == Page(has_more=False, next_start=None)
