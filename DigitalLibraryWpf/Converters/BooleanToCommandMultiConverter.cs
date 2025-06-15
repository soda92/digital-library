using System;
using System.Globalization;
using System.Windows.Data;
using System.Windows.Input;

namespace DigitalLibraryWpf.Converters
{
    public class BooleanToCommandMultiConverter : IMultiValueConverter
    {
        public object Convert(object[] values, Type targetType, object parameter, CultureInfo culture)
        {
            if (values == null || values.Length < 3)
                return Binding.DoNothing; // Or null, or a default command

            if (values[0] is bool isLoggedIn && values[1] is ICommand commandIfFalse && values[2] is ICommand commandIfTrue)
            {
                return isLoggedIn ? commandIfTrue : commandIfFalse;
            }

            return Binding.DoNothing; // Or handle error appropriately
        }

        public object[] ConvertBack(object value, Type[] targetTypes, object parameter, CultureInfo culture)
        {
            throw new NotImplementedException();
        }
    }
}
