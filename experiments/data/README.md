# Standard observer data

Original, unmodified CSV and metadata from the International Commission on Illumination (CIE), downloaded 2026-09-24.

- CIE (2019), *Colour-matching functions of CIE 1931 standard colorimetric observer*, DOI [10.25039/CIE.DS.xvudnb9b](https://doi.org/10.25039/CIE.DS.xvudnb9b). CSV MD5: `17cca777db64b17170f06f67ce9d3ab7`.
- CIE (2019), *CIE 1964 colour-matching functions*, DOI [10.25039/CIE.DS.sqksu2n5](https://doi.org/10.25039/CIE.DS.sqksu2n5). CSV MD5: `6140e032f9326d88c5a0959b29b4d8f3`, confirmed by the downloaded metadata (the landing page lists a different checksum).

The 1964 metadata specifies the z-bar domain as 360–559 nm and zero extrapolation. Its NaN cells at wavelengths ≥560 nm are therefore replaced with zero in the embedded subset only. The original file is preserved unchanged. Other non-finite cells fail the build.

These datasets and their adaptations are **CC BY-SA 4.0**, a separate licence from the book's CC BY-NC-SA 4.0. See the original metadata and [licence](https://creativecommons.org/licenses/by-sa/4.0/). The generated HTML embeds a labelled adaptation: 380–780 nm inclusive sampled every 5 nm (81 rows), with no interpolation. This subset remains CC BY-SA 4.0. CIE is not affiliated with or endorsing these experiments.

The light spectra and reflectance samples in the rendering lab are explicitly **synthetic analytical examples**, not measurements of commercial lamps, skin, food or materials. Numerical integration uses a rectangular 5 nm sum over the limited wavelength range; previews are clipped to sRGB.
