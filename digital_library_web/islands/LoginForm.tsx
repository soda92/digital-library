import { useSignal } from "@preact/signals";
import { jwtToken } from "../signals/auth.tsx"; // Import the shared signal

interface LoginFormProps {
  API_BASE_URL: string;
}

export default function LoginForm({ API_BASE_URL }: LoginFormProps) {
  const username = useSignal("");
  const password = useSignal("");
  const error = useSignal<string | null>(null);
  const isLoading = useSignal(false);

  // API_BASE_URL is now passed as a prop

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
      // The effect in signals/auth.tsx will handle localStorage persistence.

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