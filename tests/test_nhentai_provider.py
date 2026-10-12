"""Testes unitários para o provedor NHentai."""

import unittest
from unittest.mock import MagicMock
from providers import NHentaiProvider, ProviderRegistry, USER_AGENT
from manga_core import QueueTask, calculate_task_estimates


class TestNHentaiProvider(unittest.TestCase):
    def setUp(self):
        self.provider = NHentaiProvider()
        self.user_url = "https://nhentai.to/g/624421/"

    def test_can_handle(self):
        self.assertTrue(self.provider.can_handle(self.user_url))
        self.assertTrue(self.provider.can_handle("https://nhentai.to/g/624421"))
        self.assertTrue(self.provider.can_handle("https://nhentai.net/g/12345/"))
        self.assertTrue(self.provider.can_handle("https://nhentai.xxx/g/99999/"))
        self.assertFalse(self.provider.can_handle("https://mangadex.org/title/1234"))
        self.assertFalse(self.provider.can_handle("https://hitomi.la/doujinshi/test-123.html"))
        self.assertFalse(self.provider.can_handle(""))

    def test_extract_gallery_id(self):
        self.assertEqual(self.provider._extract_gallery_id(self.user_url), "624421")
        self.assertEqual(self.provider._extract_gallery_id("https://nhentai.to/g/624421#2"), "624421")
        self.assertEqual(self.provider._extract_gallery_id("https://nhentai.net/g/624421/?test=1"), "624421")
        self.assertEqual(self.provider._extract_gallery_id("624421"), "624421")

    def test_provider_registry_resolution(self):
        prov = ProviderRegistry.get_provider_for_url(self.user_url)
        self.assertIsInstance(prov, NHentaiProvider)
        self.assertEqual(prov.name, "nhentai")
        self.assertEqual(prov.display_name, "NHentai")

    def test_request_headers(self):
        headers = self.provider.get_request_headers("https://supercdn.site/galleries/624421/1.webp", "https://nhentai.to/g/624421/")
        self.assertEqual(headers.get("User-Agent"), USER_AGENT)
        self.assertEqual(headers.get("Referer"), "https://nhentai.to")

    def test_get_manga_info(self):
        mock_html = """
        <html>
            <head><title>[Kokusan JK] Ihen Deguch » nhentai: hentai doujinshi and manga</title></head>
            <body>
                <div id="info">
                    <h1>[Kokusan JK (Velzhe)] Ihen Deguch - The Exit Anomaly</h1>
                </div>
                <div id="cover">
                    <img src="https://supercdn.site/galleries/624421/thumb.webp" />
                </div>
                <div class="tag-container">
                    <a href="/language/english/"><span class="name">english</span></a>
                    <a href="/group/kokusan-jk/"><span class="name">kokusan jk</span></a>
                </div>
            </body>
        </html>
        """
        mock_session = MagicMock()
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.text = mock_html
        mock_session.get.return_value = mock_res

        info = self.provider.get_manga_info(self.user_url, mock_session)
        self.assertEqual(info["title"], "[Kokusan JK (Velzhe)] Ihen Deguch - The Exit Anomaly")
        self.assertEqual(info["cover_url"], "https://supercdn.site/galleries/624421/thumb.webp")
        self.assertEqual(info["available_langs"], ["en"])
        self.assertEqual(len(info["chapters"]), 1)
        self.assertEqual(info["chapters"][0]["chapter"], "1")
        self.assertEqual(info["chapters"][0]["group"], "kokusan jk")

    def test_get_chapter_pages(self):
        mock_html = """
        <html>
            <body>
                <div id="thumbnail-container">
                    <div class="thumb-container">
                        <a href="/g/624421/1/"><img data-src="https://supercdn.site/galleries/624421/1t.webp" /></a>
                    </div>
                    <div class="thumb-container">
                        <a href="/g/624421/2/"><img data-src="https://supercdn.site/galleries/624421/2t.webp" /></a>
                    </div>
                    <div class="thumb-container">
                        <a href="/g/624421/3/"><img data-src="https://supercdn.site/galleries/624421/3t.webp" /></a>
                    </div>
                </div>
            </body>
        </html>
        """
        mock_session = MagicMock()
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.text = mock_html
        mock_session.get.return_value = mock_res

        chapter = {"id": "624421", "url": self.user_url}
        pages = self.provider.get_chapter_pages(chapter, mock_session)
        self.assertEqual(len(pages), 3)
        self.assertEqual(pages[0], "https://supercdn.site/galleries/624421/1.webp")
        self.assertEqual(pages[1], "https://supercdn.site/galleries/624421/2.webp")
        self.assertEqual(pages[2], "https://supercdn.site/galleries/624421/3.webp")

    def test_task_estimates(self):
        task = QueueTask(
            id="test-1",
            url=self.user_url,
            title="Test Manga",
            provider="nhentai",
            selected_chapters=[{"id": "624421", "chapter": "1"}]
        )
        mb, sec = calculate_task_estimates(task)
        self.assertGreater(mb, 0)
        self.assertGreater(sec, 0)


if __name__ == "__main__":
    unittest.main()
