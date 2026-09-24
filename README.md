# The Book of Color

색채 이론의 주요 개념을 설명하고 인터랙티브 실험으로 이해를 돕는 정적 웹사이트.

- Public site: https://yalkongs.github.io/cspace/
- Public repository: https://github.com/yalkongs/cspace
- `main`: source, translations, build tools and static assets
- `gh-pages`: generated HTML and assets, served directly by GitHub Pages

## Build

Requires Python 3.10+ and Node.js 20+. No third-party build dependencies.

```sh
./deploy.sh --build-only
```

The highest numbered `index<N>.html` in the project root is the source (currently
`index32.html`). Files under `antigravity_builds/` are separate experiments and are
not selected automatically. Use `--source` to explicitly build another source:

```sh
python3 -B build/build.py --source index32.html --output site
```

`i18n/*.json` provides 11 language configurations. Indonesian is a partial
translation with English fallback. Unmatched translation entries are reported;
they are not proof of a fully translated page. `static/` contains the ancillary
pages, images and ten existing PDF editions, so rebuilding does not depend on
an old `dist/` directory. PDFs are preserved editions, not regenerated from HTML.

The build validates JavaScript syntax, JSON-LD, canonical URLs, language links,
internal routes and assets. Page routes use directory indexes and work under the
GitHub Pages `/cspace/` project path.

## Publish

```sh
gh auth login
./deploy.sh
```

The publisher requires `yalkongs/cspace` to be public. It pushes only `site/`
and the license to `gh-pages`, using an isolated temporary Git checkout. GitHub
Pages is configured to publish the root of that branch. No application build runs
on GitHub. `.nojekyll` preserves the generated files as-is.

The former Vercel deployment is retained as an existing historical deployment;
`deploy.sh` no longer invokes Vercel.

## Tests

```sh
python3 -B -m unittest discover -s build -p 'test_*.py'
node build/validate.mjs site https://yalkongs.github.io/cspace
```

Content and illustrations: CC BY-NC-SA 4.0; see `LICENSE`.
