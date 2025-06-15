using DigitalLibraryWpf.Services;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Input;

namespace DigitalLibraryWpf.ViewModels
{
    public class LoginViewModel : BaseViewModel
    {
        private readonly ApiService _apiService;
        // private readonly CredentialsManager _credentialsManager; // If using separate manager
        private readonly Action _onLoginSuccess; // Callback to notify MainViewModel

        private string _username = string.Empty;
        public string Username
        {
            get => _username;
            set => SetField(ref _username, value);
        }

        private string _password = string.Empty;
        public string Password // PasswordBox updates this via code-behind
        {
            get => _password;
            set => SetField(ref _password, value);
        }

        private string _errorMessage = string.Empty;
        public string ErrorMessage
        {
            get => _errorMessage;
            set => SetField(ref _errorMessage, value);
        }

        private bool _isLoggingIn;
        public bool IsLoggingIn
        {
            get => _isLoggingIn;
            set => SetField(ref _isLoggingIn, value);
        }

        private bool _rememberMe;
        public bool RememberMe
        {
            get => _rememberMe;
            set
            {
                if (SetField(ref _rememberMe, value))
                {
                    if (!_rememberMe) // If unchecked
                    {
                        // Optionally clear password field if it was from remembered credentials
                        // Password = string.Empty; // This might be too aggressive if user is just editing
                        // PasswordBoxClearRequested?.Invoke(this, EventArgs.Empty);
                    }
                }
            }
        }

        public event EventHandler? PasswordBoxClearRequested;


        public ICommand LoginCommand { get; }

        public LoginViewModel(ApiService apiService, Action onLoginSuccess)
        {
            _apiService = apiService;
            _onLoginSuccess = onLoginSuccess;
            // _credentialsManager = new CredentialsManager(); // If using separate manager

            LoadCredentials();

            LoginCommand = new RelayCommand(async _ => await ExecuteLoginAsync(), _ => CanLogin());
        }

        private bool CanLogin()
        {
            return !string.IsNullOrWhiteSpace(Username) && 
                   !string.IsNullOrWhiteSpace(Password) &&
                   !IsLoggingIn;
        }

        private async Task ExecuteLoginAsync()
        {
            IsLoggingIn = true;
            ErrorMessage = string.Empty;
            CommandManager.InvalidateRequerySuggested(); // To update CanExecute

            var (apiSuccess, message) = await _apiService.LoginAsync(Username, Password);

            if (apiSuccess)
            {
                if (RememberMe)
                {
                    CredentialsManager.SaveCredentials(Username, Password, true);
                }
                else
                {
                    CredentialsManager.ClearCredentials();
                }
                _onLoginSuccess?.Invoke();
            }
            else
            {
                ErrorMessage = message ?? "Login failed. Please try again.";
                // Do not clear RememberMe or saved credentials on failed login attempt
            }
            IsLoggingIn = false;
            CommandManager.InvalidateRequerySuggested();
        }

        private void LoadCredentials()
        {
            var (loadedUsername, loadedPassword, loadedRememberMe) = CredentialsManager.LoadCredentials();
            if (loadedRememberMe)
            {
                Username = loadedUsername ?? string.Empty;
                Password = loadedPassword ?? string.Empty; // This will be set in PasswordBox by View's code-behind
                RememberMe = true;
            }
            else
            {
                // If not set to remember, or no credentials, ensure fields are clear or default
                Username = loadedUsername ?? string.Empty; // Keep username if it was saved without "RememberMe" (e.g. previous version)
                Password = string.Empty;
                RememberMe = false;
            }
        }

        // This method could be called if the user explicitly wants to forget credentials
        // or when RememberMe is unchecked.
        public void ForgetCredentials()
        {
            CredentialsManager.ClearCredentials();
            Password = string.Empty; // Clear password from VM
            RememberMe = false; // Ensure checkbox is unchecked
            PasswordBoxClearRequested?.Invoke(this, EventArgs.Empty); // Request UI to clear password box
        }
    }
}
