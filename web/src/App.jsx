import { useState } from 'react'
import axios from 'axios'
import './App.css'

function App() {
  const [topic, setTopic] = useState("The Romantic Era")
  const [lectureData, setLectureData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const [selectedComposer, setSelectedComposer] = useState(null)
  const [composerData, setComposerData] = useState(null)
  
  const [recommendations, setRecommendations] = useState(null)

  // Step 1: Get Lecture
  const fetchLecture = async () => {
    setLoading(true);
    setError(null);
    setLectureData(null);
    setComposerData(null);
    setRecommendations(null);
    setSelectedComposer(null);

    try {
      const response = await axios.post('/api/v1/execute/my-agent.music_lecture', {
        input: { topic: topic }
      });
      setLectureData(response.data.result);
    } catch (err) {
      setError("Failed to fetch lecture. Is the agent running?");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Get Composer Info
  const fetchComposerInfo = async (composerName) => {
    setLoading(true);
    setError(null);
    setSelectedComposer(composerName);
    setComposerData(null);
    setRecommendations(null);

    try {
      const response = await axios.post('/api/v1/execute/my-agent.music_get_composer_info', {
        input: { name: composerName }
      });
      setComposerData(response.data.result);
    } catch (err) {
      setError(`Failed to fetch info for ${composerName}`);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Step 3: Get Recommendations
  const fetchRecommendations = async (composerName) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post('/api/v1/execute/my-agent.music_recommend_music', {
        input: { similar_to: composerName }
      });
      setRecommendations(response.data.result);
    } catch (err) {
      setError("Failed to fetch recommendations");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <h1>Classical Music Explorer</h1>
      
      {/* Step 1: Topic Selection */}
      <div className="card">
        <h2>1. Start with a Topic</h2>
        <div className="input-group">
          <input 
            type="text" 
            value={topic} 
            onChange={(e) => setTopic(e.target.value)} 
            placeholder="e.g., Baroque, Beethoven, Opera"
          />
          <button onClick={fetchLecture} disabled={loading}>
            {loading ? 'Thinking...' : 'Get Lecture'}
          </button>
        </div>
        {error && <p className="error">{error}</p>}
      </div>

      {/* Lecture Results */}
      {lectureData && (
        <div className="card result-card">
          <h3>Lecture: {lectureData.topic}</h3>
          <p className="summary">{lectureData.summary}</p>
          
          <div className="composers-list">
            <h4>Related Composers (Click to explore):</h4>
            <div className="tags">
              {lectureData.related_composers?.map((composer, index) => (
                <button 
                  key={index} 
                  className={`tag ${selectedComposer === composer ? 'active' : ''}`}
                  onClick={() => fetchComposerInfo(composer)}
                >
                  {composer}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Step 2: Composer Detail */}
      {composerData && (
        <div className="card result-card fade-in">
          <div className="composer-header">
            {composerData.image_url && (
              <img src={composerData.image_url} alt={composerData.name} className="composer-img" />
            )}
            <div>
              <h2>{composerData.name}</h2>
              <p className="subtitle">{composerData.era} | {composerData.nationality}</p>
              {composerData.life_dates && <p className="dates">{composerData.life_dates}</p>}
            </div>
          </div>
          
          <p className="description">{composerData.description}</p>
          
          <div className="actions">
            <button 
              className="primary-btn"
              onClick={() => fetchRecommendations(composerData.name)}
            >
              Get Music Recommendations for {composerData.name}
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Recommendations */}
      {recommendations && (
        <div className="card result-card fade-in">
          <h3>Recommended Listening</h3>
          <div className="recommendations-grid">
            {recommendations.recommendations?.map((rec, index) => (
              <div key={index} className="rec-item">
                <h4>{rec.piece}</h4>
                <p><strong>Composer:</strong> {rec.composer}</p>
                <p className="reason">{rec.reason}</p>
                {rec.video_url && (
                  <a href={rec.video_url} target="_blank" rel="noreferrer" className="video-link">
                    Watch on YouTube
                  </a>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default App