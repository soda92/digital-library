import { effect, signal } from "@preact/signals";

// Initialize jwtToken from localStorage on load
export const jwtToken = signal<string | null>(
  typeof localStorage !== "undefined" ? localStorage.getItem("jwt") : null,
);

export const loggedInUsername = signal<string | null>(null);

// Function to decode JWT and get username (simplified)
function getUsernameFromToken(token: string): string | null {
  // Basic check for token structure
  if (!token || typeof token !== 'string' || token.split('.').length !== 3) {
    console.error("Invalid token format provided to getUsernameFromToken.");
    return null;
  }
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return payload.sub || null;
  } catch (e) {
    console.error("Failed to decode token:", e);
    return null;
  }
}

// Effect to synchronize jwtToken changes with localStorage and update username
effect(() => {
  if (jwtToken.value) {
    const username = getUsernameFromToken(jwtToken.value);
    if (username) {
      // Token is valid, username extracted
      loggedInUsername.value = username;
      if (typeof localStorage !== "undefined") {
        localStorage.setItem("jwt", jwtToken.value);
      }
    } else {
      // Token was present but invalid
      loggedInUsername.value = null;
      if (typeof localStorage !== "undefined") localStorage.removeItem("jwt");
      // Clear the invalid token from the signal to prevent re-processing
      // and to reflect the invalid state.
      jwtToken.value = null; 
    }
  } else {
    // Token is null, remove from storage and clear username
    loggedInUsername.value = null;
    if (typeof localStorage !== "undefined") localStorage.removeItem("jwt");
  }
});
