import { effect, signal } from "@preact/signals";

// Initialize jwtToken from localStorage on load
export const jwtToken = signal<string | null>(
  typeof localStorage !== "undefined" ? localStorage.getItem("jwt") : null,
);

export const loggedInUsername = signal<string | null>(null);

// Function to decode JWT and get username (simplified)
function getUsernameFromToken(token: string): string | null {
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return payload.sub || null;
  } catch (e) {
    console.error("Failed to decode token:", e);
    jwtToken.value = null; // Clear invalid token
    return null;
  }
}

// Effect to synchronize jwtToken changes with localStorage and update username
effect(() => {
  if (jwtToken.value) {
    // Token is set, store it and update username
    if (typeof localStorage !== "undefined") {
      localStorage.setItem("jwt", jwtToken.value);
    }
    loggedInUsername.value = getUsernameFromToken(jwtToken.value);
  } else {
    // Token is null, remove from storage and clear username
    loggedInUsername.value = null;
    if (typeof localStorage !== "undefined") localStorage.removeItem("jwt");
  }
});
