import pytest
import crawl


@pytest.mark.parametrize('expected_url, base_url, year, month', [
    ("https://test.de/?=what/2000-01/", "https://test.de/?=what/", 2000, 1),
    ("https://test.de/?=what/2019-12/", "https://test.de/?=what/", 2019, 12),
    ("https://test.de/?x=1&y=2019-12/", "https://test.de/?x=1&y=", 2019, 12)])
def test_build_url_for_month(expected_url, base_url, year, month):
    assert expected_url == crawl.build_url_for_month(base_url, year, month)


def test_get_html_of_month():
    html = crawl.get_html_of_month("http://localhost:8081/", 2019, 8, testing=True)
    assert len(html) >= 10000


def test_get_html_of_month_different_months_are_different():
    july = crawl.get_html_of_month("http://localhost:8081/", 2019, 7, testing=True)
    august = crawl.get_html_of_month("http://localhost:8081/", 2019, 8, testing=True)
    assert july != august
    