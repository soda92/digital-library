using DigitalLibraryWpf.ViewModels;
using System.Windows.Controls;
using System.Windows;

namespace DigitalLibraryWpf.Views
{
    public partial class LoginView : UserControl
    {
        public LoginView()
        {
            InitializeComponent();
            this.DataContextChanged += OnDataContextChanged;
        }

        private void OnDataContextChanged(object sender, DependencyPropertyChangedEventArgs e)
        {
            if (e.OldValue is LoginViewModel oldViewModel)
            {
                oldViewModel.PasswordBoxClearRequested -= ViewModel_PasswordBoxClearRequested;
            }
            if (e.NewValue is LoginViewModel viewModel)
            {
                // If ViewModel has a pre-loaded password and RememberMe was true, set it in PasswordBox.
                // This assumes LoginViewModel loads credentials in its constructor or an init method.
                if (viewModel.RememberMe && !string.IsNullOrEmpty(viewModel.Password))
                {
                    PasswordBox.Password = viewModel.Password;
                }
                viewModel.PasswordBoxClearRequested += ViewModel_PasswordBoxClearRequested;
            }
        }
        private void ViewModel_PasswordBoxClearRequested(object? sender, EventArgs e)
        {
            PasswordBox.Password = string.Empty; // Clear the password box
        }

        // Helper to update ViewModel's Password property from PasswordBox
        private void PasswordBox_PasswordChanged(object sender, RoutedEventArgs e)
        {
            if (this.DataContext is LoginViewModel viewModel && sender is PasswordBox passwordBox)
            {
                viewModel.Password = passwordBox.Password;
            }
        }
    }
}
