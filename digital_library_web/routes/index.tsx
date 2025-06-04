import { Signal, useSignal } from "@preact/signals";
import { define } from "../utils.ts";
import BookList from "../islands/BookList.tsx"; // Import the new island

// API_BASE_URL will be used for the POST request here, and also within BookList.tsx
const API_BASE_URL = "http://127.0.0.1:9000";

export default define.page(function Home() {
  // Signal to trigger refresh in BookList island
  const refreshTrigger = useSignal(0);

  // Form-specific error message
  const addBookFormError = useSignal<string | null>(null);

  // Form input signals
  const newBookTitle = useSignal("");
  const newBookAuthor = useSignal("");
  const newBookIsbn = useSignal("");

  async function handleAddBook(e: Event) {
    e.preventDefault();
    addBookFormError.value = null;

    if (!newBookTitle.value.trim() || !newBookAuthor.value.trim() || !newBookIsbn.value.trim()) {
      addBookFormError.value = "All fields (Title, Author, ISBN) are required.";
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/books/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          title: newBookTitle.value,
          author: newBookAuthor.value,
          isbn: newBookIsbn.value,
          // is_borrowed defaults to false on the backend
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `HTTP error! status: ${response.status}` }));
        throw new Error(errorData.detail || `Failed to add book. Status: ${response.status}`);
      }

      // Clear form and refresh book list
      newBookTitle.value = "";
      newBookAuthor.value = "";
      newBookIsbn.value = "";
      refreshTrigger.value++; // Trigger refresh in BookList island
    } catch (error) {
      console.error("Error adding book:", error);
      addBookFormError.value = error instanceof Error ? error.message : "An unexpected error occurred while adding the book.";
    }
  }

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

        {/* Add Book Form */}
        <form onSubmit={handleAddBook} class="w-full bg-white p-6 rounded-lg shadow-md my-8">
          <h2 class="text-2xl font-semibold mb-4 text-gray-700">Add New Book</h2>
          {addBookFormError.value && <p class="text-red-500 text-sm mb-3">{addBookFormError.value}</p>}
          <div class="mb-4">
            <label for="title" class="block text-gray-700 text-sm font-bold mb-2">Title:</label>
            <input type="text" id="title" value={newBookTitle.value} onInput={(e) => newBookTitle.value = (e.target as HTMLInputElement).value} class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline" />
          </div>
          <div class="mb-4">
            <label for="author" class="block text-gray-700 text-sm font-bold mb-2">Author:</label>
            <input type="text" id="author" value={newBookAuthor.value} onInput={(e) => newBookAuthor.value = (e.target as HTMLInputElement).value} class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline" />
          </div>
          <div class="mb-6">
            <label for="isbn" class="block text-gray-700 text-sm font-bold mb-2">ISBN:</label>
            <input type="text" id="isbn" value={newBookIsbn.value} onInput={(e) => newBookIsbn.value = (e.target as HTMLInputElement).value} class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline" />
          </div>
          <button type="submit" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline">
            Add Book
          </button>
        </form>

        {/* Book List */}
        <div class="w-full mt-8">
          <h2 class="text-3xl font-semibold mb-6 text-gray-700">Available Books</h2>
          <BookList refreshTrigger={refreshTrigger} />
        </div>
      </div>
    </div>
  );
});
