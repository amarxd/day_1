

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from models import Todo, Base
from database import engine, SessionLocal

app = FastAPI()

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

class TodoItem(BaseModel):
	id: int | None = None
	task: str
	done: bool = False

	class Config:
		orm_mode = True

def get_db():
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()

# List all todos
@app.get("/todos", response_model=list[TodoItem])
def get_todos(db: Session = Depends(get_db)):
	todos = db.query(Todo).all()
	return todos

# Add a new todo
@app.post("/todos", response_model=TodoItem)
def add_todo(todo: TodoItem, db: Session = Depends(get_db)):
	db_todo = Todo(task=todo.task, done=todo.done)
	db.add(db_todo)
	db.commit()
	db.refresh(db_todo)
	return db_todo

# Update a todo
@app.put("/todos/{id}", response_model=TodoItem)
def update_todo(id: int, todo: TodoItem, db: Session = Depends(get_db)):
	db_todo = db.query(Todo).filter(Todo.id == id).first()
	if not db_todo:
		raise HTTPException(status_code=404, detail="Todo not found")
	db_todo.task = todo.task
	db_todo.done = todo.done
	db.commit()
	db.refresh(db_todo)
	return db_todo

# Delete a todo
@app.delete("/todos/{id}")
def delete_todo(id: int, db: Session = Depends(get_db)):
	db_todo = db.query(Todo).filter(Todo.id == id).first()
	if not db_todo:
		raise HTTPException(status_code=404, detail="Todo not found")
	db.delete(db_todo)
	db.commit()
	return {"message": "Deleted successfully"}
