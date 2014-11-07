from node_mapper.test import test
from node_mapper.kivyui.main import launch

def main():
    root_node = test()
    return launch(interactive=True, root_node=root_node)
    
    
if __name__ == '__main__':
    main()
