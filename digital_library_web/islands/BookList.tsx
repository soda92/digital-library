import { Signal, useSignal } from "@preact/signals";
import { useEffect } from "preact/hooks";

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

interface BookListProps {
  refreshTrigger: Signal<number>;
}

export default function BookList(props: BookListProps) {
  const books = useSignal<Book[]>([]);
  const isLoadingBooks = useSignal(true);
  const fetchBooksError = useSignal<string | null>(null);

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

  return (
    <>
      {isLoadingBooks.value && <p class="text-gray-600">Loading books...</p>}
      {fetchBooksError.value && <p class="text-red-500 bg-red-100 p-3 rounded-md">{fetchBooksError.value}</p>}
      {!isLoadingBooks.value && !fetchBooksError.value && books.value.length === 0 && <p class="text-gray-600">No books in the library yet.</p>}
      {!isLoadingBooks.value && !fetchBooksError.value && books.value.length > 0 && (
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
      )}
    </>
  );
}