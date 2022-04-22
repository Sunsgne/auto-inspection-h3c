from xml.dom.minidom import parse

from web.models import Commands


# 使用minidom解析器打开 XML 文档
def read_xml(filepath, prefix):
    dom_tree = parse(filepath)
    # 文档根元素
    root_node = dom_tree.documentElement

    # 获取文档中所有指令
    commands = root_node.getElementsByTagName("command")

    # 定义存入数据库的指令集
    command_list = []
    # 遍历文档中每个指令的信息，处理后加入command_list
    for command in commands:
        one = Commands()
        # if command.hasAttribute("protocol"):
        #     print("protocol: %s" % command.getAttribute("protocol"))
        if command.hasAttribute("gather_time"):
            one.gather_time = command.getAttribute("gather_time")
        if command.hasAttribute("depend_script"):
            depend_script = command.getAttribute("depend_script")
            if depend_script.endswith(".py"):
                depend_script = prefix + depend_script[:-3]
            one.depend_script = depend_script
        if command.hasAttribute("depend_script2"):
            depend_script2 = command.getAttribute("depend_script2")
            if depend_script2.endswith(".py"):
                depend_script2 = prefix + depend_script2[:-3]
            one.depend_script2 = depend_script2
        if command.hasAttribute("outview"):
            one.outview = command.getAttribute("outview")
        if command.hasAttribute("inview"):
            one.inview = command.getAttribute("inview")
        if command.hasAttribute("yesorno"):
            one.yes_no = command.getAttribute("yesorno")

        if command.hasChildNodes and command.childNodes:
            one.content = command.childNodes[0].data

        command_list.append(one)

    return command_list
