import { Signal, useSignal } from "@preact/signals";
import { jwtToken } from "../signals/auth.ts"; // Import JWT signal

interface AddBookFormProps {
  refreshTrigger: Signal<number>;
  API_BASE_URL: string;
}

export default function AddBookForm({ refreshTrigger, API_BASE_URL }: AddBookFormProps) {
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

    if (!jwtToken.value) {
      addBookFormError.value = "You must be logged in to add a book.";
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/books/`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${jwtToken.value}`},
        body: JSON.stringify({
          title: newBookTitle.value,
          author: newBookAuthor.value,
          isbn: newBookIsbn.value,
          // is_borrowed defaults to false on the backend
        }),
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error("Unauthorized. Please log in again.");
        }
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
  );
}