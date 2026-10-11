"""Offline source checks for the papers; these do not compile TeX or verify research claims."""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PaperSourceTests(unittest.TestCase):
    def test_paper_environments_references_and_local_assets(self):
        papers = sorted((ROOT / "papers").glob("*/main.tex"))
        self.assertTrue(papers, "No paper sources found")
        for paper in papers:
            with self.subTest(paper=paper.relative_to(ROOT)):
                source = re.sub(r"(?<!\\)%.*", "", paper.read_text())
                stack = []
                for command, environment in re.findall(r"\\(begin|end)\{([^}]+)\}", source):
                    if command == "begin":
                        stack.append(environment)
                    else:
                        self.assertTrue(stack, f"Unexpected end of {environment}")
                        self.assertEqual(stack.pop(), environment)
                self.assertEqual(stack, [], "Unclosed environments")
                labels = re.findall(r"\\label\{([^}]+)\}", source)
                self.assertEqual(len(labels), len(set(labels)), "Duplicate labels")
                for reference in re.findall(r"\\(?:ref|eqref|autoref)\{([^}]+)\}", source):
                    self.assertIn(reference, labels, f"Undefined reference {reference}")
                bibliography_keys = set()
                for names in re.findall(r"\\bibliography\{([^}]+)\}", source):
                    for name in names.split(","):
                        bibliography = (paper.parent / name.strip()).with_suffix(".bib")
                        self.assertTrue(bibliography.is_file(), f"Missing bibliography {name}")
                        bibliography_keys.update(re.findall(r"@\w+\s*\{\s*([^,\s]+)\s*,", bibliography.read_text()))
                for names in re.findall(r"\\cite\w*\*?(?:\[[^\]]*\])*\{([^}]+)\}", source):
                    for key in names.split(","):
                        self.assertIn(key.strip(), bibliography_keys, f"Unknown citation {key}")
                for name in re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", source):
                    self.assertTrue((paper.parent / name).is_file(), f"Missing figure {name}")
