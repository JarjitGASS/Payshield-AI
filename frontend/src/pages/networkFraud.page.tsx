import { useState } from "react";
import GoToHomePage from "../component/goToHomePage.component";

function getDeviceFingerprint() {
  const ua = navigator.userAgent;
  const platform = navigator.platform;
  const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
  const offset = new Date().getTimezoneOffset();
  const width = screen.width;
  const height = screen.height;
  const dpr = window.devicePixelRatio || 1;
  const language = navigator.language;

  // you can add more hints if needed
  return [
    `ua=${ua}`,
    `platform=${platform}`,
    `tz=${tz}`,
    `offset=${offset}`,
    `res=${width}x${height}`,
    `dpr=${dpr}`,
    `lang=${language}`,
  ].join("|");
}

export default function NetworkFraudPage() {
  const [username, setUsername] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string>("");

  function handleUsernameChange(e: React.ChangeEvent<HTMLInputElement>) {
    setUsername(e.target.value);
  }

  function handlePasswordChange(e: React.ChangeEvent<HTMLInputElement>) {
    setPassword(e.target.value);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const deviceId = getDeviceFingerprint();
    try {
      const form = new URLSearchParams();
      form.append("user_id", username);
      form.append("device_id", deviceId);

      const response = await fetch("http://localhost:8000/verify-network-fraud", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: form.toString(),
      });

      const data = await response.json();
      if (!response.ok) {
        setError(data.detail || "Network fraud check failed");
        setResult(null);
      } else {
        setResult(data);
        setError("");
      }
    } catch (err) {
      console.error(err);
      setError("Network error");
      setResult(null);
    }
  }

  return (
    <div className="min-h-screen w-screen flex items-center justify-center bg-gray-100 p-6">
      <div className="bg-white p-8 rounded-2xl shadow-xl w-full max-w-md">
        <GoToHomePage />
        <h1 className="text-3xl font-bold text-center text-gray-800 mb-8">
          Network Fraud Simulator
        </h1>
        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="flex flex-col">
            <label className="text-sm font-semibold text-gray-600 mb-1">
              Username
            </label>
            <input
              name="username"
              type="text"
              required
              className="p-2 border rounded-lg text-black focus:ring-2 focus:ring-blue-500 outline-none"
              value={username}
              onChange={handleUsernameChange}
            />
          </div>
          <div className="flex flex-col">
            <label className="text-sm font-semibold text-gray-600 mb-1">
              Password
            </label>
            <input
              name="password"
              type="password"
              required
              className="p-2 border rounded-lg text-black focus:ring-2 focus:ring-blue-500 outline-none"
              value={password}
              onChange={handlePasswordChange}
            />
          </div>
          <button
            type="submit"
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-lg transition-all"
          >
            Check Fraud
          </button>
        </form>
        {error && <p className="text-red-600 text-center mt-4">{error}</p>}
        {result && (
          <div className="mt-4 p-4 border rounded-lg bg-gray-50">
            <pre className="text-xs whitespace-pre-wrap">
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
