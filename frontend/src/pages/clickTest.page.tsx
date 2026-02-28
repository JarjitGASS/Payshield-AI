import { useState } from "react";
import { Link } from "react-router-dom";
import GoToHomePage from "../component/goToHomePage.component";

export default function ClickTestPage() {
  const [notification, setNotification] = useState<string>("");

  function showNotification(msg: string) {
    setNotification(msg);
    setTimeout(() => setNotification(""), 3000);
  }

  async function handleClick(e: React.MouseEvent<HTMLDivElement, MouseEvent>) {
    const x = e.clientX;
    const y = e.clientY;
    try {
      const form = new URLSearchParams();
      form.append("user_id", "user");
      form.append("x", x.toString());
      form.append("y", y.toString());

      const res = await fetch("http://localhost:8000/store-click", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: form.toString(),
      });
      const data = await res.json();
      if (res.ok) {
        showNotification(`Stored click at ${x},${y}`);
      } else {
        showNotification(`Error: ${data.detail || res.statusText}`);
      }
    } catch (err) {
      console.error(err);
      showNotification("Network error");
    }
  }

  return (
    <div className="min-h-screen flex flex-col bg-gray-100" onClick={handleClick}>
      <GoToHomePage />
      {/* Navbar */}
      <nav className="bg-blue-600 text-white px-6 py-4 flex justify-between items-center">
        <div className="text-lg font-semibold">ClickTest</div>
        <div className="space-x-6 text-sm font-medium">
          <Link to="/" className="hover:underline">
            Home
          </Link>
          <Link to="/login" className="hover:underline">
            Login
          </Link>
          <Link to="/click-test" className="hover:underline">
            Click Test
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="flex-1 flex items-center justify-center px-6">
        <div className="bg-white rounded-xl shadow-lg p-10 max-w-xl w-full text-center">
          <h1 className="text-3xl font-bold text-gray-800 mb-4">
            Welcome to ClickTest
          </h1>

          <p className="text-gray-600 mb-8 leading-relaxed">
            A simple application to capture user click behavior for testing,
            analytics, and security research.
          </p>

          <Link
            to="/click-test"
            className="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition"
          >
            Start Click Test
          </Link>
        </div>
      </main>

      {/* Footer */}
      <footer className="text-center text-sm text-gray-500 py-4">
        © 2026 ClickTest. All rights reserved.
      </footer>

      {notification && (
        <div className="fixed bottom-4 right-4 bg-black text-white px-4 py-2 rounded shadow-lg z-50">
          {notification}
        </div>
      )}
    </div>
  );
}
