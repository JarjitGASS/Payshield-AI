import { useState } from "react";
import GoToHomePage from "../component/goToHomePage.component";

interface IdentityData {
  ktp_match_score: number;
  face_similarity_score: number;
  email_age_days: number;
  geo_ip_mismatch: boolean;
  name_has_digits_or_symbols: boolean;
  name_entropy: number;
  name_ngram_entropy: number;
  entity_sentiment_score: number;
}

interface BehavioralData {
  typing_cadence_variance: number;
  mouse_entropy_score: number;
  session_duration_sec: number;
  login_hour: number;
  navigation_consistency_score: number;
}

interface NetworkData {
  shared_device_count: number;
  shared_ip_count: number;
}

interface AssessmentResult {
  user_id: string;
  session_state: {
    session_id: string;
    user_id: string;
    current_step: string;
    flags: string[];
  };
  final_decision: string;
  meta_result: {
    decision: string;
    overall_risk: number;
    confidence: number;
    recommendation: string;
  };
}

// Generate synthetic identity data
function generateSyntheticIdentity(): IdentityData {
  return {
    ktp_match_score: 0.85 + Math.random() * 0.15, // 0.85-1.0
    face_similarity_score: 0.78 + Math.random() * 0.22, // 0.78-1.0
    email_age_days: Math.floor(Math.random() * 1500) + 30, // 30-1530 days
    geo_ip_mismatch: Math.random() > 0.7, // 30% chance of mismatch
    name_has_digits_or_symbols: Math.random() > 0.85, // 15% chance
    name_entropy: 3.5 + Math.random() * 1.5, // 3.5-5.0
    name_ngram_entropy: 2.8 + Math.random() * 1.2, // 2.8-4.0
    entity_sentiment_score: 0.6 + Math.random() * 0.4, // 0.6-1.0 (positive sentiment)
  };
}

// Generate synthetic behavioral data
function generateSyntheticBehavioral(): BehavioralData {
  return {
    typing_cadence_variance: 0.1 + Math.random() * 0.3, // 0.1-0.4
    mouse_entropy_score: 0.4 + Math.random() * 0.5, // 0.4-0.9
    session_duration_sec: Math.floor(Math.random() * 2400) + 300, // 5-45 minutes
    login_hour: Math.floor(Math.random() * 24), // 0-23
    navigation_consistency_score: 0.5 + Math.random() * 0.5, // 0.5-1.0
  };
}

// Generate synthetic network data
function generateSyntheticNetwork(): NetworkData {
  return {
    shared_device_count: Math.floor(Math.random() * 5), // 0-4
    shared_ip_count: Math.floor(Math.random() * 8), // 0-7
  };
}

