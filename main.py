import sys

def kivy_main():
    from node_mapper.kivyui.main import launch
    def main(root_node=None):
        return launch(interactive=True, root_node=root_node)
    main()
def clutter_main():
    from node_mapper.clutterui.main import main
    main()
    
    
if __name__ == '__main__':
    if 'kivy' in sys.argv:
        kivy_main()
    elif 'clutter' in sys.argv:
        clutter_main()


