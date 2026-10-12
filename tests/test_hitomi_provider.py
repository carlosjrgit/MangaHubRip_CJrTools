"""Testes unitários para o provedor Hitomi.la."""

import unittest
from unittest.mock import MagicMock, patch
from providers import HitomiProvider, ProviderRegistry, USER_AGENT


class TestHitomiProvider(unittest.TestCase):
    def setUp(self):
        self.provider = HitomiProvider()
        self.user_url = (
            "https://hitomi.la/doujinshi/%E7%95%B0%E4%B8%96%E7%95%8C%E3%83%8F%E3%83%BC%E3%83%AC%E3%83%A0"
            "%E3%83%91%E3%83%A9%E3%83%80%E3%82%A4%E3%82%B9%E7%95%AA%E5%A4%96%E7%B7%A8%EF%BD%9E%E7%A6%81"
            "%E6%AC%B2%E3%81%AE%E3%82%B7%E3%82%B9%E3%82%BF%E3%83%BC%E3%81%AE%E5%9B%BD%EF%BD%9E-ver2.0-"
            "%E6%97%A5%E6%9C%AC%E8%AA%9E-2789276.html#1"
        )

    def test_can_handle(self):
        self.assertTrue(self.provider.can_handle(self.user_url))
        self.assertTrue(self.provider.can_handle("https://hitomi.la/reader/2789276.html"))
        self.assertTrue(self.provider.can_handle("https://hitomi.la/manga/some-manga-12345.html"))
        self.assertTrue(self.provider.can_handle("https://hitomi.la/gamecg/game-999.html"))
        self.assertFalse(self.provider.can_handle("https://mangadex.org/title/1234"))
        self.assertFalse(self.provider.can_handle("https://mangalivre.net/manga/1234"))
        self.assertFalse(self.provider.can_handle(""))

    def test_extract_gallery_id(self):
        self.assertEqual(self.provider._extract_gallery_id(self.user_url), "2789276")
        self.assertEqual(self.provider._extract_gallery_id("https://hitomi.la/reader/2789276.html#12"), "2789276")
        self.assertEqual(self.provider._extract_gallery_id("https://hitomi.la/galleries/2789276.html"), "2789276")
        self.assertEqual(self.provider._extract_gallery_id("https://hitomi.la/doujinshi/sample-55512.html"), "55512")
        self.assertEqual(self.provider._extract_gallery_id("2789276"), "2789276")

    def test_provider_registry_resolution(self):
        prov = ProviderRegistry.get_provider_for_url(self.user_url)
        self.assertIsInstance(prov, HitomiProvider)
        self.assertEqual(prov.name, "hitomi")
        self.assertEqual(prov.display_name, "Hitomi.la")

    def test_request_headers(self):
        headers = self.provider.get_request_headers("https://w1.gold-usergeneratedcontent.net/1/page.webp")
        self.assertEqual(headers.get("User-Agent"), USER_AGENT)
        self.assertEqual(headers.get("Referer"), "https://hitomi.la/")

    def test_build_image_url(self):
        gg_params = {
            "b": "1790910001/",
            "default_o": 1,
            "case_o": 0,
            "cases": {1425},  # 1425 matches hash ending with 915 -> 591 hex = 1425
            "domain2": "gold-usergeneratedcontent.net"
        }
        file_info = {
            "hash": "fcb8f2f0b03ba673e03bc2c216cbcee5a62d2118a6760c4431439fdfce7ca915",
            "haswebp": 1,
            "name": "01.jpg"
        }
        url = self.provider._build_image_url(file_info, gg_params)
        # val will be case_o (0) because 1425 is in cases -> subdomain w(1+0) = w1
        self.assertEqual(
            url,
            "https://w1.gold-usergeneratedcontent.net/1790910001/1425/fcb8f2f0b03ba673e03bc2c216cbcee5a62d2118a6760c4431439fdfce7ca915.webp"
        )

    @patch.object(HitomiProvider, "_get_gallery_info")
    @patch.object(HitomiProvider, "_get_gg_params")
    def test_get_manga_info_and_chapters(self, mock_gg, mock_info):
        mock_gg.return_value = {
            "b": "1790910001/",
            "default_o": 1,
            "case_o": 0,
            "cases": {1425},
            "domain2": "gold-usergeneratedcontent.net"
        }
        mock_info.return_value = {
            "title": "Sample Romaji Title",
            "japanese_title": "サンプル日本語タイトル",
            "language": "japanese",
            "groups": [{"group": "SampleGroup"}],
            "files": [
                {
                    "hash": "fcb8f2f0b03ba673e03bc2c216cbcee5a62d2118a6760c4431439fdfce7ca915",
                    "haswebp": 1,
                    "name": "01.jpg"
                }
            ]
        }

        mock_session = MagicMock()
        info = self.provider.get_manga_info(self.user_url, mock_session)

        self.assertEqual(info["title"], "サンプル日本語タイトル")
        self.assertEqual(info["available_langs"], ["ja"])
        self.assertIn("gold-usergeneratedcontent.net", info["cover_url"])
        self.assertEqual(len(info["chapters"]), 1)
        self.assertEqual(info["chapters"][0]["chapter"], "1")
        self.assertEqual(info["chapters"][0]["group"], "SampleGroup")

        pages = self.provider.get_chapter_pages(info["chapters"][0], mock_session)
        self.assertEqual(len(pages), 1)
        self.assertTrue(pages[0].endswith(".webp"))


if __name__ == "__main__":
    unittest.main()
