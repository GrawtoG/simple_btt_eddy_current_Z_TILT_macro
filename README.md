# AUTO\_TILT\_EDDY — Simple Klipper Leveling for Eddy Probe

## Description

Very simple 3-point Z screw leveling for **Eddy Current Probe only** (e.g., BTT Eddy).
Measures 3 points, fits a plane, and moves 3 Z steppers with `FORCE_MOVE`.
**Primitive** — no advanced safety or multi-probe support.

---

## Install

1. Copy `eddy_single.py` to:

   ```bash
   ~/klipper/klippy/extras/
   ```
2. In `printer.cfg` add:

   ```ini
   [auto_tilt]
   z_positions:  10,10
                 200,10
                 105,200
   points:       80,160
                 40,40
                 160,40
   speed: 150
   z_hop: 5
   z_hop_speed: 5
   max_retries: 3
   retry_tolerance: 0.1
   home_position: 70,100
   ```
3. Ensure `force_move` is enabled in your Klipper configuration to allow the required stepper moves.
4. Restart Klipper:

   ```bash
   sudo service klipper restart
   ```

---

## Run

```gcode
AUTO_TILT_EDDY
```

1. Probe 3 points with Eddy probe.
2. Calculate bed plane.
3. Adjust each Z screw.
4. Return to home position.
5. Home Z axis.

---

## Limitations

* **Only works with Eddy probe coil** (`probe_eddy_current btt_eddy`).
* Requires `force_move` enabled.
* No mesh leveling or advanced checks.
* Uses raw `FORCE_MOVE` — ensure adjustments are mechanically safe.
