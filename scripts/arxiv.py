"""Build Paper 1 and verify its source archive using only the pinned Docker TeX image."""

import gzip
import io
import os
import re
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SUFFIXES = {".tex", ".bib", ".sty", ".cls", ".png", ".jpg", ".jpeg", ".pdf", ".eps"}
PATH_COMMAND = re.compile(
    r"\\(?:input|include|includegraphics|bibliography|bibliographystyle)(?:\[[^]]*\])?\{([^}]+)\}"
)


def validate_paths(text: str) -> None:
    """Reject non-portable literal input paths (TeX resolves macros during the isolated build)."""
    text = re.sub(r"(?<!\\)%[^\n]*", "", text)
    for group in PATH_COMMAND.findall(text):
        for name in group.split(","):
            path = PurePosixPath(name.strip())
            if path.is_absolute() or ".." in path.parts or re.match(r"^[A-Za-z]:", name):
                raise ValueError(f"Non-portable TeX input: {name}")


def stage_sources(root: Path, stage: Path) -> None:
    paper = root / "papers/europriv-bench"
    for source in sorted(paper.rglob("*")):
        if source.is_symlink():
            raise ValueError(f"Symlink in paper sources: {source}")
        if not source.is_file() or source.suffix not in SOURCE_SUFFIXES or source.name == "main.pdf":
            continue
        target = stage / source.relative_to(paper)
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.suffix == ".tex":
            text = source.read_text().replace(r"\bibliography{../../shared/klusai}", r"\bibliography{klusai}")
            validate_paths(text)
            target.write_text(text)
        else:
            shutil.copyfile(source, target)
    shutil.copyfile(root / "shared/klusai.bib", stage / "klusai.bib")


def docker_tex(directory: Path, *command: str) -> None:
    # Stream files rather than bind-mounting: shared/remote Docker daemons may not
    # expose the client worktree. The container sees only this build directory.
    payload = io.BytesIO()
    with tarfile.open(fileobj=payload, mode="w") as bundle:
        for path in sorted(directory.iterdir()):
            bundle.add(path, arcname=path.name)
    result = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--network",
            "none",
            "--interactive",
            "--workdir",
            "/work",
            os.environ["TEX_IMAGE"],
            "sh",
            "-c",
            'tar -xf - && { "$@" >&2; status=$?; tar -cf - .; exit "$status"; }',
            "sh",
            *command,
        ],
        input=payload.getvalue(),
        stdout=subprocess.PIPE,
    )
    if result.stdout:
        with tarfile.open(fileobj=io.BytesIO(result.stdout)) as bundle:
            bundle.extractall(directory, filter="data")
    result.check_returncode()


def check_log(directory: Path) -> None:
    log = (directory / "main.log").read_text()
    errors = [
        r"LaTeX Warning: (?:Citation|Reference).*undefined",
        r"There were undefined (?:references|citations)",
        r"LaTeX Warning: Label\(s\) may have changed",
        r"Overfull \\[hv]box",
        r"Missing character:",
        r"^!",
    ]
    for pattern in errors:
        if re.search(pattern, log, re.MULTILINE):
            raise ValueError(f"Unclean TeX build ({pattern}); see {directory / 'main.log'}")
    if not (directory / "main.pdf").is_file():
        raise ValueError("TeX did not produce main.pdf")


def archive_inputs(stage: Path) -> list[Path]:
    """Use TeX's recorder to include referenced figures/styles, excluding build debris."""
    paths = {Path("main.tex"), Path("main.bbl"), Path("klusai.bib")}
    for line in (stage / "main.fls").read_text().splitlines():
        if not line.startswith("INPUT "):
            continue
        name = line[6:]
        if name.startswith("/work/"):
            name = name[len("/work/") :]
        path = Path(name)
        if path.is_absolute():  # TeX distribution files are provided by the pinned image.
            continue
        if ".." in path.parts:
            raise ValueError(f"TeX input escapes the archive: {name}")
        if path.suffix in SOURCE_SUFFIXES or path.suffix == ".bbl":
            paths.add(path)
    for path in paths:
        if not (stage / path).is_file():
            raise ValueError(f"Missing archive input: {path}")
    if not (stage / "main.bbl").stat().st_size:
        raise ValueError("Empty bibliography")
    return sorted(paths)


def pack_archive(stage: Path, archive: Path) -> None:
    # Stable headers make the source tarball reproducible across worktrees and build dates.
    with archive.open("wb") as output, gzip.GzipFile(fileobj=output, mode="wb", filename="", mtime=0) as zipped:
        with tarfile.open(fileobj=zipped, mode="w") as bundle:
            for path in archive_inputs(stage):
                info = bundle.gettarinfo(str(stage / path), arcname=path.as_posix())
                info.uid = info.gid = info.mtime = 0
                info.uname = info.gname = ""
                info.mode = 0o644
                with (stage / path).open("rb") as source:
                    bundle.addfile(info, source)


def main() -> None:
    build = ROOT / "build/paper1"
    dist = ROOT / "dist"
    build.mkdir(parents=True, exist_ok=True)
    dist.mkdir(exist_ok=True)
    # Work in a fresh directory: stale aux/bbl/figures cannot mask missing dependencies.
    with tempfile.TemporaryDirectory(dir=build, prefix="source-") as temporary:
        stage = Path(temporary)
        stage_sources(ROOT, stage)
        docker_tex(
            stage,
            "latexmk",
            "-pdf",
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-file-line-error",
            "-latexoption=-no-shell-escape",
            "main.tex",
        )
        check_log(stage)
        archive = stage / "paper1-arxiv.tar.gz"
        pack_archive(stage, archive)
        with tempfile.TemporaryDirectory(dir=build, prefix="verify-") as extracted:
            verify = Path(extracted)
            with tarfile.open(archive) as bundle:
                bundle.extractall(verify, filter="data")
            # Only the extracted archive is transferred; BibTeX is deliberately not run.
            for _ in range(2):
                docker_tex(
                    verify,
                    "pdflatex",
                    "-no-shell-escape",
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    "-file-line-error",
                    "main.tex",
                )
            check_log(verify)
            shutil.copyfile(verify / "main.pdf", dist / "paper1.pdf")
            shutil.copyfile(verify / "main.log", build / "verified.log")
        shutil.copyfile(archive, dist / archive.name)
    print("Verified: dist/paper1.pdf and dist/paper1-arxiv.tar.gz", flush=True)


if __name__ == "__main__":
    main()
