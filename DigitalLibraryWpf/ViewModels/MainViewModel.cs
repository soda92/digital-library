using DigitalLibraryWpf.Models;
using DigitalLibraryWpf.Services;
using System.Collections.ObjectModel;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Input;

namespace DigitalLibraryWpf.ViewModels
{
    public class MainViewModel : BaseViewModel
    {
        private readonly ApiService _apiService;

        private ObservableCollection<Book> _books = new ObservableCollection<Book>();
        public ObservableCollection<Book> Books
        {
            get => _books;
            set => SetField(ref _books, value);
        }

        private Book? _selectedBook;
        public Book? SelectedBook
        {
            get => _selectedBook;
            set => SetField(ref _selectedBook, value);
        }

        // Properties for new book creation
        private string _newBookTitle = string.Empty;
        public string NewBookTitle
        {
            get => _newBookTitle;
            set => SetField(ref _newBookTitle, value);
        }

        private string _newBookAuthor = string.Empty;
        public string NewBookAuthor
        {
            get => _newBookAuthor;
            set => SetField(ref _newBookAuthor, value);
        }

        private string _newBookIsbn = string.Empty;
        public string NewBookIsbn
        {
            get => _newBookIsbn;
            set => SetField(ref _newBookIsbn, value);
        }
        
        private string _serverUrl = "http://localhost:9000"; // User inputs this
        public string ServerUrl
        {
            get => _serverUrl;
            set
            {
                if (SetField(ref _serverUrl, value))
                {
                    _apiService.SetBaseUrl(_serverUrl); // Update ApiService when URL changes
                }
            }
        }

        private string _authToken = string.Empty;
        public string AuthToken
        {
            get => _authToken;
            set
            {
                if(SetField(ref _authToken, value))
                {
                    _apiService.SetAuthToken(_authToken);
                }
            }
        }


        public ICommand LoadBooksCommand { get; }
        public ICommand AddBookCommand { get; }
        public ICommand DeleteBookCommand { get; }
        public ICommand ApplyServerUrlCommand { get; }


        public MainViewModel()
        {
            _apiService = new ApiService();
            _apiService.SetBaseUrl(ServerUrl); // Initialize with default URL
            _apiService.SetAuthToken(AuthToken); // Initialize with empty/default token

            LoadBooksCommand = new RelayCommand(async _ => await LoadBooksAsync());
            AddBookCommand = new RelayCommand(async _ => await AddBookAsync(), _ => CanAddBook());
            DeleteBookCommand = new RelayCommand(async _ => await DeleteBookAsync(), _ => SelectedBook != null);
            ApplyServerUrlCommand = new RelayCommand(_ => _apiService.SetBaseUrl(ServerUrl));


            // Load books on startup (optional)
            // Task.Run(async () => await LoadBooksAsync());
        }

        private async Task LoadBooksAsync()
        {
            var booksList = await _apiService.GetBooksAsync();
            if (booksList != null)
            {
                Application.Current.Dispatcher.Invoke(() => // Ensure UI updates on UI thread
                {
                    Books.Clear();
                    foreach (var book in booksList)
                    {
                        Books.Add(book);
                    }
                });
            }
        }

        private bool CanAddBook()
        {
            return !string.IsNullOrWhiteSpace(NewBookTitle) &&
                   !string.IsNullOrWhiteSpace(NewBookAuthor) &&
                   !string.IsNullOrWhiteSpace(NewBookIsbn);
        }

        private async Task AddBookAsync()
        {
            if (string.IsNullOrEmpty(AuthToken))
            {
                MessageBox.Show("Auth Token is required to add a book. Please enter it in the settings.", "Authentication Required", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            var newBookDto = new BookCreateDto
            {
                Title = NewBookTitle,
                Author = NewBookAuthor,
                Isbn = NewBookIsbn
            };

            var createdBook = await _apiService.CreateBookAsync(newBookDto);
            if (createdBook != null)
            {
                Application.Current.Dispatcher.Invoke(() => Books.Add(createdBook));
                NewBookTitle = string.Empty;
                NewBookAuthor = string.Empty;
                NewBookIsbn = string.Empty;
                MessageBox.Show("Book added successfully!", "Success", MessageBoxButton.OK, MessageBoxImage.Information);
            }
            else
            {
                // Error message already shown by ApiService
            }
        }

        private async Task DeleteBookAsync()
        {
            if (SelectedBook == null) return;

            // Optional: Confirm before deleting
            var result = MessageBox.Show($"Are you sure you want to delete '{SelectedBook.Title}'?",
                                         "Confirm Delete", MessageBoxButton.YesNo, MessageBoxImage.Warning);
            if (result == MessageBoxResult.No) return;
            
            // Note: The current FastAPI delete_book endpoint does not require authentication.
            // If it did, and AuthToken was empty, you might add a check here similar to AddBookAsync.

            bool success = await _apiService.DeleteBookAsync(SelectedBook.Id);
            if (success)
            {
                Application.Current.Dispatcher.Invoke(() => Books.Remove(SelectedBook));
                SelectedBook = null;
                MessageBox.Show("Book deleted successfully!", "Success", MessageBoxButton.OK, MessageBoxImage.Information);
            }
            else
            {
                 // Error message already shown by ApiService
            }
        }
    }
}
