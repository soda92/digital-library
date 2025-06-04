import { useSignal } from "@preact/signals";
import { define } from "../utils.ts";
import BookList from "../islands/BookList.tsx";
import AddBookForm from "../islands/AddBookForm.tsx";
import LoginForm from "../islands/LoginForm.tsx";
import RegisterForm from "../islands/RegisterForm.tsx";
import AuthStatus from "../islands/AuthStatus.tsx";
import { loggedInUsername } from "../signals/auth.tsx"; // Import login state

// API_BASE_URL will be used for the POST request here, and also within BookList.tsx
const API_BASE_URL = "http://127.0.0.1:9000";

export default define.page(function Home() {
  // Signal to trigger refresh in BookList island
  // This signal will now also be used by AddBookForm to trigger BookList
  const refreshTrigger = useSignal(0);

  return (
    <div class="px-4 py-8 mx-auto bg-gray-100 min-h-screen font-sans">
      <div class="max-w-screen-md mx-auto flex flex-col items-center justify-center">
        <img
          class="my-6"
          src="/logo.svg"
          width="96"
          height="96"
          alt="Digital Library logo"
        />
        <h1 class="text-4xl font-bold text-gray-800">Digital Library</h1>

        <AuthStatus />

        {!loggedInUsername.value && (
          <div class="w-full md:flex md:space-x-4">
            <RegisterForm />
            <LoginForm />
          </div>
        )}

        {/* Add Book Form - Show only if logged in */}
        {loggedInUsername.value && <AddBookForm refreshTrigger={refreshTrigger} API_BASE_URL={API_BASE_URL} />}

        {/* Book List */}
        <div class="w-full mt-8">
          <h2 class="text-3xl font-semibold mb-6 text-gray-700">Available Books</h2>
          <BookList refreshTrigger={refreshTrigger} />
        </div>
      </div>
    </div>
  );
});
