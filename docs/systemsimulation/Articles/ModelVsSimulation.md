# Models Vs Simulations

What is the difference between a model and a simulation?
Modeling and simulation are often mentioned together in several contexts just like "Science & Technology"

!!! tip "Science Vs Technology"
    Science gives us the governing principles of systems around us and technology consume this knowledge to serve specific practical purpose

Though these are closely connected topics, they are different and and serve different purpose.

**"Model"** is an abstract mathematical description of a "system". It usually consist of a set of variables and equations connecting them.
These can be "empirical" - Derived from experiments or observations, or "physics-based" - derived from the governing principles in mechanics, thermodynamics, electromagnetism etc.

**Empirical models** are computationally simpler and provides good accuracy within the the training data. But these are not extensible and have limited scope when parameters are changed.
These are used either when the physics is too complex/unknown or the usability demands high accuracy in a limited range + sufficient data is available..

**Physics-based models** are more general and capture the fundamental characteristic of the system. These are mathematically complex to solve. They provide reasonable accuracy over a wide range of parameter variations. These are excellent for modeling inter-connected complex systems for exploring new concepts where high quality experiment data is not available.

**Hybrid-models** often represents a combination of both worlds where the model is based on physics principles but certain key parameters like " heat transfer coefficient", "coefficient of friction", etc are empirically derived.

**"Simulation"** is a virtual experiment performed by consuming any of the above models to solve a design problem or decide operational strategies. Simulations consume 1 or more models in an environment and execute numerical solvers. They solve the set of equations defined the models involved in it to calculate parameter values over a period of time defined in the simulation.
Simulations are unique experiments and cater to a specific need. One need to make sure that the models used in the simulation are capable of serving the purpose of simulation.

Happy Simulations !!!!