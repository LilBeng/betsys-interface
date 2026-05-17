import os
import subprocess
import xml.etree.ElementTree as ElementTree

script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)

qrc_path = os.path.join(parent_dir, "resources.qrc")
output_path = os.path.join(parent_dir, "resources_rc.py")

root = ElementTree.Element("RCC")
qresource = ElementTree.SubElement(root, "qresource", prefix="/")

resources_dir = os.path.join(parent_dir, "resources")
for dir_path, dir_names, filenames in os.walk(resources_dir):
    for filename in filenames:
        full_path = os.path.join(dir_path, filename)
        rel_path = os.path.relpath(full_path, parent_dir)
        ElementTree.SubElement(qresource, "file").text = rel_path

if __name__ == "__main__":
    tree = ElementTree.ElementTree(root)
    tree.write(qrc_path, encoding="utf-8", xml_declaration=True)

    subprocess.run(["pyside6-rcc", qrc_path, "-o", output_path], check=True)