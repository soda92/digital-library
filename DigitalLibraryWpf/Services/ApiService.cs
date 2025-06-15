using DigitalLibraryWpf.Models;
using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Net.Http.Json; // Requires System.Net.Http.Json NuGet package if not implicitly available
using System.Text.Json;
using System.Threading.Tasks;
using System.Windows; // For MessageBox

namespace DigitalLibraryWpf.Services
{
    public class ApiService
    {
        private HttpClient _httpClient;
        private string _baseApiUrl = "http://localhost:9000/api"; // Default, will be appended with /api
        private string? _authToken;

        private readonly JsonSerializerOptions _jsonSerializerOptions = new JsonSerializerOptions
        {
            PropertyNameCaseInsensitive = true,
            // Add any other converters or options if needed
        };
        
        public ApiService()
        {
            _httpClient = new HttpClient();
        }

        public void SetBaseUrl(string serverUrl)
        {
            if (string.IsNullOrWhiteSpace(serverUrl))
            {
                MessageBox.Show("Server URL cannot be empty.", "Configuration Error", MessageBoxButton.OK, MessageBoxImage.Error);
                return;
            }
            // Ensure it ends with /api
            if (serverUrl.EndsWith("/api"))
            {
                 _baseApiUrl = serverUrl;
            }
            else if (serverUrl.EndsWith("/"))
            {
                _baseApiUrl = serverUrl + "api";
            }
            else
            {
                _baseApiUrl = serverUrl + "/api";
            }
            // Test with a simple request or just update the base address
            try
            {
                _httpClient.BaseAddress = new Uri(_baseApiUrl + "/"); // Trailing slash for proper relative URI resolution
                 MessageBox.Show($"API Base URL set to: {_httpClient.BaseAddress}", "API Service", MessageBoxButton.OK, MessageBoxImage.Information);
            }
            catch (UriFormatException ex)
            {
                 MessageBox.Show($"Invalid Server URL format: {ex.Message}", "Configuration Error", MessageBoxButton.OK, MessageBoxImage.Error);
                 _baseApiUrl = "http://localhost:9000/api"; // Revert to default or handle appropriately
                 _httpClient.BaseAddress = new Uri(_baseApiUrl + "/");
            }
        }

        public void SetAuthToken(string? token)
        {
            _authToken = token;
            _httpClient.DefaultRequestHeaders.Authorization =
                !string.IsNullOrEmpty(_authToken)
                ? new AuthenticationHeaderValue("Bearer", _authToken)
                : null;
        }

        private async Task<T?> HandleResponse<T>(HttpResponseMessage response, string operationName)
        {
            if (response.IsSuccessStatusCode)
            {
                if (response.Content.Headers.ContentLength == 0 || response.StatusCode == System.Net.HttpStatusCode.NoContent)
                {
                    return default; // For 204 No Content
                }
                try
                {
                    return await response.Content.ReadFromJsonAsync<T>(_jsonSerializerOptions);
                }
                catch (JsonException ex)
                {
                    MessageBox.Show($"Error deserializing {operationName} response: {ex.Message}", "API Error", MessageBoxButton.OK, MessageBoxImage.Error);
                    return default;
                }
            }
            else
            {
                string errorContent = await response.Content.ReadAsStringAsync();
                string errorMessage = $"Error {operationName}: {response.StatusCode}";
                if (!string.IsNullOrWhiteSpace(errorContent))
                {
                    try
                    {
                        // Try to parse FastAPI error detail
                        var errorDetail = JsonSerializer.Deserialize<Dictionary<string, string>>(errorContent);
                        if (errorDetail != null && errorDetail.TryGetValue("detail", out var detail))
                        {
                            errorMessage += $"\nDetails: {detail}";
                        }
                        else
                        {
                             errorMessage += $"\nResponse: {errorContent}";
                        }
                    }
                    catch
                    {
                        errorMessage += $"\nResponse: {errorContent}";
                    }
                }
                MessageBox.Show(errorMessage, "API Error", MessageBoxButton.OK, MessageBoxImage.Error);
                return default;
            }
        }


        public async Task<List<Book>?> GetBooksAsync()
        {
            try
            {
                HttpResponseMessage response = await _httpClient.GetAsync("books/");
                return await HandleResponse<List<Book>>(response, "fetching books");
            }
            catch (HttpRequestException ex)
            {
                MessageBox.Show($"Network error fetching books: {ex.Message}", "API Error", MessageBoxButton.OK, MessageBoxImage.Error);
                return null;
            }
        }

        public async Task<Book?> CreateBookAsync(BookCreateDto newBook)
        {
             if (string.IsNullOrEmpty(_authToken))
            {
                MessageBox.Show("Authentication token is not set. Please set it to create a book.", "Auth Error", MessageBoxButton.OK, MessageBoxImage.Warning);
                return null;
            }
            try
            {
                HttpResponseMessage response = await _httpClient.PostAsJsonAsync("books/", newBook, _jsonSerializerOptions);
                return await HandleResponse<Book>(response, "creating book");
            }
            catch (HttpRequestException ex)
            {
                MessageBox.Show($"Network error creating book: {ex.Message}", "API Error", MessageBoxButton.OK, MessageBoxImage.Error);
                return null;
            }
        }

        public async Task<bool> DeleteBookAsync(int bookId)
        {
            // Note: The current FastAPI delete_book endpoint does not require authentication.
            // If it's updated to require auth, this token will be sent.
            // if (string.IsNullOrEmpty(_authToken))
            // {
            //     MessageBox.Show("Authentication token is not set. Please set it to delete a book if API requires it.", "Auth Info", MessageBoxButton.OK, MessageBoxImage.Information);
            //     // Depending on API, you might want to return false or proceed if API allows anonymous delete
            // }
            try
            {
                HttpResponseMessage response = await _httpClient.DeleteAsync($"books/{bookId}");
                if (response.IsSuccessStatusCode)
                {
                    return true;
                }
                await HandleResponse<object>(response, "deleting book"); // To show error message
                return false;
            }
            catch (HttpRequestException ex)
            {
                MessageBox.Show($"Network error deleting book: {ex.Message}", "API Error", MessageBoxButton.OK, MessageBoxImage.Error);
                return false;
            }
        }
    }
}
