---
marp: true
theme: default
paginate: true
backgroundColor: #fff
html: true
style: |
  /* Base font sizing for readability */
  section {
    font-size: 26px;
    padding: 40px;
  }

  /* Headings */
  h1 {
    font-size: 48px;
    margin-bottom: 0.5em;
  }

  h2 {
    font-size: 36px;
    margin-bottom: 0.5em;
    border-bottom: 3px solid #0066cc;
    padding-bottom: 0.2em;
  }

  /* Compact lists for content-heavy slides */
  section ul, section ol {
    margin: 0.5em 0;
  }

  section li {
    margin: 0.3em 0;
    line-height: 1.4;
  }

  /* Nested lists even more compact */
  section li ul, section li ol {
    margin: 0.2em 0 0.2em 1em;
  }

  section li li {
    margin: 0.2em 0;
    font-size: 0.95em;
  }

  /* Two-column layouts */
  .columns {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 2rem;
    margin: 1em 0;
  }

  /* Three-column layouts for dense content */
  .columns-3 {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 1.5rem;
    margin: 1em 0;
  }

  /* Compact lists in columns */
  .columns ul, .columns ol,
  .columns-3 ul, .columns-3 ol {
    margin: 0.3em 0;
    padding-left: 1.2em;
  }

  .columns li, .columns-3 li {
    margin: 0.2em 0;
    font-size: 0.9em;
    line-height: 1.3;
  }

  /* Code blocks - compact */
  section pre {
    font-size: 0.75em;
    line-height: 1.3;
    margin: 0.5em 0;
    padding: 0.8em;
  }

  section code {
    font-size: 0.85em;
    padding: 0.1em 0.3em;
  }

  /* Diagrams - responsive and centered */
  section > div > img {
    max-width: 100%;
    max-height: 500px;
    height: auto;
    display: block;
    margin: 1em auto;
  }

  /* Inline images (emojis) */
  p img {
    display: inline !important;
    vertical-align: middle;
    margin: 0 0.2em;
    height: 1em;
  }

  /* Tables - compact and styled */
  table {
    font-size: 0.85em;
    margin: 0.5em auto;
    border-collapse: collapse;
  }

  th, td {
    padding: 0.4em 0.6em;
    border: 1px solid #ddd;
  }

  th {
    background: #f5f5f5;
    font-weight: bold;
  }

  /* Blockquotes */
  blockquote {
    border-left: 4px solid #0066cc;
    padding-left: 1em;
    margin: 0.5em 0;
    font-style: italic;
    color: #555;
  }

  /* Emphasis boxes */
  .box {
    background: #f8f9fa;
    border: 2px solid #0066cc;
    border-radius: 8px;
    padding: 1em;
    margin: 1em 0;
  }

  .box-warning {
    background: #fff3cd;
    border-color: #ffc107;
  }

  .box-success {
    background: #d4edda;
    border-color: #28a745;
  }

  .box-info {
    background: #d1ecf1;
    border-color: #17a2b8;
  }

  /* Compact sections for dense slides */
  section.compact {
    font-size: 22px;
    padding: 30px;
  }

  section.compact h2 {
    font-size: 32px;
    margin-bottom: 0.3em;
  }

  section.compact li {
    margin: 0.2em 0;
    line-height: 1.3;
  }

  section.compact code {
    font-size: 0.8em;
  }

  /* Small text utility */
  .small {
    font-size: 0.85em;
  }

  .smaller {
    font-size: 0.75em;
  }

  /* Footer styling */
  footer {
    font-size: 0.7em;
    color: #666;
  }
---
