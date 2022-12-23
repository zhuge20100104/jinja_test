import json
import shutil
from collections import OrderedDict
from jinja2 import FileSystemLoader, Environment
from pose_pic_gen import *

class JsonConvertor(object):  
    def make_new_key(self, old_key):
        arr = old_key.split(" ")
        new_key = ""
        for ele in arr:
            new_key += ele 
            new_key += "_"
        new_key = new_key.lower()
        return new_key[:-1]

    def add_show_descriptions(self, old_json):
        test_cases = old_json[Keys.k_test_cases]
        for test_case in test_cases:
            test_case["show_descriptions"] = dict()
            descriptions = test_case[Keys.k_descriptions]
            for key, val in descriptions.items():
                new_key = self.make_new_key(key)
                test_case["show_descriptions"][new_key] = val
        return old_json
        

class ReportGen(object):
    def __init__(self, result_file, tpl_path, report_path, report_name, module_name):
        self.result_file = result_file
        self.tpl_path = tpl_path
        self.report_path = report_path
        self.report_name = report_name
        self.module_name = module_name


    def render_report(self, dic):
        loader = FileSystemLoader(self.tpl_path)
        env = Environment(
            loader = loader
        )

        template = env.get_template('index-tpl.html')

        list_render_res = template.render(report=dic)
        with open(self.report_path + "/index.htm", "w") as f:
            f.write(list_render_res.encode("utf-8"))
        print(list_render_res)

    # Make the report dir and image dir
    def prepare_dirs(self):
        report_dir = self.report_path
        it_tpl_dir = self.tpl_path
        # Make the report dir and image dir
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)
        image_path = os.path.join(report_dir, "images")
        if not os.path.exists(image_path):
            os.makedirs(image_path)
        
        css_src_dir = os.path.join(it_tpl_dir, "css")
        js_src_dir = os.path.join(it_tpl_dir, "js")
        css_dst_dir = os.path.join(report_dir, "css")
        js_dst_dir = os.path.join(report_dir, "js")
        if not os.path.exists(css_dst_dir) or not os.path.exists(js_dst_dir):
            shutil.copytree(css_src_dir, css_dst_dir)
            shutil.copytree(js_src_dir, js_dst_dir)

    def generate(self):
        with open(self.result_file) as res_f:
            old_json = json.load(res_f, object_pairs_hook=OrderedDict)
            json_conv = JsonConvertor()
            # Add a show_descriptions field for displaying
            json_result = json_conv.add_show_descriptions(old_json)
            # Make the test report title
            final_report_name = "Integration Test Report for %s" % (self.report_name)
            json_result["report_name"] = final_report_name
            # Make passed rate shows more friendly, 2 float points
            pass_rate = json_result["pass_rate"]
            json_result["pass_rate"] = round(pass_rate, 2) 

            # Split passed and failed cases to two part
            json_result["failed_test_cases"] = list()
            json_result["passed_test_cases"] = list()

            all_test_cases = json_result[Keys.k_test_cases]
            for index, test_case in enumerate(all_test_cases):
                test_case["index"] = index
                is_pass = test_case[Keys.k_case_pass]
                if is_pass:
                    json_result["passed_test_cases"].append(test_case)
                else:
                    json_result["failed_test_cases"].append(test_case)
            
            if self.module_name == "planning":
                # If this is the planning module, generate failed route pictures
                failed_test_cases = json_result["failed_test_cases"]
                image_path = os.path.join(self.report_path, "images")
                for failed_case in failed_test_cases:
                    tp = TrackParser(failed_case)
                    t_res = tp.parse_test_case()
                    if t_res.result is True:
                        rp = RoadPrinter(t_res.case_info, t_res.trajectory, image_path)
                        res_image_paths = rp.plot_pictures()
                        # Use relative paths for the report pictures
                        res_image_rel_paths = ["./"+raw_path.split(self.report_path)[1] for raw_path in res_image_paths]
                        channels = failed_case[Keys.k_channels]
                        for channel in channels:
                            if channel[Keys.k_topic_name] == 'TrajectoryFully':
                                channel[Keys.k_saved_images] = res_image_rel_paths
            self.render_report(json_result)
            

if __name__ == '__main__':
  
    if len(sys.argv) < 6:
        print("Usage: python report_gen.py {result_json_path} {it_template_dir} {report_dir} {Report_name} {module_name}")
        print("Example: python report_gen.py ./result.json ./it_template ./report 'Planning BVT' planning")
        exit(-1)
    
    result_js_path = sys.argv[1]
    it_tpl_dir = sys.argv[2]
    report_dir = sys.argv[3]
    report_name = sys.argv[4]
    module_name = sys.argv[5]

    rg = ReportGen(result_js_path, it_tpl_dir, report_dir, report_name, module_name)
    rg.prepare_dirs()
    rg.generate()

