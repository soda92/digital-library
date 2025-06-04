import { jwtToken, loggedInUsername } from "../signals/auth.ts";

export default function AuthStatus() {
  function handleLogout() {
    jwtToken.value = null; // This will trigger effect to clear localStorage and username
  }

  return (
    <div class="my-4 p-4 bg-gray-200 rounded-md text-center">
      {loggedInUsername.value
        ? (
          <>
            <p class="text-gray-700">Logged in as: <span class="font-semibold">{loggedInUsername.value}</span></p>
            <button onClick={handleLogout} class="btn btn-sm btn-outline mt-2">
              Logout
            </button>
          </>
        )
        : <p class="text-gray-700">You are not logged in.</p>}
    </div>
  );
}