export default function AgenticRiskAssessmentPage() {
  const [identityData, setIdentityData] = useState<IdentityData>(generateSyntheticIdentity());
  const [behavioralData, setBehavioralData] = useState<BehavioralData>(generateSyntheticBehavioral());
  const [networkData, setNetworkData] = useState<NetworkData>(generateSyntheticNetwork());
  const [userId, setUserId] = useState("user_" + Math.random().toString(36).substring(7));
  const [result, setResult] = useState<AssessmentResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");

  // Human review state
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [reviewRating, setReviewRating] = useState<"GOOD" | "BAD">("GOOD");
  const [overrideDecision, setOverrideDecision] = useState<"APPROVE" | "REJECT">("APPROVE");
  const [reviewNote, setReviewNote] = useState("");
  const [reviewLoading, setReviewLoading] = useState(false);
  const [reviewMessage, setReviewMessage] = useState<{ text: string; error: boolean } | null>(null);

  const handleGenerateNewData = () => {
    setIdentityData(generateSyntheticIdentity());
    setBehavioralData(generateSyntheticBehavioral());
    setNetworkData(generateSyntheticNetwork());
    setResult(null);
    setError("");
    setReviewMessage(null);
  };

  const handleAssessment = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setReviewMessage(null);

    try {
      const payload = {
        user_id: userId,
        identity: identityData,
        behavioral: behavioralData,
        network: networkData,
      };

      const response = await fetch("http://localhost:8000/agentic-risk-assessment", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.detail || "Failed to perform risk assessment");
      } else {
        setResult(data);
        setShowReviewForm(false);
        setReviewNote("");
      }
    } catch (err) {
      setError(`Error: ${err}`);
    } finally {
      setLoading(false);
    }
  };

  const handleHumanReview = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!result) {
      setReviewMessage({ text: "No assessment result to review", error: true });
      return;
    }

    if (reviewRating === "BAD" && !overrideDecision) {
      setReviewMessage({ text: "Override decision is required when rating is BAD", error: true });
      return;
    }

    if (reviewNote.length < 5) {
      setReviewMessage({ text: "Note must be at least 5 characters", error: true });
      return;
    }

    setReviewLoading(true);

    try {
      const payload = {
        session_id: result.session_state.session_id,
        rating: reviewRating,
        override_decision: reviewRating === "BAD" ? overrideDecision : undefined,
        note: reviewNote,
      };

      const response = await fetch("http://localhost:8000/human-review", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (!response.ok) {
        setReviewMessage({ text: data.detail || "Failed to submit review", error: true });
      } else {
        setReviewMessage({
          text: `Review submitted successfully! ${data.message}`,
          error: false,
        });
        setReviewNote("");
        setShowReviewForm(false);
      }
    } catch (err) {
      setReviewMessage({ text: `Error: ${err}`, error: true });
    } finally {
      setReviewLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-screen bg-gray-50">
      <GoToHomePage />
      
      <div className="max-w-7xl mx-auto p-6">
        <h1 className="text-4xl font-bold text-gray-800 mb-2">Agentic Risk Assessment</h1>
        <p className="text-gray-600 mb-8">
          Comprehensive fraud detection using identity, behavioral, and network analysis
        </p>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Input Data */}
          <div className="lg:col-span-1 space-y-6">
            {/* User ID */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-lg font-bold text-gray-800 mb-4">Test Parameters</h2>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-semibold text-gray-600 mb-1">User ID</label>
                  <input
                    type="text"
                    value={userId}
                    onChange={(e) => setUserId(e.target.value)}
                    className="w-full p-2 border rounded text-black"
                  />
                </div>
                <button
                  onClick={handleGenerateNewData}
                  className="w-full bg-green-600 hover:bg-green-700 text-white py-2 rounded font-medium transition"
                >
                  Generate New Data
                </button>
              </div>
            </div>

            {/* Identity Data */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="font-bold text-gray-800 mb-3">Identity Data</h3>
              <div className="space-y-2 text-sm">
                <div>
                  <label className="text-gray-600">KTP Match Score</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="1"
                    value={identityData.ktp_match_score}
                    onChange={(e) =>
                      setIdentityData({ ...identityData, ktp_match_score: parseFloat(e.target.value) })
                    }
                    className="w-full p-1 border rounded text-black text-xs"
                  />
                  <p className="text-xs text-gray-500 mt-1">{(identityData.ktp_match_score * 100).toFixed(1)}%</p>
                </div>
                <div>
                  <label className="text-gray-600">Face Similarity Score</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="1"
                    value={identityData.face_similarity_score}
                    onChange={(e) =>
                      setIdentityData({ ...identityData, face_similarity_score: parseFloat(e.target.value) })
                    }
                    className="w-full p-1 border rounded text-black text-xs"
                  />
                  <p className="text-xs text-gray-500 mt-1">{(identityData.face_similarity_score * 100).toFixed(1)}%</p>
                </div>
                <div>
                  <label className="text-gray-600">Email Age (days)</label>
                  <input
                    type="number"
                    value={identityData.email_age_days}
                    onChange={(e) =>
                      setIdentityData({ ...identityData, email_age_days: parseInt(e.target.value) })
                    }
                    className="w-full p-1 border rounded text-black text-xs"
                  />
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={identityData.geo_ip_mismatch}
                    onChange={(e) =>
                      setIdentityData({ ...identityData, geo_ip_mismatch: e.target.checked })
                    }
                    className="rounded"
                  />
                  <label className="text-gray-600 text-xs">Geo IP Mismatch</label>
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={identityData.name_has_digits_or_symbols}
                    onChange={(e) =>
                      setIdentityData({ ...identityData, name_has_digits_or_symbols: e.target.checked })
                    }
                    className="rounded"
                  />
                  <label className="text-gray-600 text-xs">Name Has Digits/Symbols</label>
                </div>
                <div>
                  <label className="text-gray-600">Name Entropy</label>
                  <input
                    type="number"
                    step="0.01"
                    value={identityData.name_entropy}
                    onChange={(e) =>
                      setIdentityData({ ...identityData, name_entropy: parseFloat(e.target.value) })
                    }
                    className="w-full p-1 border rounded text-black text-xs"
                  />
                </div>
                <div>
                  <label className="text-gray-600">Entity Sentiment Score</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="1"
                    value={identityData.entity_sentiment_score}
                    onChange={(e) =>
                      setIdentityData({ ...identityData, entity_sentiment_score: parseFloat(e.target.value) })
                    }
                    className="w-full p-1 border rounded text-black text-xs"
                  />
                </div>
              </div>
            </div>

            {/* Behavioral Data */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="font-bold text-gray-800 mb-3">Behavioral Data</h3>
              <div className="space-y-2 text-sm">
                <div>
                  <label className="text-gray-600">Typing Cadence Variance</label>
                  <input
                    type="number"
                    step="0.01"
                    value={behavioralData.typing_cadence_variance}
                    onChange={(e) =>
                      setBehavioralData({ ...behavioralData, typing_cadence_variance: parseFloat(e.target.value) })
                    }
                    className="w-full p-1 border rounded text-black text-xs"
                  />
                </div>
                <div>
                  <label className="text-gray-600">Mouse Entropy Score</label>
                  <input
                    type="number"
                    step="0.01"
                    value={behavioralData.mouse_entropy_score}
                    onChange={(e) =>
                      setBehavioralData({ ...behavioralData, mouse_entropy_score: parseFloat(e.target.value) })
                    }
                    className="w-full p-1 border rounded text-black text-xs"
                  />
                </div>
                <div>
                  <label className="text-gray-600">Session Duration (sec)</label>
                  <input
                    type="number"
                    value={behavioralData.session_duration_sec}
                    onChange={(e) =>
                      setBehavioralData({ ...behavioralData, session_duration_sec: parseInt(e.target.value) })
                    }
                    className="w-full p-1 border rounded text-black text-xs"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    {(behavioralData.session_duration_sec / 60).toFixed(1)} minutes
                  </p>
                </div>
                <div>
                  <label className="text-gray-600">Login Hour</label>
                  <input
                    type="number"
                    min="0"
                    max="23"
                    value={behavioralData.login_hour}
                    onChange={(e) =>
                      setBehavioralData({ ...behavioralData, login_hour: parseInt(e.target.value) })
                    }
                    className="w-full p-1 border rounded text-black text-xs"
                  />
                </div>
                <div>
                  <label className="text-gray-600">Navigation Consistency</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="1"
                    value={behavioralData.navigation_consistency_score}
                    onChange={(e) =>
                      setBehavioralData({ ...behavioralData, navigation_consistency_score: parseFloat(e.target.value) })
                    }
                    className="w-full p-1 border rounded text-black text-xs"
                  />
                </div>
              </div>
            </div>

            {/* Network Data */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="font-bold text-gray-800 mb-3">Network Data</h3>
              <div className="space-y-2 text-sm">
                <div>
                  <label className="text-gray-600">Shared Device Count</label>
                  <input
                    type="number"
                    min="0"
                    value={networkData.shared_device_count}
                    onChange={(e) =>
                      setNetworkData({ ...networkData, shared_device_count: parseInt(e.target.value) })
                    }
                    className="w-full p-1 border rounded text-black text-xs"
                  />
                </div>
                <div>
                  <label className="text-gray-600">Shared IP Count</label>
                  <input
                    type="number"
                    min="0"
                    value={networkData.shared_ip_count}
                    onChange={(e) =>
                      setNetworkData({ ...networkData, shared_ip_count: parseInt(e.target.value) })
                    }
                    className="w-full p-1 border rounded text-black text-xs"
                  />
                </div>
              </div>
            </div>

            {/* Submit Button */}
            <button
              onClick={handleAssessment}
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white py-3 rounded-lg font-bold transition"
            >
              {loading ? "Assessing..." : "Run Risk Assessment"}
            </button>

            {error && (
              <div className="bg-red-50 border border-red-200 p-4 rounded text-red-700 text-sm">
                {error}
              </div>
            )}
          </div>

          {/* Right Column - Results and Review */}
          <div className="lg:col-span-2">
            {result && (
              <div className="space-y-6">
                {/* Assessment Results */}
                <div className="bg-white p-6 rounded-lg shadow">
                  <h2 className="text-2xl font-bold text-gray-800 mb-4">Assessment Results</h2>

                  {/* Decision Box */}
                  <div
                    className={`p-6 rounded-lg mb-6 ${
                      result.final_decision === "APPROVE"
                        ? "bg-green-50 border-2 border-green-500"
                        : result.final_decision === "REJECT"
                        ? "bg-red-50 border-2 border-red-500"
                        : "bg-yellow-50 border-2 border-yellow-500"
                    }`}
                  >
                    <p className="text-lg font-bold mb-3">
                      {result.final_decision === "APPROVE" && "✓ APPROVED"}
                      {result.final_decision === "REJECT" && "✗ REJECTED"}
                      {result.final_decision === "REVIEW" && "⏳ REQUIRES REVIEW"}
                    </p>
                    <div className="space-y-2 text-sm">
                      <p>
                        <strong>Risk Score:</strong>{" "}
                        {(result.meta_result.overall_risk * 100).toFixed(1)}%
                      </p>
                      <p>
                        <strong>Confidence:</strong>{" "}
                        {(result.meta_result.confidence * 100).toFixed(1)}%
                      </p>
                      <p className="mt-2">
                        <strong>Recommendation:</strong> {result.meta_result.recommendation}
                      </p>
                    </div>
                  </div>

                  {/* Session Info */}
                  <div className="grid grid-cols-2 gap-4 mb-6">
                    <div className="bg-gray-50 p-4 rounded">
                      <p className="text-xs text-gray-600">Session ID</p>
                      <p className="text-sm font-mono break-all">
                        {result.session_state.session_id}
                      </p>
                    </div>
                    <div className="bg-gray-50 p-4 rounded">
                      <p className="text-xs text-gray-600">User ID</p>
                      <p className="text-sm font-mono">{result.user_id}</p>
                    </div>
                  </div>

                  {/* Flags */}
                  {result.session_state.flags.length > 0 && (
                    <div className="mb-6">
                      <p className="font-semibold text-gray-800 mb-2">Triggered Flags:</p>
                      <div className="flex flex-wrap gap-2">
                        {result.session_state.flags.map((flag, idx) => (
                          <span key={idx} className="bg-orange-100 text-orange-700 px-3 py-1 rounded-full text-sm font-medium">
                            {flag}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Full Result JSON */}
                  <details className="cursor-pointer">
                    <summary className="font-semibold text-gray-700 hover:text-gray-900">
                      View Full Response
                    </summary>
                    <pre className="mt-3 bg-gray-100 p-4 rounded text-xs overflow-x-auto">
                      {JSON.stringify(result, null, 2)}
                    </pre>
                  </details>
                </div>

                {/* Human Review Form */}
                {result.final_decision === "REVIEW" && (
                  <div className="bg-yellow-50 border-2 border-yellow-500 p-6 rounded-lg">
                    <h3 className="text-xl font-bold text-gray-800 mb-4">This session requires human review</h3>
                    <button
                      onClick={() => setShowReviewForm(!showReviewForm)}
                      className="bg-yellow-600 hover:bg-yellow-700 text-white py-2 px-6 rounded font-medium transition"
                    >
                      {showReviewForm ? "Hide Review Form" : "Submit Human Review"}
                    </button>
                  </div>
                )}

                {/* Always show review form for testing */}
                {showReviewForm && (
                <div className="bg-white p-6 rounded-lg shadow">
                  <h3 className="text-xl font-bold text-gray-800 mb-4">
                    Submit Analyst Review
                  </h3>
                  <form onSubmit={handleHumanReview} className="space-y-4">
                    <div>
                      <label className="block text-sm font-semibold text-gray-600 mb-2">
                        Rating
                      </label>
                      <div className="flex gap-4">
                        <label className="flex items-center gap-2">
                          <input
                            type="radio"
                            name="rating"
                            value="GOOD"
                            checked={reviewRating === "GOOD"}
                            onChange={(e) => setReviewRating(e.target.value as "GOOD" | "BAD")}
                            className="rounded"
                          />
                          <span className="text-gray-700">✓ GOOD (AI decision correct)</span>
                        </label>
                        <label className="flex items-center gap-2">
                          <input
                            type="radio"
                            name="rating"
                            value="BAD"
                            checked={reviewRating === "BAD"}
                            onChange={(e) => setReviewRating(e.target.value as "GOOD" | "BAD")}
                            className="rounded"
                          />
                          <span className="text-gray-700">✗ BAD (AI decision wrong)</span>
                        </label>
                      </div>
                    </div>

                    {reviewRating === "BAD" && (
                      <div>
                        <label className="block text-sm font-semibold text-gray-600 mb-2">
                          Override Decision
                        </label>
                        <div className="flex gap-4">
                          <label className="flex items-center gap-2">
                            <input
                              type="radio"
                              name="override"
                              value="APPROVE"
                              checked={overrideDecision === "APPROVE"}
                              onChange={(e) => setOverrideDecision(e.target.value as "APPROVE" | "REJECT")}
                              className="rounded"
                            />
                            <span className="text-gray-700">APPROVE</span>
                          </label>
                          <label className="flex items-center gap-2">
                            <input
                              type="radio"
                              name="override"
                              value="REJECT"
                              checked={overrideDecision === "REJECT"}
                              onChange={(e) => setOverrideDecision(e.target.value as "APPROVE" | "REJECT")}
                              className="rounded"
                            />
                            <span className="text-gray-700">REJECT</span>
                          </label>
                        </div>
                      </div>
                    )}

                    <div>
                      <label className="block text-sm font-semibold text-gray-600 mb-2">
                        Analyst Note (5-2000 characters)
                      </label>
                      <textarea
                        value={reviewNote}
                        onChange={(e) => setReviewNote(e.target.value)}
                        placeholder="Explain your reasoning for this review..."
                        className="w-full p-3 border rounded text-black h-24 resize-none"
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        {reviewNote.length}/2000 characters
                      </p>
                    </div>

                    <button
                      type="submit"
                      disabled={reviewLoading}
                      className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white py-2 rounded font-bold transition"
                    >
                      {reviewLoading ? "Submitting..." : "Submit Review"}
                    </button>
                  </form>

                  {reviewMessage && (
                    <div
                      className={`mt-4 p-4 rounded ${
                        reviewMessage.error
                          ? "bg-red-50 border border-red-200 text-red-700"
                          : "bg-green-50 border border-green-200 text-green-700"
                      }`}
                    >
                      {reviewMessage.text}
                    </div>
                  )}
                  </div>
                )}

              </div>
            )}

            {!result && !loading && (
              <div className="bg-white p-12 rounded-lg shadow text-center">
                <p className="text-gray-500 text-lg">
                  Run an assessment to see results and submit human reviews
                </p>
              </div>
            )}

            {loading && (
              <div className="bg-white p-12 rounded-lg shadow text-center">
                <p className="text-gray-500 text-lg animate-pulse">
                  Running risk assessment...
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
