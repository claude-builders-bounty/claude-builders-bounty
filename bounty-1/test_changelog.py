import pathlib, subprocess, tempfile

SCRIPT = pathlib.Path(__file__).with_name("changelog.sh")

def run(*args, cwd):
    return subprocess.run(args, cwd=cwd, check=True, text=True, capture_output=True)

def test_changelog():
    with tempfile.TemporaryDirectory() as td:
        repo=pathlib.Path(td)
        run("git","init","-q",cwd=repo)
        run("git","config","user.email","test@example.com",cwd=repo)
        run("git","config","user.name","Test User",cwd=repo)
        (repo/"a.txt").write_text("base")
        run("git","add",".",cwd=repo); run("git","commit","-qm","chore: base",cwd=repo); run("git","tag","v1.0.0",cwd=repo)
        for msg, val in [("feat: add export","1"),("fix: repair parser","2"),("refactor: simplify flow","3"),("remove: old flag","4")]:
            (repo/"a.txt").write_text(val)
            run("git","add",".",cwd=repo); run("git","commit","-qm",msg,cwd=repo)
        run("bash",str(SCRIPT),cwd=repo)
        out=(repo/"CHANGELOG.md").read_text()
        assert "feat: add export" in out and "fix: repair parser" in out
        assert "refactor: simplify flow" in out and "remove: old flag" in out
        assert "chore: base" not in out
        for heading in ["### Added","### Fixed","### Changed","### Removed"]:
            assert heading in out

if __name__ == "__main__":
    test_changelog(); print("ok")
