using DigitalLibraryWpf.Models;
using DigitalLibraryWpf.Services;
using System.Collections.ObjectModel;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Input;

namespace DigitalLibraryWpf.ViewModels
{
    public class BookManagementViewModel : BaseViewModel
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

        public ICommand LoadBooksCommand { get; }
        public ICommand AddBookCommand { get; }
        public ICommand DeleteBookCommand { get; }

        public BookManagementViewModel(ApiService apiService)
        {
            _apiService = apiService;

            LoadBooksCommand = new RelayCommand(async _ => await LoadBooksAsync());
            AddBookCommand = new RelayCommand(async _ => await AddBookAsync(), _ => CanAddBook());
            DeleteBookCommand = new RelayCommand(async _ => await DeleteBookAsync(), _ => SelectedBook != null && _apiService.IsUserLoggedIn);
            
            // Automatically load books when this view model becomes active
            // Consider if this should be triggered by an event or explicit call
             if (_apiService.IsUserLoggedIn) // Only load if already logged in (e.g. app startup with stored token)
             {
                Task.Run(async () => await LoadBooksAsync());
             }
        }

        public async Task LoadBooksAsync() // Made public to be called by MainViewModel after login
        {
            var booksList = await _apiService.GetBooksAsync();
            Application.Current.Dispatcher.Invoke(() =>
            {
                Books.Clear();
                if (booksList != null)
                {
                    foreach (var book in booksList)
                    {
                        Books.Add(book);
                    }
                }
            });
        }

        private bool CanAddBook()
        {
            return !string.IsNullOrWhiteSpace(NewBookTitle) &&
                   !string.IsNullOrWhiteSpace(NewBookAuthor) &&
                   !string.IsNullOrWhiteSpace(NewBookIsbn) &&
                   _apiService.IsUserLoggedIn;
        }

        private async Task AddBookAsync()
        {
            if (!_apiService.IsUserLoggedIn)
            {
                MessageBox.Show("You must be logged in to add a book.", "Authentication Required", MessageBoxButton.OK, MessageBoxImage.Warning);
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
        }

        private async Task DeleteBookAsync()
        {
            if (SelectedBook == null) return;
            if (!_apiService.IsUserLoggedIn)
            {
                MessageBox.Show("You must be logged in to delete a book.", "Authentication Required", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            var result = MessageBox.Show($"Are you sure you want to delete '{SelectedBook.Title}'?",
                                         "Confirm Delete", MessageBoxButton.YesNo, MessageBoxImage.Warning);
            if (result == MessageBoxResult.No) return;

            bool success = await _apiService.DeleteBookAsync(SelectedBook.Id);
            if (success)
            {
                Application.Current.Dispatcher.Invoke(() => Books.Remove(SelectedBook));
                SelectedBook = null;
                MessageBox.Show("Book deleted successfully!", "Success", MessageBoxButton.OK, MessageBoxImage.Information);
            }
        }
    }
}
