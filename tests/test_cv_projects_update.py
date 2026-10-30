from pathlib import Path
import re
import unittest


class CvProjectsUpdateTests(unittest.TestCase):
    def test_profile_uses_new_portrait_and_preserves_original(self):
        config = Path("_config.yml").read_text(encoding="utf-8")
        self.assertRegex(
            config,
            r'(?m)^  avatar\s+: "images/profile_202606\.jpg"$',
        )
        self.assertTrue(Path("images/profile_202606.jpg").is_file())
        self.assertTrue(Path("images/profile.png").is_file())

    def test_bilingual_cv_assets_and_configuration(self):
        config = Path("_config.yml").read_text(encoding="utf-8")
        self.assertRegex(
            config,
            r'(?m)^  cv_en\s+: "assets/files/CV202609_EN\.pdf"$',
        )
        self.assertRegex(
            config,
            r'(?m)^  cv_zh\s+: "assets/files/CV202609_ZH\.pdf"$',
        )
        self.assertNotRegex(config, r"(?m)^  cv\s+:")
        for path in (
            Path("assets/files/CV202609_EN.pdf"),
            Path("assets/files/CV202609_ZH.pdf"),
        ):
            with self.subTest(path=path):
                self.assertTrue(path.is_file())
                self.assertGreater(path.stat().st_size, 0)

    def test_sidebar_exposes_both_localized_cv_links(self):
        profile = Path("_includes/author-profile.html").read_text(
            encoding="utf-8"
        )
        for label in (
            "CV (English, Sep 2026)",
            "CV (Chinese, Sep 2026)",
            "英文简历（2026 年 9 月）",
            "中文简历（2026 年 9 月）",
        ):
            with self.subTest(label=label):
                self.assertIn(label, profile)
        for key, label_key in (("cv_en", "t_cv_en"), ("cv_zh", "t_cv_zh")):
            with self.subTest(key=key):
                self.assertEqual(2, profile.count(f"{{% if author.{key} %}}"))
                self.assertEqual(
                    2,
                    profile.count(
                        f'href="{{{{ site.baseurl }}}}/{{{{ author.{key} }}}}"'
                    ),
                )
                self.assertIn(f'aria-label="{{{{ {label_key} }}}}"', profile)

    def test_interns_and_projects_are_visible_and_ordered(self):
        expected = {
            Path("_pages/includes/recent_projects.md"): (
                "# 🚀 Interns and Projects",
                "## Intern Experience",
                "## Projects {#project-list}",
                "ByteDance",
                "Human Intelligence",
                "Details forthcoming",
                [
                "General-Purpose Cybersecurity Agent",
                "Low-Dimensional Spatiotemporal Dynamics of the Human Brain",
                "Complex Social Awareness Modeling",
                "Intelligent Factory Security",
                "Large Language Model for Early Childhood Education",
                "Xiangqi Game-Playing System",
                ],
            ),
            Path("_pages/includes/zh/recent_projects.md"): (
                "# 🚀 实习与项目",
                "## 实习经历",
                "## 项目经历 {#project-list-zh}",
                "字节跳动",
                "智能知识",
                "详情待补充",
                [
                "通用网安智能体",
                "低维人脑时空动态",
                "复杂社会意识建模",
                "工厂智慧安防",
                "幼教大模型",
                "中国象棋博弈系统",
                ],
            ),
        }
        for path, values in expected.items():
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                heading, internship_heading, project_heading, first_intern, second_intern, placeholder, titles = values
                self.assertIn(heading, text)
                self.assertIn(internship_heading, text)
                self.assertIn(project_heading, text)
                self.assertNotIn("<details", text)
                self.assertLess(text.index(internship_heading), text.index(project_heading))
                self.assertLess(text.index(first_intern), text.index(second_intern))
                self.assertIn(placeholder, text)
                positions = [text.index(f"**{title}**") for title in titles]
                self.assertEqual(sorted(positions), positions)
                self.assertEqual(6, len(positions))
                self.assertIn("/bytedance", text)
                self.assertIn("/human-intelligence", text)

        self.assertTrue(any(Path("_pages/includes/images").glob("bytedance.*")))
        self.assertTrue(any(Path("_pages/includes/images").glob("human-intelligence.*")))

        self.assertIn(
            "title: 'Interns & Projects'",
            Path("_data/navigation.yml").read_text(encoding="utf-8"),
        )
        self.assertIn(
            "title: '实习与项目'",
            Path("_data/navigation-zh.yml").read_text(encoding="utf-8"),
        )

    def test_recent_projects_include_verified_metrics_only(self):
        english = Path("_pages/includes/recent_projects.md").read_text(
            encoding="utf-8"
        )
        chinese = Path("_pages/includes/zh/recent_projects.md").read_text(
            encoding="utf-8"
        )
        for phrase in (
            "5 specialized agents",
            "16-node bounded state machine",
            "R0-R3",
            "Finding-Evidence",
            "5 iterations",
            "100+ problems",
            "6.4/7",
            "600+ formalized data items",
            "70%+",
            "2,000+ data items",
            "11 production and quality specifications",
        ):
            with self.subTest(language="en", phrase=phrase):
                self.assertIn(phrase, english)
        for phrase in (
            "5 类专业 Agent",
            "16 节点有界状态机",
            "R0-R3",
            "Finding-Evidence",
            "5 个版本",
            "100 题以上",
            "6.4/7",
            "600+ 条形式化数据",
            "70%+",
            "2,000+ 条数据",
            "11 份数据生产与质量规范",
        ):
            with self.subTest(language="zh", phrase=phrase):
                self.assertIn(phrase, chinese)
        for obsolete in (
            "Development of LLM-Driven Smart Cultural Tourism System",
            "Leadership Evaluation Framework Under Polygenic Risk",
            "7-role",
            "thousands of agent actions",
        ):
            self.assertNotIn(obsolete, english)
        for obsolete in (
            "大模型驱动的智慧文旅系统",
            "多基因风险下的领导力评估框架",
            "7 角色",
            "上千次智能体动作",
        ):
            self.assertNotIn(obsolete, chinese)

    def test_homepage_timestamps_are_september_2026(self):
        self.assertIn(
            "Last updated: Sep. 2026",
            Path("_pages/about.md").read_text(encoding="utf-8"),
        )
        self.assertIn(
            "最后更新：2026 年 9 月",
            Path("_pages/zh.md").read_text(encoding="utf-8"),
        )


if __name__ == "__main__":
    unittest.main()
