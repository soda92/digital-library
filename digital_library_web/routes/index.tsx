import Home from "../islands/Home.tsx";

// Read API_BASE_URL from environment variable, with a fallback for local dev
const apiBaseUrl = Deno.env.get("API_BASE_URL") || "http://127.0.0.1:9000";
export default function App() {
  return <Home API_BASE_URL={apiBaseUrl} />;
}
