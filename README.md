# HAL - AI code generator 
This project aims to be an AI assistant which generates code on the basis of a given codebase. It can also be extended to modify the current codebase. The project is still in very early iterations. I have only been able to generate smaller/simpler pieces of code.

### How does this work?
Hal creates a syntax tree of the code base. So if a function is a node it's children will be the functions that it depends on. Using this tree a description of every function is generated and stored as a vector embedding. When a coding task is given, it is broken into multiple steps and then checked against the functions already present (if they can be used to solve it).

![Syntax tree](https://i.ibb.co/2Kmp57S/Screenshot-2023-04-19-at-1-34-20-PM.png) ![alt text](https://i.ibb.co/42jpWmr/Screenshot-2023-04-19-at-1-33-41-PM.png)


### Getting Started
- Clone the repo and create a virtual python environment using ```python3 -m venv venv```
- Install the dependencies using ```pip install -r requirements.txt```
- Make sure you have have docker running. Use ```docker-compose -f dev.yaml up -d``` to start the postgres instance with vector extension
- Run the app using ```python app.py```

### Known Issues/Improvements
- Try different variations of prompts (especially CoT) and temperature settings
- While building the tree, if the syntax anywhere is not correct then the code breaks. Try to correct the syntax or remove such files/directories from codemap.py
- I am using local postgres for vector operations. If you are not completely familiar with it then you can create a Pinecone client 

## Contribute
I will be actively working on this. If you are looking for a fun side-project or just passionate about AI please join the discord channel here https://discord.gg/nJRuTkck