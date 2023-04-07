from settings import project_init
from utils.solver import solve
from utils.task_tree import TaskNode


def main():
    project_init()

    task = input("Task: ")
    root = TaskNode(task)
    res = solve(root)
    print(res)

if __name__ == '__main__':
    main()