from node_mapper.test import test as node_test
from node_mapper.kivyui.main import launch

def test(root_node=None):
    if root_node is None:
        root_node = node_test(y_invert=True)
    return launch(interactive=True, root_node=root_node)
    
    
if __name__ == '__main__':
    test()
