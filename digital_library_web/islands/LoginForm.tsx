import { useSignal } from "@preact/signals";
import { jwtToken } from "../signals/auth.ts"; // Import the shared signal

const API_BASE_URL = "http://127.0.0.1:9000"; // Or pass as prop

export default function LoginForm() {
  const username = useSignal("");
  const password = useSignal("");
  const error = useSignal<string | null>(null);
  const isLoading = useSignal(false);

  async function handleLogin(e: Event) {
    e.preventDefault();
    error.value = null;
    isLoading.value = true;

    if (!username.value.trim() || !password.value.trim()) {
      error.value = "Username and password are required.";
      isLoading.value = false;
      return;
    }

    try {
      const formData = new URLSearchParams();
      formData.append('username', username.value);
      formData.append('password', password.value);

      const response = await fetch(`${API_BASE_URL}/token`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `HTTP error! Status: ${response.status}` }));
        throw new Error(errorData.detail || `Login failed. Status: ${response.status}`);
      }

      const data = await response.json();
      jwtToken.value = data.access_token; // This will trigger the effect in signals/auth.ts
      if (typeof localStorage !== "undefined") localStorage.setItem("jwt", data.access_token); // Explicitly set for immediate effect

      username.value = ""; // Clear form
      password.value = "";
    } catch (err) {
      error.value = err instanceof Error ? err.message : "An unexpected error occurred.";
    } finally {
      isLoading.value = false;
    }
  }

  return (
    <form onSubmit={handleLogin} class="w-full max-w-sm bg-white p-6 rounded-lg shadow-md my-4">
      <h2 class="text-xl font-semibold mb-4 text-gray-700">Login</h2>
      {error.value && <p class="text-red-500 text-sm mb-3">{error.value}</p>}
      <div class="mb-4">
        <input type="text" placeholder="Username" value={username.value} onInput={(e) => username.value = (e.target as HTMLInputElement).value} class="input input-bordered w-full" disabled={isLoading.value} />
      </div>
      <div class="mb-4">
        <input type="password" placeholder="Password" value={password.value} onInput={(e) => password.value = (e.target as HTMLInputElement).value} class="input input-bordered w-full" disabled={isLoading.value} />
      </div>
      <button type="submit" class="btn btn-primary w-full" disabled={isLoading.value}>
        {isLoading.value ? "Logging in..." : "Login"}
      </button>
    </form>
  );
}