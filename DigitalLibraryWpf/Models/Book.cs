using System.Text.Json.Serialization;
using System.ComponentModel;
using System;

namespace DigitalLibraryWpf.Models
{
    public class Book : INotifyPropertyChanged
    {
        private int _id;
        [JsonPropertyName("id")]
        public int Id
        {
            get => _id;
            set { _id = value; OnPropertyChanged(nameof(Id)); }
        }

        private string _title = string.Empty;
        [JsonPropertyName("title")]
        public string Title
        {
            get => _title;
            set { _title = value; OnPropertyChanged(nameof(Title)); }
        }

        private string _author = string.Empty;
        [JsonPropertyName("author")]
        public string Author
        {
            get => _author;
            set { _author = value; OnPropertyChanged(nameof(Author)); }
        }

        private string _isbn = string.Empty;
        [JsonPropertyName("isbn")]
        public string Isbn
        {
            get => _isbn;
            set { _isbn = value; OnPropertyChanged(nameof(Isbn)); }
        }

        private bool _isBorrowed;
        [JsonPropertyName("is_borrowed")]
        public bool IsBorrowed
        {
            get => _isBorrowed;
            set { _isBorrowed = value; OnPropertyChanged(nameof(IsBorrowed)); }
        }

        private DateTime? _dueDate;
        [JsonPropertyName("due_date")]
        public DateTime? DueDate
        {
            get => _dueDate;
            set { _dueDate = value; OnPropertyChanged(nameof(DueDate)); }
        }

        private int? _borrowerId;
        [JsonPropertyName("borrower_id")]
        public int? BorrowerId
        {
            get => _borrowerId;
            set { _borrowerId = value; OnPropertyChanged(nameof(BorrowerId)); }
        }

        private string? _borrowerUsername;
        [JsonPropertyName("borrower_username")]
        public string? BorrowerUsername
        {
            get => _borrowerUsername;
            set { _borrowerUsername = value; OnPropertyChanged(nameof(BorrowerUsername)); }
        }

        public event PropertyChangedEventHandler? PropertyChanged;
        protected virtual void OnPropertyChanged(string propertyName)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }

        public override string ToString()
        {
            return $"{Title} by {Author} (ISBN: {Isbn}){(IsBorrowed ? $" - Borrowed by: {BorrowerUsername ?? "N/A"}, Due: {DueDate?.ToShortDateString() ?? "N/A"}" : "")}";
        }
    }

    // Model for creating a book, matching BookCreate Pydantic model
    public class BookCreateDto
    {
        [JsonPropertyName("title")]
        public string Title { get; set; } = string.Empty;

        [JsonPropertyName("author")]
        public string Author { get; set; } = string.Empty;

        [JsonPropertyName("isbn")]
        public string Isbn { get; set; } = string.Empty;
    }

     public class Token
    {
        [JsonPropertyName("access_token")]
        public string AccessToken { get; set; } = string.Empty;

        [JsonPropertyName("token_type")]
        public string TokenType { get; set; } = string.Empty;
    }
}
