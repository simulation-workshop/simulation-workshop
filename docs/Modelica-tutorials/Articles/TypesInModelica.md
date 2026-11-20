# Bridging the gap between physics and Mathematics in Modelica

**Units and Dimensions bring physical meaning to mathematical quantities. The number 4 means widely different things depending on whether it is 4m length, 4kg mass or 4C temperature.**


As Simulations stand on the intersection of physical world and mathematical algorithms, efficient management of units is vital for accurate modeling of physical systems using mathematical frameworks.
​
Modelica provides an effective way to handle physical quantities using types. Modelica has primitive types such as:

- Real
- Integer
- String
- Boolean
- enumeration


On top of these, Modelica provides derived types that Inherit from the primitive types. Majority of physical quantities are derived from Real types as they have to represent continuously varying values.

Derived types enforce:
​Dimensional Consistency across equations
!!! success "This is a valid equation"
    $$
    \text{Velocity} \times \text{time} = \text{displacement}
    $$

!!! failure "This is not a valid equation"
    $$
    Temperature + Pressure = Energy 
    $$


​Define range and default values to quantities to improve solver stability, physical consistency and drag and drop implementation of components.
​
### Additional key attributes that make Modelica types even more powerful:

**DisplayUnit & quantity:** Decouples the underlying SI unit used in numerical solver calculations from the units shown in GUI dialogs and plot axes.

**Nominal:** Tells non-linear solvers the expected scale/magnitude of a variable, ensuring balanced numerical precision across vastly different physical scales.

!!! hint "The key takeway"
    Modelica at its core is a mathematical equation solver and features like units and dimensions provide the physical guard rails to keep the simulation under realistic conditions