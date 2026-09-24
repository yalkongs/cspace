# The Book of Color

**Understand color theory by reading, experimenting, and comparing.**

[한국어](README.md) · English

[Read the book](https://yalkongs.github.io/cspace/) · [Read in Korean](https://yalkongs.github.io/cspace/ko/) · [About and references](https://yalkongs.github.io/cspace/about/) · [How to cite](https://yalkongs.github.io/cspace/cite/)

## About the book

**The Book of Color** is an interactive web book that explains the main concepts of color theory through experiments readers can manipulate themselves. It begins with wavelengths of light and moves through vision, the mixing of light and paint, color spaces and harmonies, the history of names and pigments, and color in nature and on displays.

Read a passage, move a slider, change an illuminant, or place two colors beside one another. Explore why equal numerical values can look different, how different spectra can produce a color match, and why mixing colors on a screen differs from mixing paint. The book connects an explanation with an experiment on the same page.

It is intended for students and teachers, designers and developers, people working with painting and photography, and anyone curious about everyday color. Read it in sequence or open a chapter directly through its own URL. Reading the website requires no account or installation.

## Fourteen chapters

| Chapter | Main ideas | Experiments and tools |
|---|---|---|
| [1. Light](https://yalkongs.github.io/cspace/light/) | Visible wavelengths, refraction and dispersion, temperature and the color of light | Newton's prism, a visible-spectrum explorer, the Planckian locus |
| [2. The Eye](https://yalkongs.github.io/cspace/eye/) | Cone responses, trichromacy, metamerism, chromatic adaptation, and vision at low light levels | Cone responses, illuminant-dependent metamerism, the Abney effect, white balance, the Purkinje shift, Benham's top |
| [3. Mixing](https://yalkongs.github.io/cspace/mixing/) | Additive light, subtractive filters and inks, pigment absorption and scattering, temporal mixing | Light versus pigment, a Kubelka–Munk mixing model, Maxwell's spinning discs |
| [4. The Wheel](https://yalkongs.github.io/cspace/wheel/) | Arranging hues in a circle; the perspectives of Newton, Goethe, and Itten | RGB/RYB wheel switching and historical color-wheel comparisons |
| [5. Three Dimensions](https://yalkongs.github.io/cspace/space/) | Hue, value, and chroma as a space; color solids and their cross-sections | Rotating and slicing color solids, value–saturation exploration, tints, shades, and tones |
| [6. Harmony](https://yalkongs.github.io/cspace/harmony/) | Complementary, analogous, triadic, and other relationships; the geometry of palettes | A harmony explorer, composition previews, Newton's color–music keyboard |
| [7. Color Spaces](https://yalkongs.github.io/cspace/spaces/) | HSL and OKLCH, perceptual uniformity, CIE chromaticity, and device gamuts | HSL/OKLCH comparison, Helmholtz–Kohlrausch brightness matching, the CIE 1931 diagram, a gamut viewfinder |
| [8. The Interaction of Color](https://yalkongs.github.io/cspace/interaction/) | The effects of surrounding colors, adaptation, and context; opponent processes and color constancy | Hering's color cancellation, Albers-style simultaneous contrast, neon color spreading, afterimages, Land's two-color projection |
| [9. Color in Practice](https://yalkongs.github.io/cspace/practice/) | Text/background contrast, differences in color vision, and the proportions of a composition | A contrast checker, a color-vision-deficiency simulator, a 60–30–10 proportion experiment |
| [10. A Glossary of Color](https://yalkongs.github.io/cspace/glossary/) | The vocabulary of the preceding chapters and the relationships between concepts | A searchable glossary with chapter cross-references |
| [11. Names](https://yalkongs.github.io/cspace/names/) | Color names, linguistic categories, and theories about culture and color discrimination | Berlin and Kay's stage theory and a color-discrimination reaction-time experiment |
| [12. Pigments](https://yalkongs.github.io/cspace/pigments/) | Pigment history, lightfastness and fading, paint materials and labeling | A pigment timeline, a light-exposure fading model, a paint-tube label guide |
| [13. Nature](https://yalkongs.github.io/cspace/nature/) | Pigment and structural color, atmospheric scattering, and fluorescence | Rayleigh's sky and a fluorescence experiment illustrating the Stokes shift |
| [14. Practice: Displays and Production](https://yalkongs.github.io/cspace/practice2/) | Display gamut, accuracy, bit depth, HDR, calibration, and ICC profiles | A monitor-specification guide that changes with the selected use case |

The chapters are followed by [A Chronology](https://yalkongs.github.io/cspace/#chronology), tracing milestones in the history of color, and [A Palette of Your Own](https://yalkongs.github.io/cspace/#coda). The palette generator combines harmony relationships with OKLCH lightness steps to suggest five colors, exportable as **Hex values, CSS custom properties, a Tailwind configuration snippet, or SVG**.

## Experiments to try first

1. **Move through the spectrum — Chapters 1 and 2.** Change the wavelength and compare its position in the spectrum, the displayed color, and the cone-response representation. Start connecting a physical stimulus to visual perception.
2. **Change the illuminant — Chapter 2.** Observe how two samples that look similar under one light can separate under another. Connect metamerism to familiar experiences with clothing, fabrics, and printed material.
3. **Mix light and paint — Chapter 3.** Change the mixing ratio and compare the outcomes of different models. Distinguish calculations on RGB values from the physical mixing of pigments.
4. **Put one color on two backgrounds — Chapter 8.** Keep the central color fixed while changing its surroundings. Compare a color viewed as an isolated swatch with the same color in a composition.
5. **Build a readable palette — Chapter 9 and the Coda.** Explore text/background contrast and color-vision simulations, then generate a palette and copy it in a format suitable for your work.

## Suggested reading paths

- **New to color theory:** Chapters 1 → 2 → 3 → 4 → 5. Build an understanding of light, vision, and mixing before moving to wheels and spaces. Use Chapter 10 to look up unfamiliar terms.
- **Design and web development:** Chapters 6 → 7 → 8 → 9 → the palette generator. Connect harmony, perception, context, and readability.
- **Painting, photography, and print:** Chapters 2 → 3 → 7 → 12 → 14. Follow illumination and mixing through to pigments and reproduction media.
- **History, culture, and nature:** Chapters 4 → 11 → 12 → 13 → the chronology. Explore how people have classified, named, and produced colors.

## Reading the experiments

The interface uses neutral grays to reduce interference from surrounding UI colors and keep attention on the colors under discussion. Compare patches with the accompanying values, curves, and explanations, changing one variable at a time.

The figures are educational models running in a browser on a display. They cannot reproduce every physical property of monochromatic light, pigments, fluorescence, or printed material. Gamut, display settings, ambient light, and individual perception can affect what you observe. Reaction-time, color-vision, and brightness-matching activities do not replace professional measurement or diagnosis. Historical theories and palette rules should also be read in their respective contexts.

The implementation includes keyboard interactions, ARIA descriptions, status feedback, reduced-motion handling, and print styles. The presentation and accessibility of individual experiments remain open to review and improvement.

## Languages and offline editions

[English](https://yalkongs.github.io/cspace/) · [한국어](https://yalkongs.github.io/cspace/ko/) · [日本語](https://yalkongs.github.io/cspace/ja/) · [Español](https://yalkongs.github.io/cspace/es/) · [中文](https://yalkongs.github.io/cspace/zh/) · [Français](https://yalkongs.github.io/cspace/fr/) · [Deutsch](https://yalkongs.github.io/cspace/de/) · [Português](https://yalkongs.github.io/cspace/pt/) · [Italiano](https://yalkongs.github.io/cspace/it/) · [Tiếng Việt](https://yalkongs.github.io/cspace/vi/) · [Bahasa Indonesia](https://yalkongs.github.io/cspace/id/)

There are 11 language configurations, and translations are a work in progress. Indonesian is a partial translation; some English passages also remain in other editions. The language selector supports switching languages while viewing a chapter.

Ten PDF editions, including [English](https://yalkongs.github.io/cspace/pdf/book-of-color-en.pdf) and [Korean](https://yalkongs.github.io/cspace/pdf/book-of-color-ko.pdf), are available from the [About page](https://yalkongs.github.io/cspace/about/). These are **archived May 2026 editions** and may differ from the current website. Interactive figures appear in a static reading state.

## Implementation and repository

The final deliverable is **generated HTML and static assets**. Experiments use vanilla JavaScript, Canvas 2D, SVG, and CSS; Python generates the language and chapter pages. GitHub Pages serves the result without an application server or frontend framework.

| Path or branch | Purpose |
|---|---|
| [`index32.html`](index32.html) | Current source for the book's text, styles, and interactions |
| [`i18n/`](i18n/) | Translation JSON files and terminology glossaries |
| [`static/`](static/) | About, citation, and 404 pages; images; archived PDFs |
| [`build/`](build/) | HTML generation, validation, and publishing tools |
| `site/` | Locally generated deployment output; not committed to `main` |
| `main` | Public branch containing source, translations, build tools, and static source assets |
| [`gh-pages`](https://github.com/yalkongs/cspace/tree/gh-pages) | Public deployment branch serving the generated files |

### Build locally

Requires Python 3.10+ and Node.js 20+. The standard build has no third-party package dependencies.

```sh
git clone https://github.com/yalkongs/cspace.git
cd cspace
./deploy.sh --build-only
```

The build selects the highest-numbered `index<N>.html` in the project root, currently `index32.html`. A local `antigravity_builds/` folder contains separate experiments and is not selected automatically. You can also specify the source and output explicitly:

```sh
python3 -B build/build.py --source index32.html --output site
```

Unmatched translation entries produce warnings; a successful build does not establish translation completeness. PDFs are copied from `static/`, not regenerated from HTML.

### Validate

```sh
python3 -B -m unittest discover -s build -p 'test_*.py'
node build/validate.mjs site https://yalkongs.github.io/cspace
```

The build checks JavaScript syntax, JSON-LD, canonical URLs, duplicate language links, internal routes, and assets. Optional browser checks live in [`build/smoke.mjs`](build/smoke.mjs) and require a separate Playwright and Chrome installation.

### Publish to GitHub Pages

Maintainers with repository write access and an authenticated GitHub CLI can publish with:

```sh
gh auth login
./deploy.sh
```

The publisher verifies that `yalkongs/cspace` is **public**, then pushes only the validated `site/` output and the license to `gh-pages` through an isolated temporary Git checkout. GitHub Pages publishes that branch's root, with `.nojekyll` preserving the generated files. Routes use the `/cspace/` project path and directory indexes, so they do not depend on Vercel URL rewrites.

The former Vercel deployment remains as a historical deployment; the current `deploy.sh` targets GitHub Pages.

## References, contributions, and license

See [About and references](https://yalkongs.github.io/cspace/about/) for the book's background and bibliography. The [citation guide](https://yalkongs.github.io/cspace/cite/) provides APA, Chicago, MLA, and BibTeX formats for the whole book or a selected chapter.

Corrections to the text, translations, experiment behavior, and accessibility are welcome through [GitHub issues](https://github.com/yalkongs/cspace/issues). Include the chapter and language, the relevant passage or reproduction steps, and supporting references where possible. For a new theory or experiment, explain the learning question, the variable the reader would manipulate, the expected observation, and the model's limitations.

The text, illustrations, interactive figures, and accompanying source are licensed under **CC BY-NC-SA 4.0**. See [LICENSE](LICENSE) for the repository's license notice and terms.
