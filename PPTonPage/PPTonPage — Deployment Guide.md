# PPTonPage — Deployment Guide

Because rendering happens entirely in the browser, deployment is unusually simple: you are
deploying **two static files** and the CORS headers that let a page on another domain read
them. There is no conversion worker, no headless LibreOffice, no render queue, and no
per-request CPU cost that scales with deck complexity.

Your server's whole job:

| Artifact                 | Served as                          | Needs CORS?                          |
| ------------------------ | ---------------------------------- | ------------------------------------ |
| `dist/pptx-viewer.js`    | JavaScript, long cache             | Only if loaded from another origin   |
| `*.pptx`                 | `application/vnd...presentationml.presentation` | **Yes — always, if the embedding page is on a different domain** |

---

## 1. Pick your topology

| # | Shape | When to use | Flask involved? |
| - | ----- | ----------- | --------------- |
| **A** | Flask serves the bundle **and** the decks | Default. Decks are private, behind auth, or change often. | Yes |
| **B** | Flask serves decks; CDN serves the bundle | High traffic, or many embedding sites. | Yes |
| **C** | Everything static on S3/CloudFront/nginx | Decks are public and rarely change. | No |

Options A and B use `server/pptonpage.py`. Option C needs no Python at all — the component
does not care what serves the bytes, only that the headers are right.

---

## 2. Build the bundle

Do this once per release, on any machine with Node available. Node is a **build-time**
dependency only; it is never needed in production.

```bash
cd pptonpage
npx esbuild src/index.js --bundle --format=iife \
  --global-name=PptxViewerBundle --target=es2020 \
  --minify --sourcemap --outfile=dist/pptx-viewer.js
```

Output sizes, measured:

| File | Raw | gzip |
| ---- | --- | ---- |
| `dist/pptx-viewer.js` | 1.1 MB | **342 KB** |

Commit `dist/pptx-viewer.js` to your repo or publish it as a build artifact. **Do not ship
`dist/pptx-viewer.js.map` or `dist/pptx-viewer.debug.js` to production** — the debug build
is 1.6 MB and the sourcemap is 3.2 MB.

Compression is not optional at this size. See §7.

---

## 3. Option A — Flask serves everything

### 3.1 Layout

```
/srv/pptonpage/
  app.py
  pptonpage.py            <- from server/pptonpage.py
  dist/pptx-viewer.js
  decks/
    quarterly-review.pptx
    onboarding.pptx
  requirements.txt
  venv/
```

### 3.2 `requirements.txt`

```
Flask>=3.0
gunicorn>=21.2
```

Verified against Flask 3.1. The blueprint has no dependencies beyond Flask itself.

### 3.3 `app.py`

```python
import os
from pathlib import Path
from flask import Flask
from pptonpage import pptonpage

BASE = Path(__file__).resolve().parent

app = Flask(__name__)

app.register_blueprint(
    pptonpage(
        decks_dir=BASE / "decks",
        bundle_path=BASE / "dist" / "pptx-viewer.js",
        # In production, list your embedding origins explicitly.
        allowed_origins=os.environ.get("PPTX_ORIGINS", "*").split(","),
        cache_seconds=3600,
        bundle_cache_seconds=31536000,   # bundle is versioned by URL, see §8
        allow_listing=False,             # don't advertise your deck inventory
    ),
    url_prefix="/pptonpage",
)
```

Note `allow_listing=False`. The default `True` exposes `GET /pptonpage/decks/` as a JSON
inventory of every deck you host, which is usually not what you want in public.

### 3.4 Run it under gunicorn

Rendering is client-side, so worker sizing is driven purely by how many concurrent file
downloads you expect — not by deck complexity.

```bash
gunicorn --workers 3 --threads 4 \
         --bind 127.0.0.1:8000 \
         --access-logfile - --error-logfile - \
         app:app
```

