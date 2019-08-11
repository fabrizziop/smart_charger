# smart_charger
Smart charger using a ESP32 Dev board, microPython and a DROK 200220 DC buck converter.

The micropython module for the DC buck converter control is in https://github.com/fabrizziop/micropython_drok200220_module

This program charges a LEAD ACID (AGM) battery with two stages:

1. Voltage setpoint set higher than normal float, also called absorption voltage. This handles the bulk and absorption charge stages, as the DC buck converter has a current limit, so during bulk, it is charged at the set current and voltage rises gradually as the battery is charged. When the voltage limit is reached, charging continues under constant voltage and the current diminishes slowly.
2. Voltage setpoint set to the desired float voltage.

The decision is made automatically by the program, thanks to two current paramenters. 

Transition HI is defined as the electrical current necessary to switch from float to absorption charging mode. When the charger is in float mode, and the current exceeds T-HI, it will go to absorption. (This will increase the current even more)

Transition LO is defined as the electrical current necessary to switch from absorption to float charging mode. When the charger is in absorption mode, and the current goes below T-LO, it will go to float. (This will decrease the current).

If communication is lost with the DC module, the program will go into emergency mode, and retry every emergency_retry seconds. In emergency mode, a buzzer is activated and the protection relay that goes between the main DC module and the battery is opened.

Both effects create the required hysteresis to avoid unnecessary switching.

Now, with the electrical details. A schottky diode was added between the DC output and the battery, to avoid backfeeding it. A relay module (normally open) was added also in this path, for safety purposes. The ESP32 and relays are powered with a DC Buck converter, connected to the battery, so in case of a power outage, the microcontroller will stay on (a switch should be added between battery and dc buck). Three LEDs are also connected, indicating Absorption/Float/Emergency.

Voltages are in centivolts (1V -> 100cV), currents in centiamps (1A -> 100cA), as this is the way they are handled by the DC module.
