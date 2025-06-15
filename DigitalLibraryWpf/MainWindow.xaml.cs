using System.Windows;

namespace DigitalLibraryWpf
{
    public partial class MainWindow : Window
    {
        public MainWindow()
        {
            InitializeComponent();
            // DataContext is set in XAML, but could also be set here:
             this.DataContext = new ViewModels.MainViewModel();
        }
    }
}
