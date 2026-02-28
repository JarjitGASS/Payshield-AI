import { useState } from "react";
import GoToHomePage from "../component/goToHomePage.component";

export default function GeoIpPage() {
  // component for Geo IP verification
  const [declaredCountry, setDeclaredCountry] = useState<string>("");
  const [declaredCity, setDeclaredCity] = useState<string>("");
  const [message, setMessage] = useState<string>("");
  const [error, setError] = useState<string>("");

  function handleCountryChange(e: React.ChangeEvent<HTMLInputElement>) {
    setDeclaredCountry(e.target.value);
  }

  function handleCityChange(e: React.ChangeEvent<HTMLInputElement>) {
    setDeclaredCity(e.target.value);
  }
  
  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    try{
      const response = await fetch("http://localhost:8000/verify-geo-ip", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: `declared_country=${encodeURIComponent(declaredCountry)}&declared_city=${encodeURIComponent(declaredCity)}`,
      });

      if(!response.ok) {
        const errorData = await response.json();
        setMessage("");
        setError(errorData.detail || "Failed to verify geo IP. Please try again.");
        return;
      }
      const data = await response.json();
      console.log(data);
      setMessage("Geo IP verified successfully! " + JSON.stringify(data).replaceAll(",", ",\n"));
      setError("");
    }
    catch (error) {
      console.error("Error verifying geo IP:", error);
      setMessage("");
      setError("Failed to verify geo IP. Please try again later.");
    }
  }

  return (
    <div className="min-h-screen w-screen flex items-center justify-center bg-gray-100 p-6">
      <div className="bg-white p-8 rounded-2xl shadow-xl w-full max-w-md">
        <GoToHomePage></GoToHomePage>
        <h1 className="text-3xl font-bold text-center text-gray-800 mb-8">Verify Geo IP</h1>
        <form action=""  className="space-y-5">
          <div className="flex flex-col">
            <label className="text-sm font-semibold text-gray-600 mb-1">Declared Country *</label>
            <input
              name="declared_country"
              type="text"
              required
              className="p-2 border rounded-lg text-black focus:ring-2 focus:ring-blue-500 outline-none"
              placeholder="indonesia"
              onChange={handleCountryChange}
              value={declaredCountry}
            />
          </div>
          <div className="flex flex-col">
            <label className="text-sm font-semibold text-gray-600 mb-1">Declared City</label>
            <input
              name="declared_city"
              type="text"
              className="p-2 border rounded-lg text-black focus:ring-2 focus:ring-blue-500 outline-none"
              placeholder="(optional)"
              onChange={handleCityChange}
              value={declaredCity}
            />
          </div>
          <button 
            type="button" 
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-lg transition-all"
            onClick={handleSubmit}
          >
            Continue
          </button>
          {
            message && <p className="text-green-600 text-center mt-4">{message}</p>
          }
          {
            error && <p className="text-red-600 text-center mt-4">{error}</p>
          }
        </form>
      </div>
    </div>
  )
}