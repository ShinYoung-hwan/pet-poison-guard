from sqlalchemy import Column, String, Integer, JSON, Text, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from pgvector.sqlalchemy import Vector

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
