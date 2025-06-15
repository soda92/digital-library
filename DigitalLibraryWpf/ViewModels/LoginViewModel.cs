using DigitalLibraryWpf.Services;
using System.Threading.Tasks;
using System.Windows.Input;

namespace DigitalLibraryWpf.ViewModels
{
    public class LoginViewModel : BaseViewModel
    {
        private readonly ApiService _apiService;
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

        public ICommand LoginCommand { get; }

        public LoginViewModel(ApiService apiService, Action onLoginSuccess)
        {
            _apiService = apiService;
            _onLoginSuccess = onLoginSuccess;
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

            var (success, message) = await _apiService.LoginAsync(Username, Password);

            if (success)
            {
                _onLoginSuccess?.Invoke();
            }
            else
            {
                ErrorMessage = message ?? "Login failed. Please try again.";
            }
            IsLoggingIn = false;
            CommandManager.InvalidateRequerySuggested();
        }
    }
}
