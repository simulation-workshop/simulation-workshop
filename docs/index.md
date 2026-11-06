---
title: Simulation workshop
template: home.html
description: Simulation Workshop.
hero:
  title: Simulation Workshop
  text: Building Worlds through equations
  actions:
    - text: System Simulations
      link: systemsimulation/systemsimulation.md
      style: primary

    - text: Modelica Video Tutorials
      link: Modelica-tutorials/Video-Tutorials.md
      style: secondary

  code_title: A simple Modelica Example 
  code_lang: modelica
  code: |
    model simpleSpringMass
      parameter Real M = 5;
      parameter Real k = 12;
      parameter Real C = 8;
      Real x;
      Real v;
    initial equation 
      x = 1;
    equation
      der(x) = v;
      M*der(v) + C*v + k*x = 0;
    annotation(
        experiment(StartTime = 0, StopTime = 10, Tolerance = 1e-06, Interval = 0.002));
    end simpleSpringMass;

features:
  - title: The Philosophy of System Simulation
    text: Read short and comprehensive articles about the concept of system simulation and methodologies used for it. Understand governing equations. System Dynamics, Numerical techniques, Visualizations and lot more.
    link: systemsimulation/systemsimulation.md
    

  - title: Modelica Tutorials
    text: Press Ctrl+K or Cmd+K to search every page and heading. No server needed.
    link: Modelica-tutorials/Video-Tutorials.md

  - title: Modelica Video Tutorials
    text: Add YouTube, PDFs and live demos with one line, and reuse Markdown partials.
    link: Modelica-tutorials/Video-Tutorials.md

  - title: Articles and Blog Posts
    text: The theme follows the reader's system setting and remembers their choice, with an accent color you set in one line.
    link: systemsimulation/OtherArticles.md
    
---

## Quick start

Are You new to Modelica ? These are the places to check out for more content
