import { useSignal } from "@preact/signals";

interface RegisterFormProps {
  API_BASE_URL: string;
}

export default function RegisterForm({ API_BASE_URL }: RegisterFormProps) {
  // API_BASE_URL is now passed as a prop
  const username = useSignal("");
  const password = useSignal("");
  const error = useSignal<string | null>(null);
  const successMessage = useSignal<string | null>(null);
  const isLoading = useSignal(false);

  async function handleRegister(e: Event) {
    e.preventDefault();
    error.value = null;
    successMessage.value = null;
    isLoading.value = true;

    if (!username.value.trim() || !password.value.trim()) {
      error.value = "Username and password are required.";
      isLoading.value = false;
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/users/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: username.value,
          password: password.value,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `HTTP error! Status: ${response.status}` }));
        throw new Error(errorData.detail || `Registration failed. Status: ${response.status}`);
      }

      successMessage.value = "Registration successful! You can now log in.";
      username.value = "";
      password.value = "";
    } catch (err) {
      error.value = err instanceof Error ? err.message : "An unexpected error occurred.";
    } finally {
      isLoading.value = false;
    }
  }

  return (
    <form onSubmit={handleRegister} class="w-full max-w-sm bg-white p-6 rounded-lg shadow-md my-4">
      <h2 class="text-xl font-semibold mb-4 text-gray-700">Register</h2>
      {error.value && <p class="text-red-500 text-sm mb-3">{error.value}</p>}
      {successMessage.value && <p class="text-green-500 text-sm mb-3">{successMessage.value}</p>}
      <div class="mb-4">
        <input type="text" placeholder="Username" value={username.value} onInput={(e) => username.value = (e.target as HTMLInputElement).value} class="input input-bordered w-full" disabled={isLoading.value} />
      </div>
      <div class="mb-4">
        <input type="password" placeholder="Password" value={password.value} onInput={(e) => password.value = (e.target as HTMLInputElement).value} class="input input-bordered w-full" disabled={isLoading.value} />
      </div>
      <button type="submit" class="btn btn-primary w-full" disabled={isLoading.value}>
        {isLoading.value ? "Registering..." : "Register"}
      </button>
    </form>
  );
}