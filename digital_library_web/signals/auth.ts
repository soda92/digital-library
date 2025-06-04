import { signal, effect } from "@preact/signals";

export const jwtToken = signal<string | null>(null);
export const loggedInUsername = signal<string | null>(null);

// Function to decode JWT and get username (simplified)
function getUsernameFromToken(token: string): string | null {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.sub || null;
  } catch (e) {
    console.error("Failed to decode token:", e);
    jwtToken.value = null; // Clear invalid token
    return null;
  }
}

// Effect to synchronize with localStorage and update username
effect(() => {
  const storedToken = typeof localStorage !== "undefined" ? localStorage.getItem("jwt") : null;
  jwtToken.value = storedToken;

  if (jwtToken.value) {
    loggedInUsername.value = getUsernameFromToken(jwtToken.value);
  } else {
    loggedInUsername.value = null;
    if (typeof localStorage !== "undefined") localStorage.removeItem("jwt");
  }
});