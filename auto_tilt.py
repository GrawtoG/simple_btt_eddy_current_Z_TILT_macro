# klippy/extras/auto_tilt.py
import time

class EddySingleMeasure:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.gcode = self.printer.lookup_object('gcode')

        self.z_positions = config.getlists('z_positions', seps=(',', '\n'),
                                           parser=float, count=2)
        self.points = config.getlists('points', seps=(',', '\n'),
                                           parser=float, count=2)
        self.speed = config.getfloat('speed', 150, above=0.0)
        self.z_hop = config.getfloat('z_hop', 5.0, above=5.0)
        self.z_hop_speed = config.getfloat('z_hop_speed', 5.0, above=0.0)

        self.max_retries = config.getint('max_retries', 3, minval=0)
        self.retry_tolerance = config.getfloat('retry_tolerance', 0.1,
                                               above=0.0)

        raw_home_pos = config.get('home_position', None)
        if raw_home_pos is not None:
            self.home_position = [float(v) for v in raw_home_pos.replace('\n', ',').split(',')]
        else:
            self.home_position = [70.0, 100.0]







        self.gcode.register_command("AUTO_TILT_EDDY",
                               self.cmd_AUTO_TILT_EDDY,
                               desc="Do single eddy current measurement")




    def cmd_AUTO_TILT_EDDY(self, gcmd):

        self.eddy_probe = self.printer.lookup_object('probe_eddy_current btt_eddy')
        self.eddy_descend = self.eddy_probe.eddy_descend
        try:
            for i in range(self.max_retries + 1):
                gcmd.respond_info(f"Attempt {i+1}/{self.max_retries + 1}")
                result = self.scan_and_make_adjustments(gcmd)
                if result <= self.retry_tolerance:
                    gcmd.respond_info(f"Adjustments within tolerance: {result} <= {self.retry_tolerance}")
                    break

        except Exception as e:
            gcmd.respond_info(f"Exception: {e}")

        toolhead = self.printer.lookup_object('toolhead')
        move = toolhead.manual_move
        pos = toolhead.get_position()

        pos[2] += self.z_hop
        move(pos, speed=self.z_hop_speed)
        toolhead.wait_moves()
        pos = toolhead.get_position()
        pos[0], pos[1]=self.home_position
        move(pos, speed=self.speed)
        toolhead.wait_moves()

        self.gcode.run_script_from_command("G28 Z")
        toolhead.wait_moves()

        pos = toolhead.get_position()
        pos[2] += self.z_hop
        move(pos, speed=self.z_hop_speed)
        toolhead.wait_moves()
        gcmd.respond_info(f"END AUTO_TILT_EDDY")


        return {'applied': True}

    def scan_and_make_adjustments(self, gcmd):
        results = [0]*len(self.points)
        session = self.eddy_probe.eddy_descend.start_probe_session(gcmd)

        toolhead = self.printer.lookup_object('toolhead')
        move = toolhead.manual_move

        toolhead.wait_moves()

        for i in range(3):
            pos = toolhead.get_position()
            pos[2] += self.z_hop
            move(pos, speed=self.z_hop_speed)
            toolhead.wait_moves()
            p = self.points[i]
            gcmd.respond_info(f"Moving to point {p}")
            pos = toolhead.get_position()
            pos[0] = p[0]
            pos[1] = p[1]
            move(pos, speed=self.speed)
            toolhead.wait_moves()
            session.run_probe(gcmd)
            results[i] = session.pull_probed_results()[0][:3]

        adjustments = self.calculate_adjustments(results)

        gcmd.respond_info("Adjustments:\n"+'\n'.join(f"screw{i} : {ad}" for i, ad in enumerate(adjustments)))


        gcmd.respond_info(f"Adjusting stepper_z by {adjustments[0]}")
        self.gcode.run_script_from_command(f"FORCE_MOVE STEPPER=stepper_z DISTANCE={adjustments[0]} VELOCITY=3")

        gcmd.respond_info(f"Adjusting stepper_z1 by {adjustments[1]}")
        self.gcode.run_script_from_command(f"FORCE_MOVE STEPPER=stepper_z1 DISTANCE={adjustments[1]} VELOCITY=3")

        gcmd.respond_info(f"Adjusting stepper_z2 by {adjustments[2]}")
        self.gcode.run_script_from_command(f"FORCE_MOVE STEPPER=stepper_z2 DISTANCE={adjustments[2]} VELOCITY=3")


        toolhead.wait_moves()
        session.end_probe_session()
        gcmd.respond_info("Adjustments applied")
        return max(adjustments)


    def calculate_adjustments(self, results):


        func = self.get_plane_from_points(results)
        screws_height = [-func(x, y) for x, y in self.z_positions]
        screw_max = max(screws_height)
        adjustments = [screw_max - screw_height  for screw_height in screws_height]
        adjustments = [round(adjustment, 3) for adjustment in adjustments]

        return adjustments


    def get_plane_from_points(self, points):
        # Calculate the plane from the points
        if len(points) < 3:
            raise ValueError("At least 3 points are required to define a plane")

        p1, p2, p3 = points
        x1, y1, z1 = p1
        x2, y2, z2 = p2
        x3, y3, z3 = p3

        D = (x1*(y2 - y3) - y1*(x2 - x3) + (x2*y3 - x3*y2))
        if D == 0:
            raise ValueError("Punkty są współliniowe!")

        a = ((z1*(y2 - y3) - y1*(z2 - z3) + (y2*z3 - y3*z2))) / D
        b = ((x1*(z2 - z3) - z1*(x2 - x3) + (x2*z3 - x3*z2))) / D
        c = ((x1*(y3*z2 - y2*z3) - y1*(x3*z2 - x2*z3) + z1*(x2*y3 - x3*y2))) / D

        return lambda x, y: a*x + b*y + c

def load_config(config):
    return EddySingleMeasure(config)
