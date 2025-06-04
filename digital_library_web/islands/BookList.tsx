import { Signal, useSignal } from "@preact/signals";
import { useEffect } from "preact/hooks";
import { jwtToken } from "../signals/auth.tsx"; // Import JWT signal

// Define the Book type based on your API's BookInDB model
// Note: API uses integer IDs, so `id` is number.
interface Book {
  id: number;
  title: string;
  author: string;
  isbn: string;
  is_borrowed: boolean;
  borrower_username?: string | null; // Changed from borrower_name
  due_date?: string | null; // Dates will be strings from JSON
}

const API_BASE_URL = "http://127.0.0.1:9000";

interface BookListProps {
  refreshTrigger: Signal<number>;
}

export default function BookList(props: BookListProps) {
  const books = useSignal<Book[]>([]);
  const isLoadingBooks = useSignal(true);
  const fetchBooksError = useSignal<string | null>(null);
  const actionError = useSignal<string | null>(null); // For borrow/return errors

  async function fetchBooks() {
    isLoadingBooks.value = true;
    fetchBooksError.value = null;
    try {
      const response = await fetch(`${API_BASE_URL}/books/`);
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({
          detail: `HTTP error! status: ${response.status}`,
        }));
        throw new Error(
          errorData.detail || `HTTP error! status: ${response.status}`,
        );
      }
      const data: Book[] = await response.json();
      books.value = data;
    } catch (error) {
      console.error("Error fetching books:", error);
      fetchBooksError.value = error instanceof Error
        ? error.message
        : "Failed to load books. Make sure the API server is running.";
    } finally {
      isLoadingBooks.value = false;
    }
  }

  useEffect(() => {
    fetchBooks();
  }, [props.refreshTrigger.value]); // Re-fetch when refreshTrigger changes

  async function handleBorrow(bookId: number, bookTitle: string) {
    actionError.value = null;
    if (!jwtToken.value) {
      actionError.value = "You must be logged in to borrow a book.";
      // Optionally, redirect to login or show a more prominent login prompt
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/books/${bookId}/borrow`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${jwtToken.value}`,
        },
        body: JSON.stringify({}), // No borrower_name needed, backend uses token
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error("Unauthorized. Please log in again to borrow.");
        }
        const errorData = await response.json().catch(() => ({
          detail: `HTTP error! status: ${response.status}`,
        }));
        throw new Error(
          errorData.detail ||
            `Failed to borrow book. Status: ${response.status}`,
        );
      }
      props.refreshTrigger.value++; // Refresh book list
    } catch (error) {
      console.error("Error borrowing book:", error);
      actionError.value = error instanceof Error
        ? error.message
        : "An unexpected error occurred while borrowing the book.";
    }
  }

  async function handleReturn(bookId: number) {
    actionError.value = null;
    if (!jwtToken.value) {
      actionError.value = "You must be logged in to return a book.";
      return;
    }
    try {
      const response = await fetch(`${API_BASE_URL}/books/${bookId}/return`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${jwtToken.value}`,
        },
      });

      if (!response.ok) {
        if (response.status === 401) throw new Error("Unauthorized. Please log in again to return.");
        const errorData = await response.json().catch(() => ({
          detail: `HTTP error! status: ${response.status}`,
        }));
        throw new Error(
          errorData.detail ||
            `Failed to return book. Status: ${response.status}`,
        );
      }
      props.refreshTrigger.value++; // Refresh book list
    } catch (error) {
      console.error("Error returning book:", error);
      actionError.value = error instanceof Error
        ? error.message
        : "An unexpected error occurred while returning the book.";
    }
  }

  return (
    <>
      {isLoadingBooks.value && <p class="text-gray-600">Loading books...</p>}
      {fetchBooksError.value && (
        <p class="text-red-500 bg-red-100 p-3 rounded-md mb-4">
          Error loading books: {fetchBooksError.value}
        </p>
      )}
      {actionError.value && (
        <p class="text-red-500 bg-red-100 p-3 rounded-md mb-4">
          {actionError.value}
        </p>
      )}
      {!isLoadingBooks.value && !fetchBooksError.value &&
        books.value.length === 0 && (
        <p class="text-gray-600">No books in the library yet.</p>
      )}
      {!isLoadingBooks.value && !fetchBooksError.value &&
        books.value.length > 0 && (
        <ul class="space-y-4">
          {books.value.map((book) => (
            <li key={book.id} class="bg-white p-4 rounded-lg shadow">
              <h3 class="text-xl font-semibold text-gray-800">{book.title}</h3>
              <p class="text-gray-600">by {book.author}</p>
              <p class="text-sm text-gray-500">ISBN: {book.isbn}</p>
              {book.is_borrowed && (
                <p class="text-sm text-red-500 mt-1">
                  Borrowed by: {book.borrower_username || "N/A"} (Due:{" "}
                  {book.due_date
                    ? new Date(book.due_date).toLocaleDateString()
                    : "N/A"})
                </p>
              )}
              <div class="mt-2">
                {book.is_borrowed
                  ? (
                    <button type="button"
                      onClick={() => handleReturn(book.id)}
                      class="bg-yellow-500 hover:bg-yellow-700 text-white font-bold py-1 px-3 rounded text-sm focus:outline-none focus:shadow-outline"
                    >
                      Return Book
                    </button>
                  )
                  : (
                    <button
                      type="button"
                      onClick={() => handleBorrow(book.id, book.title)}
                      class="bg-green-500 hover:bg-green-700 text-white font-bold py-1 px-3 rounded text-sm focus:outline-none focus:shadow-outline"
                    >
                      Borrow Book
                    </button>
                  )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}
