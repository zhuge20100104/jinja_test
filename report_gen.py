import copy
import json
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
    def __init__(self, result_file, tpl_path, report_path, report_name):
        self.result_file = result_file
        self.tpl_path = tpl_path
        self.report_path = report_path
        self.report_name = report_name


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

    def generate(self):
        with open(self.result_file) as res_f:
            old_json = json.load(res_f, object_pairs_hook=OrderedDict)
            json_conv = JsonConvertor()
            json_result = json_conv.add_show_descriptions(old_json)
            final_report_name = "Integration Test Report for %s" % (self.report_name)
            json_result["report_name"] = final_report_name
            # Make passed rate shows more friendly, 2 float points
            pass_rate = json_result["pass_rate"]
            json_result["pass_rate"] = round(pass_rate, 2) 

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
            self.render_report(json_result)
            


if __name__ == '__main__':
    # 3 parameters  1. result.json   2. it_template   3. report_dir  4. image_dir = report_dir/images
    rg = ReportGen("./result.json", "./it_template", "./report", "Planning BVT")
    rg.generate()

