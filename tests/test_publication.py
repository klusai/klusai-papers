"""Publication contracts; the actual clean-room TeX integration test is `make arxiv`."""

import json
import re
import tarfile
import tempfile
import unittest
from pathlib import Path

import yaml

from scripts.arxiv import ROOT, archive_inputs, check_log, pack_archive, stage_sources, validate_paths


class PublicationTests(unittest.TestCase):
    def test_metadata_agrees_with_manuscript(self):
        citation = yaml.safe_load((ROOT / "CITATION.cff").read_text())
        zenodo = json.loads((ROOT / ".zenodo.json").read_text())
        source = (ROOT / "papers/europriv-bench/main.tex").read_text()
        title = re.search(r"\\title\{([^}]+)\}", source)[1]
        title = " ".join(title.replace(r"\\", " ").split())
        self.assertEqual(title, citation["title"])
        self.assertEqual(title, citation["preferred-citation"]["title"])
        self.assertEqual(title, zenodo["title"])
        self.assertIn(title, (ROOT / "README.md").read_text())
        self.assertIn(title, (ROOT / "shared/klusai.bib").read_text())
        author = re.search(r"\\author\{([^}]+)\}", source)[1]
        self.assertEqual([author], [a["name"] for a in citation["authors"]])
        self.assertEqual([author], [a["name"] for a in zenodo["creators"]])
        self.assertEqual(zenodo["license"], citation["license"])
        self.assertEqual(zenodo["license"], "Apache-2.0")
        self.assertEqual(zenodo["upload_type"], "publication")
        self.assertEqual(zenodo["publication_type"], "preprint")
        self.assertEqual(len(zenodo["related_identifiers"]), 3)
        self.assertTrue(zenodo["keywords"])

    def test_reject_nonportable_tex_paths(self):
        for name in ("/Users/author/figure.pdf", "../figure", "../../refs", "C:/figure.pdf"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                validate_paths(r"\input{" + name + "}")
        validate_paths(r"\includegraphics[width=\textwidth]{figures/plot.pdf}")

    def test_staging_rewrites_bibliography(self):
        with tempfile.TemporaryDirectory() as temp:
            stage = Path(temp)
            stage_sources(ROOT, stage)
            self.assertIn(r"\bibliography{klusai}", (stage / "main.tex").read_text())
            self.assertTrue((stage / "klusai.bib").is_file())

    def test_archive_contains_only_referenced_assets_and_bibliography(self):
        with tempfile.TemporaryDirectory() as temp:
            stage = Path(temp)
            for name in ("main.tex", "main.bbl", "klusai.bib", "plot.pdf", "unused.png", "main.aux"):
                (stage / name).write_text("fixture")
            (stage / "main.fls").write_text(
                "INPUT /work/main.tex\nINPUT ./plot.pdf\nINPUT main.aux\nINPUT /usr/local/texlive/article.cls\n"
            )
            archive = stage / "sources.tar.gz"
            pack_archive(stage, archive)
            with tarfile.open(archive) as bundle:
                self.assertEqual(bundle.getnames(), ["klusai.bib", "main.bbl", "main.tex", "plot.pdf"])
            first = archive.read_bytes()
            pack_archive(stage, archive)
            self.assertEqual(first, archive.read_bytes())
            (stage / "main.bbl").unlink()
            with self.assertRaisesRegex(ValueError, "Missing archive input"):
                archive_inputs(stage)

    def test_missing_figure_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            stage = Path(temp)
            for name in ("main.tex", "main.bbl", "klusai.bib"):
                (stage / name).write_text("fixture")
            (stage / "main.fls").write_text("INPUT figures/missing.png\n")
            with self.assertRaisesRegex(ValueError, "Missing archive input"):
                archive_inputs(stage)

    def test_unresolved_citation_or_overflow_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            stage = Path(temp)
            (stage / "main.pdf").write_bytes(b"%PDF-fixture")
            for warning in ("LaTeX Warning: Citation `missing' on page 1 undefined", r"Overfull \hbox (20pt too wide)"):
                (stage / "main.log").write_text(warning)
                with self.assertRaisesRegex(ValueError, "Unclean TeX build"):
                    check_log(stage)

    def test_release_trigger_and_asset_order(self):
        # BaseLoader preserves YAML's `on` key as a string instead of YAML 1.1's boolean.
        workflow = yaml.load((ROOT / ".github/workflows/paper1-release.yml").read_text(), Loader=yaml.BaseLoader)
        self.assertEqual(workflow["on"], {"push": {"tags": ["paper1-v*"]}})
        steps = workflow["jobs"]["release"]["steps"]
        commands = "\n".join(step.get("run", "") for step in steps)
        self.assertLess(commands.index("make check"), commands.index("make arxiv"))
        self.assertLess(commands.index("make arxiv"), commands.index("gh release create"))
        self.assertLess(commands.index("gh release upload"), commands.index("--draft=false"))
        self.assertIn("dist/paper1.pdf dist/paper1-arxiv.tar.gz", commands)


if __name__ == "__main__":
    unittest.main()
