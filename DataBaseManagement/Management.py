from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import List
from sqlalchemy import create_engine, Column, Integer, String, Date, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, Session


# Is done: Base de datos en persistencia SQLite
database_url = "sqlite:///./tasksmanager.db"
enguine = create_engine(database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=enguine)
Base = declarative_base()   

class TaskDB(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(100), nullable=False)
    contenido = Column(String(200), nullable=False)
    deadline = Column(Date, nullable=False)
    completada = Column(Boolean, default=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=enguine)

# Is done: Modelos Pydantic
class TaskCreate(BaseModel):
    titulo: str = Field(min_length=1, max_length=100, description="Título de la tarea")
    contenido: str = Field(min_length=1, max_length=200, description="Contenido de la tarea")
    deadline: date = Field(description="Fecha de vencimiento")

class TaskUpdate(BaseModel):
    titulo: str = Field(min_length=1, max_length=100, description="Edit Título de la tarea") 
    contenido: str = Field(min_length=1, max_length=200, description="Edit Contenido de la tarea")
    deadline: date = Field(description="Edit fecha de vencimiento")
    completada: bool = Field(description="Edit estado de completado")

class TaskResponse(BaseModel):
    id: int
    titulo: str
    contenido: str
    deadline: date
    completada: bool
    fecha_creacion: datetime

    class Config:
        orm_mode = True

# Is done: Implementar clase TaskManager con lógica de negocio
# class TaskManager:

class TaskManager:
    def __init__(self, db: Session):
        self.db = db

    def _is_future_deadline(self, deadline: date) -> bool:
        return deadline >= date.today()
    
    def _clean_text(self, text: str) -> str:
        """Función para normalizar o censurar palabras malsonantes en títulos y contenidos"""
        # Implementar lógica de limpieza de palabras malsonantes
        censored_words = ["maldición", "tonto", "idiota","malo", "tonto", "feo"]
        for word in censored_words:
            text = text.replace(word, "****")
        return text.strip()
    
    def add_task(self, task_create: TaskCreate) -> TaskDB:
        """Crear una nueva tarea en la base de datos de tareas"""
        newTask = TaskDB(
            titulo=self._clean_text(task_create.titulo),
            contenido=self._clean_text(task_create.contenido),
            deadline=task_create.deadline,
            completada=False,
            fecha_creacion=datetime.utcnow()
        )
        self.db.add(newTask)
        self.db.commit()
        self.db.refresh(newTask)
        return newTask

    def get_task(self, task_id: int) -> TaskDB:
        # Obtener una tarea por su ID
        itemtask = self.db.query(TaskDB).filter(TaskDB.id == task_id).first()
        if not itemtask:
            raise ValueError(f"Tarea con ID {task_id} no encontrada")   
        return itemtask
                    
    def get_all_tasks(self) -> List[TaskDB]:
        # Obtener todas las tareas de la base de datos
        return self.db.query(TaskDB).all()
                        
    def set_task_completed(self, task_id: int) -> TaskDB:
        # Marcar una tarea como completada 
        itemtask = self.get_task(task_id)
        if itemtask:
            itemtask.completada = True
            self.db.commit()
            self.db.refresh(itemtask)
        return itemtask
  
    def update_task(self, task_id: int, task_update: TaskUpdate) -> TaskDB:
        # Actualizar una tarea existente
        itemtask = self.get_tarea(task_id)
        if itemtask:
            itemtask.titulo = self._clean_text(task_update.titulo)
            itemtask.contenido = self._clean_text(task_update.contenido)
            itemtask.deadline = task_update.deadline
            itemtask.completada = task_update.completada
            self.db.commit()
            self.db.refresh(itemtask)
        return itemtask
    
    def delete_task(self, task_id: int) -> bool:
        # Eliminar una tarea por su ID
        itemtask = self.get_task(task_id)
        if itemtask:
            self.db.delete(itemtask)
            self.db.commit()
            return True
        return False    
    
    def get_expired_tasks(self) -> List[TaskDB]:
        # Obtener tareas caducadas (deadline < fecha actual)
        today = date.today()
        return self.db.query(TaskDB).filter(TaskDB.deadline < today).all()
    
    def get_tasks_by_completion(self, completed: bool) -> List[TaskDB]: 
        # Obtener tareas por estado de completado
        return self.db.query(TaskDB).filter(TaskDB.completada == completed).all()
    
    def get_tasks_by_deadline(self, deadline: date) -> List[TaskDB]:
        # Obtener tareas por fecha de vencimiento específica
        return self.db.query(TaskDB).filter(TaskDB.deadline == deadline).all()
    
    def count_tasks(self) -> int:
        # Contar el número total de tareas en la base de datos
        return self.db.query(TaskDB).count()  
    
    def count_overdue(self) -> int:
        # Contar el número de tareas vencidas
        today = date.today()
        return self.db.query(TaskDB).filter(TaskDB.deadline < today, TaskDB.completada == False).count()
    
    def count_completed_tasks(self) -> int:
        # Contar el número de tareas completadas
        return self.db.query(TaskDB).filter(TaskDB.completada == True).count()
    
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()    