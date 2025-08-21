


from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session
from models import Todo, User
from database import SessionLocal
from auth import hash_password, verify_password, create_access_token

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

class UserCreate(BaseModel):
	username: str
	email: str
	password: str

class UserOut(BaseModel):
	id: int
	username: str
	email: str
	is_active: bool
	class Config:
		orm_mode = True

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

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
	from jose import JWTError, jwt
	from auth import SECRET_KEY, ALGORITHM
	credentials_exception = HTTPException(
		status_code=status.HTTP_401_UNAUTHORIZED,
		detail="Could not validate credentials",
		headers={"WWW-Authenticate": "Bearer"},
	)
	try:
		payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
		username: str = payload.get("sub")
		if username is None:
			raise credentials_exception
	except JWTError:
		raise credentials_exception
	user = db.query(User).filter(User.username == username).first()
	if user is None:
		raise credentials_exception
	return user

# User registration
@app.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
	if db.query(User).filter((User.username == user.username) | (User.email == user.email)).first():
		raise HTTPException(status_code=400, detail="Username or email already registered")
	hashed_pw = hash_password(user.password)
	db_user = User(username=user.username, email=user.email, hashed_password=hashed_pw)
	db.add(db_user)
	db.commit()
	db.refresh(db_user)
	return db_user

# User login
@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
	user = db.query(User).filter(User.username == form_data.username).first()
	if not user or not verify_password(form_data.password, user.hashed_password):
		raise HTTPException(status_code=401, detail="Invalid credentials")
	token = create_access_token({"sub": user.username})
	return {"access_token": token, "token_type": "bearer"}

# List all todos for current user
@app.get("/todos", response_model=list[TodoItem])
def get_todos(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
	return db.query(Todo).filter(Todo.owner_id == current_user.id).all()

# Add a new todo for current user
@app.post("/todos", response_model=TodoItem)
def add_todo(todo: TodoItem, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
	db_todo = Todo(task=todo.task, done=todo.done, owner_id=current_user.id)
	db.add(db_todo)
	db.commit()
	db.refresh(db_todo)
	return db_todo

# Update a todo for current user
@app.put("/todos/{id}", response_model=TodoItem)
def update_todo(id: int, todo: TodoItem, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
	db_todo = db.query(Todo).filter(Todo.id == id, Todo.owner_id == current_user.id).first()
	if not db_todo:
		raise HTTPException(status_code=404, detail="Todo not found")
	db_todo.task = todo.task
	db_todo.done = todo.done
	db.commit()
	db.refresh(db_todo)
	return db_todo

# Delete a todo for current user
@app.delete("/todos/{id}")
def delete_todo(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
	db_todo = db.query(Todo).filter(Todo.id == id, Todo.owner_id == current_user.id).first()
	if not db_todo:
		raise HTTPException(status_code=404, detail="Todo not found")
	db.delete(db_todo)
	db.commit()
	return {"message": "Deleted successfully"}
	db.commit()
	return {"message": "Deleted successfully"}
