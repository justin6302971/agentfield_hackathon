from agentfield import AgentRouter
from pydantic import BaseModel, Field
from typing import List, Optional
import wikipedia
from youtubesearchpython import VideosSearch

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
    image_url: Optional[str] = Field(description="URL to an image of the composer")

class Recommendation(BaseModel):
    """A single music recommendation."""
    piece: str = Field(description="Title of the piece")
    composer: str = Field(description="Composer of the piece")
    reason: str = Field(description="Why this was recommended")
    youtube_search_query: str = Field(description="Optimized search query for finding a recording")
    video_url: Optional[str] = Field(description="YouTube video URL (populated by skill)")

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
    related_composers: List[str] = Field(description="List of key composers associated with this topic")
    recommended_listening: List[str] = Field(description="List of specific pieces to listen to")
    fun_fact: str = Field(description="An interesting or obscure fact related to the topic")

class WikiResult(BaseModel):
    """Structured result from Wikipedia search."""
    title: str = Field(description="Page title")
    summary: str = Field(description="Page summary")
    url: str = Field(description="Page URL")
    error: Optional[str] = Field(description="Error message if search failed")

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

# --- Skills ---

@reasoners_router.skill()
def search_wikipedia(query: str) -> dict:
    """
    Searches Wikipedia for a topic and returns a structured result.
    This is a deterministic skill that fetches external data.
    """
    try:
        results = wikipedia.search(query)
        if not results:
            return {"error": f"No results found for {query}"}
        
        # Fetch the page (blocking call, but acceptable for this skill)
        page = wikipedia.page(results[0], auto_suggest=False)
        return {
            "title": page.title,
            "summary": page.summary,
            "url": page.url
        }
    except wikipedia.exceptions.DisambiguationError as e:
        return {"error": f"Ambiguous search. Options: {e.options[:5]}"}
    except wikipedia.exceptions.PageError:
        return {"error": "Page not found."}
    except Exception as e:
        return {"error": str(e)}

@reasoners_router.skill()
def search_video(query: str, limit: int = 1) -> dict:
    """
    Searches for a video on YouTube using the provided query.
    Returns the video URL and title of the top result.
    """
    try:
        videos_search = VideosSearch(query, limit=limit)
        results = videos_search.result()
        
        if not results or not results.get("result"):
            reasoners_router.app.note(
                f"Video search failed for query: {query}",
                tags=["video-search", "failed"]
            )
            return {"error": f"No videos found for: {query}"}
            
        top_result = results["result"][0]
        
        # Log successful search for observation
        reasoners_router.app.note(
            f"Video found: {top_result.get('title')} ({top_result.get('link')})",
            tags=["video-search", "success"]
        )
        
        return {
            "title": top_result.get("title"),
            "link": top_result.get("link"),
            "duration": top_result.get("duration"),
            "channel": top_result.get("channel", {}).get("name")
        }
    except Exception as e:
        reasoners_router.app.note(
            f"Video search error: {str(e)}",
            tags=["video-search", "error"]
        )
        return {"error": str(e)}

@reasoners_router.skill()
def get_artist_image(artist_name: str) -> dict:
    """
    Fetches the main image URL for an artist or composer from Wikipedia.
    """
    try:
        # Search for the page
        results = wikipedia.search(artist_name)
        if not results:
            return {"error": f"No Wikipedia page found for {artist_name}"}
        
        # Get the page
        page = wikipedia.page(results[0], auto_suggest=False)
        
        # Get images
        images = page.images
        if not images:
             return {"error": "No images found on Wikipedia page."}
        
        # Simple heuristic: prefer .jpg or .png, filter out svg icons if possible
        # Wikipedia images often include icons, maps, etc.
        # We'll take the first one that looks like a photo
        valid_extensions = (".jpg", ".jpeg", ".png")
        best_image = None
        
        for img_url in images:
            if img_url.lower().endswith(valid_extensions):
                # Wikipedia often puts the main portrait first or second in the list logic, 
                # but technically 'images' is a set or list with no guaranteed order in some versions.
                # However, usually the main image is prominent. 
                # Let's just take the first valid image for now.
                best_image = img_url
                break
        
        if not best_image and images:
             best_image = images[0] # Fallback
             
        return {"image_url": best_image, "source": page.url}

    except Exception as e:
        return {"error": str(e)}

# --- Reasoners ---
@reasoners_router.reasoner()
async def get_composer_info(name: str) -> dict:
    """
    Hybrid composer lookup. Checks local database first, then Wikipedia, then falls back to AI.
    """
    key = name.strip().lower()
    
    # 1. Local Lookup
    if key in COMPOSER_INDEX:
        profile_data = COMPOSER_INDEX[key]
        return ComposerProfile(
            name=profile_data["name"],
            era=profile_data["era"],
            nationality=profile_data["nationality"],
            notable_works=profile_data["notable_works"],
            life_dates=None,
            description="Profile retrieved from local database."
        ).model_dump()
    
    # 2. Wikipedia Lookup via Skill
    # We call the skill function directly. The router/agent framework ensures 
    # this call is tracked if configured.
    wiki_data = search_wikipedia(name)
    
    # Also fetch image
    image_data = get_artist_image(name)
    image_url = image_data.get("image_url")
    
    wiki_context = ""
    if "error" not in wiki_data:
        wiki_context = f"Wikipedia Summary for {wiki_data.get('title')}: {wiki_data.get('summary')}"
    
    # 3. AI Generation
    system_prompt = "You are a classical music encyclopedia. Provide a structured profile for the requested composer."
    user_prompt = f"Profile for composer: {name}"
    if wiki_context:
        user_prompt += f"\n\nContext from Wikipedia:\n{wiki_context}"

    result = await reasoners_router.app.ai(
        system=system_prompt,
        user=user_prompt,
        schema=ComposerProfile
    )
    
    # Inject the image URL if found
    if image_url:
        result.image_url = image_url
        
    return result.model_dump()

@reasoners_router.reasoner()
async def recommend_music(mood: Optional[str] = None, similar_to: Optional[str] = None, difficulty: Optional[str] = None) -> dict:
    """
    Suggests classical music based on mood or similarity, and finds video links for them.
    """
    system_prompt = (
        "You are a music curator. Recommend 3-5 classical pieces based on the user's criteria. "
        "Include a mix of well-known and hidden gems."
    )
    
    user_prompt = ""
    if mood:
        user_prompt += f"I feel {mood}. "
    if similar_to:
        user_prompt += f"I like {similar_to}. "
    if difficulty:
        user_prompt += f"I am a {difficulty} listener. "
    
    if not user_prompt:
        user_prompt = "Recommend me some great classical music."

    # 1. Get Recommendations from AI
    result = await reasoners_router.app.ai(
        system=system_prompt,
        user=user_prompt,
        schema=RecommendationList
    )
    
    # 2. Enrich with Video Links
    enriched_recommendations = []
    for rec in result.recommendations:
        # Call the search_video skill for each recommendation
        # We use the generated search query
        video_info = search_video(rec.youtube_search_query)
        
        if "link" in video_info:
            rec.video_url = video_info["link"]
        
        enriched_recommendations.append(rec)
    
    result.recommendations = enriched_recommendations
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
        "Identify key composers associated with the topic. "
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
