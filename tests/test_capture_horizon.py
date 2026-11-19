from pathlib import Path

import httpx
import pytest

from app.capture_horizon import parse_feed, refresh


def atom(body: str) -> bytes:
    return ('''<feed xmlns="http://www.w3.org/2005/Atom"><title>Horizon</title><id>horizon</id>
    <entry><title>Horizon Summary: 2026-11-18 (ZH)</title>
    <link href="https://thysrael.github.io/Horizon/2026/11/18/summary-zh.html"/>
    <id>day</id><content type="html"><![CDATA[''' + body + ''']]></content></entry></feed>''').encode()


ARTICLE = '''<h2>科技新闻</h2><ol><li><a href="#item-1">目录标题</a></li></ol>
<p><a id="item-1"></a></p><h3 id="article-1"><a href="https://example.org/news">新工具发布</a> ⭐️ 8.0/10</h3>
<p>这是摘要<script>evil()</script>，保留纯文本。</p><p>hackernews · <a href="https://news.ycombinator.com/item?id=42">社区讨论</a></p>
<p><strong>标签</strong>: <code>#AI</code></p><hr>
<h2>科技博客</h2><h3><a href="javascript:alert(1)">恶意链接</a> 9/10</h3><p>不要显示</p>'''


def test_parse_digest_keeps_attribution_links_category_and_score_without_toc_or_html():
    payload = parse_feed(atom(ARTICLE))
    assert payload['attribution'] == 'Horizon · Thysrael'
    assert len(payload['items']) == 1
    row = payload['items'][0]
    assert row['title'] == '新工具发布'
    assert row['category'] == '科技新闻'
    assert row['score'] == 8
    assert row['tags'] == ['AI']
    assert row['summary'] == '这是摘要，保留纯文本。'
    assert row['digest_url'].endswith('#article-1')
    assert row['discussion_url'].endswith('id=42')


@pytest.mark.parametrize('body', ['<h2>changed markup</h2>', '<html>challenge</html>'])
def test_unrecognized_feed_preserves_previous_snapshot(tmp_path: Path, body: str):
    output = tmp_path / 'server-horizon.json'
    output.write_text('old snapshot', encoding='utf-8')
    with httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200, content=atom(body)))) as client:
        with pytest.raises(ValueError):
            refresh(output, client=client)
    assert output.read_text() == 'old snapshot'


def test_http_failure_preserves_snapshot(tmp_path: Path):
    output = tmp_path / 'feed.json'
    output.write_text('old snapshot')
    with httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(503))) as client:
        with pytest.raises(httpx.HTTPStatusError):
            refresh(output, client=client)
    assert output.read_text() == 'old snapshot'


def test_successful_capture_replaces_snapshot_atomically(tmp_path: Path):
    output = tmp_path / 'feed.json'
    with httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200, content=atom(ARTICLE)))) as client:
        result = refresh(output, client=client)
    assert result['latest_issue'] == '2026-11-18'
    assert '新工具发布' in output.read_text(encoding='utf-8')
    assert len(list(tmp_path.iterdir())) == 1
