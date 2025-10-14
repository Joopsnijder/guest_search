# Presentation Templates

Reusable Marp templates for consistent presentation styling.

## Available Templates

### Default Theme (`default-theme.md`)

Professional theme optimized for technical presentations with:
- **Adaptive layouts** - Content automatically scales
- **Column layouts** - 2 and 3 column support
- **Compact mode** - For content-heavy slides
- **Responsive diagrams** - Auto-scaling images
- **Styled code blocks** - Readable syntax
- **Emoji support** - Inline emoji rendering

## Usage

### 1. Copy Template Frontmatter

Copy the entire YAML frontmatter (between `---`) from `default-theme.md` to your presentation:

```markdown
---
marp: true
theme: default
# ... rest of template config
---

# Your Presentation Title
```

### 2. Use Layout Classes

#### Two-Column Layout
```markdown
<div class="columns">

**Column 1:**
- Item 1
- Item 2

**Column 2:**
- Item 3
- Item 4

</div>
```

#### Three-Column Layout
```markdown
<div class="columns-3">

**Col 1:**
- Item 1

**Col 2:**
- Item 2

**Col 3:**
- Item 3

</div>
```

#### Compact Slide
```markdown
<!-- _class: compact -->

## Dense Content Slide

This slide will use smaller fonts and tighter spacing.
```

### 3. Emphasis Boxes

```markdown
<div class="box">
Important information here
</div>

<div class="box-warning">
⚠️ Warning message
</div>

<div class="box-success">
✅ Success message
</div>

<div class="box-info">
ℹ️ Info message
</div>
```

### 4. Size Utilities

```markdown
<span class="small">Smaller text</span>
<span class="smaller">Even smaller text</span>
```

## Layout Guidelines

### When Content Doesn't Fit

**Option 1: Use Two Columns**
- Split content horizontally
- Good for: comparisons, parallel info

**Option 2: Use Compact Mode**
```markdown
<!-- _class: compact -->
```
- Reduces font size and spacing
- Good for: lists, code examples

**Option 3: Split Into Multiple Slides**
- Best for: complex topics
- Keeps audience engaged

**Option 4: Use Smaller Text**
```markdown
<div class="small">
- Dense list item 1
- Dense list item 2
</div>
```

## Best Practices

### Content Density

**Do:**
- ✅ 5-7 bullet points max per slide
- ✅ Use columns for 8+ items
- ✅ Short, concise text (1-2 lines per bullet)
- ✅ Break complex topics into multiple slides

**Don't:**
- ❌ More than 10 items on one slide
- ❌ Long paragraphs
- ❌ Font size below 20px
- ❌ More than 3 nesting levels

### Code Blocks

```markdown
# Compact code
```python
def compact_code():
    return "Short is better"
```

# For longer code, use compact mode
<!-- _class: compact -->
```

### Diagrams

- Mermaid diagrams auto-convert to SVG
- Max 7-8 nodes for readability
- Use colors sparingly
- Label connections clearly

## Examples

See existing presentations:
- `../guest-finder/presentation.md`
- `../topic-researcher/presentation.md`
- `../architecture/presentation.md`

## Customization

To customize the theme:

1. Copy `default-theme.md` to your presentation
2. Modify the `style: |` section
3. Add your custom CSS

Example:
```yaml
style: |
  /* Import default styles */
  section {
    font-size: 26px;
  }

  /* Your custom styles */
  .custom-class {
    color: red;
  }
```

## Tips

### Automatic Layout Selection

Use this decision tree:

```
Content fits comfortably?
├─ Yes → Use normal layout
└─ No
   ├─ 2 related groups? → Use columns
   ├─ Many small items? → Use compact mode
   ├─ Very technical? → Use smaller font
   └─ Too much info? → Split into 2 slides
```

### Testing Layouts

1. Build presentation: `./scripts/build-presentations.sh your-file.md`
2. Open HTML: `open presentation-final.html`
3. Check each slide in browser
4. Adjust layouts as needed
5. Rebuild and verify

### Common Issues

**Text overflows slide:**
- Add `<!-- _class: compact -->` to slide
- Or split into columns
- Or break into 2 slides

**Diagram too large:**
- Reduce node count
- Simplify connections
- Use abbreviations

**List too long:**
- Group related items
- Use sub-bullets
- Split across columns

## Building

Use the standard build process:

```bash
# Single presentation
./scripts/build-presentations.sh docs/presentations/your-presentation/presentation.md

# All presentations
./scripts/build-all-presentations.sh
```

Templates are applied via the frontmatter - no separate compilation needed!

## Contributing

When adding new template features:

1. Update `default-theme.md` with new CSS
2. Add usage examples to this README
3. Test with existing presentations
4. Document in "Available Templates" section

## License

MIT License - Same as main project
