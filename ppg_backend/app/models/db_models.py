from sqlalchemy import Column, String, Integer, JSON, Text, ARRAY
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import declarative_base
Base = declarative_base()

class RecipeData(Base):
    __tablename__ = 'recipe_data'
    id = Column(String, primary_key=True)
    data = Column(JSON)

class RecEmbed(Base):
    __tablename__ = 'rec_embeds'
    id = Column(String, primary_key=True)
    embedding = Column(Vector(1024))

class PetPoison(Base):
    __tablename__ = 'pet_poisons'
    id = Column(Integer, primary_key=True)
    name = Column(Text)
    alternate_names = Column(ARRAY(Text))
    poison_description = Column(Text)
    desktop_thumb = Column(Text)

# TODO : Migrate from in-memory task management to DB-backed task management
# # Task model for async analysis jobs
# from sqlalchemy import DateTime, func
# from sqlalchemy.dialects.postgresql import UUID
# import uuid

# class Task(Base):
#     __tablename__ = 'tasks'
#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     status = Column(String, nullable=False, default='pending')
#     input_meta = Column(JSON)
#     result = Column(JSON, nullable=True)
#     retries = Column(Integer, default=0)
#     last_error = Column(Text, nullable=True)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
