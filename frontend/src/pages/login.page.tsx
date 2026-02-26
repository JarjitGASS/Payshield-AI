// pages/RegisterPage.tsx
import { useState } from "react";
import useBehavioralMonitor from "../hooks/useBehavioralMonitor.hook";

export default function LoginPage() {
  const { flush } = useBehavioralMonitor();
  const [isError, setIsError] = useState<boolean | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [result, setResult] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    const form = e.currentTarget; 
    
    const behaviorData = await flush();

    const formData = new FormData(form);
    const username = formData.get('username');
    const password = formData.get('password');

    const payload = {
      username,
      password,
      behavior: behaviorData,
    };

    try {
      const response = await fetch('http://localhost:3000/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const result = await response.json();

      setIsError(!result.success);
      setMessage(result.message);
      setResult(result.analysis || null);

    } catch (err) {
      console.error("Submission error:", err);
    }
  };

  return (
    <div className="min-h-screen w-screen flex items-center justify-center bg-gray-100 p-4">
      <div className="bg-white p-8 rounded-2xl shadow-xl w-full max-w-md">
        <h1 className="text-3xl font-bold text-center text-gray-800 mb-8">Login</h1>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="flex flex-col">
            <label htmlFor="username" className="text-sm font-semibold text-gray-600 mb-2">
              Username
            </label>
            <input 
              name="username"
              type="text" 
              required
              id="username"
              className="px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 outline-none text-black"
            />
          </div>

          <div className="flex flex-col">
            <label htmlFor="password" className="text-sm font-semibold text-gray-600 mb-2">
              Password
            </label>
            <input 
              name="password"
              type="password" 
              required
              id="password"
              className="px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 outline-none text-black"
            />
          </div>

          <button 
            type="submit" 
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-lg transition-all shadow-lg active:scale-[0.98]"
          >
            Login
          </button>

        </form>
        {isError !== null && (
          <div className={`mt-6 p-4 rounded-lg ${isError ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
            {message}
            {result && (
              <div className="mt-2 text-sm">
                <p className="font-semibold">Analysis:</p>
                <p>{result}</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}