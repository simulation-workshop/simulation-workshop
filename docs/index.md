---
title: Simulation workshop
template: home.html
description: Documentation for the Acme platform.
hero:
  title: Simulation Workshop
  text: Building Worlds through equations
  actions:
    - text: Get started
      link: getting-started/installation.md
      style: primary
    - text: Modelica Video Tutorials
      link: guide/embedding.md
      style: secondary
  code_title: modelica example.mo
  code_lang: modelica
  code: |
    model simpleSpringMass
      parameter Real M = 5;
      parameter Real k = 12;
      parameter Real C = 8;
      Real x;
      Real v;
    equation
      der(x) = v;
      M*der(v) + C*v + k*x = 0;
    end simpleSpringMass;
features:
  - title: The Philosophy of System Simulation
    text: Read short and comprehensive articles about the concept of system simulation and methodologies used for it. Understand governing equations. System Dynamics, Numerical techniques, Visualizations and lot more.
    link: systemsimulation/systemsimulation.md
    wide: true
  - title: Modelica Tips and Tricks
    text: Press Ctrl+K or Cmd+K to search every page and heading. No server needed.
    link: reference/cli.md
  - title: Modelica Quiz Corner
    text: Add YouTube, PDFs and live demos with one line, and reuse Markdown partials.
    link: guide/embedding.md
  - title: Articles and Blog Posts
    text: The theme follows the reader's system setting and remembers their choice, with an accent color you set in one line.
    link: getting-started/configuration.md
    wide: true
---

## Quick start

```bash
pip install markdown pyyaml jinja2 pygments
python build.py serve
```

Open `http://127.0.0.1:8000`. Edit any file in `docs/` and the page reloads. When you're ready to publish, run `python build.py build` and upload the `site/` folder.
