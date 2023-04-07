class TaskNode:
    def __init__(self, task, first=None, second=None, third=None):
        self.task = task
        self.first = first
        self.second = second
        self.third = third
        self.result = None
        self.priority_level = 1     # ranges from 1 to 10


def print_level_wise_tree(root: TaskNode):
    if root is None:
        return

    current_level = [root]
    
    while current_level:
        print([node.task for node in current_level])

        next_level = []
        for node in current_level:
            if node.first is not None:
                next_level.append(node.first)
            if node.second is not None:
                next_level.append(node.second)
            if node.third is not None:
                next_level.append(node.third)

        current_level = next_level