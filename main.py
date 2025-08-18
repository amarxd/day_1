
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

todos = []

class TodoItem(BaseModel):
	id: int
	task: str
	done: bool

# List all todos
@app.get("/todos")
def get_todos():
	return todos

# Add a new todo
@app.post("/todos")
def add_todo(todo: TodoItem):
	todos.append(todo)
	return todo

# Update a todo
@app.put("/todos/{id}")
def update_todo(id: int, todo: TodoItem):
	for i, t in enumerate(todos):
		if t.id == id:
			todos[i] = todo
			return todo
	return {"error": "Todo not found"}

# Delete a todo
@app.delete("/todos/{id}")
def delete_todo(id: int):
	for i, t in enumerate(todos):
		if t.id == id:
			todos.pop(i)
			return {"message": "Deleted successfully"}
	return {"error": "Todo not found"}
