# StyleSeed Adoption Notes

## Source

- Local reference folder: `styleseed-main/`
- Primary files reviewed:
  - `engine/DESIGN-LANGUAGE.md`
  - `skins/vercel/theme.css`
  - `skins/linear/theme.css`
  - `engine/css/base.css`

## Adoption Strategy

StyleSeed was used as a design reference, not as a full component import.

The project already has a working Next.js app, custom CSS, React Flow diagrams, and backend-driven legal analysis. Copying the full StyleSeed engine would introduce Tailwind v4, Radix/shadcn conventions, and extra component structure that do not match the current app.

## Applied Principles

- Single accent color
  - Adopted a restrained Linear-style indigo accent.
- Five-level grayscale hierarchy
  - Replaced strong blue/teal surfaces with softer neutral page/card/text tokens.
- Card/background separation
  - Cards remain white on a subtle page background with quiet borders and low-opacity shadows.
- Scarce status colors
  - Success, warning, and danger colors are used in small badges/notices only.
- Text hierarchy
  - Labels use muted uppercase styling; important content uses stronger dark text.
- Subtle elevation
  - Shadows use 4-6% opacity and remain secondary to borders.
- Tool-first layout
  - Kept the interface dense and document-oriented instead of turning it into a marketing-style UI.

## Chosen Skin Direction

The app now follows a Vercel/Linear hybrid:

- Vercel influence
  - Monochrome discipline
  - High readability
  - Tool/document feel
- Linear influence
  - Indigo accent
  - Work-focused panels
  - Refined status surfaces

## Not Adopted

- Full StyleSeed component copy
- Tailwind v4 theme directives
- shadcn/Radix component migration
- Mobile dashboard page composition rules that do not fit this legal workspace

