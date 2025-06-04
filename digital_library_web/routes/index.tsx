import { Signal, useSignal } from "@preact/signals";
import { useEffect } from "preact/hooks";
import { define } from "../utils.ts";

// Define the Book type based on your API's BookInDB model
interface Book {
  id: string; // UUID is a string
  title: string;
  author: string;
  isbn: string;
  is_borrowed: boolean;
  borrower_name?: string | null;
  due_date?: string | null; // Dates will be strings from JSON
}

const API_BASE_URL = "http://127.0.0.1:9000";

export default define.page(function Home() {
  const books = useSignal<Book[]>([]);
  const isLoading = useSignal(true);
  const errorMessage = useSignal<string | null>(null);

  // Form input signals
  const newBookTitle = useSignal("");
  const newBookAuthor = useSignal("");
  const newBookIsbn = useSignal("");

  async function fetchBooks() {
    isLoading.value = true;
    errorMessage.value = null;
    try {
      const response = await fetch(`${API_BASE_URL}/books/`);
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `HTTP error! status: ${response.status}` }));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }
      const data: Book[] = await response.json();
      books.value = data;
    } catch (error) {
      console.error("Error fetching books:", error);
      errorMessage.value = error instanceof Error ? error.message : "Failed to load books. Make sure the API server is running.";
    } finally {
      isLoading.value = false;
    }
  }

  async function handleAddBook(e: Event) {
    e.preventDefault();
    errorMessage.value = null;

    if (!newBookTitle.value.trim() || !newBookAuthor.value.trim() || !newBookIsbn.value.trim()) {
      errorMessage.value = "All fields (Title, Author, ISBN) are required.";
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
      await fetchBooks();
    } catch (error) {
      console.error("Error adding book:", error);
      errorMessage.value = error instanceof Error ? error.message : "An unexpected error occurred while adding the book.";
    }
  }

  // Fetch books on component mount
  useEffect(() => {
    fetchBooks();
  }, []);

  return (
    <div class="px-4 py-8 mx-auto bg-gray-100 min-h-screen">
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
          {errorMessage.value && errorMessage.value.includes("required") && <p class="text-red-500 text-sm mb-3">{errorMessage.value}</p>}
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
          {isLoading.value && <p class="text-gray-600">Loading books...</p>}
          {errorMessage.value && !errorMessage.value.includes("required") && <p class="text-red-500 bg-red-100 p-3 rounded-md">{errorMessage.value}</p>}
          {!isLoading.value && !errorMessage.value && books.value.length === 0 && <p class="text-gray-600">No books in the library yet.</p>}
          <ul class="space-y-4">
            {books.value.map((book) => (
              <li key={book.id} class="bg-white p-4 rounded-lg shadow">
                <h3 class="text-xl font-semibold text-gray-800">{book.title}</h3>
                <p class="text-gray-600">by {book.author}</p>
                <p class="text-sm text-gray-500">ISBN: {book.isbn}</p>
                {book.is_borrowed && (
                  <p class="text-sm text-red-500 mt-1">
                    Borrowed by: {book.borrower_name || "N/A"} (Due: {book.due_date ? new Date(book.due_date).toLocaleDateString() : "N/A"})
                  </p>
                )}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
});
