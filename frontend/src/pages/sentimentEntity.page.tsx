import { useState } from "react";
import GoToHomePage from "../component/goToHomePage.component";

export default function SentimentEntityPage() {
  const [company, setCompany] = useState<string>("");
  const [message, setMessage] = useState<string>("");
  const [error, setError] = useState<string>("");

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    setCompany(e.target.value);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    try {
      const response = await fetch("http://localhost:8000/sentiment-entity-analysis", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: `company_name=${encodeURIComponent(company)}`,
      });

      if (!response.ok) {
        const errorData = await response.json();
        setMessage("");
        setError(errorData.detail || "Failed to analyze company. Please try again.");
        return;
      }
      const data = await response.json();
      console.log(data);
      setMessage("Analysis result:" + JSON.stringify(data).replaceAll(",", ",\n"));
      setError("");
    } catch (error) {
      console.error("Error analyzing company:", error);
      setMessage("");
      setError("Failed to analyze company. Please try again later.");
    }
  }

  return (
    <div className="min-h-screen w-screen flex items-center justify-center bg-gray-100 p-6">
      <div className="bg-white p-8 rounded-2xl shadow-xl w-full max-w-md">
        <GoToHomePage />
        <h1 className="text-3xl font-bold text-center text-gray-800 mb-8">
          Sentiment Entity Analysis
        </h1>
        <form action="" className="space-y-5">
          <div className="flex flex-col">
            <label className="text-sm font-semibold text-gray-600 mb-1">
              Company Name *
            </label>
            <input
              name="company_name"
              type="text"
              required
              className="p-2 border rounded-lg text-black focus:ring-2 focus:ring-blue-500 outline-none"
              placeholder="ftx"
              onChange={handleChange}
              value={company}
            />
          </div>
          <button
            type="button"
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-lg transition-all"
            onClick={handleSubmit}
          >
            Continue
          </button>
          {message && <p className="text-green-600 text-center mt-4">{message}</p>}
          {error && <p className="text-red-600 text-center mt-4">{error}</p>}
        </form>
      </div>
    </div>
  );
}
