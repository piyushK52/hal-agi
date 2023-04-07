from utils.solver import solve
from utils.task_tree import TaskNode


def main():
    task = input("Task: ")
    root = TaskNode(task)
    res = solve(root, debug=False)
    print(res)

if __name__ == '__main__':
    main()