`--threads` matters more than `--workers` here: every request is a file read streamed to
the client, so the work is I/O-bound. Three workers × four threads comfortably saturates a
small VM.

### 3.5 systemd unit

`/etc/systemd/system/pptonpage.service`:

```ini
[Unit]
Description=PPTonPage deck server
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/srv/pptonpage
Environment="PPTX_ORIGINS=https://intranet.example.com,https://docs.example.com"
ExecStart=/srv/pptonpage/venv/bin/gunicorn \
  --workers 3 --threads 4 --bind 127.0.0.1:8000 \
  --access-logfile - --error-logfile - app:app
Restart=always
RestartSec=3

# Hardening — the process only ever reads files.
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadOnlyPaths=/srv/pptonpage

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now pptonpage
sudo systemctl status pptonpage
```

### 3.6 nginx in front

```nginx
server {
    listen 443 ssl http2;
    server_name decks.example.com;

    ssl_certificate     /etc/letsencrypt/live/decks.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/decks.example.com/privkey.pem;

    # A 1.1 MB bundle must be compressed. .pptx is already a ZIP — never gzip it.
    gzip             on;
    gzip_vary        on;
    gzip_min_length  1024;
    gzip_comp_level  6;
    gzip_types       text/javascript application/javascript application/json;

    # Decks can be tens of MB; don't let nginx buffer them to disk.
    proxy_max_temp_file_size 0;
    client_max_body_size     0;

    location /pptonpage/ {
        proxy_pass         http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        # Pass Origin through — the blueprint echoes it back per its allow-list.
        proxy_set_header   Origin            $http_origin;
    }
}
```

Two details that bite people:

- **`proxy_set_header Origin $http_origin`** — nginx forwards `Origin` by default, but if
  you have `proxy_set_header` blocks that clear headers, the blueprint sees no origin and
  falls back to your first allowed origin, which the browser then rejects.
- **Never gzip `.pptx`.** It is already a ZIP; recompressing wastes CPU for ~0% gain. The
  `gzip_types` list above deliberately excludes it.

If you'd rather nginx serve decks straight off disk and skip Python for that path, see §6 —
just make sure you add the CORS headers there instead.

---

## 4. Option A2 — Docker

`Dockerfile`:

```dockerfile
# ---- build the bundle ----
FROM node:22-slim AS bundle
WORKDIR /build
COPY src/ src/
COPY vendor/ vendor/
RUN npx --yes esbuild src/index.js --bundle --format=iife \
      --global-name=PptxViewerBundle --target=es2020 \
      --minify --outfile=dist/pptx-viewer.js

# ---- runtime ----
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server/pptonpage.py app.py ./
COPY --from=bundle /build/dist/pptx-viewer.js ./dist/pptx-viewer.js

RUN useradd -r -u 10001 pptx && chown -R pptx /app
USER pptx

EXPOSE 8000
CMD ["gunicorn", "--workers", "3", "--threads", "4", \
     "--bind", "0.0.0.0:8000", "--access-logfile", "-", "app:app"]
```

`compose.yaml`:

```yaml
services:
  pptonpage:
    build: .
    ports: ["8000:8000"]
    environment:
      PPTX_ORIGINS: "https://intranet.example.com"
    volumes:
      # Decks live outside the image so you can add one without a rebuild.
      - ./decks:/app/decks:ro
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "python -c \"import urllib.request as u; u.urlopen('http://127.0.0.1:8000/pptonpage/pptx-viewer.js')\""]
      interval: 30s
      timeout: 5s
      retries: 3
```

Mounting `./decks` read-only means adding a deck is a file copy, not a deploy.

---

## 5. Option A3 — Managed platforms

The app is a plain WSGI app, so anything that runs Flask runs this. The one thing every
platform gets wrong by default is **ephemeral disk**: decks written to the container
filesystem vanish on redeploy. Put decks in object storage (§6) or bake them into the
image.

**Render / Railway / Heroku** — `Procfile`:

