from eco_damage_monitor.cleaners.text_cleaner import clean_html_text, split_sentences


def test_clean_html_text_removes_noise() -> None:
    html = "<html><body><script>x=1</script><div>正文内容</div><div>责任编辑:张三</div></body></html>"
    cleaned = clean_html_text(html)
    assert "正文内容" in cleaned
    assert "责任编辑" not in cleaned


def test_split_sentences() -> None:
    text = "毁林问题严重。已经启动修复！"
    parts = split_sentences(text)
    assert len(parts) == 2
