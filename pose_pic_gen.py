import os
import sys
import json
import math
from collections import namedtuple
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib as mpl


Point = namedtuple("Point", ["x", "y"])
Pose = namedtuple("Pose", ["x", "y", "theta", "direction", "speed"])
Lot = namedtuple("Lot", ["p0", "p1", "p2", "p3"])

Trajectory = namedtuple("Trajectory", ["plan_failed_reasons", "car_loc", \
    "parking_space", "expect_tracks", "actual_track"])

CaseInfo = namedtuple("CaseInfo", ["case_id", "description"])

TrajectResult = namedtuple("TrajectResult", ["result", "case_info", "trajectory"])

class Keys(object):
    k_test_cases = "test_cases"
    k_descriptions = "descriptions"
    k_description = "Description"
    k_case_id = "Test Case ID"
    k_case_pass = "pass"
    k_channels = "channels"
    k_topic_name = "topic_name"
    k_failed_reason = "plan_failed_reasons"
    k_car_loc = "car_loc"
    k_x = "x"
    k_y = "y"
    k_theta = "theta"
    k_parking_space = "parking_space"
    k_p0 = "p0"
    k_p1 = "p1"
    k_p2 = "p2"
    k_p3 = "p3"
    k_out_messages = "output_messages"
    k_waypoints = "waypoints"
    k_direction = "direction"
    k_speed = "speed"
    k_pose = "pose"
    k_saved_images = "saved_images"


class Consts(object):
    TRAJECTORY_TOPIC_NAME = "TrajectoryFully"
    FullFailReasonColl = ["TypeValidationFailure",
                            "StartEndDistanceFailure",
                            "TurnCountDiffFailure",
                            "TurnCurveRateFailure"]
class State(object):
    Unknown = 0
    BeginActual = 1
    EndActual = 2
    BeginExpect = 3
    EndExpect = 4

class OutMessageParser(object):
    def __init__(self, in_msg_list):
        self.msg_list = in_msg_list

    def parse(self):
        state = State.Unknown
        acutal_lines = []
        expect_lines = []
        for msg_line in self.msg_list:
            if state == State.Unknown:
                if msg_line.strip() == "Actual Message:":
                    state = State.BeginActual
                if msg_line.strip() == "Expect Message:":
                    state = State.BeginExpect

            elif state == State.BeginActual:
                if msg_line.strip() != "":
                    acutal_lines.append(msg_line)
                if msg_line.strip() == "":
                    state = State.Unknown
            
            elif state == State.BeginExpect:
                if msg_line.strip() != "":
                    expect_lines.append(msg_line)
                
                if msg_line.strip() == "":
                    state = State.Unknown
        actual_msg = ""
        expect_msg = ""
        for line in acutal_lines:
            actual_msg += line
        
        for line in expect_lines:
            expect_msg += line
        return json.loads(actual_msg), json.loads(expect_msg)


