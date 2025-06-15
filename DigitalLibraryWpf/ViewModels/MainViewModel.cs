using DigitalLibraryWpf.Services;
using System.Threading.Tasks;
using System.Windows.Input;
using System.Windows; // For Application.Current.Dispatcher

namespace DigitalLibraryWpf.ViewModels
{
    public class MainViewModel : BaseViewModel
    {
        private readonly ApiService _apiService;
        private LoginViewModel _loginViewModel;
        private BookManagementViewModel _bookManagementViewModel;

        private BaseViewModel _currentPageViewModel;
        public BaseViewModel CurrentPageViewModel
        {
            get => _currentPageViewModel;
            set => SetField(ref _currentPageViewModel, value);
        }

        private bool _isLoggedIn;
        public bool IsLoggedIn
        {
            get => _isLoggedIn;
            set
            {
                if (SetField(ref _isLoggedIn, value))
                {
                    OnPropertyChanged(nameof(LoginLogoutButtonText));
                    // Re-evaluate commands that depend on login state
                    CommandManager.InvalidateRequerySuggested();
                }
            }
        }
        
        public string LoginLogoutButtonText => IsLoggedIn ? "Logout" : "Login";

        private string _serverUrl = "http://127.0.0.1:9000";
        public string ServerUrl
        {
            get => _serverUrl;
            set
            {
                if (SetField(ref _serverUrl, value))
                {
                    // Apply immediately or via button
                    // _apiService.SetBaseUrl(_serverUrl); 
                }
            }
        }

        public ICommand ApplyServerUrlCommand { get; }
        public ICommand LogoutCommand { get; }
        public ICommand LoginCommand { get; } // Will navigate to login view if not already there

        public MainViewModel()
        {
            _apiService = new ApiService();
            _apiService.SetBaseUrl(ServerUrl); // Initialize with default URL
            _apiService.AuthTokenChanged += OnAuthTokenChanged; // Subscribe to token changes

            _loginViewModel = new LoginViewModel(_apiService, OnLoginSuccess);
            _bookManagementViewModel = new BookManagementViewModel(_apiService);
            
            ApplyServerUrlCommand = new RelayCommand(_ => _apiService.SetBaseUrl(ServerUrl), _ => !string.IsNullOrWhiteSpace(ServerUrl));
            LogoutCommand = new RelayCommand(ExecuteLogout, (_) => IsLoggedIn);
            LoginCommand = new RelayCommand(ExecuteShowLogin, (_) => !IsLoggedIn);


            // Initial state
            IsLoggedIn = _apiService.IsUserLoggedIn; // Check if already logged in (e.g. token persistence later)
            if (IsLoggedIn)
            {
                CurrentPageViewModel = _bookManagementViewModel;
                // If starting logged in, ensure books are loaded
                Task.Run(async () => await _bookManagementViewModel.LoadBooksAsync());
            }
            else
            {
                CurrentPageViewModel = _loginViewModel;
            }
        }

        private void OnAuthTokenChanged()
        {
            // Update IsLoggedIn property which will trigger UI updates
            // Ensure this is run on the UI thread if it modifies UI-bound properties directly
            // or if ApiService calls it from a non-UI thread.
            Application.Current.Dispatcher.Invoke(() =>
            {
                IsLoggedIn = _apiService.IsUserLoggedIn;
            });
        }

        private void OnLoginSuccess()
        {
            IsLoggedIn = true;
            CurrentPageViewModel = _bookManagementViewModel;
            // Trigger book loading after successful login
            Task.Run(async () => await _bookManagementViewModel.LoadBooksAsync());
        }

        private void ExecuteLogout(object? _)
        {
            _apiService.Logout();
            IsLoggedIn = false; // This should also be set by OnAuthTokenChanged
            CurrentPageViewModel = _loginViewModel;
            _bookManagementViewModel.Books.Clear(); // Clear books on logout
        }

        private void ExecuteShowLogin(object? parameter)
        {
            if (!IsLoggedIn) // Should always be true due to CanExecute
            {
                 CurrentPageViewModel = _loginViewModel;
            }
        }
    }
}
