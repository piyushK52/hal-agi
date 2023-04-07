from settings import MAX_TREE_DEPTH
from utils.ai_agent.ai_agent import get_ai_agent
from utils.task_tree import TaskNode, print_level_wise_tree


def solve(task_node: TaskNode):
    ai_agent = get_ai_agent(debug=True)

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


    print_level_wise_tree(task_node)

    # prioritize tasks in different levels
    # get task results and combine the answer 