class RoadPrinter(object):
    def __init__(self, _case_info, _trajectory, _image_path):
        self.trajectory = _trajectory
        self.case_info = _case_info
        self.image_path = _image_path
        self.circle_size = 80
        self.car_circle_size = 180
        self.car_length = 4.765
        self.car_width = 1.845

    def init_plot(self):
        print("init_plot")
        plt.figure(figsize=(14.0, 14.0), dpi=80)
        
    def plot_one_waypoint_line(self, waypoints, color_, label_, line_width=0.5):
        x_list = list()
        y_list = list()

        for waypoint in waypoints:
            x_list.append(waypoint.x)
            y_list.append(waypoint.y)
        plt.plot(x_list, y_list, color=color_, linewidth=line_width, label=label_)

    def make_failed_reason(self, failed_rea):
        failed_rea_s = ""
        for rea in failed_rea:
            failed_rea_s += rea + ", "
        return failed_rea_s[:-2]

    def plot_waypoint_line(self, expect_track, actual_track, failed_rea):
        failed_rea_s = self.make_failed_reason(failed_rea)
        expect_label = "expect tracks: %s" % failed_rea_s
        actual_label = "actual tracks: %s" % failed_rea_s
        self.plot_one_waypoint_line(expect_track, "green", expect_label, line_width=2)
        self.plot_one_waypoint_line(actual_track, "red", actual_label, line_width=2)
    
    def plot_one_direction_line(self, waypoint, color_):
        x = waypoint.x
        y = waypoint.y
        theta = -waypoint.theta
        x2 = x + 1.5*math.cos(theta)
        y2 = y + 1.5*math.sin(theta)
        plt.plot([x, x2], [y, y2], color=color_, linewidth=0.5)
        

    def plot_waypoint_direction_lines(self, expect_track, actual_track):
        for waypoint in expect_track:
            self.plot_one_direction_line(waypoint, "green")
        for waypoint in actual_track:
            self.plot_one_direction_line(waypoint, "red")

    def plot_waypoint_circle(self, waypoints, color):
        for waypoint in waypoints:
            plt.scatter(waypoint.x, waypoint.y, s=self.circle_size, \
                facecolors='none', edgecolors=color)

    def plot_one_waypoint(self, expect_track, actual_track):
        self.plot_waypoint_circle(expect_track, "red")
        self.plot_waypoint_circle(actual_track, "black")
    
    def plot_car_pos(self, car_loc):
        print("plot car pos...")
        x = car_loc.x
        y = car_loc.y
        theta = car_loc.theta
        car_loc_label = "car loc: x: %s, y: %s, theta: %s" % (x, y, theta)
        plt.scatter(x, y, s=self.car_circle_size, color="red", label=car_loc_label)
        
    def plot_car_direction_arrow(self, waypoint, color_):
        x = waypoint.x
        y = waypoint.y
        theta = waypoint.theta

        degree = theta* 180/ math.pi
        x2 = x + 1.5
        y2 = y
        ax = plt.axes()
        arr = patches.Arrow(x, y, x2, y2, width=0.1)
        t2 = mpl.transforms.Affine2D().rotate_deg(degree) + ax.transData
        arr.set_transform(t2) 
        ax.add_patch(arr)

    def plot_car_body(self, car_loc):
        print("plot car body...")
        x = car_loc.x
        y = car_loc.y
        theta = car_loc.theta
        degree = theta* 180/ math.pi
        x -= self.car_length / 2
        y -= self.car_width / 2
        car_rec = patches.Rectangle((x, y), self.car_length, self.car_width, \
            color="blue", fill=False)
        ax = plt.axes()
        t2 = mpl.transforms.Affine2D().rotate_deg(degree) + ax.transData
        car_rec.set_transform(t2) 
        ax.add_patch(car_rec)

    def plot_car(self, car_loc):
        print("car loc...")
        self.plot_car_pos(car_loc)
        self.plot_car_direction_arrow(car_loc, "green")
        self.plot_car_body(car_loc)

    def plot_lots(self, parking_space):
        print("parking")
        print(parking_space)
        points = list()
        points.append(parking_space.p0)
        points.append(parking_space.p1)
        points.append(parking_space.p2)
        points.append(parking_space.p3)
        x_list = list()
        y_list = list()
        for point in points:
            x_list.append(point.x)
            y_list.append(point.y)
        plt.plot(x_list, y_list, color='green', linewidth=3.0)

    def plot_pictures(self):
        print("Start to plot pictures...")
        expect_tracks = self.trajectory.expect_tracks
        actual_track = self.trajectory.actual_track
        plan_failed_reas = self.trajectory.plan_failed_reasons
        car_loc = self.trajectory.car_loc
        parking_space = self.trajectory.parking_space
        image_paths = list()
        for i, expect_track in enumerate(expect_tracks):
            self.init_plot()
            self.plot_one_waypoint(expect_track, actual_track)
            failed_rea = plan_failed_reas[i]
            print(failed_rea)
            self.plot_waypoint_line(expect_track, actual_track, failed_rea)
            # It's too messy to print out the direction lines, so omit them
            # self.plot_waypoint_direction_lines(expect_track, actual_track)
            self.plot_car(car_loc)
            self.plot_lots(parking_space)
            plt.legend(loc='best')
            case_id = self.case_info.case_id
            description = self.case_info.description
            description = description.replace("/", "\\")
            img_name = "%s_%s_%s.png" % (case_id, description, i)
            # img_name = img_name.replace(" ", "_")
            img_path = os.path.join(self.image_path, img_name)
            plt.savefig(img_path)
            image_paths.append(img_path)
        return image_paths
            

