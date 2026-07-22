"""Self-contained SVG status badges — the trust index, rendered for a README.

No external service (shields.io), no network, no fonts to embed: a badge is a
flat two-cell SVG whose width is approximated from the character count, so it
renders identically wherever it is served or cached. The colour is derived from
the value against the platform's own `0.74` confidence threshold, so a badge
tells the truth the same way the terminal does — green only when the record
genuinely earns it.

`CONTENT_TYPE` is the SVG mimetype; `cvi_color` maps a 0–1 index to a hue band;
`render` builds the two-cell badge. Pure functions, no state.
"""

CONTENT_TYPE = "image/svg+xml"

# Threshold-aligned colour bands. 0.74 is the platform's held/attested line
# (attestation.py, DECISIONS/0001): below it the record is not trustworthy, and
# the badge must not read green. The bands step down from there.
_GREEN = "#3fb950"
_YELLOW = "#d29922"
_ORANGE = "#db6d28"
_RED = "#f85149"
_GREY = "#8b949e"


def cvi_color(value):
    """Map a CVI (0–1) to a colour band anchored on the 0.74 threshold.

    At or above threshold is green (trustworthy); a near-miss is yellow; the
    lower bands are orange then red. Values outside [0, 1] clamp to the ends,
    so a malformed index still yields a defined colour rather than an error.
    """
    try:
        v = float(value)
    except (TypeError, ValueError):
        return _GREY
    if v != v:  # NaN
        return _GREY
    v = max(0.0, min(1.0, v))
    if v >= 0.74:
        return _GREEN
    if v >= 0.6:
        return _YELLOW
    if v >= 0.4:
        return _ORANGE
    return _RED


def _escape(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _cell_width(text):
    # ~7px per glyph plus symmetric padding; good enough for a flat badge, and
    # deterministic so the SVG is byte-stable for caching.
    return len(str(text)) * 7 + 10


def render(label, message, color):
    """Return a flat two-cell SVG badge: grey `label` | coloured `message`.

    Width is derived from the text length so the cells always fit their
    content, and both strings are XML-escaped. `color` is used verbatim as the
    right cell's fill (see `cvi_color` for the CVI mapping).
    """
    label = _escape(label)
    message = _escape(message)
    lw = _cell_width(label)
    mw = _cell_width(message)
    total = lw + mw
    label_x = lw / 2
    message_x = lw + mw / 2
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total}" height="20" '
        f'role="img" aria-label="{label}: {message}">'
        f'<title>{label}: {message}</title>'
        f'<linearGradient id="s" x2="0" y2="100%">'
        f'<stop offset="0" stop-color="#bbb" stop-opacity=".1"/>'
        f'<stop offset="1" stop-opacity=".1"/></linearGradient>'
        f'<clipPath id="r"><rect width="{total}" height="20" rx="3" fill="#fff"/></clipPath>'
        f'<g clip-path="url(#r)">'
        f'<rect width="{lw}" height="20" fill="#555"/>'
        f'<rect x="{lw}" width="{mw}" height="20" fill="{color}"/>'
        f'<rect width="{total}" height="20" fill="url(#s)"/></g>'
        f'<g fill="#fff" text-anchor="middle" '
        f'font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11">'
        f'<text x="{label_x}" y="15" fill="#010101" fill-opacity=".3">{label}</text>'
        f'<text x="{label_x}" y="14">{label}</text>'
        f'<text x="{message_x}" y="15" fill="#010101" fill-opacity=".3">{message}</text>'
        f'<text x="{message_x}" y="14">{message}</text>'
        f'</g></svg>'
    )
