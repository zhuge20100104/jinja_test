
from jinja2 import FileSystemLoader, Environment
from collections import namedtuple

Person = namedtuple("Person", ["name", "age", "sex"])


class Student(object):
    def __init__(self, name, age, score):
        self.name = name
        self.age = age
        self.score = score


def test_render_list():
    print("render list")
    loader = FileSystemLoader("./sources")
    env = Environment(
        loader = loader
    )
    persons = [Person("ZhangSan", 23, "Man"),
                Person("LiSi", 22, "Man"),
                Person("YanYuanYuan", 18, "Woman")]    

    template = env.get_template('list.htm')
    list_render_res = template.render(persons=persons)
    with open("dests/list.htm", "w") as f:
        f.write(list_render_res)
    print(list_render_res)
    assert True, "Test render list failed!"


def test_render_object():
    print("render object")
    loader = FileSystemLoader("./sources")
    env = Environment(
        loader = loader
    )

    template = env.get_template('obj.htm')
    stu = Student("ZhangSan", 18, 81)
    list_render_res = template.render(stu=stu)
    with open("dests/obj.htm", "w") as f:
        f.write(list_render_res)
    print(list_render_res)
    assert True, "Test render obj failed!"


def test_render_dict():
    print("render dict")
    loader = FileSystemLoader("./sources")
    env = Environment(
        loader = loader
    )

    template = env.get_template('dict.htm')
    dic = {
        "test": {
            "test1": {
                "test2": "hehe"
            }
        }
    }
    list_render_res = template.render(dic=dic)
    with open("dests/dict.htm", "w") as f:
        f.write(list_render_res)
    print(list_render_res)
    assert True, "Test render dict failed!"


