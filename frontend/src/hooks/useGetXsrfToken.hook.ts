import { useEffect } from "react";

export default function useGetXsrfToken() {
  useEffect(() => {
    fetch("http://localhost:8000/csrf", {
      credentials: "include",
    })
      .then(res => res.json())
      .then(data => {
        (window as any).csrfToken = data.csrfToken;
      })
      .catch(err => {
        console.error("Failed to get CSRF token", err);
      });
  }, []);
}