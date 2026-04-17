# Flint hero image — three concepts

Paste any prompt below into an image generator (Midjourney v6, GPT image,
Imagen 3, Flux, Nano Banana, SDXL). Render at **1600×900 or 1920×1080** for
GitHub OG preview + social cards.

**Important:** image models write text badly. Generate the illustration
**without baked-in text**, then overlay the metrics in Figma / Canva /
Photoshop. Each concept includes the exact text block to paste on top.

---

## Concept A — "Striking the spark"

Hero, quiet, premium. Cave-painting-meets-Pixar. Best for the repo front page
if you want Flint to feel *timeless, serious, archeo-tech*.

### Prompt

> Pixar-style 3D animated movie still, a prehistoric cave explorer crouched in a
> dim cave, holding a hand-sized obsidian flint stone in his right hand and a
> dark pyrite rock in his left. He is about to strike them together. A single
> bright golden-orange spark is caught mid-flight between the stones, the
> brightest point in the frame. Soft volumetric rim lighting, deep warm brown
> and charcoal-black palette, faint red-ochre cave paintings of hand prints and
> mammoths on the back wall, cinematic shallow depth of field, centered
> composition, negative space at the bottom third for typography overlay.
> High detail, octane render quality, warm color grading, no text, no letters,
> no logo, 16:9 aspect ratio.

### Text to overlay (bottom third, centered, mono/geometric sans)

```
FLINT
caveman prompts. flint delivers.

VERBOSE 736  ·  CAVEMAN 423  ·  FLINT 186   (output tokens)
```

### Use

- GitHub README hero (`assets/launch/hero.png`)
- GitHub repo social preview (Settings → Social preview)
- HN post thumbnail

---

## Concept B — "Evolution of prompting"

Meme-first, immediately parseable in a Twitter scroll. Best as a **secondary**
asset for X / Reddit / HN comments. Lower authority than A but far higher
virality.

### Prompt

> Pixar-style 3D animated movie still, three cartoon characters standing side
> by side in the evolution-of-man silhouette pose, all facing the same
> direction, warm studio-lit background fading from brown on the left to
> golden-yellow on the right. Character 1 (leftmost): a slouched, exhausted
> scholar in a long robe, surrounded by a messy cloud of floating paper
> scrolls with scribbled text, one hand rubbing his forehead, tired
> expression. Character 2 (middle): a hunched caveman wearing a rough fur
> wrap, grunting with mouth open, no tools in hand, confused expression,
> cartoon sweat drops. Character 3 (rightmost): a confident upright explorer
> in tidy prehistoric leather, holding a glowing obsidian flint stone in one
> raised hand, a single bright orange spark flying off, smiling with quiet
> pride. All three characters have the same friendly Pixar facial style —
> expressive eyes, soft skin shading, slightly exaggerated proportions.
> Clean 16:9 composition, each character occupying one third of the frame,
> soft drop shadows on a warm neutral floor, no text, no letters, no logo.

### Text to overlay (three columns under each character, bold mono)

```
VERBOSE CLAUDE        CAVEMAN PROMPTS        FLINT
736 tokens            423 tokens             186 tokens
15s                   9s                     5s
86% concepts          84% concepts           95% concepts
```

### Use

- X / Twitter image attachment
- Reddit post thumbnail
- HN top comment with image link
- Discord #share-your-work

---

## Concept C — "The stone that started it all"

Hero-shot icon. Minimal. Works at tiny sizes (OG preview, favicon source,
talk slide). Best if you want a logomark moment.

### Prompt

> Pixar-style 3D animated close-up, a weathered but friendly prehistoric hand
> holding a palm-sized obsidian flint stone. The stone is cracked open to
> reveal a glowing warm-orange molten core. Five tiny bright sparks are
> flying off the stone, arranged in a gentle arc; each spark has a faintly
> visible single letter inside it — G, C, P, V, A — glowing like embers,
> rendered as warm ember-orange dots, not sharp typography. Deep dark brown
> background with a single soft spotlight from the upper left. Cinematic
> product-shot framing, shallow depth of field, hand slightly out of focus,
> stone in sharp focus at the golden-ratio point. Warm color grading, no
> extra text, no logo, 16:9 aspect ratio.

### Text to overlay (one line, bottom, small uppercase letterspaced mono)

```
4× SHORTER  ·  3× FASTER  ·  +9 CONCEPT POINTS  ·  WINS EVERY COLUMN
```

### Use

- GitHub README hero (if you want a tight, icon-like feel vs. concept A's wide scene)
- Talk slide title card
- Blog post featured image

---

## How to pick

| concept | vibe | best use |
| --- | --- | --- |
| **A** Striking the spark | premium, serious, archeo-tech | README hero for "authority" framing |
| **B** Evolution of prompting | meme-ready, high virality | X / Reddit social post |
| **C** The stone that started it all | iconic, minimal, logo-ish | README hero for "product-shot" framing |

My vote: **C as README hero, B as social asset**. A is beautiful but reads as
quiet; C has the same aesthetic with a tighter, more iconic read at thumbnail
size. B is the one that makes people screenshot and repost.

## Drop-in workflow

1. Generate the image (any tool).
2. Save to `assets/launch/hero.png` (concept A or C) and
   `assets/launch/meme_evolution.png` (concept B).
3. Add the text overlay in Figma/Canva using a geometric sans
   (Space Grotesk, Inter Tight, or JetBrains Mono for the numbers line).
4. Ping me — I update the README to reference the new file.
