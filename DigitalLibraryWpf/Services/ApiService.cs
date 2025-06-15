using DigitalLibraryWpf.Models;
using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using System.Windows;

namespace DigitalLibraryWpf.Services
{
    public class ApiService
    {
        private HttpClient _httpClient;
        private string _baseApiUrl = "http://127.0.0.1:9000/api";
        private string? _authToken;

        public event Action? AuthTokenChanged;

        public bool IsUserLoggedIn => !string.IsNullOrEmpty(_authToken);

        private readonly JsonSerializerOptions _jsonSerializerOptions = new JsonSerializerOptions
        {
            PropertyNameCaseInsensitive = true,
        };

        public ApiService()
        {
            _httpClient = new HttpClient();
            // SetBaseUrl will initialize _httpClient.BaseAddress
        }

        public void SetBaseUrl(string serverUrl)
        {
            if (string.IsNullOrWhiteSpace(serverUrl))
            {
                MessageBox.Show("Server URL cannot be empty.", "Configuration Error", MessageBoxButton.OK, MessageBoxImage.Error);
                _baseApiUrl = "http://127.0.0.1:9000/api"; // Revert to a safe default
            }
            else if (serverUrl.EndsWith("/api"))
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

            try
            {
                _httpClient.BaseAddress = new Uri(_baseApiUrl + "/");
                MessageBox.Show($"API Base URL set to: {_httpClient.BaseAddress}", "API Service", MessageBoxButton.OK, MessageBoxImage.Information);
            }
            catch (UriFormatException ex)
            {
                MessageBox.Show($"Invalid Server URL format: {ex.Message}. Reverting to default.", "Configuration Error", MessageBoxButton.OK, MessageBoxImage.Error);
                _baseApiUrl = "http://127.0.0.1:9000/api";
                _httpClient.BaseAddress = new Uri(_baseApiUrl + "/");
            }
        }

        private void SetAuthTokenInternal(string? token)
        {
            _authToken = token;
            _httpClient.DefaultRequestHeaders.Authorization =
                !string.IsNullOrEmpty(_authToken)
                ? new AuthenticationHeaderValue("Bearer", _authToken)
                : null;
            AuthTokenChanged?.Invoke();
        }

        public async Task<(bool Success, string? ErrorMessage)> LoginAsync(string username, string password)
        {
            if (_httpClient.BaseAddress == null)
            {
                return (false, "API Base URL is not set. Please configure it first.");
            }
            try
            {
                var content = new FormUrlEncodedContent(new[]
                {
                    new KeyValuePair<string, string>("username", username),
                    new KeyValuePair<string, string>("password", password)
                });

                HttpResponseMessage response = await _httpClient.PostAsync("token", content);

                if (response.IsSuccessStatusCode)
                {
                    var tokenResponse = await response.Content.ReadFromJsonAsync<Token>(_jsonSerializerOptions);
                    if (tokenResponse != null && !string.IsNullOrEmpty(tokenResponse.AccessToken))
                    {
                        SetAuthTokenInternal(tokenResponse.AccessToken);
                        return (true, null);
                    }
                    return (false, "Received an empty or invalid token from the server.");
                }
                else
                {
                    string errorContent = await response.Content.ReadAsStringAsync();
                    string errorMessage = $"Login failed: {response.StatusCode}";
                     try
                    {
                        var errorDetail = JsonSerializer.Deserialize<Dictionary<string, string>>(errorContent);
                        if (errorDetail != null && errorDetail.TryGetValue("detail", out var detail))
                        {
                            errorMessage += $"\nDetails: {detail}";
                        } else {
                             errorMessage += $"\nResponse: {errorContent}";
                        }
                    }
                    catch { errorMessage += $"\nResponse: {errorContent}"; }
                    return (false, errorMessage);
                }
            }
            catch (HttpRequestException ex)
            {
                return (false, $"Network error during login: {ex.Message}");
            }
            catch (JsonException ex)
            {
                return (false, $"Error deserializing login response: {ex.Message}");
            }
            catch (Exception ex)
            {
                return (false, $"An unexpected error occurred during login: {ex.Message}");
            }
        }

        public void Logout()
        {
            SetAuthTokenInternal(null);
        }

        private async Task<T?> HandleResponse<T>(HttpResponseMessage response, string operationName)
        {
            if (response.IsSuccessStatusCode)
            {
                if (response.Content.Headers.ContentLength == 0 || response.StatusCode == System.Net.HttpStatusCode.NoContent)
                {
                    return default;
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
                if (response.StatusCode == System.Net.HttpStatusCode.Unauthorized)
                {
                    // If unauthorized, clear token and notify for potential redirect to login
                    SetAuthTokenInternal(null);
                }
                return default;
            }
        }

        public async Task<List<Book>?> GetBooksAsync()
        {
            if (_httpClient.BaseAddress == null) { MessageBox.Show("API URL not set."); return null; }
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
            if (!IsUserLoggedIn)
            {
                MessageBox.Show("You must be logged in to create a book.", "Authentication Required", MessageBoxButton.OK, MessageBoxImage.Warning);
                return null;
            }
            if (_httpClient.BaseAddress == null) { MessageBox.Show("API URL not set."); return null; }
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
            if (!IsUserLoggedIn)
            {
                MessageBox.Show("You must be logged in to delete a book.", "Authentication Required", MessageBoxButton.OK, MessageBoxImage.Warning);
                return false;
            }
            if (_httpClient.BaseAddress == null) { MessageBox.Show("API URL not set."); return false; }
            try
            {
                HttpResponseMessage response = await _httpClient.DeleteAsync($"books/{bookId}");
                if (response.IsSuccessStatusCode)
                {
                    return true;
                }
                await HandleResponse<object>(response, "deleting book");
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
