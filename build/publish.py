"""Publish only validated, generated files; never publish the parent workspace."""
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = 'yalkongs/cspace'
BASE = 'https://yalkongs.github.io/cspace'


def run(*args, cwd=ROOT, capture=False):
    return subprocess.run(args, cwd=cwd, text=True, check=True,
                          stdout=subprocess.PIPE if capture else None).stdout


def main():
    run('node', 'build/validate.mjs', 'site', BASE)
    repo = json.loads(run('gh', 'repo', 'view', REPO, '--json', 'visibility,url', capture=True))
    if repo['visibility'] != 'PUBLIC':
        raise SystemExit('Publication requires a PUBLIC repository: ' + REPO)
    remote = f'https://github.com/{REPO}.git'
    # An isolated checkout keeps drafts and unrelated workspace files local.
    with tempfile.TemporaryDirectory(prefix='cspace-publish-') as tmp:
        checkout = Path(tmp)
        run('git', 'init', '-b', 'gh-pages', cwd=checkout)
        run('git', 'remote', 'add', 'origin', remote, cwd=checkout)
        refs = run('git', 'ls-remote', '--heads', remote, 'gh-pages', capture=True)
        if refs.strip():
            run('git', 'fetch', '--depth=1', 'origin', 'gh-pages', cwd=checkout)
            run('git', 'reset', '--soft', 'FETCH_HEAD', cwd=checkout)
        shutil.copytree(ROOT / 'site', checkout, dirs_exist_ok=True)
        shutil.copy2(ROOT / 'LICENSE', checkout / 'LICENSE')
        run('git', 'add', '--all', cwd=checkout)
        changed = run('git', 'status', '--porcelain', cwd=checkout, capture=True)
        if changed.strip():
            run('git', 'commit', '-m', 'Publish generated Book of Color site', cwd=checkout)
            run('git', 'push', 'origin', 'HEAD:gh-pages', cwd=checkout)
    print('Published generated files to ' + repo['url'] + '/tree/gh-pages')
    print('GitHub Pages: ' + BASE + '/')


if __name__ == '__main__':
    main()