```
web: gunicorn --workers 3 --threads 4 --bind 0.0.0.0:$PORT app:app
```

Build command: `pip install -r requirements.txt` (commit `dist/pptx-viewer.js` so the
platform doesn't need Node).

**Fly.io** — `fly.toml`:

```toml
app = "pptonpage"
primary_region = "bom"          # closest region to your audience

[build]
  dockerfile = "Dockerfile"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = "suspend"
  auto_start_machines = true
  min_machines_running = 0

[[vm]]
  memory = "512mb"
  cpu_kind = "shared"
  cpus = 1

[[mounts]]
  source = "decks"
  destination = "/app/decks"
```

512 MB is genuinely enough — the server never parses a deck, it only streams bytes. The
memory-hungry work happens in the viewer's browser.

---

## 6. Option C — No Flask at all

If your decks are public, skip the backend. Upload `pptx-viewer.js` and your `.pptx` files
to any static host and set the headers yourself.

### S3 + CloudFront

Bucket CORS configuration:

```json
[
  {
    "AllowedOrigins": ["https://intranet.example.com"],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedHeaders": ["Range", "Content-Type"],
    "ExposeHeaders": ["Content-Length", "Content-Range", "Accept-Ranges", "ETag"],
    "MaxAgeSeconds": 86400
  }
]
```

S3 does not infer the PowerPoint MIME type, so set it at upload time:

```bash
aws s3 cp quarterly.pptx s3://my-decks/ \
  --content-type application/vnd.openxmlformats-officedocument.presentationml.presentation \
  --cache-control "public, max-age=3600"

aws s3 cp dist/pptx-viewer.js s3://my-decks/ \
  --content-type text/javascript \
  --content-encoding gzip \
  --cache-control "public, max-age=31536000, immutable"
```

On CloudFront, attach a cache policy that **includes `Origin` in the cache key**.
Otherwise the first viewer's `Access-Control-Allow-Origin` gets cached and served to
everyone else, and the second embedding domain breaks in a way that looks random.

### nginx serving decks off disk

```nginx
location /decks/ {
    root /srv;
    types { application/vnd.openxmlformats-officedocument.presentationml.presentation pptx; }
    add_header Access-Control-Allow-Origin  "https://intranet.example.com" always;
    add_header Access-Control-Allow-Methods "GET, HEAD, OPTIONS" always;
    add_header Access-Control-Expose-Headers "Content-Length, Accept-Ranges, ETag" always;
    add_header Vary Origin always;
    expires 1h;
}
```

The `always` flag matters: without it nginx drops the headers on error responses, so a
404 or 304 arrives without CORS and the browser reports a misleading network error instead
of the real status.

---

## 7. CORS — the one thing that actually breaks

Roughly every "it doesn't work" report is this. The browser fetches the `.pptx` with
`fetch()`, which means same-origin rules apply, which means the **deck host** must opt in.

Decision table:

| Embedding page | Deck host | What you need |
| -------------- | --------- | ------------- |
| Same origin as deck | same | Nothing. |
| Different origin, public deck | yours | `Access-Control-Allow-Origin: *` |
| Different origin, several known sites | yours | `allowed_origins=[...]` + `Vary: Origin` |
| Different origin, cookie-protected deck | yours | Explicit origin (**not** `*`) + `Access-Control-Allow-Credentials: true` + `credentials="include"` on the element |
| Deck on a third-party host you don't control | theirs | You cannot fix this client-side. Proxy it through your Flask app. |

The blueprint handles the first four. It echoes the caller's `Origin` when it's on the
allow-list, sets `Vary: Origin` so caches don't cross-contaminate, and only emits
`Access-Control-Allow-Credentials` when a specific origin is in play — because the spec
forbids combining `*` with credentials.

For the cookie-protected case, both sides must agree:

```python
allowed_origins=["https://intranet.example.com"]   # never "*" with credentials
```

```html
<pptx-viewer src="https://decks.example.com/pptonpage/decks/private.pptx"
             credentials="include"></pptx-viewer>
```

### Third-party decks: the proxy escape hatch

If the deck lives somewhere you can't add headers, add a route that fetches it server-side
and re-serves it with your own. Keep an allow-list of hosts, or you've built an open proxy:

```python
import requests
from urllib.parse import urlparse
from flask import Response, abort, request

ALLOWED_DECK_HOSTS = {"sharepoint.example.com", "files.partner.com"}

@app.route("/proxy-deck")
def proxy_deck():
    url = request.args.get("url", "")
    host = urlparse(url).netloc
    if host not in ALLOWED_DECK_HOSTS:
        abort(403)
    upstream = requests.get(url, stream=True, timeout=30)
    if upstream.status_code != 200:
        abort(502)
    return Response(
        upstream.iter_content(64 * 1024),
        content_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "public, max-age=300",
        },
    )
```

This is the only situation where bytes touch your server's CPU, and even then it's a
pass-through stream.

---

## 8. Caching and releasing new versions

The bundle and the decks want opposite caching strategies.

**Bundle — cache forever, version the URL.** Put the release in the path or query so a new
release is a new URL and you never fight a stale cache:

```html
<script src="https://decks.example.com/pptonpage/pptx-viewer.js?v=1.0.0"></script>
```

with `bundle_cache_seconds=31536000`. Bump `?v=` on every release.

**Decks — short cache, rely on ETags.** The blueprint sets `conditional=True`, so Flask
emits an `ETag` and answers repeat requests with `304 Not Modified` (verified). A one-hour
`cache_seconds` plus ETags means an updated deck goes live within the hour and costs
nothing to revalidate.

If a deck must update instantly, either set `cache_seconds=0` for that route or version
deck filenames the same way you version the bundle.

---

## 9. Protecting private decks

The component sends whatever the browser sends, so all three standard patterns work:

1. **Cookie session** — set `credentials="include"` and an explicit `allowed_origins`.
   Your deck route checks the session before returning the file. Simplest when the
   embedding page and the deck live under the same auth domain.
2. **Signed URLs** — generate a short-lived token server-side and render it into the
   `src`. Works cross-domain with no cookie complications, and it's the right answer for
   S3/CloudFront presigned URLs.
3. **Gateway auth** — put the whole prefix behind your existing SSO proxy. Just make sure
   the proxy passes `OPTIONS` preflights through **unauthenticated**, because browsers
   don't attach credentials to a preflight and an authenticating proxy will 401 it,
   producing a CORS error that looks nothing like an auth problem.

Note the privacy property worth telling stakeholders about: because parsing is client-side,
the deck's contents are never processed by your server or any third party. The bytes go
from your storage to the viewer's browser. Nothing is uploaded anywhere for conversion.

---

## 10. Post-deploy verification

Run these against the deployed host. Each one catches a distinct failure.

```bash
HOST=https://decks.example.com
ORIGIN=https://intranet.example.com

# 1. Bundle is served as JavaScript and compressed.
curl -sI -H "Accept-Encoding: gzip" $HOST/pptonpage/pptx-viewer.js \
  | grep -iE 'content-type|content-encoding|cache-control'
# expect: text/javascript · gzip · a long max-age

# 2. Deck has the right MIME type and CORS for your embedding origin.
curl -sI -H "Origin: $ORIGIN" $HOST/pptonpage/decks/quarterly.pptx \
  | grep -iE 'content-type|access-control-allow-origin|vary|etag'
# expect: ...presentationml.presentation · your origin (or *) · Vary: Origin

# 3. Preflight succeeds without credentials.
curl -si -X OPTIONS -H "Origin: $ORIGIN" \
  -H "Access-Control-Request-Method: GET" \
  $HOST/pptonpage/decks/quarterly.pptx | head -1
# expect: 204 (NOT 401 — a common gateway-auth mistake)

# 4. Conditional requests work (saves bandwidth on every revisit).
ETAG=$(curl -sI $HOST/pptonpage/decks/quarterly.pptx | grep -i etag | cut -d' ' -f2 | tr -d '\r')
curl -so /dev/null -w '%{http_code}\n' -H "If-None-Match: $ETAG" \
  $HOST/pptonpage/decks/quarterly.pptx
# expect: 304

# 5. Path traversal is blocked.
curl -so /dev/null -w '%{http_code}\n' "$HOST/pptonpage/decks/../../app.py"
# expect: 404

# 6. Deck inventory is not public.
curl -so /dev/null -w '%{http_code}\n' $HOST/pptonpage/decks/
# expect: 404 when allow_listing=False
```

Then the browser check, from a page on your real embedding domain:

1. Open DevTools → Network, load the page.
2. `pptx-viewer.js` → 200, `Content-Encoding: gzip`, transferred ~342 KB.
3. The `.pptx` → 200, and **no** CORS error in Console.
4. Click the slide. The first animation step should play.
5. Reload. The bundle should come from cache (`304` or `disk cache`).

If step 3 shows a CORS error, the message in the viewer itself will say so explicitly —
that error state exists precisely because this is the common failure.

---

## 11. Troubleshooting

| Symptom | Cause | Fix |
| ------- | ----- | --- |
| Viewer shows "the file could not be fetched… Access-Control-Allow-Origin" | Deck host has no CORS header | §7 |
| Works on one embedding domain, breaks on the second | CDN cached the first `Access-Control-Allow-Origin` | Add `Origin` to the CDN cache key; confirm `Vary: Origin` |
| Preflight returns 401 | Auth gateway is challenging `OPTIONS` | Exempt `OPTIONS` from auth |
| "That URL did not return a .pptx file (missing ZIP signature)" | The URL returned HTML — usually a login redirect or a 404 page with a 200 status | Fetch the URL with curl and look at what actually comes back |
| Bundle takes seconds to load | Compression is off | Enable gzip/brotli for `text/javascript` (§7) |
| Deck loads but slides are blank | Nothing has animated yet — slide 1's content is an entrance animation, exactly as in PowerPoint | Click, or add `autoplay` |
| Fonts differ / lines wrap differently than PowerPoint | Deck fonts aren't available to the browser | Serve them as webfonts on the embedding page |
| Fullscreen button missing | Page is in an iframe without `allowfullscreen` | Add `allowfullscreen` to the iframe; the button hides itself rather than failing |
| Decks vanish after redeploy | Ephemeral container disk | Mount a volume or use object storage (§5) |
| Very large deck is slow on mobile | Client-side parse of a big ZIP with many images | Compress images in the source deck; this is the one real scaling limit |

---

## 12. Operational notes

- **The server does no rendering.** CPU and memory stay flat regardless of how complex the
  decks are. Capacity planning is bandwidth planning.
- **Bandwidth is the real cost.** A 20 MB deck downloads in full before the first slide
  paints. Compressing images inside the `.pptx` is the single highest-leverage
  optimisation, and it's a PowerPoint-side task, not a server one.
- **Zip-bomb protection is already on.** The viewer parses with the library's
  `RECOMMENDED_ZIP_LIMITS`, so a malicious archive can't exhaust the client.
- **Monitoring:** alert on 5xx from the deck route and on p95 transfer time for the bundle.
  There's no render queue to watch.
- **Rollback** is replacing one JS file. Keep the previous `pptx-viewer.js` at its
  versioned URL and rollback is a one-line change on the embedding page.
- **Browser support:** the bundle targets ES2020 and relies on the Web Animations API,
  Custom Elements, shadow DOM, `ResizeObserver` and container queries — current Chrome,
  Edge, Firefox and Safari all qualify. There is no IE/legacy path.
