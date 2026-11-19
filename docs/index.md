---
title: Simulation workshop
template: home.html
description: Simulation Workshop.

hero:
  title: Simulation Workshop
  text: Building Worlds through equations
  image: assets/small_log.png
  image_alt: Simulation Workshop
  actions:
    - text: Modelica Video Tutorials
      link: Modelica-tutorials/Video-Tutorials.md
      style: primary

    - text: Modelica Written Tutorials
      link: Modelica-tutorials/Written-Tutorials.md
      style: secondary


features:
  - title: Getting Started With Open Modelica Ecosystem
    text: Basic walkthrough of major tools and libraries required to get started with Open Modelica and associated opertions including simulations, FMU, SSP and python-based automation and co-simulation.
    link: systemsimulation/Introduction_openModelica.md
    

  - title: Modelica Tutorials
    text: Checkout hands-on tutorials on the theoritical concepts and modelica implementation of practically relevant simulation problems on engineering domains. Video tutorials are hosted in youtube at [Simulation Workshop Channel]
    link: Modelica-tutorials/Video-Tutorials.md    

  - title: Other Articles on Technology and Simulation
    text: Read about the interesting developments and insights about cool tools and technologies that are useful in terms of system modeling and simulations. As an open source enthusiast. I want to stick to open source or free tools as much as possible.
    link: systemsimulation/OtherArticles.md   
---

## Quick start
This is a very basic Modelica code to simulate the motion of a spring - mass - damper system.
Check out more amazing content at the tutorial sections or find out how to get started below.
```modelica
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
```
!!! tip "Are You new to Modelica ?" 
    These are the places to check out for more content

**Modelica Official Website :** [modelica.org](https://modelica.org)

**OpenModelica Official Website :** [openmodelica.org](https://openmodelica.org)

**Modelica by Example by Dr. Michael M. Tiller :** [Modelica by Example](https://mbe.modelica.university)

**OMPython - A python wrapper for OpenModelica compiler :**[OMPython](https://pypi.org/project/OMPython/)

**FMpy - For running FMUs generated from Modelica in python :** [FMPY](https://fmpy.readthedocs.io/en/latest/)

**Simulation Workshop Youtube Channel :** [Simulation Workshop](https://www.youtube.com/@simulationworkshop)


