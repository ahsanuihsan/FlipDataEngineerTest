from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import httpx
import random
import string
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import json

# Database setup
DATABASE_URL = "sqlite:///./pokemon_abilities.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Model
class PokemonAbility(Base):
    __tablename__ = "pokemon_abilities"
    
    id = Column(Integer, primary_key=True, index=True)
    raw_id = Column(String(13), nullable=False)
    user_id = Column(String(7), nullable=False)
    pokemon_ability_id = Column(Integer, nullable=False)
    effect = Column(Text, nullable=False)
    language = Column(Text, nullable=False)
    short_effect = Column(Text, nullable=False)

# Create tables
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(title="Pokemon Ability API", version="1.0.0")

# Pydantic models
class InputData(BaseModel):
    raw_id: str
    user_id: str
    pokemon_ability_id: str

class EffectEntry(BaseModel):
    effect: str
    language: Dict[str, str]
    short_effect: str

class OutputData(BaseModel):
    raw_id: str
    user_id: str
    returned_entries: List[EffectEntry]
    pokemon_list: List[str]

# Helper functions
def generate_random_id(length: int) -> str:
    """Generate random string with alphanumeric characters"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

@app.get("/")
async def root():
    return {"message": "Pokemon Ability API", "status": "running"}

@app.post("/process-ability", response_model=OutputData)
async def process_ability(input_data: InputData):
    """
    Process pokemon ability data:
    1. Receive input JSON
    2. Fetch data from PokeAPI
    3. Normalize and store effect_entries
    4. Return formatted response
    """
    try:
        # Fetch data from PokeAPI
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"https://pokeapi.co/api/v2/ability/{input_data.pokemon_ability_id}"
            )
            response.raise_for_status()
            ability_data = response.json()
        
        # Extract effect_entries
        effect_entries = ability_data.get("effect_entries", [])
        
        # Extract pokemon list
        pokemon_list = [
            pokemon["pokemon"]["name"] 
            for pokemon in ability_data.get("pokemon", [])
        ]
        
        # Store in database
        db = SessionLocal()
        try:
            for entry in effect_entries:
                db_entry = PokemonAbility(
                    raw_id=input_data.raw_id,
                    user_id=input_data.user_id,
                    pokemon_ability_id=int(input_data.pokemon_ability_id),
                    effect=entry.get("effect", ""),
                    language=json.dumps(entry.get("language", {})),
                    short_effect=entry.get("short_effect", "")
                )
                db.add(db_entry)
            db.commit()
        finally:
            db.close()
        
        # Format response
        returned_entries = [
            EffectEntry(
                effect=entry.get("effect", ""),
                language=entry.get("language", {}),
                short_effect=entry.get("short_effect", "")
            )
            for entry in effect_entries
        ]
        
        return OutputData(
            raw_id=input_data.raw_id,
            user_id=input_data.user_id,
            returned_entries=returned_entries,
            pokemon_list=pokemon_list
        )
        
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Error fetching data from PokeAPI: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/abilities/{raw_id}/{user_id}")
async def get_stored_abilities(raw_id: str, user_id: str):
    """
    Retrieve stored abilities by raw_id and user_id
    """
    db = SessionLocal()
    try:
        abilities = db.query(PokemonAbility).filter(
            PokemonAbility.raw_id == raw_id,
            PokemonAbility.user_id == user_id
        ).all()
        
        if not abilities:
            raise HTTPException(status_code=404, detail="No abilities found")
        
        result = []
        for ability in abilities:
            result.append({
                "id": ability.id,
                "raw_id": ability.raw_id,
                "user_id": ability.user_id,
                "pokemon_ability_id": ability.pokemon_ability_id,
                "effect": ability.effect,
                "language": json.loads(ability.language),
                "short_effect": ability.short_effect
            })
        
        return {"data": result}
        
    finally:
        db.close()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "database": "connected"}