class TrackParser(object):
    def __init__(self, _case_js):
        self.case_js = _case_js

    def parse_waypoints(self, waypoints):
        poses = list()
        for waypoint in waypoints:
            direction = waypoint[Keys.k_direction]
            speed = waypoint[Keys.k_speed]
            x = waypoint[Keys.k_pose][Keys.k_x]
            y = waypoint[Keys.k_pose][Keys.k_y]
            theta = waypoint[Keys.k_pose][Keys.k_theta]
            poses.append(Pose(x, y, theta, direction, speed))
        return poses


    def parse_trajectory_channel(self, channel):
        # If there's no plan_fail_reason, this means actual messages is null
        if Keys.k_failed_reason not in channel:
            return None

        plan_failed_reas = channel[Keys.k_failed_reason]
        print(plan_failed_reas)

        car_loc_js = channel[Keys.k_car_loc]
        car_loc = Pose(car_loc_js[Keys.k_x], car_loc_js[Keys.k_y],\
             car_loc_js[Keys.k_theta], 0, 0)
        print(car_loc)

        parking_space_js = channel[Keys.k_parking_space]
        p0 = Point(parking_space_js[Keys.k_p0][Keys.k_x], parking_space_js[Keys.k_p0][Keys.k_y]) 
        p1 = Point(parking_space_js[Keys.k_p1][Keys.k_x], parking_space_js[Keys.k_p1][Keys.k_y]) 
        p2 = Point(parking_space_js[Keys.k_p2][Keys.k_x], parking_space_js[Keys.k_p2][Keys.k_y]) 
        p3 = Point(parking_space_js[Keys.k_p3][Keys.k_x], parking_space_js[Keys.k_p3][Keys.k_y]) 
        lot = Lot(p0, p1, p2, p3)
        print(lot)

        raw_output_messages = channel[Keys.k_out_messages]
        raw_output_message = raw_output_messages[0]

        output_messages = raw_output_message.split("<br/>")
        omsg_parser = OutMessageParser(output_messages)
        actual_msg, expect_msg = omsg_parser.parse()
        # Adjust the expect_msg to be a list
        if  not isinstance(expect_msg, list):
            expect_msg = [expect_msg]

        expect_roads = list()
        # Expect_tracks has multiple roads
        for expect in expect_msg:
            waypoints = expect[Keys.k_waypoints]
            expect_roads.append(self.parse_waypoints(waypoints))
        # Actual_tracks has only one road
        actual_road = self.parse_waypoints(actual_msg[Keys.k_waypoints])

        traject = Trajectory(plan_failed_reas, car_loc, lot, expect_roads, actual_road)
        return traject

    def parse_test_case(self):
        descriptions = self.case_js[Keys.k_descriptions]
        case_id = descriptions[Keys.k_case_id]
        case_pass = self.case_js[Keys.k_case_pass]
        # If the case is passed, skip the trajectory printing process
        if case_pass is True:
            return TrajectResult(False, None, None)

        description = descriptions[Keys.k_description]
        channels = self.case_js[Keys.k_channels]
        case_info = CaseInfo(case_id, description)


        trjactory = None
        for channel in channels:
            topic_name = channel[Keys.k_topic_name]
            if topic_name == Consts.TRAJECTORY_TOPIC_NAME:
                trjactory = self.parse_trajectory_channel(channel)
                break
        if trjactory is None:
            return TrajectResult(False, None, None)
        return TrajectResult(True, case_info, trjactory)
    
class PosePrint(object):
    def __init__(self, _result_file, _image_path):
        self.result_file = _result_file
        self.image_path = _image_path

    def print_poses(self):
        with open(self.result_file) as result_f:
            result_js = json.load(result_f)
            test_cases = result_js[Keys.k_test_cases]
            for test_case in test_cases:
                tp = TrackParser(test_case)
                t_res = tp.parse_test_case()
                if t_res.result is True:
                    rp = RoadPrinter(t_res.case_info, t_res.trajectory, self.image_path)
                    rp.plot_pictures()

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python pose_pic_gen.py {result_json_path} {image_out_path}")
        print("Example:  python pose_pic_gen.py ./result.json ./images")
        exit(-1)

    result_js_path = sys.argv[1]
    image_path = sys.argv[2]
    if not os.path.exists(image_path):
        os.makedirs(image_path)

    p = PosePrint(result_js_path, image_path)
    p.print_poses()    