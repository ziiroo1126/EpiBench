# Project webpage

The project page uses plain HTML, CSS, and JavaScript. It reuses the paper figures in
`assets/figures/` and needs no build step or external font/script downloads.

## Preview locally

From the repository root:

```bash
python -m http.server 8000 --bind 127.0.0.1
```

Open <http://127.0.0.1:8000/>. The page can also be opened directly from `index.html`;
if clipboard access is unavailable, the copy buttons select the text for manual copying.

## Publish with GitHub Pages

In [Settings → Pages](https://github.com/ziiroo1126/EpiBench/settings/pages):

1. Set **Source** to **Deploy from a branch**.
2. Select the **main** branch and **/ (root)** folder.
3. Save and wait for the Pages deployment to finish.

After Pages is enabled, the project URL is <https://ziiroo1126.github.io/EpiBench/>.
Future pushes to `main` update the page automatically. The root `.nojekyll` file
ensures GitHub serves these static files without Jekyll processing.

## Content and attribution

- Paper: <https://arxiv.org/abs/2608.06022v1>.
- Author affiliations, task descriptions, and results follow this paper version.
- The results table reproduces paper Table 2, including its T3 accuracy label. The
  dataset card instead lists balanced accuracy; both conventions are noted on the page.
- Figures and their extraction notes: [`assets/figures/README.md`](../assets/figures/README.md).
- The layout is inspired by the [ExplicitShortCut project page](https://edapinenut.github.io/explicitshortcut-project-page/),
  with an original implementation. No scripts or media from that site are bundled.
