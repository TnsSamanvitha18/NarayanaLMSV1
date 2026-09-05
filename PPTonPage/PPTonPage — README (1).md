# PPTonPage

A drop-in web component that renders a `.pptx` URL inline on any web page — keeping the
click-by-click animations, slide transitions and hyperlinks the original file was authored
with.

```html
<script src="https://your-host/pptonpage/pptx-viewer.js"></script>

<pptx-viewer src="https://your-host/decks/quarterly.pptx"></pptx-viewer>
```

Rendering is **100% client-side**. The `.pptx` is fetched by the browser, unzipped in
memory and drawn as real DOM. Nothing is uploaded anywhere and no server-side conversion
step is involved — your Flask app only serves two static things.

---

## How it works

1. `fetch()` the `.pptx` and verify the ZIP signature.
2. Parse the OOXML package with [`@aiden0z/pptx-renderer`](https://github.com/aiden0z/pptx-renderer)
   (Apache-2.0) and render each slide lazily into a shadow-DOM layer as positioned HTML +
   SVG. Individual shapes stay addressable, which is what makes per-shape animation possible.
3. Separately parse each slide's own `<p:timing>` and `<p:transition>` XML to recover the
   animation sequence — which shape animates, with which effect, in which click group,
   with what delay and duration.
4. Replay that sequence with the Web Animations API, mapping PowerPoint effects onto
   `clip-path`, `opacity` and `transform` keyframes.

The renderer library does not interpret `p:timing` or `p:transition` at all; that layer is
implemented here in `src/timing.js`, `src/effects.js` and `src/transitions.js`.

---

## Requirements

The only hard requirement is **CORS on the host serving the `.pptx`**. The browser reads
the file with `fetch()`, so a cross-origin deck needs:

```
Access-Control-Allow-Origin: *
```

(or your specific embedding origin). If that header is missing the component shows an
explicit error explaining exactly this — it is by far the most common setup mistake.

No requirement on the embedding page: the component works on a plain HTML page, inside
React/Vue/Svelte, or in a CMS that allows a `<script>` tag.

---

## Flask integration

`server/pptonpage.py` is a self-contained blueprint. It has no dependencies beyond Flask.

```python
from flask import Flask
from pptonpage import pptonpage

app = Flask(__name__)

app.register_blueprint(
    pptonpage(
        decks_dir="/srv/decks",
        allowed_origins="*",              # or ["https://intranet.example.com"]
    ),
    url_prefix="/pptonpage",
)
```

Routes it adds:

| Route                            | Purpose                                                 |
| -------------------------------- | ------------------------------------------------------- |
| `GET /pptonpage/pptx-viewer.js`  | the bundle, cached for a day                            |
| `GET /pptonpage/decks/<name>`    | a `.pptx` with CORS, correct MIME type, ETag and ranges  |
| `GET /pptonpage/decks/`          | JSON index of available decks                           |

Options: `bundle_path`, `allowed_origins`, `cache_seconds`, `bundle_cache_seconds`,
`allow_listing`, `name`. Deck paths are resolved strictly inside `decks_dir`, so `../`
traversal and symlink escapes return 404.

**Already serving your decks?** Then skip the blueprint entirely. Serve
`dist/pptx-viewer.js` as a normal static file and add the one CORS header to your existing
`.pptx` response.

Run the bundled demo locally:

```bash
python server/pptonpage.py      # http://localhost:5000
```

---

## Attributes

Everything is optional except `src`. Attributes are reactive — change `slide` and the
viewer navigates.

| Attribute       | Default        | Description                                                                     |
| --------------- | -------------- | ------------------------------------------------------------------------------- |
| `src`           | —              | URL of the `.pptx`. Cross-origin requires `Access-Control-Allow-Origin`.        |
| `slide`         | `1`            | One-based starting slide. Set it later to navigate.                             |
| `animations`    | `on`           | `off` skips effects and jumps straight to each step's end state.                |
| `controls`      | `default`      | `none` hides all chrome for a kiosk-style embed.                                |
| `theme`         | `auto`         | `light` uses a lighter letterbox behind the slide.                              |
| `click-advance` | `on`           | `off` stops a click on the slide body from advancing.                           |
| `autoplay`      | off            | Present: plays itself. Optional value = seconds per step (default `3.2`).       |
| `loop`          | off            | Present: wraps from the last slide back to the first.                           |
| `credentials`   | `same-origin`  | `include` sends cookies with the deck request.                                  |

`autoplay` stops permanently the moment the viewer clicks, presses a key, or uses the
controls — the deck never fights the user for control.

## Methods and properties

```js
const v = document.querySelector('pptx-viewer');

v.next();                    // next animation step, then next slide
v.previous();
v.goToSlide(3);              // zero-based
v.goToSlide(3, { animate: false, atEnd: true });
v.goToStep(2);               // -1 = nothing revealed yet
v.toggleFullscreen();

v.slideCount;  v.slideIndex; // zero-based
v.stepCount;   v.stepIndex;
```

### Loading a deck without a URL

`loadBuffer()` renders bytes you already hold, skipping `src` and the network
entirely. It accepts an `ArrayBuffer`, a typed array, a `Blob` or a `File`, so a
file input, a drag-and-drop, or a deck inlined as base64 all work:

```js
// From a file input
input.addEventListener('change', () => {
  v.loadBuffer(input.files[0], { name: input.files[0].name });
});

// From bytes you already decoded
v.loadBuffer(arrayBuffer, { name: 'quarterly-review.pptx' });
```

`options.name` is only a label: it appears in the `src` field of the
`pptx-loadstart` / `pptx-load` events. Because nothing is fetched, this path has
no CORS requirement at all, and it is what lets the standalone demo run from a
`file://` URL.

## Events

All events bubble and carry a `detail` object.

| Event               | `detail`                                | Notes                             |
| ------------------- | --------------------------------------- | --------------------------------- |
| `pptx-loadstart`    | `{ src }`                               |                                   |
| `pptx-load`         | `{ src, slideCount, width, height }`    | deck is ready                     |
| `pptx-error`        | `{ src, error, message }`               | `message` is human-readable       |
| `pptx-slidechange`  | `{ slide, slideNumber, slideCount }`    |                                   |
| `pptx-step`         | `{ slide, step, stepCount }`            | one animation group played        |
| `pptx-transition`   | `{ from, to, kind }`                    |                                   |
| `pptx-end`          | —                                       | past the last step, no `loop`     |
| `pptx-link`         | `{ url }`                               | **cancelable** — see below        |
| `pptx-navigate`     | `{ slideIndex }`                        | **cancelable** in-deck jump       |
| `pptx-node-error`   | `{ slide, nodeId, error }`              | one shape failed, deck still fine |

```js
// Route in-deck links through your SPA router instead of opening a tab.
v.addEventListener('pptx-link', (e) => {
  e.preventDefault();
  router.push(e.detail.url);
});
```

## Keyboard

| Key                                        | Action                        |
| ------------------------------------------ | ----------------------------- |
| `→` · `PageDown` · `Space` · `Enter`       | next animation step / slide   |
| `←` · `PageUp` · `Backspace`               | back one step / slide         |
| `Home` / `End`                             | first / last slide            |
| `F`                                        | fullscreen                    |
| `G`                                        | thumbnail grid                |
| `Esc`                                      | close the grid                |

## Styling

The viewer lives in a shadow root, so your page CSS cannot leak in and break the slides.
Customise it through custom properties on the element:

```css
pptx-viewer {
  --pptx-surface: #0e1116;   /* letterbox behind the slide */
  --pptx-chrome: rgba(16, 19, 25, 0.72);
  --pptx-on-chrome: #f2f4f7;
  --pptx-accent: #2e8b8b;    /* progress bar, focus ring, active thumbnail */
  --pptx-radius: 10px;
  width: 100%;
  max-width: 900px;
}
```

The element sizes itself to its container at the deck's true aspect ratio, so give it a
width and it handles the rest.

---

## Supported today

- **Entrance and exit animations** — fade, dissolve, wipe, fly-in/slide, blinds,
  checkerboard, random bars, strips, barn, box, circle, diamond, plus, wedge, wheel, zoom,
  spin, colour change, motion paths, and explicit `set` visibility.
- **Emphasis animations** — scale, rotate, colour.
- **Slide transitions** — cut, fade (incl. through-black), dissolve, push, pull, cover,
  uncover, wipe, split, blinds, checkerboard, comb, strips, random bars, circle, diamond,
  plus, wedge, wheel, zoom, fly-through, newsflash, and the decorative family
  (vortex, ripple, honeycomb, glitter, shred). Reverse navigation replays in reverse.
- **Click groups and timing** — "on click", "with previous" and "after previous" grouping,
  per-behaviour delays and durations, paragraph-level targeting (`p:pRg`), and automatic
  slide advance (`advTm`).
- **Hyperlinks and click actions** — text links, shape links, and in-deck "jump to slide".
- **Charts, tables, SmartArt, gradients, preset and custom geometry** — via the renderer.
- **Navigation** — click-to-advance, keyboard, thumbnail grid, progress bar, fullscreen.
- **Accessibility** — focusable application region, `aria-live` slide announcements, full
  keyboard control, and `prefers-reduced-motion` (jumps to end states instead of animating).
- **Responsive** — scales to its container; container queries compact the chrome on narrow
  embeds.

## Known limits

- Embedded **video and audio** render as static shapes; playback is not wired up.
- Effects with no CSS equivalent (true 3-D rotations, most `morph` transitions) fall back
  to a cross-fade.
- Font substitution: fonts not available to the browser are substituted, so line breaks
  can differ slightly from PowerPoint. Serving the deck's fonts as webfonts on the host
  page fixes this.
- Trigger-on-click-of-a-specific-shape animations are treated as ordinary click steps.
- The deck host must send CORS headers.

---

## Repository layout

```
src/
  index.js         entry point; registers <pptx-viewer>, exposes window.PptxViewer
  viewer.js        the custom element: loading, slide cache, stepping, chrome, a11y
  timing.js        OOXML <p:timing> / <p:transition> parser
  effects.js       PowerPoint effect  ->  Web Animations keyframes
  transitions.js   slide transition implementations
  styles.js        shadow-DOM stylesheet
  icons.js         inline SVG control icons
vendor/            @aiden0z/pptx-renderer browser ESM build (Apache-2.0)
dist/
  pptx-viewer.js         minified bundle — this is the drop-in file
  pptx-viewer.debug.js   unminified, for readable stack traces
server/pptonpage.py      Flask blueprint
demo/
  index.html                 host page
  pptonpage-demo.html        single-file offline demo (generated)
  _standalone-template.html  source template for the above
  decks/animated-demo.pptx   sample deck
tools/
  make_fixtures.py       builds the animated test deck
  build_standalone.py    inlines bundle + deck into the single-file demo
test/                    Playwright QA scripts and screenshots
```

## The standalone demo

`demo/pptonpage-demo.html` is one self-contained file: the viewer bundle is
inlined and the sample deck is embedded as base64. Open it by double-clicking —
no server, no install, and it works with the network unplugged. It exposes the
live attribute toggles, an event log, and a file picker so you can drop in your
own deck.

Rebuild it, optionally around a different deck:

```bash
python tools/build_standalone.py
python tools/build_standalone.py --deck path/to/my.pptx -o my-demo.html
```

## Building

```bash
npx esbuild src/index.js --bundle --format=iife \
  --global-name=PptxViewerBundle --target=es2020 \
  --minify --sourcemap --outfile=dist/pptx-viewer.js
```

The bundle is a single self-contained IIFE (~1.1 MB, ~300 KB gzipped) with no runtime
dependencies. It registers `<pptx-viewer>` on load and also exposes
`window.PptxViewer` (`{ version, PptxViewerElement, define, internals }`) so you can
register the element under a different tag name if `pptx-viewer` is taken:

```js
window.PptxViewer.define('my-deck');
```

## Licence

This component is yours to use. It bundles
[`@aiden0z/pptx-renderer`](https://github.com/aiden0z/pptx-renderer), which is
Apache-2.0 licensed — keep that attribution when you redistribute the bundle.
