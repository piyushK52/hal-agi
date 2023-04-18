from settings import MAX_TREE_DEPTH
from utils.ai_agent.ai_agent import get_ai_agent
from utils.task_tree import TaskNode, print_level_wise_tree


def is_solved_or_null(node):
    return node == None or node.result != None

def solve(task_node: TaskNode, debug=False):
    ai_agent = get_ai_agent(debug=debug)

    # generate sub-task tree
    tree_height = MAX_TREE_DEPTH
    queue = [task_node]
    while len(queue):
        next_level = []
        tree_height -= 1
        
        for node in queue:
            if tree_height and ai_agent.is_breakdown_of_task_needed(node.task):
                sub_task_data = ai_agent.breakdown_into_subtask(node.task)
                sub_task_list = sub_task_data.split(';')

                first = TaskNode(sub_task_list[0]) if len(sub_task_list) else None
                second = TaskNode(sub_task_list[1]) if len(sub_task_list) > 1 else None
                third = TaskNode(sub_task_list[2]) if len(sub_task_list) > 2 else None 
                
                first and next_level.append(first)
                second and next_level.append(second)
                third and next_level.append(third)

                node.first = first
                node.second = second
                node.third = third
        
        queue = next_level
        print("new tasks created: ", [x.task for x in queue])


    # print_level_wise_tree(task_node)

    # get task results and combine the answer
    def recursive_solver(node: TaskNode):
        if not node:
            return
        
        if not (is_solved_or_null(node.first) and is_solved_or_null(node.second) and is_solved_or_null(node.third)):
            recursive_solver(node.first)
            recursive_solver(node.second)
            recursive_solver(node.third)
            
        data = ''
        data += node.first.result if node.first else ''
        data += node.second.result if node.second else ''
        data += node.third.result if node.third else ''

        data = data if data else None

        res = ai_agent.solve_task(node.task, data)
        node.result = res

    recursive_solver(task_node)
    return task_node.result

def break_dict_by_length(data, max_chars):
    result = []
    current = {}
    current_chars = 0

    for k, v in data.items():
        item_chars = len(str(k)) + len(str(v))
        if current_chars + item_chars > max_chars:
            result.append(current)
            current = {}
            current_chars = 0
        current[k] = v
        current_chars += item_chars

    if current:
        result.append(current)

    return result
