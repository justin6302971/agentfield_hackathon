from agentfield import AgentRouter
from pydantic import BaseModel, Field
from typing import List, Optional

# Group related reasoners with a router
reasoners_router = AgentRouter(prefix="music", tags=["classical-music", "education"])

# --- Models ---

class ComposerProfile(BaseModel):
    """Structured data for a composer profile."""
    name: str = Field(description="Full name of the composer")
    era: str = Field(description="Musical era (e.g., Baroque, Classical, Romantic)")
    nationality: str = Field(description="Country of origin")
    notable_works: List[str] = Field(description="List of famous compositions")
    life_dates: Optional[str] = Field(description="Birth and death years (e.g., 1685-1750)")
    description: Optional[str] = Field(description="Brief biography or style description")

class Recommendation(BaseModel):
    """A single music recommendation."""
    piece: str = Field(description="Title of the piece")
    composer: str = Field(description="Composer of the piece")
    reason: str = Field(description="Why this was recommended")
    youtube_search_query: str = Field(description="Optimized search query for finding a recording")

class RecommendationList(BaseModel):
    """List of recommendations."""
    recommendations: List[Recommendation]

class SheetMusicSample(BaseModel):
    """Structured output for sheet music sample."""
    title: str = Field(description="Title of the piece")
    composer: str = Field(description="Composer name")
    key_signature: str = Field(description="Key of the excerpt (e.g., C Major, G Minor)")
    time_signature: str = Field(description="Time signature (e.g., 4/4, 3/4)")
    abc_notation: str = Field(description="Valid ABC notation string representing the main theme. Ensure headers like X:1, T:, M:, K: are present.")
    analysis: str = Field(description="Brief theoretical analysis of the excerpt")
    imslp_link: Optional[str] = Field(description="Search URL for IMSLP")

class ClassicalMusicLecture(BaseModel):
    """Structured output for a classical music lecture."""
    topic: str = Field(description="The main topic or composer being discussed")
    summary: str = Field(description="A concise summary of the lecture")
    key_points: List[str] = Field(description="Key historical or theoretical points")
    recommended_listening: List[str] = Field(description="List of specific pieces to listen to")
    fun_fact: str = Field(description="An interesting or obscure fact related to the topic")

# --- Local Data ---

COMPOSER_INDEX = {
    "bach": {
        "name": "Johann Sebastian Bach",
        "era": "Baroque",
        "nationality": "German",
        "notable_works": [
            "Brandenburg Concertos",
            "Mass in B minor",
            "The Well-Tempered Clavier",
        ],
    },
    "mozart": {
        "name": "Wolfgang Amadeus Mozart",
        "era": "Classical",
        "nationality": "Austrian",
        "notable_works": [
            "The Magic Flute",
            "Requiem",
            "Symphony No. 41 (Jupiter)",
        ],
    },
    "beethoven": {
        "name": "Ludwig van Beethoven",
        "era": "Classical/Romantic",
        "nationality": "German",
        "notable_works": [
            "Symphony No. 5",
            "Symphony No. 9",
            "Piano Sonata No. 14 (Moonlight)",
        ],
    },
    "tchaikovsky": {
        "name": "Pyotr Ilyich Tchaikovsky",
        "era": "Romantic",
        "nationality": "Russian",
        "notable_works": [
            "Swan Lake",
            "The Nutcracker",
            "Symphony No. 6 (Pathétique)",
        ],
    },
    "debussy": {
        "name": "Claude Debussy",
        "era": "Impressionist",
        "nationality": "French",
        "notable_works": [
            "Prélude à l'après-midi d'un faune",
            "La mer",
            "Clair de lune",
        ],
    },
    "piazzolla": {
        "name": "Astor Piazzolla",
        "era": "20th century",
        "nationality": "Argentine",
        "notable_works": [
            "Adiós Nonino",
            "Libertango",
            "Las cuatro estaciones porteñas",
        ],
    },
}

# --- Reasoners ---

@reasoners_router.reasoner()
async def echo(message: str) -> dict:
    """
    Simple echo reasoner - works without AI configured.
    """
    return {
        "original": message,
        "echoed": message,
        "length": len(message)
    }

@reasoners_router.reasoner()
async def get_composer_info(name: str) -> dict:
    """
    Hybrid composer lookup. Checks local database first, then falls back to AI.
    """
    key = name.strip().lower()
    
    # 1. Local Lookup
    if key in COMPOSER_INDEX:
        profile_data = COMPOSER_INDEX[key]
        # Return in a format matching the AI schema for consistency
        # Adding defaults for fields not in local index
        return ComposerProfile(
            name=profile_data["name"],
            era=profile_data["era"],
            nationality=profile_data["nationality"],
            notable_works=profile_data["notable_works"],
            life_dates=None,
            description="Profile retrieved from local database."
        ).model_dump()
    
    # 2. AI Fallback
    system_prompt = "You are a classical music encyclopedia. Provide a structured profile for the requested composer."
    result = await reasoners_router.app.ai(
        system=system_prompt,
        user=f"Profile for composer: {name}",
        schema=ComposerProfile
    )
    return result.model_dump()

@reasoners_router.reasoner()
async def recommend_music(mood: str, similar_to: Optional[str] = None, difficulty: Optional[str] = None) -> dict:
    """
    Suggests classical music based on mood or similarity.
    """
    system_prompt = (
        "You are a music curator. Recommend 3-5 classical pieces based on the user's criteria. "
        "Include a mix of well-known and hidden gems."
    )
    
    user_prompt = f"I feel {mood}."
    if similar_to:
        user_prompt += f" I like {similar_to}."
    if difficulty:
        user_prompt += f" I am a {difficulty} listener."

    result = await reasoners_router.app.ai(
        system=system_prompt,
        user=user_prompt,
        schema=RecommendationList
    )
    return result.model_dump()

@reasoners_router.reasoner()
async def get_sheet_sample(piece: str) -> dict:
    """
    Generates a sheet music sample in ABC notation.
    """
    system_prompt = (
        "You are a music theorist. Provide a short, accurate excerpt of the main theme "
        "of the requested piece in valid ABC notation format. "
        "Also analyze the excerpt briefly."
    )
    
    result = await reasoners_router.app.ai(
        system=system_prompt,
        user=f"Please provide the main theme for: {piece}",
        schema=SheetMusicSample
    )
    
    # Post-process: Add IMSLP link if not generated correctly or just ensure it's robust
    if not result.imslp_link or "imslp.org" not in result.imslp_link:
        safe_query = piece.replace(" ", "+")
        result.imslp_link = f"https://imslp.org/wiki/Special:Search?search={safe_query}"
        
    return result.model_dump()

@reasoners_router.reasoner()
async def lecture(topic: str) -> dict:
    """
    AI-powered classical music expert that provides lectures and knowledge.
    """
    
    # Define the persona and instructions for the AI
    system_prompt = (
        "You are a world-renowned professor of musicology and a classical music expert. "
        "Your goal is to educate users about classical music history, theory, and appreciation. "
        "Provide accurate, insightful, and engaging lectures. "
        "When recommending listening, be specific about the work and, if applicable, the movement."
    )

    # Access AI directly through the router's app instance
    result = await reasoners_router.app.ai(
        system=system_prompt,
        user=f"Please provide a lecture on the following topic: {topic}",
        schema=ClassicalMusicLecture
    )

    # Add a note for observability in the AgentField dashboard
    reasoners_router.app.note(
        f"Delivered lecture on: {result.topic}",
        tags=["music", "lecture", "classical"]
    )

    return result.model_dump()